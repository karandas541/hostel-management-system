from datetime import datetime, timedelta
from database import get_connection
from utils.authorization import require_role, resolve_student, resolve_student_target
from utils.validators import validate_student_id
import sqlite3


def _get_next_timestamp(reference_ts=None) -> str:
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    if reference_ts:
        ref_str = str(reference_ts)[:19]
        if ref_str >= now_str:
            try:
                ref_dt = datetime.strptime(ref_str, "%Y-%m-%d %H:%M:%S")
                now = ref_dt + timedelta(seconds=1)
            except Exception:
                pass
    return now.strftime("%Y-%m-%d %H:%M:%S")


def mark_entry(student_id, actor=None, remarks=None, **kwargs):
    remarks_val = (remarks or kwargs.get("remarks") or "").strip() or None
    try:
        student_id = validate_student_id(student_id)
    except ValueError as error:
        return False, str(error)

    student_db_id, _ = resolve_student_target(actor, student_id)
    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Check today's latest attendance record for this student
        cursor.execute(
            """
            SELECT id, entry_time, exit_time
            FROM attendance
            WHERE student_id = ?
            AND attendance_date = DATE('now')
            ORDER BY id DESC
            LIMIT 1
            """,
            (student_db_id,)
        )

        record = cursor.fetchone()

        # If already entered and currently present
        if record and record[1] is not None:
            if record[2] is None or str(record[1]) >= str(record[2]):
                return False, "Student is already marked present."

        if record is None:
            ts = _get_next_timestamp(None)
            cursor.execute(
                """
                INSERT INTO attendance
                (student_id, entry_time, exit_time, attendance_date, remarks)
                VALUES (?, ?, NULL, DATE('now'), ?)
                """,
                (student_db_id, ts, remarks_val)
            )
        else:
            # Update the latest open exit row: fill entry_time, preserve exit_time
            ts = _get_next_timestamp(record[2])
            cursor.execute(
                """
                UPDATE attendance
                SET entry_time = ?, remarks = COALESCE(?, remarks)
                WHERE id = ?
                """,
                (ts, remarks_val, record[0])
            )

        connection.commit()
        return True, "Entry marked successfully."

    except sqlite3.Error:
        connection.rollback()
        return False, "The attendance entry could not be saved. Please try again."

    finally:
        connection.close()


def mark_exit(student_id, actor=None, remarks=None, **kwargs):
    remarks_val = (remarks or kwargs.get("remarks") or "").strip() or None
    try:
        student_id = validate_student_id(student_id)
    except ValueError as error:
        return False, str(error)

    student_db_id, _ = resolve_student_target(actor, student_id)
    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Check today's latest attendance record for this student
        cursor.execute(
            """
            SELECT id, entry_time, exit_time
            FROM attendance
            WHERE student_id = ?
            AND attendance_date = DATE('now')
            ORDER BY id DESC
            LIMIT 1
            """,
            (student_db_id,)
        )

        record = cursor.fetchone()

        if record is None:
            ts = _get_next_timestamp(None)
            cursor.execute(
                """
                INSERT INTO attendance
                (student_id, entry_time, exit_time, attendance_date, remarks)
                VALUES (?, NULL, ?, DATE('now'), ?)
                """,
                (student_db_id, ts, remarks_val)
            )
            connection.commit()
            return True, "Exit marked successfully."

        rec_id, entry_time, exit_time = record

        # If already exited (exit_time is set and entry_time is None OR exit_time > entry_time)
        if exit_time is not None:
            if entry_time is None or str(exit_time) > str(entry_time):
                return False, "Student is already marked exited."

        # If previous exit-entry cycle is complete (both exit_time and entry_time exist):
        # Create a brand new row for this next exit so previous trip is never rewritten!
        if exit_time is not None and entry_time is not None:
            ts = _get_next_timestamp(entry_time)
            cursor.execute(
                """
                INSERT INTO attendance
                (student_id, entry_time, exit_time, attendance_date, remarks)
                VALUES (?, NULL, ?, DATE('now'), ?)
                """,
                (student_db_id, ts, remarks_val)
            )
            connection.commit()
            return True, "Exit marked successfully."

        # Otherwise (exit_time is None and entry_time is set):
        # First exit following an entry record, update exit_time on this row
        ts = _get_next_timestamp(entry_time)
        cursor.execute(
            """
            UPDATE attendance
            SET exit_time = ?, remarks = COALESCE(?, remarks)
            WHERE id = ?
            """,
            (ts, remarks_val, rec_id)
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
            attendance.attendance_date,
            attendance.remarks
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


def update_attendance_remarks(attendance_id, remarks, actor=None):
    require_role(actor, "admin")
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "UPDATE attendance SET remarks = ? WHERE id = ?",
            ((remarks or "").strip() or None, attendance_id)
        )
        connection.commit()
        return True, "Remarks updated successfully."
    except sqlite3.Error as e:
        connection.rollback()
        return False, str(e)
    finally:
        connection.close()


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


def delete_attendance(attendance_id, actor=None):
    """Delete an attendance entry by its ID (Admin only)."""
    require_role(actor, "admin")
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM attendance WHERE id = ?", (attendance_id,))
        connection.commit()
        return True, "Attendance record deleted successfully."
    except sqlite3.Error:
        connection.rollback()
        return False, "Failed to delete attendance record."
    finally:
        connection.close()
