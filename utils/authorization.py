"""Authorization helpers shared by the UI and service layer."""

import secrets
import sqlite3
from functools import wraps

from database import get_connection


class AuthorizationError(PermissionError):
    """Raised when an operation is not permitted for the current user."""


_active_sessions = {}


def issue_session(user_id):
    """Create an opaque in-process proof for a successfully authenticated user."""
    token = secrets.token_urlsafe(32)
    _active_sessions[token] = int(user_id)
    return token


def revoke_session(token):
    if token:
        _active_sessions.pop(token, None)


def load_actor(actor):
    """Load the authoritative, active user record from the database."""
    if not isinstance(actor, dict) or actor.get("id") is None:
        raise AuthorizationError("A valid signed-in user is required.")
    token = actor.get("session_token")
    if not token or _active_sessions.get(token) != int(actor["id"]):
        raise AuthorizationError("Your session is invalid. Please sign in again.")

    connection = get_connection()
    try:
        user_cols = {col[1] for col in connection.execute("PRAGMA table_info(users)").fetchall()}
        if "student_id" in user_cols:
            row = connection.execute(
                "SELECT id, username, email, role, is_active, full_name, phone, student_id "
                "FROM users WHERE id = ?",
                (actor["id"],),
            ).fetchone()
            student_id = row[7] if row else None
        else:
            row = connection.execute(
                "SELECT id, username, email, role, is_active, full_name, phone "
                "FROM users WHERE id = ?",
                (actor["id"],),
            ).fetchone()
            student_id = None
    finally:
        connection.close()

    if row is None or not row[4]:
        raise AuthorizationError("This account is unavailable.")

    return {
        "id": row[0],
        "username": row[1],
        "email": row[2],
        "role": row[3],
        "session_token": token,
        "full_name": row[5],
        "phone": row[6],
        "student_id": student_id,
    }


def require_role(actor, *allowed_roles):
    """Return the verified actor or reject the operation."""
    verified = load_actor(actor)
    if verified["role"] not in allowed_roles:
        raise AuthorizationError("You do not have permission to perform this action.")
    return verified


def resolve_student(actor):
    """Resolve a student login by its student_id or email mapping."""
    verified = require_role(actor, "student")
    user_id = verified.get("id")
    email = (verified.get("email") or "").strip()
    username = (verified.get("username") or "").strip()
    sid_from_actor = (verified.get("student_id") or "").strip()

    connection = get_connection()
    try:
        rows = []
        if sid_from_actor:
            rows = connection.execute(
                "SELECT id, student_id FROM students WHERE lower(trim(student_id)) = lower(trim(?))",
                (sid_from_actor,),
            ).fetchall()

        if not rows and user_id:
            user_cols = {col[1] for col in connection.execute("PRAGMA table_info(users)").fetchall()}
            if "student_id" in user_cols:
                u_row = connection.execute("SELECT student_id FROM users WHERE id = ?", (user_id,)).fetchone()
                if u_row and u_row[0]:
                    rows = connection.execute(
                        "SELECT id, student_id FROM students WHERE lower(trim(student_id)) = lower(trim(?))",
                        (u_row[0].strip(),),
                    ).fetchall()

        if not rows and email:
            rows = connection.execute(
                "SELECT id, student_id FROM students WHERE lower(trim(email)) = lower(trim(?))",
                (email,),
            ).fetchall()

        if not rows and username:
            rows = connection.execute(
                "SELECT id, student_id FROM students WHERE lower(trim(student_id)) = lower(trim(?))",
                (username,),
            ).fetchall()
    finally:
        connection.close()

    if len(rows) != 1:
        raise AuthorizationError(
            "The student account must match exactly one student record."
        )
    return rows[0]


def resolve_student_target(actor, student_id):
    """Resolve a target student; students may resolve only themselves."""
    verified = load_actor(actor)
    if verified["role"] == "student":
        own_id, own_student_id = resolve_student(verified)
        if str(student_id).strip().casefold() != str(own_student_id).casefold():
            raise AuthorizationError("Students may access only their own records.")
        return own_id, verified
    if verified["role"] != "admin":
        raise AuthorizationError("You do not have permission to perform this action.")

    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT id FROM students WHERE student_id = ?", (student_id,)
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        raise AuthorizationError("Student record not found.")
    return row[0], verified


def require_menu_access(actor, menu_name):
    """Verify a module route using the database role, not a UI-provided role."""
    from utils.role_access import get_menu_for_role

    verified = load_actor(actor)
    if menu_name not in get_menu_for_role(verified["role"]):
        raise AuthorizationError("You do not have access to this module.")
    return verified


def guard_authorization_errors(function):
    """Keep authorization, validation, and service failures out of GUI tracebacks."""
    @wraps(function)
    def wrapped(self, *args, **kwargs):
        try:
            return function(self, *args, **kwargs)
        except AuthorizationError as error:
            from tkinter import messagebox
            messagebox.showwarning("Access denied", str(error), parent=self)
            return None
        except ValueError as error:
            from tkinter import messagebox
            messagebox.showwarning("Check your input", str(error), parent=self)
            return None
        except sqlite3.Error:
            from tkinter import messagebox
            messagebox.showerror(
                "Operation failed",
                "The database could not complete this request. Please try again.",
                parent=self,
            )
            return None
        except Exception:
            from tkinter import messagebox
            messagebox.showerror(
                "Operation failed",
                "Something went wrong while completing this request. Please try again.",
                parent=self,
            )
            return None
    return wrapped
