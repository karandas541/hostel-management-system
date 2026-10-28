"""Admin and student record access with validation, dashboard aggregation, and safe delete behavior."""

import sqlite3

from database import get_connection
from utils.authorization import require_role, resolve_student, resolve_student_target
from utils.validators import (
    optional_text, required_text, validate_email, validate_integer,
    validate_iso_date, validate_phone, validate_room_number, validate_student_id,
)


STUDENT_COLUMNS = (
    "student_id", "name", "parent_name", "gender", "date_of_birth", "phone",
    "email", "address", "course", "branch", "year", "admission_date",
    "room_number", "bed_number", "status",
)


def _clean_student_data(data):
    """Normalize and validate fields shared by add and update operations."""
    values = {key: data.get(key) for key in STUDENT_COLUMNS}
    for key, value in values.items():
        if isinstance(value, str):
            values[key] = value.strip() or None

    values["student_id"] = validate_student_id(values["student_id"])
    values["name"] = required_text(values["name"], "Student name", max_length=100)
    values["email"] = validate_email(values["email"])
    values["phone"] = validate_phone(values["phone"])
    values["date_of_birth"] = validate_iso_date(values["date_of_birth"], "Date of birth")
    values["admission_date"] = validate_iso_date(values["admission_date"], "Admission date")
    values["year"] = (
        validate_integer(values["year"], "Year", minimum=1, maximum=10)
        if values["year"] is not None else None
    )
    values["bed_number"] = (
        validate_integer(values["bed_number"], "Bed number", minimum=1)
        if values["bed_number"] is not None else None
    )
    if values["room_number"]:
        values["room_number"] = validate_room_number(values["room_number"])
    for field, label, limit in (
        ("parent_name", "Parent name", 100), ("gender", "Gender", 30),
        ("address", "Address", 500), ("course", "Course", 100),
        ("branch", "Branch", 100), ("room_number", "Room number", 50),
        ("status", "Status", 30),
    ):
        values[field] = optional_text(values[field], label, max_length=limit)

    values["status"] = values["status"] or "Active"
    return values


def _student_record(row):
    if row is None:
        return None
    keys = ("id",) + STUDENT_COLUMNS + ("created_at",)
    return dict(zip(keys, row))


def add_student(
    student_id, name, email=None, phone=None, course=None, year=None,
    gender=None, actor=None, *, parent_name=None, date_of_birth=None,
    address=None, branch=None, admission_date=None, room_number=None,
    bed_number=None, status="Active",
):
    require_role(actor, "admin")
    data = _clean_student_data({
        "student_id": student_id, "name": name, "email": email,
        "phone": phone, "course": course, "year": year, "gender": gender,
        "parent_name": parent_name, "date_of_birth": date_of_birth,
        "address": address, "branch": branch, "admission_date": admission_date,
        "room_number": room_number, "bed_number": bed_number, "status": status,
    })
    connection = get_connection()
    try:
        if data["email"] and connection.execute(
            "SELECT 1 FROM students WHERE lower(trim(email)) = lower(trim(?)) LIMIT 1",
            (data["email"],),
        ).fetchone():
            return False, "That email address is already assigned to a student."
        columns = ", ".join(STUDENT_COLUMNS)
        placeholders = ", ".join("?" for _ in STUDENT_COLUMNS)
        connection.execute(
            f"INSERT INTO students ({columns}) VALUES ({placeholders})",
            tuple(data[column] for column in STUDENT_COLUMNS),
        )
        connection.commit()
        return True, "Student added successfully."
    except sqlite3.IntegrityError as error:
        connection.rollback()
        message = str(error)
        if "UNIQUE constraint failed: students.student_id" in message:
            message = "That Student ID is already in use."
        elif "UNIQUE constraint failed: students.email" in message:
            message = "That email address is already in use."
        else:
            message = "Student details conflict with an existing record. Check the values and try again."
        return False, message
    except sqlite3.Error:
        connection.rollback()
        message = "A database error prevented the student from being saved."
        return False, message
    finally:
        connection.close()


