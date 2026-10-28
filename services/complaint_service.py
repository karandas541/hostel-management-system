from database import get_connection
from utils.authorization import require_role, resolve_student, resolve_student_target
from services.notification_service import notify_student_record
from utils.validators import required_text, validate_student_id


def add_complaint(student_id, category, description, priority="Medium", actor=None):
    try:
        student_id = validate_student_id(student_id)
    except ValueError as error:
        return False, str(error)
    student_db_id, _ = resolve_student_target(actor, student_id)
    try:
        category = required_text(category, "Complaint category", max_length=100)
        description = required_text(description, "Complaint description", max_length=2000)
        priority = required_text(priority, "Priority", max_length=20)
    except ValueError as error:
        return False, str(error)
    connection = get_connection()
    cursor = connection.cursor()

    try:
        valid_priorities = ["Low", "Medium", "High", "Urgent"]

        if priority not in valid_priorities:
            return False, "Invalid priority."

        # Insert complaint
        cursor.execute(
            """
            INSERT INTO complaints
            (student_id, category, description, priority, status)
            VALUES (?, ?, ?, ?, 'Submitted')
            """,
            (
                student_db_id,
                category,
                description,
                priority
            )
        )
        complaint_pk = cursor.lastrowid

        # Dispatch notification to all active admins so the admin's notification badge alerts them
        admin_users = cursor.execute(
            """SELECT users.id FROM users
               LEFT JOIN user_settings ON user_settings.user_id = users.id
               WHERE users.role = 'admin' AND users.is_active = 1
                 AND COALESCE(user_settings.notifications_enabled, 1) = 1"""
        ).fetchall()
        for (admin_id,) in admin_users:
            cursor.execute(
                "INSERT INTO notifications (user_id, title, message) VALUES (?, ?, ?)",
                (admin_id, f"New Complaint: {category}", f"Student submitted #{complaint_pk} ({priority} priority): {description[:100]}"),
            )

        connection.commit()

        return True, "Complaint submitted successfully."

    except Exception as error:
        connection.rollback()
        return False, "The complaint could not be saved. Please try again."

    finally:
        connection.close()


def get_all_complaints(actor=None):
    verified = require_role(actor, "admin", "student")
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        SELECT
            complaints.id,
            students.student_id,
            students.name,
            complaints.category,
            complaints.description,
            complaints.priority,
            complaints.status,
            complaints.assigned_staff,
            complaints.created_at,
            complaints.resolved_at,
            complaints.resolution_remarks
        FROM complaints
        JOIN students
            ON complaints.student_id = students.id
        """
    if verified["role"] == "student":
        own_id, _ = resolve_student(verified)
        query += " WHERE complaints.student_id = ?"
        cursor.execute(query + " ORDER BY complaints.id DESC", (own_id,))
    else:
        cursor.execute(query + " ORDER BY complaints.id DESC")

    complaints = cursor.fetchall()

    connection.close()

    return complaints


def get_complaint(complaint_id, actor=None):
    verified = require_role(actor, "admin", "student")
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        SELECT
            id,
            student_id,
            category,
            description,
            priority,
            status,
            assigned_staff,
            created_at,
            resolved_at,
            resolution_remarks
        FROM complaints
        WHERE id = ?
        """
    params = [complaint_id]
    if verified["role"] == "student":
        own_id, _ = resolve_student(verified)
        query += " AND student_id = ?"
        params.append(own_id)
    cursor.execute(query, params)

    complaint = cursor.fetchone()

    connection.close()

    return complaint


def update_complaint_status(complaint_id, status, actor=None):
    require_role(actor, "admin")
    connection = get_connection()
    cursor = connection.cursor()

    try:
        valid_statuses = [
            "Submitted",
            "Assigned",
            "In Progress",
            "Resolved",
            "Closed"
        ]

        if status not in valid_statuses:
            return False, "Invalid complaint status."

        cursor.execute(
            "SELECT student_id, status FROM complaints WHERE id = ?",
            (complaint_id,)
        )

        complaint = cursor.fetchone()

        if complaint is None:
            return False, "Complaint not found."

        if status == "Resolved":
            cursor.execute(
                """
                UPDATE complaints
                SET status = ?,
                    resolved_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, complaint_id)
            )

        else:
            cursor.execute(
                """
                UPDATE complaints
                SET status = ?
                WHERE id = ?
                """,
                (status, complaint_id)
            )

        connection.commit()

        if status == "Resolved" and complaint[1] != "Resolved":
            try:
                notify_student_record(
                    complaint[0],
                    "Complaint resolved",
                    f"Your complaint #{complaint_id} has been resolved.",
                    actor=actor,
                )
            except Exception:
                pass

        return True, "Complaint status updated successfully."

    except Exception as error:
        connection.rollback()
        return False, "The complaint status could not be updated. Please try again."

    finally:
        connection.close()


def assign_complaint(complaint_id, assigned_staff, actor=None):
    require_role(actor, "admin")
    connection = get_connection()
    cursor = connection.cursor()

    try:
        try:
            assigned_staff = required_text(assigned_staff, "Staff name", max_length=100)
        except ValueError as error:
            return False, str(error)

        cursor.execute(
            "SELECT id FROM complaints WHERE id = ?",
            (complaint_id,)
        )

        complaint = cursor.fetchone()

        if complaint is None:
            return False, "Complaint not found."

        cursor.execute(
            """
            UPDATE complaints
            SET assigned_staff = ?,
                status = 'Assigned'
            WHERE id = ?
            """,
            (assigned_staff, complaint_id)
        )

        connection.commit()

        return True, "Complaint assigned successfully."

    except Exception as error:
        connection.rollback()
        return False, "The complaint could not be assigned. Please try again."

    finally:
        connection.close()


def resolve_complaint(complaint_id, resolution_remarks, actor=None):
    require_role(actor, "admin")
    connection = get_connection()
    cursor = connection.cursor()

    try:
        try:
            resolution_remarks = required_text(resolution_remarks, "Resolution remarks", max_length=2000)
        except ValueError as error:
            return False, str(error)

        cursor.execute(
            "SELECT student_id, status FROM complaints WHERE id = ?",
            (complaint_id,)
        )

        complaint = cursor.fetchone()

        if complaint is None:
            return False, "Complaint not found."

        cursor.execute(
            """
            UPDATE complaints
            SET status = 'Resolved',
                resolved_at = CURRENT_TIMESTAMP,
                resolution_remarks = ?
            WHERE id = ?
            """,
            (resolution_remarks, complaint_id)
        )

        connection.commit()

        if complaint[1] != "Resolved":
            try:
                notify_student_record(
                    complaint[0],
                    "Complaint resolved",
                    f"Your complaint #{complaint_id} has been resolved.",
                    actor=actor,
                )
            except Exception:
                pass

        return True, "Complaint resolved successfully."

    except Exception as error:
        connection.rollback()
        return False, "The complaint could not be resolved. Please try again."

    finally:
        connection.close()


def close_complaint(complaint_id, actor=None):
    require_role(actor, "admin")
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            "SELECT id FROM complaints WHERE id = ?",
            (complaint_id,)
        )

        complaint = cursor.fetchone()

        if complaint is None:
            return False, "Complaint not found."

        cursor.execute(
            """
            UPDATE complaints
            SET status = 'Closed'
            WHERE id = ?
            """,
            (complaint_id,)
        )

        connection.commit()

        return True, "Complaint closed successfully."

    except Exception as error:
        connection.rollback()
        return False, "The complaint could not be closed. Please try again."

    finally:
        connection.close()
