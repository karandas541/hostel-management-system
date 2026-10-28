"""Tests for Student Dashboard and Admin Credential Creation."""

import unittest
from pathlib import Path
from uuid import uuid4

import database
from services import auth_service, student_service, room_service, fee_service, complaint_service, attendance_service, notification_service
from utils.authorization import AuthorizationError, issue_session, revoke_session, resolve_student
from utils.security import hash_password


class StudentDashboardAndCredentialsTests(unittest.TestCase):
    def setUp(self):
        self.original_database_path = database.DATABASE_PATH
        self.db_path = Path(__file__).resolve().parents[1] / f".qa-stu-{uuid4().hex}.sqlite"
        database.DATABASE_PATH = self.db_path
        database.initialize_database()

        # Create Admin
        shared_hash = hash_password("AdminPass123")
        connection = database.get_connection()
        connection.execute(
            "INSERT INTO users (username, email, password_hash, role, full_name, phone) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("admin_test", "admin_test@hostel.org", shared_hash, "admin", "Super Admin", "9998887770"),
        )
        self.admin_user_id = connection.execute("SELECT id FROM users WHERE username = 'admin_test'").fetchone()[0]

        # Create 2 Students
        connection.execute(
            """INSERT INTO students (student_id, name, email, phone, course, branch, year, status, room_number, bed_number)
               VALUES ('STU901', 'Rahul Sharma', 'rahul@hostel.org', '9876543210', 'B.Tech', 'CSE', 3, 'Active', '101', 1)"""
        )
        connection.execute(
            """INSERT INTO students (student_id, name, email, phone, course, branch, year, status, room_number, bed_number)
               VALUES ('STU902', 'Aman Verma', 'aman@hostel.org', '9876543211', 'B.Tech', 'IT', 3, 'Active', '101', 2)"""
        )
        # Create Room
        connection.execute(
            """INSERT INTO rooms (room_number, floor, room_type, capacity, occupied_beds, status)
               VALUES ('101', 1, 'Double', 2, 2, 'Occupied')"""
        )
        r_id = connection.execute("SELECT id FROM rooms WHERE room_number = '101'").fetchone()[0]
        s1_id = connection.execute("SELECT id FROM students WHERE student_id = 'STU901'").fetchone()[0]
        s2_id = connection.execute("SELECT id FROM students WHERE student_id = 'STU902'").fetchone()[0]

        # Allocations
        connection.execute(
            "INSERT INTO room_allocations (student_id, room_id, bed_number) VALUES (?, ?, 1)",
            (s1_id, r_id),
        )
        connection.execute(
            "INSERT INTO room_allocations (student_id, room_id, bed_number) VALUES (?, ?, 2)",
            (s2_id, r_id),
        )

        # Fees
        connection.execute(
            "INSERT INTO fees (student_id, amount, due_date, status) VALUES (?, 30000.0, '2026-11-01', 'Pending')",
            (s1_id,),
        )
        f_id = connection.execute("SELECT id FROM fees WHERE student_id = ?", (s1_id,)).fetchone()[0]
        connection.execute(
            "INSERT INTO payments (fee_id, amount, payment_mode, payment_date, receipt_number) VALUES (?, 20000.0, 'UPI', '2026-10-25', 'REC-001')",
            (f_id,),
        )

        # Announcement
        connection.execute(
            "INSERT INTO announcements (title, message, created_by) VALUES ('Curfew Notice', 'Gate closes at 10 PM', ?)",
            (self.admin_user_id,),
        )

        connection.commit()
        connection.close()

        self.admin = {"id": self.admin_user_id, "session_token": issue_session(self.admin_user_id)}

    def tearDown(self):
        revoke_session(self.admin.get("session_token"))
        database.DATABASE_PATH = self.original_database_path
        for suffix in ("", "-wal", "-shm"):
            path = Path(str(self.db_path) + suffix)
            if path.exists():
                try:
                    path.unlink()
                except OSError:
                    pass

    def test_admin_creates_student_credentials_and_student_logins(self):
        # 1. Check initial status: STU901 has no login account yet
        ok, status = auth_service.get_student_credentials("STU901", actor=self.admin)
        self.assertTrue(ok)
        self.assertFalse(status["has_account"])
        self.assertEqual(status["username"], "STU901")

        # 2. Admin creates login credentials for STU901
        ok, msg = auth_service.create_or_update_student_credentials(
            student_id="STU901",
            username="STU901",
            password="StudentPass@123",
            actor=self.admin,
        )
        self.assertTrue(ok, msg)

        # 3. Verify status shows account created
        ok, status = auth_service.get_student_credentials("STU901", actor=self.admin)
        self.assertTrue(ok)
        self.assertTrue(status["has_account"])
        self.assertEqual(status["username"], "STU901")

        # 4. Student logs in through the same login pathway
        login_ok, stu_user = auth_service.login_user("STU901", "StudentPass@123")
        self.assertTrue(login_ok)
        self.assertEqual(stu_user["role"], "student")
        self.assertEqual(stu_user["username"], "STU901")

        # 5. Admin logs in through same login pathway
        admin_login_ok, admin_user = auth_service.login_user("admin_test", "AdminPass123")
        self.assertTrue(admin_login_ok)
        self.assertEqual(admin_user["role"], "admin")

        # 6. Student fetches their complete dashboard data
        dash_data = student_service.get_student_dashboard_data(actor=stu_user)
        self.assertIsNotNone(dash_data)

        # Verify Student Info
        student_info = dash_data["student"]
        self.assertEqual(student_info["student_id"], "STU901")
        self.assertEqual(student_info["name"], "Rahul Sharma")
        self.assertEqual(student_info["course"], "B.Tech")

        # Verify Room & Roommates Info
        room_info = dash_data["room"]
        self.assertIsNotNone(room_info)
        self.assertEqual(room_info["room_number"], "101")
        self.assertEqual(room_info["bed_number"], 1)

        roommates = dash_data["roommates"]
        self.assertEqual(len(roommates), 1)
        self.assertEqual(roommates[0]["student_id"], "STU902")
        self.assertEqual(roommates[0]["name"], "Aman Verma")
        self.assertEqual(roommates[0]["bed_number"], 2)

        # Verify Fees Info
        fees_info = dash_data["fees"]
        self.assertEqual(fees_info["total"], 30000.0)
        self.assertEqual(fees_info["paid"], 20000.0)
        self.assertEqual(fees_info["balance"], 10000.0)
        self.assertEqual(len(fees_info["recent_payments"]), 1)
        self.assertEqual(fees_info["recent_payments"][0]["receipt"], "REC-001")

        # Verify Announcements
        announcements = dash_data["announcements"]
        self.assertEqual(len(announcements), 1)
        self.assertEqual(announcements[0]["title"], "Curfew Notice")

    def test_non_admin_cannot_create_student_credentials(self):
        # Create student account first
        auth_service.create_or_update_student_credentials(
            student_id="STU901",
            username="STU901",
            password="StudentPass@123",
            actor=self.admin,
        )
        _, stu_user = auth_service.login_user("STU901", "StudentPass@123")

        # Student attempts to create/modify credentials
        with self.assertRaises(AuthorizationError):
            auth_service.create_or_update_student_credentials(
                student_id="STU902",
                username="STU902",
                password="HackPassword123",
                actor=stu_user,
            )


if __name__ == "__main__":
    unittest.main()