def update_student(current_student_id, data, actor=None):
    require_role(actor, "admin")
    values = _clean_student_data(data)
    connection = get_connection()
    try:
        current = connection.execute(
            "SELECT id, email FROM students WHERE student_id = ?",
            (current_student_id,),
        ).fetchone()
        if current is None:
            return False, "Student not found."
        email_changed = (current[1] or "").strip().casefold() != (values["email"] or "").strip().casefold()
        linked_user = None
        if email_changed and current[1]:
            linked_user = connection.execute(
                "SELECT id FROM users WHERE role = 'student' AND lower(trim(email)) = lower(trim(?))",
                (current[1],),
            ).fetchone()
            if linked_user and not values["email"]:
                return False, "A student login is linked to this email, so the email cannot be cleared."
        if values["email"] and email_changed and connection.execute(
            "SELECT 1 FROM students WHERE lower(trim(email)) = lower(trim(?)) AND id != ? LIMIT 1",
            (values["email"], current[0]),
        ).fetchone():
            return False, "That email address is already assigned to another student."
        assignments = ", ".join(f"{column} = ?" for column in STUDENT_COLUMNS)
        cursor = connection.execute(
            f"UPDATE students SET {assignments} WHERE student_id = ?",
            tuple(values[column] for column in STUDENT_COLUMNS) + (current_student_id,),
        )
        if cursor.rowcount == 0:
            connection.rollback()
            return False, "Student not found."
        if linked_user:
            connection.execute(
                "UPDATE users SET email = ? WHERE id = ?",
                (values["email"], linked_user[0]),
            )
        connection.commit()
        return True, "Student details updated successfully."
    except sqlite3.IntegrityError as error:
        connection.rollback()
        message = str(error)
        if "UNIQUE constraint failed: students.student_id" in message:
            message = "That Student ID is already in use."
        elif "UNIQUE constraint failed: students.email" in message:
            message = "That email address is already in use."
        else:
            message = "Student details conflict with an existing record. Check the values and try again."
        return False, message
    except sqlite3.Error:
        connection.rollback()
        message = "A database error prevented the student details from being updated."
        return False, message
    finally:
        connection.close()


def update_student_contact(student_id, phone, email=None, actor=None):
    verified = require_role(actor, "admin", "student")
    if verified["role"] == "student":
        resolve_student_target(verified, student_id)
    phone = validate_phone(phone)
    email = validate_email(email)
    connection = get_connection()
    try:
        if email:
            conflict = connection.execute(
                "SELECT id FROM students WHERE lower(trim(email)) = lower(trim(?)) AND lower(trim(student_id)) != lower(trim(?))",
                (email, student_id),
            ).fetchone()
            if conflict:
                return False, "That email address is already assigned to another student."
        cursor = connection.execute(
            "UPDATE students SET phone = ?, email = ? WHERE student_id = ?",
            (phone, email, student_id),
        )
        if cursor.rowcount == 0:
            connection.rollback()
            return False, "Student record not found."
        user_cols = {col[1] for col in connection.execute("PRAGMA table_info(users)").fetchall()}
        if "student_id" in user_cols:
            connection.execute(
                "UPDATE users SET phone = ?, email = COALESCE(?, email) WHERE role = 'student' AND student_id = ?",
                (phone, email, student_id),
            )
        connection.commit()
        return True, "Contact details updated successfully."
    except sqlite3.Error:
        connection.rollback()
        return False, "A database error prevented contact details from being updated."
    finally:
        connection.close()


def get_all_students(actor=None):
    require_role(actor, "admin")
    connection = get_connection()
    try:
        columns = ", ".join(("id",) + STUDENT_COLUMNS + ("created_at",))
        cursor = connection.execute(f"SELECT {columns} FROM students ORDER BY name COLLATE NOCASE, id DESC")
        return [_student_record(row) for row in cursor.fetchall()]
    finally:
        connection.close()


def get_student(student_id, actor=None):
    verified = require_role(actor, "admin", "student")
    if verified["role"] == "student":
        resolve_student_target(verified, student_id)
    connection = get_connection()
    try:
        columns = ", ".join(("id",) + STUDENT_COLUMNS + ("created_at",))
        row = connection.execute(
            f"SELECT {columns} FROM students WHERE student_id = ?",
            (student_id,),
        ).fetchone()
        return _student_record(row)
    finally:
        connection.close()


