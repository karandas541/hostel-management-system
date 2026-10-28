"""Account creation and login authentication."""

import sqlite3

from database import get_connection
from utils.authorization import issue_session, require_role
from utils.security import hash_password, verify_password
from utils.validators import validate_email, validate_password, validate_username


def create_user(username, password, role, email=None, actor=None):
    """Create a validated account with a bcrypt password hash."""
    require_role(actor, "admin")
    try:
        username = validate_username(username)
        password = validate_password(password)
        role = str(role or "").strip().lower()
        if role not in {"admin", "student"}:
            return False, "Choose either the admin or student role."
        email = validate_email(email)
    except ValueError as error:
        return False, str(error)

    connection = get_connection()
    try:
        connection.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
            (username, email, hash_password(password), role),
        )
        connection.commit()
        return True, "User created successfully."
    except sqlite3.IntegrityError as error:
        connection.rollback()
        if "users.username" in str(error):
            return False, "That username is already in use."
        if "users.email" in str(error):
            return False, "That email address is already in use."
        return False, "Account details conflict with an existing record."
    except sqlite3.Error:
        connection.rollback()
        return False, "A database error prevented the account from being created."
    finally:
        connection.close()


def login_user(username, password):
    """Authenticate a username/password pair without revealing which failed."""
    username = str(username or "").strip()
    if not username or not isinstance(password, str) or not password:
        return False, "Enter both username and password."
    connection = get_connection()
    try:
        user_cols = {col[1] for col in connection.execute("PRAGMA table_info(users)").fetchall()}
        if "student_id" in user_cols:
            user = connection.execute(
                """SELECT id, username, email, password_hash, role, is_active,
                          full_name, phone, student_id
                   FROM users WHERE username = ?""",
                (username,),
            ).fetchone()
            student_id = user[8] if user else None
        else:
            user = connection.execute(
                """SELECT id, username, email, password_hash, role, is_active,
                          full_name, phone
                   FROM users WHERE username = ?""",
                (username,),
            ).fetchone()
            student_id = None
    except sqlite3.Error:
        return False, "Login is temporarily unavailable. Please try again."
    finally:
        connection.close()

    if user is None:
        return False, "Invalid username or password."
    user_id, username, email, password_hash, role, is_active, full_name, phone = user[:8]
    if not is_active:
        return False, "Your account is inactive."
    try:
        valid_password = verify_password(password, password_hash)
    except (TypeError, ValueError):
        valid_password = False
    if not valid_password:
        return False, "Invalid username or password."
    return True, {
        "id": user_id,
        "username": username,
        "email": email,
        "role": role,
        "session_token": issue_session(user_id),
        "full_name": full_name,
        "phone": phone,
        "student_id": student_id,
    }


def get_student_credentials(student_id, actor=None):
    """Retrieve existing login status and details for a student; admin only."""
    require_role(actor, "admin")
    connection = get_connection()
    try:
        stu = connection.execute(
            "SELECT id, student_id, name, email, phone FROM students WHERE student_id = ?",
            (str(student_id).strip(),),
        ).fetchone()
        if stu is None:
            return False, "Student not found."
        stu_id, stu_sid, stu_name, stu_email, stu_phone = stu

        user_cols = {col[1] for col in connection.execute("PRAGMA table_info(users)").fetchall()}
        linked = None
        if "student_id" in user_cols:
            linked = connection.execute(
                "SELECT id, username, email, is_active FROM users WHERE role = 'student' AND student_id = ?",
                (stu_sid,),
            ).fetchone()
        if not linked and stu_email:
            linked = connection.execute(
                "SELECT id, username, email, is_active FROM users WHERE role = 'student' AND lower(trim(email)) = lower(trim(?))",
                (stu_email,),
            ).fetchone()
        if not linked:
            linked = connection.execute(
                "SELECT id, username, email, is_active FROM users WHERE role = 'student' AND lower(trim(username)) = lower(trim(?))",
                (stu_sid,),
            ).fetchone()

        if linked:
            return True, {
                "has_account": True,
                "user_id": linked[0],
                "username": linked[1],
                "email": linked[2] or stu_email or "",
                "is_active": bool(linked[3]),
                "student_id": stu_sid,
                "student_name": stu_name,
            }
        else:
            return True, {
                "has_account": False,
                "user_id": None,
                "username": stu_sid,  # default suggested username
                "email": stu_email or "",
                "is_active": True,
                "student_id": stu_sid,
                "student_name": stu_name,
            }
    finally:
        connection.close()


