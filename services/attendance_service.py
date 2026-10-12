from database import get_connection
from utils.authorization import require_role, resolve_student, resolve_student_target
from utils.validators import validate_student_id
import sqlite3


def mark_entry(student_id, actor=None):
    try:
        student_id = validate_student_id(student_id)
    except ValueError as error:
        return False, str(error)
    student_db_id, _ = resolve_student_target(actor, student_id)
    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Check today's attendance
        cursor.execute(
            """
            SELECT id, exit_time
            FROM attendance
            WHERE student_id = ?
            AND attendance_date = DATE('now')
            """,
            (student_db_id,)
        )

        record = cursor.fetchone()

        # Already entered and not exited
        if record and record[1] is None:
            return False, "Student is already marked present."

        # Create today's entry
        cursor.execute(
            """
            INSERT INTO attendance
            (student_id, entry_time, attendance_date)
            VALUES (?, CURRENT_TIMESTAMP, DATE('now'))
            """,
            (student_db_id,)
        )

        connection.commit()

        return True, "Entry marked successfully."

    except sqlite3.Error:
        connection.rollback()
        return False, "The attendance entry could not be saved. Please try again."

    finally:
        connection.close()


def mark_exit(student_id, actor=None):
    try:
        student_id = validate_student_id(student_id)
    except ValueError as error:
        return False, str(error)
    student_db_id, _ = resolve_student_target(actor, student_id)
    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Find active entry
        cursor.execute(
            """
            SELECT id
            FROM attendance
            WHERE student_id = ?
            AND attendance_date = DATE('now')
            AND exit_time IS NULL
            ORDER BY id DESC
            LIMIT 1
            """,
            (student_db_id,)
        )

        attendance = cursor.fetchone()

        if attendance is None:
            return False, "No active entry found for today."

        attendance_id = attendance[0]

        cursor.execute(
            """
            UPDATE attendance
            SET exit_time = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (attendance_id,)
        )

        connection.commit()

        return True, "Exit marked successfully."

    except sqlite3.Error:
        connection.rollback()
        return False, "The attendance exit could not be saved. Please try again."

    finally:
        connection.close()


def get_all_attendance(actor=None):
    verified = require_role(actor, "admin", "student")
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        SELECT
            attendance.id,
            students.student_id,
            students.name,
            attendance.entry_time,
            attendance.exit_time,
            attendance.attendance_date
        FROM attendance
        JOIN students
            ON attendance.student_id = students.id
        """
    if verified["role"] == "student":
        own_id, _ = resolve_student(verified)
        query += " WHERE attendance.student_id = ?"
        cursor.execute(query + " ORDER BY attendance.id DESC", (own_id,))
    else:
        cursor.execute(query + " ORDER BY attendance.id DESC")

    attendance = cursor.fetchall()

    connection.close()

    return attendance


def get_today_attendance(actor=None):
    verified = require_role(actor, "admin", "student")
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        SELECT
            attendance.id,
            students.student_id,
            students.name,
            attendance.entry_time,
            attendance.exit_time,
            attendance.attendance_date
        FROM attendance
        JOIN students
            ON attendance.student_id = students.id
        WHERE attendance.attendance_date = DATE('now')
        """
    if verified["role"] == "student":
        own_id, _ = resolve_student(verified)
        query += " AND attendance.student_id = ?"
        cursor.execute(query + " ORDER BY attendance.id DESC", (own_id,))
    else:
        cursor.execute(query + " ORDER BY attendance.id DESC")

    attendance = cursor.fetchall()

    connection.close()

    return attendance