def delete_student(student_id, actor=None, cascade=False):
    require_role(actor, "admin")
    connection = get_connection()
    try:
        # Resolve by student_id string or integer primary key
        parsed_id = int(student_id) if str(student_id).isdigit() else -1
        student = connection.execute(
            "SELECT id, email, student_id FROM students WHERE student_id = ? OR id = ?",
            (str(student_id), parsed_id),
        ).fetchone()
        if student is None:
            return False, "Student not found."

        student_db_id, email, actual_sid = student
        dependencies = (
            ("room allocation history", "SELECT COUNT(*) FROM room_allocations WHERE student_id = ?", (student_db_id,)),
            ("fee records", "SELECT COUNT(*) FROM fees WHERE student_id = ?", (student_db_id,)),
            ("complaints", "SELECT COUNT(*) FROM complaints WHERE student_id = ?", (student_db_id,)),
            ("attendance records", "SELECT COUNT(*) FROM attendance WHERE student_id = ?", (student_db_id,)),
            ("feedback records", "SELECT COUNT(*) FROM feedback WHERE student_id = ?", (student_db_id,)),
        )
        linked = [
            label for label, query, params in dependencies
            if connection.execute(query, params).fetchone()[0]
        ]
        user_cols = {col[1] for col in connection.execute("PRAGMA table_info(users)").fetchall()}
        account_count = 0
        if "student_id" in user_cols:
            account_count = connection.execute(
                "SELECT COUNT(*) FROM users WHERE role = 'student' AND student_id = ?",
                (actual_sid,),
            ).fetchone()[0]
        if not account_count and email:
            account_count = connection.execute(
                "SELECT COUNT(*) FROM users WHERE role = 'student' AND lower(trim(email)) = lower(trim(?))",
                (email,),
            ).fetchone()[0]
        if account_count:
            linked.append("a linked student login")

        if linked and not cascade:
            return False, (
                "This student has linked " + ", ".join(linked) +
                ". Keep the record to preserve history; set Status to Inactive instead."
            )

        if cascade:
            # Sync room allocations
            alloc_rooms = [
                row[0]
                for row in connection.execute(
                    "SELECT DISTINCT room_id FROM room_allocations WHERE student_id = ? AND vacated_at IS NULL",
                    (student_db_id,),
                ).fetchall()
            ]
            connection.execute("DELETE FROM room_allocations WHERE student_id = ?", (student_db_id,))
            for r_id in alloc_rooms:
                connection.execute(
                    """UPDATE rooms
                       SET occupied_beds = (
                           SELECT COUNT(*) FROM room_allocations
                           WHERE room_id = rooms.id AND vacated_at IS NULL
                       ) WHERE id = ?""",
                    (r_id,),
                )
                connection.execute(
                    """UPDATE rooms
                       SET status = CASE
                           WHEN occupied_beds <= 0 THEN 'Available'
                           WHEN occupied_beds >= capacity THEN 'Occupied'
                           ELSE 'Partially Occupied'
                       END WHERE id = ?""",
                    (r_id,),
                )

            # Delete payments and fees
            connection.execute(
                "DELETE FROM payments WHERE fee_id IN (SELECT id FROM fees WHERE student_id = ?)",
                (student_db_id,),
            )
            connection.execute("DELETE FROM fees WHERE student_id = ?", (student_db_id,))

            # Delete complaint updates and complaints
            connection.execute(
                "DELETE FROM complaint_updates WHERE complaint_id IN (SELECT id FROM complaints WHERE student_id = ?)",
                (student_db_id,),
            )
            connection.execute("DELETE FROM complaints WHERE student_id = ?", (student_db_id,))

            # Delete attendance and feedback
            connection.execute("DELETE FROM attendance WHERE student_id = ?", (student_db_id,))
            connection.execute("DELETE FROM feedback WHERE student_id = ?", (student_db_id,))

            # Delete linked user account and user-related records
            user_rows = []
            if "student_id" in user_cols:
                user_rows = connection.execute(
                    "SELECT id FROM users WHERE role = 'student' AND (student_id = ? OR (email IS NOT NULL AND lower(trim(email)) = lower(trim(?))))",
                    (actual_sid, email or ""),
                ).fetchall()
            elif email:
                user_rows = connection.execute(
                    "SELECT id FROM users WHERE role = 'student' AND lower(trim(email)) = lower(trim(?))",
                    (email,),
                ).fetchall()
            for (u_id,) in user_rows:
                connection.execute("DELETE FROM notifications WHERE user_id = ?", (u_id,))
                connection.execute("DELETE FROM user_settings WHERE user_id = ?", (u_id,))
                connection.execute("DELETE FROM users WHERE id = ?", (u_id,))

        connection.execute("DELETE FROM students WHERE id = ?", (student_db_id,))
        connection.commit()
        return True, "Student deleted successfully."
    except sqlite3.Error:
        connection.rollback()
        return False, "The student could not be safely deleted because linked records still exist."
    finally:
        connection.close()