def create_or_update_student_credentials(student_id, username, password, actor=None, is_active=True):
    """Create or reset login credentials for a student; admin only."""
    require_role(actor, "admin")
    try:
        username = validate_username(username)
        password = validate_password(password)
    except ValueError as error:
        return False, str(error)

    connection = get_connection()
    try:
        stu = connection.execute(
            "SELECT id, student_id, name, email, phone FROM students WHERE student_id = ?",
            (str(student_id).strip(),),
        ).fetchone()
        if stu is None:
            return False, "Student record not found."
        stu_id, stu_sid, stu_name, stu_email, stu_phone = stu

        user_cols = {col[1] for col in connection.execute("PRAGMA table_info(users)").fetchall()}
        linked = None
        if "student_id" in user_cols:
            linked = connection.execute(
                "SELECT id, username FROM users WHERE role = 'student' AND student_id = ?",
                (stu_sid,),
            ).fetchone()
        if not linked and stu_email:
            linked = connection.execute(
                "SELECT id, username FROM users WHERE role = 'student' AND lower(trim(email)) = lower(trim(?))",
                (stu_email,),
            ).fetchone()
        if not linked:
            linked = connection.execute(
                "SELECT id, username FROM users WHERE role = 'student' AND lower(trim(username)) = lower(trim(?))",
                (stu_sid,),
            ).fetchone()

        # Check if username is used by another user
        conflict = connection.execute(
            "SELECT id FROM users WHERE lower(trim(username)) = lower(trim(?))",
            (username,),
        ).fetchone()
        if conflict and (linked is None or conflict[0] != linked[0]):
            return False, f"Username '{username}' is already in use by another account."

        hashed = hash_password(password)
        active_val = 1 if is_active else 0

        if linked:
            # Update existing user account
            user_id = linked[0]
            if "student_id" in user_cols:
                connection.execute(
                    """UPDATE users
                       SET username = ?, password_hash = ?, is_active = ?,
                           full_name = ?, phone = ?, student_id = ?, email = COALESCE(?, email)
                       WHERE id = ?""",
                    (username, hashed, active_val, stu_name, stu_phone, stu_sid, stu_email, user_id),
                )
            else:
                connection.execute(
                    """UPDATE users
                       SET username = ?, password_hash = ?, is_active = ?,
                           full_name = ?, phone = ?, email = COALESCE(?, email)
                       WHERE id = ?""",
                    (username, hashed, active_val, stu_name, stu_phone, stu_email, user_id),
                )
            connection.commit()
            return True, f"Login credentials updated successfully for {stu_name} (Username: {username})."
        else:
            # Insert new user account
            if "student_id" in user_cols:
                connection.execute(
                    """INSERT INTO users (username, email, password_hash, role, full_name, phone, student_id, is_active)
                       VALUES (?, ?, ?, 'student', ?, ?, ?, ?)""",
                    (username, stu_email, hashed, stu_name, stu_phone, stu_sid, active_val),
                )
            else:
                connection.execute(
                    """INSERT INTO users (username, email, password_hash, role, full_name, phone, is_active)
                       VALUES (?, ?, ?, 'student', ?, ?, ?)""",
                    (username, stu_email, hashed, stu_name, stu_phone, active_val),
                )
            connection.commit()
            return True, f"Login credentials created successfully for {stu_name} (Username: {username})."
    except sqlite3.IntegrityError as error:
        connection.rollback()
        err_msg = str(error)
        if "users.username" in err_msg:
            return False, "That username is already in use."
        if "users.email" in err_msg:
            return False, "That email address is already in use."
        return False, "Account details conflict with an existing record."
    except sqlite3.Error:
        connection.rollback()
        return False, "A database error occurred while creating/updating student credentials."
    finally:
        connection.close()
