"""Notification operations with explicit role and record ownership checks."""

import sqlite3

from database import get_connection
from utils.authorization import AuthorizationError, require_role, resolve_student


def _validated_user_id(user_id):
    try:
        user_id = int(user_id)
    except (TypeError, ValueError) as error:
        raise ValueError("A valid user ID is required.") from error
    if user_id <= 0:
        raise ValueError("A valid user ID is required.")
    return user_id


def _authorize_user_target(actor, user_id):
    verified = require_role(actor, "admin", "student")
    user_id = _validated_user_id(user_id)
    if verified["role"] == "student" and user_id != int(verified["id"]):
        raise AuthorizationError("Students may access only their own notifications.")
    return verified, user_id


def create_notification(user_id, title, message, actor=None):
    """Create a notification for an active account; admins only."""
    require_role(actor, "admin")
    try:
        user_id = _validated_user_id(user_id)
    except ValueError as error:
        return False, str(error)
    title = str(title or "").strip()
    message = str(message or "").strip()
    if not title:
        return False, "Notification title is required."
    if len(title) > 150:
        return False, "Notification title must be 150 characters or fewer."
    if not message:
        return False, "Notification message is required."
    if len(message) > 2000:
        return False, "Notification message must be 2000 characters or fewer."

    return _save_notification(user_id, title, message)


def _save_notification(user_id, title, message, connection=None):
    owns_connection = connection is None
    connection = connection or get_connection()
    try:
        active_user = connection.execute(
            """SELECT users.id, COALESCE(user_settings.notifications_enabled, 1)
               FROM users LEFT JOIN user_settings ON user_settings.user_id = users.id
               WHERE users.id = ? AND users.is_active = 1""",
            (user_id,),
        ).fetchone()
        if active_user is None:
            return False, "The selected account is unavailable."
        if not active_user[1]:
            return False, "Notifications are disabled for this account."
        connection.execute(
            "INSERT INTO notifications (user_id, title, message) VALUES (?, ?, ?)",
            (user_id, title, message),
        )
        if owns_connection:
            connection.commit()
        return True, "Notification created successfully."
    except sqlite3.Error:
        if owns_connection:
            connection.rollback()
        return False, "A database error prevented the notification from being created."
    finally:
        if owns_connection:
            connection.close()


def notify_student_record(student_db_id, title, message, actor=None):
    """Send an automatic notification to the account linked to a student."""
    verified = require_role(actor, "admin", "student")
    if verified["role"] == "student":
        own_student_id, _ = resolve_student(verified)
        if int(student_db_id) != int(own_student_id):
            raise AuthorizationError("Students may create notifications only for their own account.")
    connection = get_connection()
    try:
        users = connection.execute(
            """SELECT users.id
               FROM students JOIN users
                 ON lower(trim(users.email)) = lower(trim(students.email))
               WHERE students.id = ? AND users.role = 'student' AND users.is_active = 1""",
            (student_db_id,),
        ).fetchall()
    finally:
        connection.close()
    outcomes = []
    for (user_id,) in users:
        outcomes.append(_save_notification(user_id, title, message))
    return bool(users) and all(success for success, _ in outcomes)


def create_announcement(title, message, actor=None):
    """Create an announcement record and notify all opted-in active accounts."""
    verified = require_role(actor, "admin")
    title = str(title or "").strip()
    message = str(message or "").strip()
    if not title:
        return False, "Announcement title is required."
    if len(title) > 150:
        return False, "Announcement title must be 150 characters or fewer."
    if not message:
        return False, "Announcement message is required."
    if len(message) > 2000:
        return False, "Announcement message must be 2000 characters or fewer."
    connection = get_connection()
    try:
        connection.execute("BEGIN IMMEDIATE")
        announcement = connection.execute(
            "INSERT INTO announcements (title, message, created_by) VALUES (?, ?, ?)",
            (title, message, verified["id"]),
        )
        user_ids = connection.execute(
            """SELECT users.id FROM users
               LEFT JOIN user_settings ON user_settings.user_id = users.id
               WHERE users.is_active = 1 AND COALESCE(user_settings.notifications_enabled, 1) = 1"""
        ).fetchall()
        for (user_id,) in user_ids:
            connection.execute(
                "INSERT INTO notifications (user_id, title, message) VALUES (?, ?, ?)",
                (user_id, f"Announcement: {title}", message),
            )
        connection.commit()
        return True, f"Announcement saved and sent to {len(user_ids)} opted-in account(s)."
    except sqlite3.Error:
        connection.rollback()
        return False, "A database error prevented the announcement from being sent."
    finally:
        connection.close()


