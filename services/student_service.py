"""Admin-only student records with validation and safe delete behavior."""

import sqlite3

from database import get_connection
from utils.authorization import require_role
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
    require_role(actor, "admin")
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


def delete_student(student_id, actor=None):
    require_role(actor, "admin")
    connection = get_connection()
    try:
        student = connection.execute(
            "SELECT id, email FROM students WHERE student_id = ?",
            (student_id,),
        ).fetchone()
        if student is None:
            return False, "Student not found."

        student_db_id, email = student
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
        if email:
            account_count = connection.execute(
                "SELECT COUNT(*) FROM users WHERE role = 'student' AND lower(trim(email)) = lower(trim(?))",
                (email,),
            ).fetchone()[0]
            if account_count:
                linked.append("a linked student login")

        if linked:
            return False, (
                "This student has linked " + ", ".join(linked) +
                ". Keep the record to preserve history; set Status to Inactive instead."
            )

        connection.execute("DELETE FROM students WHERE id = ?", (student_db_id,))
        connection.commit()
        return True, "Student deleted successfully."
    except sqlite3.Error:
        connection.rollback()
        return False, "The student could not be safely deleted because linked records still exist."
    finally:
        connection.close()