def get_student_dashboard_data(actor=None, target_student_id=None):
    """Return complete dashboard details for the authenticated student or for admin preview."""
    verified = require_role(actor, "admin", "student")
    if verified["role"] == "student":
        student_db_id, student_id = resolve_student(verified)
    else:
        # Admin inspecting a specific student or latest active student
        connection = get_connection()
        try:
            if target_student_id:
                row = connection.execute("SELECT id, student_id FROM students WHERE student_id = ?", (target_student_id,)).fetchone()
            else:
                row = connection.execute("SELECT id, student_id FROM students ORDER BY id DESC LIMIT 1").fetchone()
            if not row:
                return None
            student_db_id, student_id = row
        finally:
            connection.close()

    connection = get_connection()
    try:
        cursor = connection.cursor()

        # 1. Student personal & academic details
        columns = ", ".join(("id",) + STUDENT_COLUMNS + ("created_at",))
        row = cursor.execute(
            f"SELECT {columns} FROM students WHERE id = ?",
            (student_db_id,),
        ).fetchone()
        student_info = _student_record(row)

        # 2. Room & Bed Allocation details
        alloc = cursor.execute(
            """
            SELECT
                rooms.id,
                rooms.room_number,
                rooms.floor,
                rooms.room_type,
                rooms.capacity,
                rooms.occupied_beds,
                rooms.status,
                room_allocations.bed_number,
                room_allocations.allocated_at
            FROM room_allocations
            JOIN rooms ON rooms.id = room_allocations.room_id
            WHERE room_allocations.student_id = ?
              AND room_allocations.vacated_at IS NULL
            ORDER BY room_allocations.id DESC
            LIMIT 1
            """,
            (student_db_id,),
        ).fetchone()

        room_info = None
        roommates = []
        if alloc:
            room_id, r_num, r_floor, r_type, r_cap, r_occ, r_status, bed_no, alloc_date = alloc
            room_info = {
                "room_id": room_id,
                "room_number": r_num,
                "floor": r_floor,
                "room_type": r_type or "Standard",
                "capacity": r_cap,
                "occupied_beds": r_occ,
                "status": r_status,
                "bed_number": bed_no,
                "allocated_at": alloc_date,
            }

            # Active roommates sharing this room
            mate_rows = cursor.execute(
                """
                SELECT
                    students.student_id,
                    students.name,
                    room_allocations.bed_number,
                    students.course,
                    students.branch,
                    students.phone
                FROM room_allocations
                JOIN students ON students.id = room_allocations.student_id
                WHERE room_allocations.room_id = ?
                  AND room_allocations.vacated_at IS NULL
                  AND room_allocations.student_id != ?
                ORDER BY room_allocations.bed_number ASC
                """,
                (room_id, student_db_id),
            ).fetchall()

            roommates = [
                {
                    "student_id": m[0],
                    "name": m[1],
                    "bed_number": m[2],
                    "course": m[3] or "—",
                    "branch": m[4] or "—",
                    "phone": m[5] or "—",
                }
                for m in mate_rows
            ]

        # 3. Fee & Payment information
        fee_rows = cursor.execute(
            """
            SELECT
                fees.id,
                fees.amount,
                fees.due_date,
                fees.status,
                COALESCE(SUM(payments.amount), 0) AS paid_amount
            FROM fees
            LEFT JOIN payments ON payments.fee_id = fees.id
            WHERE fees.student_id = ?
            GROUP BY fees.id
            ORDER BY fees.due_date DESC, fees.id DESC
            """,
            (student_db_id,),
        ).fetchall()

        total_fee_amount = sum(float(r[1]) for r in fee_rows)
        total_paid_amount = sum(float(r[4]) for r in fee_rows)
        balance_due = max(0.0, total_fee_amount - total_paid_amount)

        pay_rows = cursor.execute(
            """
            SELECT
                payments.amount,
                payments.payment_mode,
                payments.payment_date,
                payments.receipt_number
            FROM payments
            JOIN fees ON fees.id = payments.fee_id
            WHERE fees.student_id = ?
            ORDER BY payments.id DESC
            LIMIT 5
            """,
            (student_db_id,),
        ).fetchall()

        recent_payments = [
            {
                "amount": p[0],
                "mode": p[1] or "Online",
                "date": p[2] or "—",
                "receipt": p[3] or "—",
            }
            for p in pay_rows
        ]

        # 4. Attendance information
        today_att = cursor.execute(
            """
            SELECT entry_time, exit_time
            FROM attendance
            WHERE student_id = ?
              AND attendance_date = DATE('now', 'localtime')
            ORDER BY id DESC LIMIT 1
            """,
            (student_db_id,),
        ).fetchone()

        recent_att_rows = cursor.execute(
            """
            SELECT attendance_date, entry_time, exit_time
            FROM attendance
            WHERE student_id = ?
            ORDER BY attendance_date DESC, id DESC
            LIMIT 5
            """,
            (student_db_id,),
        ).fetchall()

        recent_attendance = [
            {
                "date": a[0],
                "entry": a[1] or "—",
                "exit": a[2] or "—",
            }
            for a in recent_att_rows
        ]

        # 5. Complaints information
        complaint_rows = cursor.execute(
            """
            SELECT id, category, description, priority, status, created_at, resolved_at, resolution_remarks
            FROM complaints
            WHERE student_id = ?
            ORDER BY id DESC
            LIMIT 5
            """,
            (student_db_id,),
        ).fetchall()

        total_comp = cursor.execute("SELECT COUNT(*) FROM complaints WHERE student_id = ?", (student_db_id,)).fetchone()[0]
        pending_comp = cursor.execute("SELECT COUNT(*) FROM complaints WHERE student_id = ? AND status != 'Resolved'", (student_db_id,)).fetchone()[0]
        resolved_comp = cursor.execute("SELECT COUNT(*) FROM complaints WHERE student_id = ? AND status = 'Resolved'", (student_db_id,)).fetchone()[0]

        recent_complaints = [
            {
                "id": c[0],
                "category": c[1],
                "description": c[2],
                "priority": c[3],
                "status": c[4],
                "created_at": c[5],
                "resolved_at": c[6],
                "remarks": c[7] or "—",
            }
            for c in complaint_rows
        ]

        # 6. Announcements / Notice Board
        announcement_rows = cursor.execute(
            """
            SELECT id, title, message, created_at
            FROM announcements
            ORDER BY id DESC
            LIMIT 5
            """
        ).fetchall()

        announcements = [
            {
                "id": ann[0],
                "title": ann[1],
                "message": ann[2],
                "created_at": ann[3],
            }
            for ann in announcement_rows
        ]

        return {
            "student": student_info,
            "room": room_info,
            "roommates": roommates,
            "fees": {
                "total": total_fee_amount,
                "paid": total_paid_amount,
                "balance": balance_due,
                "recent_payments": recent_payments,
            },
            "attendance": {
                "today": {"entry": today_att[0] if today_att else None, "exit": today_att[1] if today_att else None},
                "history": recent_attendance,
            },
            "complaints": {
                "summary": {"total": total_comp, "pending": pending_comp, "resolved": resolved_comp},
                "recent": recent_complaints,
            },
            "announcements": announcements,
        }
    finally:
        connection.close()