def get_user_notifications(user_id, actor=None):
    """Get notifications for the requested user, scoped for student accounts."""
    _, user_id = _authorize_user_target(actor, user_id)
    connection = get_connection()
    try:
        return connection.execute(
            """SELECT id, title, message, is_read, created_at
               FROM notifications WHERE user_id = ?
               ORDER BY created_at DESC, id DESC""",
            (user_id,),
        ).fetchall()
    finally:
        connection.close()


def get_unread_count(user_id, actor=None):
    """Return unread notification count for the requested user."""
    _, user_id = _authorize_user_target(actor, user_id)
    connection = get_connection()
    try:
        row = connection.execute(
            """SELECT COUNT(*) FROM notifications
               LEFT JOIN user_settings ON user_settings.user_id = notifications.user_id
               WHERE notifications.user_id = ? AND notifications.is_read = 0
                 AND COALESCE(user_settings.notifications_enabled, 1) = 1""",
            (user_id,),
        ).fetchone()
        return row[0] if row else 0
    finally:
        connection.close()


def mark_notification_as_read(notification_id, actor=None):
    """Mark a notification read; student updates are constrained to their own row."""
    verified = require_role(actor, "admin", "student")
    try:
        notification_id = _validated_user_id(notification_id)
    except ValueError as error:
        return False, str(error)
    connection = get_connection()
    try:
        if verified["role"] == "student":
            cursor = connection.execute(
                "UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?",
                (notification_id, verified["id"]),
            )
        else:
            cursor = connection.execute(
                "UPDATE notifications SET is_read = 1 WHERE id = ?",
                (notification_id,),
            )
        if cursor.rowcount == 0:
            connection.rollback()
            return False, "Notification was not found or cannot be accessed."
        connection.commit()
        return True, "Notification marked as read."
    except sqlite3.Error:
        connection.rollback()
        return False, "A database error prevented the notification from being updated."
    finally:
        connection.close()


def mark_all_as_read(user_id, actor=None):
    """Mark all unread notifications for one authorized account as read."""
    _, user_id = _authorize_user_target(actor, user_id)
    connection = get_connection()
    try:
        connection.execute(
            "UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0",
            (user_id,),
        )
        connection.commit()
        return True, "All notifications marked as read."
    except sqlite3.Error:
        connection.rollback()
        return False, "A database error prevented notifications from being updated."
    finally:
        connection.close()


def delete_notification(notification_id, actor=None):
    """Delete one notification; deletion is restricted to administrators."""
    require_role(actor, "admin")
    try:
        notification_id = _validated_user_id(notification_id)
    except ValueError as error:
        return False, str(error)
    connection = get_connection()
    try:
        cursor = connection.execute("DELETE FROM notifications WHERE id = ?", (notification_id,))
        if cursor.rowcount == 0:
            return False, "Notification not found."
        connection.commit()
        return True, "Notification deleted successfully."
    except sqlite3.Error:
        connection.rollback()
        return False, "A database error prevented the notification from being deleted."
    finally:
        connection.close()


def get_all_users(actor=None):
    """Return active user accounts for the admin notification recipient list."""
    require_role(actor, "admin")
    connection = get_connection()
    try:
        return connection.execute(
            "SELECT id, username, role FROM users WHERE is_active = 1 ORDER BY username COLLATE NOCASE"
        ).fetchall()
    finally:
        connection.close()
