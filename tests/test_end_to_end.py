"""Isolated service and workflow checks for the Hostel Management System."""

import csv
import sqlite3
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import database
from analytics.dashboard_analytics import get_dashboard_statistics
from analytics.satisfaction_analysis import get_satisfaction_analysis
from services import (
    attendance_service,
    auth_service,
    complaint_service,
    feedback_service,
    fee_service,
    notification_service,
    quality_service,
    room_service,
    student_service,
)
from utils.authorization import AuthorizationError, issue_session, revoke_session
from utils.security import hash_password


class _Value:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value

    def delete(self, *_args):
        self.value = ""

    def select(self):
        self.value = 1

    def deselect(self):
        self.value = 0

    def configure(self, **_kwargs):
        pass


class HostelWorkflowTests(unittest.TestCase):
    """Each test gets a fresh database and never reads or writes the user DB."""

    def setUp(self):
        self.original_database_path = database.DATABASE_PATH
        self.db_path = Path(__file__).resolve().parents[1] / f".qa-{uuid4().hex}.sqlite"
        database.DATABASE_PATH = self.db_path
        database.initialize_database()

        shared_hash = hash_password("SecurePass123")
        connection = database.get_connection()
        connection.executemany(
            "INSERT INTO users (username, email, password_hash, role, full_name, phone) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("admin", "admin@hostel.test", shared_hash, "admin", "Hostel Admin", "9876543210"),
                ("student1", "s1@hostel.test", shared_hash, "student", "Student One", "9876543211"),
                ("student2", "s2@hostel.test", shared_hash, "student", "Student Two", "9876543212"),
            ],
        )
        connection.executemany(
            "INSERT INTO students (student_id, name, email, phone, course,year, status) "
            "VALUES (?, ?, ?, ?, ?, ?, 'Active')",
            [
                ("STU001", "Student One", "s1@hostel.test", "9876543211", "Computer Science", 2),
                ("STU002", "Student Two", "s2@hostel.test", "9876543212", "Biology", 1),
            ],
        )
        connection.commit()
        self.ids = {
            username: connection.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()[0]
            for username in ("admin", "student1", "student2")
        }
        self.student_db_ids = {
            student_id: connection.execute("SELECT id FROM students WHERE student_id = ?", (student_id,)).fetchone()[0]
            for student_id in ("STU001", "STU002")
        }
        connection.close()

        self.admin = {"id": self.ids["admin"], "session_token": issue_session(self.ids["admin"])}
        self.student1 = {"id": self.ids["student1"], "session_token": issue_session(self.ids["student1"])}
        self.student2 = {"id": self.ids["student2"], "session_token": issue_session(self.ids["student2"])}

    def tearDown(self):
        for actor in (self.admin, self.student1, self.student2):
            revoke_session(actor.get("session_token"))
        database.DATABASE_PATH = self.original_database_path
        for suffix in ("", "-wal", "-shm"):
            path = Path(str(self.db_path) + suffix)
            if path.exists():
                path.unlink()

    def _student(self, student_id):
        return student_service.get_student(student_id, actor=self.admin)

    def test_authentication_authorization_and_student_crud(self):
        ok, actor = auth_service.login_user("admin", "SecurePass123")
        self.assertTrue(ok)
        self.assertEqual(actor["role"], "admin")
        self.assertFalse(auth_service.login_user("admin", "incorrect")[0])
        self.assertFalse(auth_service.login_user("missing", "incorrect")[0])
        revoke_session(actor["session_token"])

        forged_role = dict(self.student1, role="admin")
        with self.assertRaises(AuthorizationError):
            student_service.get_all_students(actor=forged_role)
        with self.assertRaises(AuthorizationError):
            student_service.add_student("STU999", "Not Allowed", actor=self.student1)
        with self.assertRaises(AuthorizationError):
            student_service.get_student("STU001", actor=None)

        ok, _ = student_service.add_student(
            "STU003", "New Student", email="new@hostel.test", phone="9876543213",
            course="Physics", year="3", actor=self.admin,
        )
        self.assertTrue(ok)
        self.assertFalse(student_service.add_student(
            "STU004", "Duplicate Email", email="NEW@HOSTEL.TEST", actor=self.admin,
        )[0])
        student = self._student("STU003")
        changed = {key: student.get(key) for key in student_service.STUDENT_COLUMNS}
        changed["name"] = "Updated Student"
        changed["year"] = 4
        self.assertTrue(student_service.update_student("STU003", changed, actor=self.admin)[0])
        self.assertEqual(self._student("STU003")["name"], "Updated Student")
        self.assertTrue(student_service.delete_student("STU003", actor=self.admin)[0])
        self.assertFalse(student_service.delete_student("STU001", actor=self.admin)[0])
        with self.assertRaises(ValueError):
            student_service.add_student("BAD ID!", "Invalid", actor=self.admin)

        # Student names are required and cannot be blank.
        with self.assertRaises(ValueError):
            student_service.add_student(
                "STU005", "", actor=self.admin,
            )

        # The year field must contain an integer in the allowed range.
        with self.assertRaises(ValueError):
            student_service.add_student(
                "STU006", "Invalid Year", year="abc", actor=self.admin,
            )

    def test_room_capacity_allocation_and_student_scope(self):
        self.assertTrue(room_service.add_room("A-101", 1, 1, actor=self.admin, room_type="Single")[0])
        self.assertTrue(room_service.add_room("A-102", 1, 2, actor=self.admin)[0])
        with self.assertRaises(AuthorizationError):
            room_service.add_room("A-103", 1, 1, actor=self.student1)

        self.assertTrue(room_service.allocate_room("STU001", "A-101", actor=self.admin)[0])
        self.assertFalse(room_service.allocate_room("STU002", "A-101", actor=self.admin)[0])
        self.assertEqual(room_service.get_room("A-101", actor=self.admin)[4:6], (1, 0))
        self.assertFalse(room_service.delete_room("A-101", actor=self.admin)[0])
        self.assertEqual(len(room_service.get_allocations(actor=self.student1)), 1)
        self.assertEqual(room_service.get_allocations(actor=self.student2), [])
        with self.assertRaises(AuthorizationError):
            room_service.allocate_room("STU002", "A-102", actor=self.student1)

        self.assertTrue(room_service.deallocate_room("STU001", actor=self.admin)[0])
        self.assertEqual(room_service.get_room("A-101", actor=self.admin)[4], 0)
        # Historical allocations remain for audit purposes, so safe deletestill refuses.
        self.assertFalse(room_service.delete_room("A-101", actor=self.admin)[0])

    def test_fees_partial_full_payment_and_student_data_isolation(self):
        self.assertTrue(fee_service.add_fee("STU001", "1000.00", "2026-12-01", actor=self.admin)[0])
        fee = fee_service.get_all_fees(actor=self.admin)[0]
        fee_id = fee[0]
        self.assertEqual(len(fee_service.get_all_fees(actor=self.student1)), 1)
        self.assertEqual(fee_service.get_all_fees(actor=self.student2), [])
        with self.assertRaises(AuthorizationError):
            fee_service.make_payment(fee_id, 10, "Cash", actor=self.student1)

        self.assertTrue(fee_service.make_payment(fee_id, 400, "UPI", "REC-001", actor=self.admin)[0])
        self.assertEqual(fee_service.get_fee_summary(fee_id, actor=self.student1), (1000, 400, 600))
        self.assertFalse(fee_service.make_payment(fee_id, 601, "Cash", actor=self.admin)[0])
        self.assertTrue(fee_service.make_payment(fee_id, 600, "Bank Transfer", "REC-002", actor=self.admin)[0])
        self.assertEqual(fee_service.get_fee(fee_id, actor=self.student1)[4], "Paid")
        self.assertIsNone(fee_service.get_fee(fee_id, actor=self.student2))
        self.assertFalse(fee_service.make_payment(fee_id, 1, "Cash", actor=self.admin)[0])
        self.assertTrue(fee_service.add_fee("STU002", 25, "2026-12-10", actor=self.admin)[0])
        fee2_id = fee_service.get_all_fees(actor=self.admin)[0][0]
        self.assertFalse(fee_service.make_payment(fee2_id, 5, "Cash", "REC-001", actor=self.admin)[0])
        self.assertFalse(fee_service.add_fee("STU001", -1, "bad-date", actor=self.admin)[0])

    def test_complaint_attendance_and_feedback_workflows_are_scoped(self):
        ok, _ = complaint_service.add_complaint(
            "STU001", "Maintenance", "Leaking tap", priority="High", actor=self.student1,
        )
        self.assertTrue(ok)
        complaint_id = complaint_service.get_all_complaints(actor=self.admin)[0][0]
        with self.assertRaises(AuthorizationError):
            complaint_service.add_complaint("STU002", "Noise", "Other student's report", actor=self.student1)
        self.assertEqual(len(complaint_service.get_all_complaints(actor=self.student1)), 1)
        self.assertEqual(complaint_service.get_all_complaints(actor=self.student2), [])
        self.assertIsNone(complaint_service.get_complaint(complaint_id, actor=self.student2))
        self.assertTrue(complaint_service.assign_complaint(complaint_id, "Maintenance Staff", actor=self.admin)[0])
        self.assertTrue(complaint_service.resolve_complaint(complaint_id, "Tap replaced", actor=self.admin)[0])
        self.assertEqual(complaint_service.get_complaint(complaint_id, actor=self.student1)[5], "Resolved")

        self.assertTrue(attendance_service.mark_entry("STU001", actor=self.admin)[0])
        self.assertFalse(attendance_service.mark_entry("STU001", actor=self.admin)[0])
        with self.assertRaises(AuthorizationError):
            attendance_service.mark_entry("STU002", actor=self.student1)
        self.assertEqual(len(attendance_service.get_today_attendance(actor=self.student1)), 1)
        self.assertEqual(attendance_service.get_today_attendance(actor=self.student2), [])
        self.assertTrue(attendance_service.mark_exit("STU001", actor=self.admin)[0])
        self.assertFalse(attendance_service.mark_exit("STU001", actor=self.admin)[0])

        ratings = [4] * 8 + [5]
        self.assertTrue(feedback_service.add_feedback(
            "STU001", *ratings, comments="Good overall", evaluation_period="Monthly", actor=self.student1,
        )[0])
        self.assertFalse(feedback_service.add_feedback(
            "STU001", 6, *([4] * 7), 5, actor=self.student1,
        )[0])
        self.assertEqual(len(feedback_service.get_all_feedback(actor=self.student1)), 1)
        self.assertEqual(feedback_service.get_all_feedback(actor=self.student2), [])
        self.assertEqual(feedback_service.get_overall_satisfaction(actor=self.student1), 5.0)
        self.assertEqual(feedback_service.get_overall_satisfaction(actor=self.student2), 0)
        self.assertAlmostEqual(feedback_service.get_average_satisfaction(actor=self.admin)[-1], 5.0)
        with self.assertRaises(AuthorizationError):
            feedback_service.get_average_satisfaction(actor=self.student1)

    def test_notifications_ownership_preferences_and_announcements(self):
        self.assertTrue(notification_service.create_notification(
            self.ids["student1"], "Notice", "Please visit the office.", actor=self.admin,
        )[0])
        n1 = notification_service.get_user_notifications(self.ids["student1"], actor=self.student1)[0][0]
        self.assertEqual(notification_service.get_user_notifications(self.ids["student2"], actor=self.student2), [])
        with self.assertRaises(AuthorizationError):
            notification_service.get_user_notifications(self.ids["student1"], actor=self.student2)
        self.assertEqual(notification_service.get_unread_count(self.ids["student1"], actor=self.student1), 1)
        self.assertTrue(notification_service.mark_notification_as_read(n1,actor=self.student1)[0])
        self.assertEqual(notification_service.get_unread_count(self.ids["student1"], actor=self.student1), 0)
        with self.assertRaises(AuthorizationError):
            notification_service.delete_notification(n1, actor=self.student1)

        connection = database.get_connection()
        connection.execute(
            "INSERT INTO user_settings (user_id, theme, notifications_enabled) VALUES (?, 'dark', 0)",
            (self.ids["student2"],),
        )
        connection.commit()
        connection.close()
        sent, _ = notification_service.create_announcement("Water maintenance", "Tank cleaning tomorrow.", actor=self.admin)
        self.assertTrue(sent)
        self.assertGreaterEqual(notification_service.get_unread_count(self.ids["student1"], actor=self.student1), 1)
        self.assertEqual(notification_service.get_user_notifications(self.ids["student2"], actor=self.student2), [])
        self.assertFalse(notification_service.create_notification(999999, "Missing", "No account", actor=self.admin)[0])

    def test_analytics_quality_recommendations_and_database_integrity(self):
        empty_stats = get_dashboard_statistics(actor=self.admin)
        self.assertEqual(empty_stats["total_students"], 2)
        self.assertIsNone(empty_stats["average_satisfaction"])
        self.assertIsNone(empty_stats["fee_payment_completion_rate"])
        recommendations = quality_service.get_quality_recommendations(actor=self.admin)
        self.assertTrue(recommendations)
        self.assertTrue(all(item["score"] is None and item["status"] == "No feedback yet" for item in recommendations))
        with self.assertRaises(AuthorizationError):
            quality_service.get_quality_recommendations(actor=self.student1)

        connection = database.get_connection()
        self.assertEqual(connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        with self.assertRaises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO fees (student_id, amount, due_date) VALUES (999999, 1, '2026-12-01')")
        connection.rollback()
        self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
        connection.close()

    def test_main_command_uses_existing_project_environment(self):
        import main

        project_root = Path(main.__file__).resolve().parent
        environment = project_root / ".venv"
        expected_python = environment / "Scripts" / "python.exe"
        if not expected_python.is_file():
            self.skipTest("Windows project virtual environment is not present")

        with patch.object(main.sys, "prefix", str(project_root)), \
             patch.object(main.subprocess, "run", return_value=SimpleNamespace(returncode=0)) as run:
            with self.assertRaises(SystemExit) as exit_context:
                main._relaunch_with_project_environment()

        self.assertEqual(exit_context.exception.code, 0)
        self.assertEqual(Path(run.call_args.args[0][0]), expected_python)
        self.assertEqual(run.call_args.kwargs["cwd"], project_root)

    def test_main_command_does_not_relaunch_inside_project_environment(self):
        import main

        project_root = Path(main.__file__).resolve().parent
        with patch.object(main.sys, "prefix", str(project_root / ".venv")), \
             patch.object(main.subprocess, "run") as run:
            self.assertIsNone(main._relaunch_with_project_environment())
        run.assert_not_called()

    def test_profile_settings_persistence_and_password_change(self):
        from views.profile import ProfileWindow
        from views.settings import SettingsWindow

        parent = SimpleNamespace(user=dict(self.student1), theme_calls=0)
        parent.apply_visual_theme = lambda: setattr(parent, "theme_calls",parent.theme_calls + 1)
        profile = SimpleNamespace(
            user_data=dict(self.student1), student_db_id=self.student_db_ids["STU001"], parent=parent,
            email_entry=_Value("updated@hostel.test"), name_entry=_Value("Student One Updated"),
            phone_entry=_Value("9876543299"), name_summary=_Value(), email_summary=_Value(), phone_summary=_Value(),
            student_contact_summary=_Value(), current_password=_Value("SecurePass123"),
            new_password=_Value("ChangedPass123"), confirm_password=_Value("ChangedPass123"),
        )
        with patch("views.profile.messagebox.showinfo"):
            ProfileWindow.update_personal_information(profile)
        self.assertEqual(profile.user_data["email"], "updated@hostel.test")
        connection = database.get_connection()
        self.assertEqual(connection.execute("SELECT email FROM users WHERE id = ?", (self.ids["student1"],)).fetchone()[0], "updated@hostel.test")
        self.assertEqual(connection.execute("SELECT email FROM students WHERE id = ?", (self.student_db_ids["STU001"],)).fetchone()[0], "updated@hostel.test")
        connection.close()

        profile.current_password = _Value("SecurePass123")
        with patch("views.profile.messagebox.showinfo"):
            ProfileWindow.change_password(profile)
        self.assertTrue(auth_service.login_user("student1", "ChangedPass123")[0])

        settings = SimpleNamespace(
            user_data=dict(self.admin), parent=SimpleNamespace(apply_visual_theme=lambda: None),
            theme_menu=_Value("Dark"), notification_switch=_Value(0),
        )
        with patch("views.settings.messagebox.showinfo"):
            SettingsWindow.save_settings(settings)
        connection = database.get_connection()
        saved = connection.execute("SELECT theme, notifications_enabled FROM user_settings WHERE user_id = ?", (self.ids["admin"],)).fetchone()
        connection.close()
        self.assertEqual(saved, ("dark", 0))
        SettingsWindow.load_settings(settings)
        self.assertEqual(settings.theme_menu.get(), "Dark")
        self.assertEqual(settings.notification_switch.get(), 0)
        with patch("views.settings.messagebox.askyesno", return_value=True), \
             patch("views.settings.messagebox.showinfo"):
            SettingsWindow.reset_settings(settings)
        connection = database.get_connection()
        reset = connection.execute("SELECT theme, notifications_enabled FROM user_settings WHERE user_id = ?", (self.ids["admin"],)).fetchone()
        connection.close()
        self.assertEqual(reset, ("light", 1))

    def test_csv_and_pdf_exports(self):
        from views.reports import ReportsWindow

        csv_path = self.db_path.with_suffix(".csv")
        pdf_path = self.db_path.with_suffix(".pdf")
        report = SimpleNamespace(
            stats=get_dashboard_statistics(actor=self.admin),
            satisfaction=get_satisfaction_analysis(actor=self.admin),
            current_figure=None,
            get_satisfaction_status=lambda score: "No data" if score is None else "Good",
        )
        try:
            with patch("views.reports.filedialog.asksaveasfilename", return_value=str(csv_path)), \
                 patch("views.reports.messagebox.showinfo") as info:
                ReportsWindow.export_csv(report)
                self.assertTrue(csv_path.exists())
                self.assertGreater(csv_path.stat().st_size, 100)
                info.assert_called_once()
            with csv_path.open(newline="", encoding="utf-8") as exported:
                rows = list(csv.reader(exported))
            self.assertIn(["Total Students", "2"], rows)
            self.assertTrue(any(row[:1] == ["SATISFACTION REPORT"] for row in rows))

            with patch("views.reports.filedialog.asksaveasfilename", return_value=str(pdf_path)), \
                 patch("views.reports.messagebox.showinfo") as info:
                ReportsWindow.export_pdf(report)
                self.assertTrue(pdf_path.exists())
                self.assertGreater(pdf_path.stat().st_size, 500)
                info.assert_called_once()
            self.assertEqual(pdf_path.read_bytes()[:4], b"%PDF")
        finally:
            for path in (csv_path, pdf_path):
                if path.exists():
                    path.unlink()


if __name__ == "__main__":
    unittest.main()
    def test_dashboard_fee_analytics_with_multiple_payments(self):
        self.assertTrue(
            fee_service.add_fee("STU001", "1000.00", "2026-12-01", actor=self.admin)[0]
        )
        fee = fee_service.get_all_fees(actor=self.admin)[0]
        fee_id = fee[0]

        self.assertTrue(
            fee_service.make_payment(fee_id, 300, "UPI", "DASH-001", actor=self.admin)[0]
        )
        self.assertTrue(
            fee_service.make_payment(fee_id, 200, "Cash", "DASH-002", actor=self.admin)[0]
        )

        stats = get_dashboard_statistics(actor=self.admin)

        self.assertEqual(stats["total_fees_amount"], 1000)
        self.assertEqual(stats["collected_fees"], 500)
        self.assertEqual(stats["pending_fees"], 500)
        self.assertEqual(stats["fee_payment_completion_rate"], 50.0)

    def test_dashboard_fee_analytics_with_multiple_payments(self):
        self.assertTrue(
            fee_service.add_fee("STU001", "1000.00", "2026-12-01", actor=self.admin)[0]
        )
        fee = fee_service.get_all_fees(actor=self.admin)[0]
        fee_id = fee[0]

        self.assertTrue(
            fee_service.make_payment(
                fee_id, 300, "UPI", "DASH-001", actor=self.admin
            )[0]
        )
        self.assertTrue(
            fee_service.make_payment(
                fee_id, 200, "Cash", "DASH-002", actor=self.admin
            )[0]
        )

        stats = get_dashboard_statistics(actor=self.admin)

        self.assertEqual(stats["total_fees_amount"], 1000)
        self.assertEqual(stats["collected_fees"], 500)
        self.assertEqual(stats["pending_fees"], 500)
        self.assertEqual(stats["fee_payment_completion_rate"], 50.0)
    def test_dashboard_fee_analytics_aggregates_multiple_fees(self):
        self.assertTrue(
            fee_service.add_fee("STU001", "1000.00", "2026-12-01", actor=self.admin)[0]
        )
        self.assertTrue(
            fee_service.add_fee("STU002", "2000.00", "2026-12-10", actor=self.admin)[0]
        )

        fees = fee_service.get_all_fees(actor=self.admin)
        fee_ids = {fee[0] for fee in fees}

        self.assertEqual(len(fee_ids), 2)

        for fee_id in fee_ids:
            fee = fee_service.get_fee(fee_id, actor=self.admin)
            student_id = "STU001" if fee[1] == "STU001" else "STU002"
            payment = 400 if student_id == "STU001" else 500

            self.assertTrue(
                fee_service.make_payment(
                    fee_id, payment, "UPI", f"AGG-{student_id}", actor=self.admin
                )[0]
            )

        stats = get_dashboard_statistics(actor=self.admin)

        self.assertEqual(stats["total_fees_amount"], 3000)
        self.assertEqual(stats["collected_fees"], 900)
        self.assertEqual(stats["pending_fees"], 2100)
        self.assertEqual(stats["fee_payment_completion_rate"], 30.0)

    def test_dashboard_fee_analytics_isolates_student_data(self):
        self.assertTrue(
            fee_service.add_fee("STU001", "1000.00", "2026-12-01", actor=self.admin)[0]
        )
        self.assertTrue(
            fee_service.add_fee("STU002", "2000.00", "2026-12-10", actor=self.admin)[0]
        )

        fees1 = fee_service.get_all_fees(actor=self.student1)
        fees2 = fee_service.get_all_fees(actor=self.student2)

        self.assertEqual(len(fees1), 1)
        self.assertEqual(len(fees2), 1)

        self.assertTrue(
            fee_service.make_payment(
                fees1[0][0], 300, "UPI", "ISO-001", actor=self.admin
            )[0]
        )
        self.assertTrue(
            fee_service.make_payment(
                fees2[0][0], 500, "Cash", "ISO-002", actor=self.admin
            )[0]
        )

        stats1 = get_dashboard_statistics(actor=self.student1)
        stats2 = get_dashboard_statistics(actor=self.student2)

        self.assertEqual(stats1["total_fees_amount"], 1000)
        self.assertEqual(stats1["collected_fees"], 300)
        self.assertEqual(stats1["pending_fees"], 700)

        self.assertEqual(stats2["total_fees_amount"], 2000)
        self.assertEqual(stats2["collected_fees"], 500)
        self.assertEqual(stats2["pending_fees"], 1500)

    def test_dashboard_fee_analytics_with_no_fees(self):
        stats = get_dashboard_statistics(actor=self.admin)

        self.assertEqual(stats["total_fees_amount"], 0)
        self.assertEqual(stats["collected_fees"], 0)
        self.assertEqual(stats["pending_fees"], 0)
        self.assertIsNone(stats["fee_payment_completion_rate"])

    def test_dashboard_student_count_is_role_scoped(self):
        admin_stats = get_dashboard_statistics(actor=self.admin)
        student_stats = get_dashboard_statistics(actor=self.student1)

        self.assertEqual(admin_stats["total_students"], 2)
        self.assertEqual(student_stats["total_students"], 1)

        self.assertIsNone(student_stats["total_rooms"])
        self.assertIsNone(student_stats["total_beds"])
        self.assertIsNone(student_stats["occupied_beds"])
        self.assertIsNone(student_stats["available_beds"])
        self.assertIsNone(student_stats["occupancy_rate"])

    def test_dashboard_complaint_metrics_are_role_scoped(self):
        self.assertTrue(
            complaint_service.add_complaint(
                "STU001", "Wi-Fi", "Internet is slow", "High",
                actor=self.admin
            )[0]
        )
        self.assertTrue(
            complaint_service.add_complaint(
                "STU002", "Cleaning", "Room needs cleaning", "Medium",
                actor=self.admin
            )[0]
        )

        admin_stats = get_dashboard_statistics(actor=self.admin)
        student1_stats = get_dashboard_statistics(actor=self.student1)
        student2_stats = get_dashboard_statistics(actor=self.student2)

        self.assertEqual(admin_stats["total_complaints"], 2)
        self.assertEqual(student1_stats["total_complaints"], 1)
        self.assertEqual(student2_stats["total_complaints"], 1)

        self.assertEqual(admin_stats["pending_complaints"], 2)
        self.assertEqual(student1_stats["pending_complaints"], 1)
        self.assertEqual(student2_stats["pending_complaints"], 1)

    def test_dashboard_complaint_resolution_metrics(self):
        self.assertTrue(
            complaint_service.add_complaint(
                "STU001", "Wi-Fi", "Internet is slow", "High",
                actor=self.admin
            )[0]
        )
        self.assertTrue(
            complaint_service.add_complaint(
                "STU002", "Cleaning", "Room needs cleaning", "Medium",
                actor=self.admin
            )[0]
        )

        complaints = complaint_service.get_all_complaints(actor=self.admin)
        self.assertEqual(len(complaints), 2)

        complaint_id = complaints[0][0]
        self.assertTrue(
            complaint_service.update_complaint_status(
                complaint_id, "Resolved", actor=self.admin
            )[0]
        )

        stats = get_dashboard_statistics(actor=self.admin)

        self.assertEqual(stats["total_complaints"], 2)
        self.assertEqual(stats["pending_complaints"], 1)
        self.assertEqual(stats["resolved_complaints"], 1)
        self.assertEqual(stats["complaint_resolution_rate"], 50.0)

    def test_dashboard_satisfaction_metrics_are_role_scoped(self):
        self.assertTrue(
            feedback_service.submit_feedback(
                5, "Excellent hostel", actor=self.student1
            )[0]
        )
        self.assertTrue(
            feedback_service.submit_feedback(
                3, "Needs improvement", actor=self.student2
            )[0]
        )

        admin_stats = get_dashboard_statistics(actor=self.admin)
        student1_stats = get_dashboard_statistics(actor=self.student1)
        student2_stats = get_dashboard_statistics(actor=self.student2)

        self.assertEqual(admin_stats["feedback_count"], 2)
        self.assertEqual(admin_stats["average_satisfaction"], 4.0)
        self.assertEqual(student1_stats["average_satisfaction"], 5.0)
        self.assertEqual(student2_stats["average_satisfaction"], 3.0)

    def test_dashboard_recent_activity_is_isolated_by_student(self):
        self.assertTrue(
            complaint_service.add_complaint(
                "STU001", "Wi-Fi", "Internet is slow", "High",
                actor=self.admin
            )[0]
        )
        self.assertTrue(
            complaint_service.add_complaint(
                "STU002", "Cleaning", "Room needs cleaning", "Medium",
                actor=self.admin
            )[0]
        )

        self.assertTrue(
            fee_service.add_fee("STU001", "1000.00", "2026-12-01", actor=self.admin)[0]
        )
        self.assertTrue(
            fee_service.add_fee("STU002", "2000.00", "2026-12-10", actor=self.admin)[0]
        )

        fees1 = fee_service.get_all_fees(actor=self.student1)
        fees2 = fee_service.get_all_fees(actor=self.student2)

        self.assertTrue(
            fee_service.make_payment(
                fees1[0][0], 100, "UPI", "RECENT-001", actor=self.admin
            )[0]
        )
        self.assertTrue(
            fee_service.make_payment(
                fees2[0][0], 200, "Cash", "RECENT-002", actor=self.admin
            )[0]
        )

        admin_stats = get_dashboard_statistics(actor=self.admin)
        student1_stats = get_dashboard_statistics(actor=self.student1)
        student2_stats = get_dashboard_statistics(actor=self.student2)

        self.assertEqual(len(admin_stats["recent_complaints"]), 2)
        self.assertEqual(len(student1_stats["recent_complaints"]), 1)
        self.assertEqual(len(student2_stats["recent_complaints"]), 1)

        self.assertTrue(
            all(row[1] == "STU001" for row in student1_stats["recent_complaints"])
        )
        self.assertTrue(
            all(row[1] == "STU002" for row in student2_stats["recent_complaints"])
        )

        self.assertEqual(len(admin_stats["recent_payments"]), 2)
        self.assertEqual(len(student1_stats["recent_payments"]), 1)
        self.assertEqual(len(student2_stats["recent_payments"]), 1)

        self.assertTrue(
            all(row[1] == "STU001" for row in student1_stats["recent_payments"])
        )
        self.assertTrue(
            all(row[1] == "STU002" for row in student2_stats["recent_payments"])
        )

        self.assertEqual(student1_stats["recent_students"], [])
        self.assertEqual(student2_stats["recent_students"], [])

    def test_dashboard_recent_activity_is_limited_to_five_latest_records(self):
        for index in range(7):
            self.assertTrue(
                complaint_service.add_complaint(
                    "STU001",
                    "Wi-Fi",
                    f"Test complaint {index}",
                    "High",
                    actor=self.admin,
                )[0]
            )

        stats = get_dashboard_statistics(actor=self.admin)
        recent = stats["recent_complaints"]

        self.assertEqual(len(recent), 5)
        self.assertEqual(
            [row[0] for row in recent],
            sorted([row[0] for row in recent], reverse=True),
        )
