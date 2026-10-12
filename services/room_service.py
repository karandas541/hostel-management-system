"""Room, bed allocation, and occupancy operations."""

import sqlite3

from database import get_connection
from utils.authorization import require_role, resolve_student
from utils.validators import optional_text, validate_integer, validate_room_number, validate_student_id
from services.notification_service import notify_student_record


ROOM_SELECT = """
    SELECT id, room_number, floor, capacity, occupied_beds,
           MAX(capacity - occupied_beds, 0) AS available_beds, status, room_type
    FROM rooms
"""


def _validated_room(room_number, floor, capacity, room_type=None):
    room_number = validate_room_number(room_number)
    floor = validate_integer(floor, "Floor", minimum=0)
    capacity = validate_integer(capacity, "Capacity", minimum=1, maximum=1000)
    room_type = optional_text(room_type, "Room type", max_length=50)
    return room_number, floor, capacity, room_type


def _sync_room_state(connection, room_id=None):
    """Recompute persisted occupancy and status from active allocations."""
    condition = " WHERE id = ?" if room_id is not None else ""
    params = (room_id,) if room_id is not None else ()
    connection.execute(
        """UPDATE rooms
           SET occupied_beds = (
               SELECT COUNT(*) FROM room_allocations
               WHERE room_id = rooms.id AND vacated_at IS NULL
           )""" + condition,
        params,
    )
    connection.execute(
        """UPDATE rooms
           SET status = CASE
               WHEN occupied_beds <= 0 THEN 'Available'
               WHEN occupied_beds >= capacity THEN 'Occupied'
               ELSE 'Partially Occupied'
           END""" + condition,
        params,
    )


def _sync_student_room(connection, student_db_id):
    allocation = connection.execute(
        """SELECT rooms.room_number, room_allocations.bed_number
           FROM room_allocations
           JOIN rooms ON rooms.id = room_allocations.room_id
           WHERE room_allocations.student_id = ? AND room_allocations.vacated_at IS NULL
           ORDER BY room_allocations.id DESC LIMIT 1""",
        (student_db_id,),
    ).fetchone()
    if allocation:
        room_number, bed_number = allocation
    else:
        room_number, bed_number = None, None
    connection.execute(
        "UPDATE students SET room_number = ?, bed_number = ? WHERE id = ?",
        (room_number, bed_number, student_db_id),
    )


def add_room(room_number, floor, capacity, actor=None, room_type=None):
    require_role(actor, "admin")
    room_number, floor, capacity, room_type = _validated_room(
        room_number, floor, capacity, room_type,
    )
    connection = get_connection()
    try:
        connection.execute(
            """INSERT INTO rooms
               (room_number, floor, room_type, capacity, occupied_beds, status)
               VALUES (?, ?, ?, ?, 0, 'Available')""",
            (room_number, floor, room_type, capacity),
        )
        connection.commit()
        return True, "Room added successfully."
    except sqlite3.IntegrityError as error:
        connection.rollback()
        if "rooms.room_number" in str(error):
            return False, "That room number already exists."
        return False, "Room details conflict with an existing record."
    except sqlite3.Error:
        connection.rollback()
        return False, "A database error prevented the room from being added."
    finally:
        connection.close()


def update_room(current_room_number, room_number, floor, capacity, room_type=None, actor=None):
    require_role(actor, "admin")
    room_number, floor, capacity, room_type = _validated_room(
        room_number, floor, capacity, room_type,
    )
    connection = get_connection()
    try:
        _sync_room_state(connection)
        room = connection.execute(
            "SELECT id, occupied_beds FROM rooms WHERE room_number = ?",
            (current_room_number,),
        ).fetchone()
        if room is None:
            connection.rollback()
            return False, "Room not found. Refresh the room list and try again."
        room_id, occupied = room
        if capacity < occupied:
            connection.rollback()
            return False, f"Capacity cannot be below the {occupied} currently allocated bed(s)."
        connection.execute(
            "UPDATE rooms SET room_number = ?, floor = ?, room_type = ?, capacity = ? WHERE id = ?",
            (room_number, floor, room_type, capacity, room_id),
        )
        if current_room_number != room_number:
            connection.execute(
                "UPDATE students SET room_number = ? WHERE room_number = ?",
                (room_number, current_room_number),
            )
        _sync_room_state(connection, room_id)
        connection.commit()
        return True, "Room details updated successfully."
    except sqlite3.IntegrityError as error:
        connection.rollback()
        if "rooms.room_number" in str(error):
            return False, "That room number already exists."
        return False, "Room details conflict with an existing record."
    except sqlite3.Error:
        connection.rollback()
        return False, "A database error prevented the room from being updated."
    finally:
        connection.close()


def get_all_rooms(actor=None):
    require_role(actor, "admin", "student")
    connection = get_connection()
    try:
        _sync_room_state(connection)
        connection.commit()
        return connection.execute(ROOM_SELECT + " ORDER BY floor, room_number COLLATE NOCASE").fetchall()
    finally:
        connection.close()


def get_room(room_number, actor=None):
    require_role(actor, "admin", "student")
    connection = get_connection()
    try:
        _sync_room_state(connection)
        connection.commit()
        return connection.execute(
            ROOM_SELECT + " WHERE room_number = ?",
            (room_number,),
        ).fetchone()
    finally:
        connection.close()


