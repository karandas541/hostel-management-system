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
        user = connection.execute(
            """SELECT id, username, email, password_hash, role, is_active,
                      full_name, phone
               FROM users WHERE username = ?""",
            (username,),
        ).fetchone()
    except sqlite3.Error:
        return False, "Login is temporarily unavailable. Please try again."
    finally:
        connection.close()

    if user is None:
        return False, "Invalid username or password."
    user_id, username, email, password_hash, role, is_active, full_name, phone = user
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
    }