def delete_room(room_number, actor=None):
    require_role(actor, "admin")
    connection = get_connection()
    try:
        room = connection.execute("SELECT id FROM rooms WHERE room_number = ?", (room_number,)).fetchone()
        if room is None:
            return False, "Room not found."
        room_id = room[0]
        allocation_count = connection.execute(
            "SELECT COUNT(*) FROM room_allocations WHERE room_id = ?", (room_id,),
        ).fetchone()[0]
        student_count = connection.execute(
            "SELECT COUNT(*) FROM students WHERE room_number = ?", (room_number,),
        ).fetchone()[0]
        if allocation_count or student_count:
            return False, "This room has current or historical student assignments and cannot be deleted."
        connection.execute("DELETE FROM rooms WHERE id = ?", (room_id,))
        connection.commit()
        return True, "Room deleted successfully."
    except sqlite3.Error:
        connection.rollback()
        return False, "The room could not be safely deleted because linked records exist."
    finally:
        connection.close()


def allocate_room(student_id, room_number, actor=None):
    require_role(actor, "admin")
    try:
        student_id = validate_student_id(student_id)
        room_number = validate_room_number(room_number)
    except ValueError as error:
        return False, str(error)
    connection = get_connection()
    try:
        connection.execute("BEGIN IMMEDIATE")
        student = connection.execute(
            "SELECT id FROM students WHERE student_id = ?", (student_id,),
        ).fetchone()
        if student is None:
            connection.rollback()
            return False, "Student not found."
        student_db_id = student[0]
        existing = connection.execute(
            "SELECT 1 FROM room_allocations WHERE student_id = ? AND vacated_at IS NULL LIMIT 1",
            (student_db_id,),
        ).fetchone()
        if existing:
            connection.rollback()
            return False, "Student already has an active room allocation. Vacate it before allocating another room."
        room = connection.execute(
            "SELECT id, capacity FROM rooms WHERE room_number = ?", (room_number,),
        ).fetchone()
        if room is None:
            connection.rollback()
            return False, "Room not found."
        room_id, capacity = room
        active = connection.execute(
            "SELECT bed_number FROM room_allocations WHERE room_id = ? AND vacated_at IS NULL ORDER BY bed_number",
            (room_id,),
        ).fetchall()
        occupied_beds = {row[0] for row in active}
        occupied_count = len(active)
        if capacity < 1 or occupied_count >= capacity:
            _sync_room_state(connection, room_id)
            connection.commit()
            return False, "Room is full; no beds are available."
        bed_number = next((number for number in range(1, capacity + 1) if number not in occupied_beds), None)
        if bed_number is None:
            _sync_room_state(connection, room_id)
            connection.commit()
            return False, "No available bed could be found in this room."
        connection.execute(
            "INSERT INTO room_allocations (student_id, room_id, bed_number) VALUES (?, ?, ?)",
            (student_db_id, room_id, bed_number),
        )
        _sync_room_state(connection, room_id)
        _sync_student_room(connection, student_db_id)
        connection.commit()
        try:
            notify_student_record(
                student_db_id,
                "Room allocated",
                f"Room {room_number}, bed {bed_number}, has been allocated to you.",
                actor=actor,
            )
        except Exception:
            pass
        return True, f"Room allocated successfully. Bed number: {bed_number}."
    except sqlite3.Error:
        connection.rollback()
        return False, "A database error prevented the room allocation. No changes were saved."
    finally:
        connection.close()


def get_allocations(actor=None):
    verified = require_role(actor, "admin", "student")
    connection = get_connection()
    try:
        query = """SELECT room_allocations.id, students.student_id, students.name,
                          rooms.room_number, rooms.floor, room_allocations.bed_number,
                          room_allocations.allocated_at
                   FROM room_allocations
                   JOIN students ON room_allocations.student_id = students.id
                   JOIN rooms ON room_allocations.room_id = rooms.id
                   WHERE room_allocations.vacated_at IS NULL"""
        params = ()
        if verified["role"] == "student":
            own_id, _ = resolve_student(verified)
            query += " AND room_allocations.student_id = ?"
            params = (own_id,)
        return connection.execute(query + " ORDER BY room_allocations.id DESC", params).fetchall()
    finally:
        connection.close()


def deallocate_room(student_id, actor=None):
    require_role(actor, "admin")
    try:
        student_id = validate_student_id(student_id)
    except ValueError as error:
        return False, str(error)
    connection = get_connection()
    try:
        connection.execute("BEGIN IMMEDIATE")
        student = connection.execute(
            "SELECT id FROM students WHERE student_id = ?", (student_id,),
        ).fetchone()
        if student is None:
            connection.rollback()
            return False, "Student not found."
        student_db_id = student[0]
        allocation = connection.execute(
            "SELECT id, room_id FROM room_allocations WHERE student_id = ? AND vacated_at IS NULL ORDER BY id DESC LIMIT 1",
            (student_db_id,),
        ).fetchone()
        if allocation is None:
            connection.rollback()
            return False, "No active room allocation was found for this student."
        allocation_id, room_id = allocation
        connection.execute(
            "UPDATE room_allocations SET vacated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (allocation_id,),
        )
        _sync_room_state(connection, room_id)
        _sync_student_room(connection, student_db_id)
        connection.commit()
        return True, "Room vacated successfully."
    except sqlite3.Error:
        connection.rollback()
        return False, "A database error prevented the room from being vacated. No changes were saved."
    finally:
        connection.close()
