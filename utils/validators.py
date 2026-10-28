"""Reusable input validators that return normalized values or clear errors."""

from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re


_EMAIL = re.compile(r"[^\s@]+@[^\s@]+\.[^\s@]+")
_INTEGER = re.compile(r"[+-]?\d+")
_ROOM_NUMBER = re.compile(r"[\w./ -]+", re.UNICODE)
_STUDENT_ID = re.compile(r"[A-Za-z0-9_-]+")
_USERNAME = re.compile(r"[A-Za-z0-9_.-]+")


def required_text(value, label, max_length=None):
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} is required.")
    if max_length is not None and len(text) > max_length:
        raise ValueError(f"{label} must be {max_length} characters or fewer.")
    return text


def optional_text(value, label, max_length=None):
    text = str(value or "").strip()
    if max_length is not None and len(text) > max_length:
        raise ValueError(f"{label} must be {max_length} characters or fewer.")
    return text or None


def validate_email(value, label="Email"):
    text = str(value or "").strip()
    if not text:
        return None
    if len(text) > 254 or not _EMAIL.fullmatch(text):
        raise ValueError(f"Enter a valid {label.lower()} address.")
    return text


def validate_phone(value, label="Phone number"):
    text = str(value or "").strip()
    if not text:
        return None
    if not re.fullmatch(r"[0-9+() .-]+", text):
        raise ValueError(f"{label} contains unsupported characters.")
    digits = re.sub(r"\D", "", text)
    if not 7 <= len(digits) <= 15:
        raise ValueError(f"{label} must contain 7 to 15 digits.")
    return text


def validate_real_mobile_phone(value, label="Mobile number"):
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} is mandatory and cannot be left blank.")
    if not text.isdigit():
        raise ValueError(f"{label} must contain numbers (0-9) only. Spaces, letters, or symbols are not allowed.")
    if len(text) != 10:
        raise ValueError(f"{label} must be exactly 10 digits. You entered {len(text)} digits.")
    if text[0] not in "6789":
        raise ValueError(f"Invalid {label.lower()}! Mobile number must start with 6, 7, 8, or 9.")
    if len(set(text)) <= 2:
        raise ValueError(f"Invalid {label.lower()}! Repetitive or fake number '{text}' is not allowed.")
    trivial_sequences = {
        "1234567890", "0123456789", "9876543210", "0987654321",
        "2345678901", "3456789012", "4567890123", "5678901234"
    }
    if text in trivial_sequences:
        raise ValueError(f"Invalid {label.lower()}! Sequential number '{text}' is not allowed.")
    return text


def validate_real_gmail(value, label="Email address"):
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} is mandatory and cannot be left blank.")
    parts = text.split("@")
    if len(parts) != 2:
        raise ValueError(f"{label} must contain exactly one '@' character.")
    username, domain = parts[0], parts[1].lower()
    if domain != "gmail.com":
        raise ValueError("Only official '@gmail.com' addresses are allowed.")
    if len(username) < 6:
        raise ValueError(f"Gmail username is too short ({len(username)} chars). Minimum 6 characters required.")
    if len(username) > 30:
        raise ValueError(f"Gmail username is too long ({len(username)} chars). Maximum 30 characters allowed.")
    if username.startswith("."):
        raise ValueError("Gmail username cannot begin with a period (.).")
    if username.endswith("."):
        raise ValueError("Gmail username cannot end with a period (.).")
    if ".." in username:
        raise ValueError("Gmail username cannot contain consecutive periods (..).")
    if not re.match(r"^[a-zA-Z0-9.]+$", username):
        invalid_chars = set(re.findall(r"[^a-zA-Z0-9.]", username))
        invalid_str = ", ".join(f"'{c}'" for c in sorted(invalid_chars))
        raise ValueError(f"Real Gmail does not allow special characters: {invalid_str}. Only letters, numbers, and periods are allowed.")
    return text.lower()


def validate_iso_date(value, label="Date"):
    text = str(value or "").strip()
    if not text:
        return None
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        raise ValueError(f"{label} must use YYYY-MM-DD format.")
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError as error:
        raise ValueError(f"{label} must be a valid date in YYYY-MM-DD format.") from error


def validate_integer(value, label, minimum=None, maximum=None):
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a whole number.")
    if isinstance(value, int):
        number = value
    else:
        text = "" if value is None else str(value).strip()
        if not _INTEGER.fullmatch(text):
            raise ValueError(f"{label} must be a whole number.")
        number = int(text)
    if minimum is not None and number < minimum:
        raise ValueError(f"{label} must be at least {minimum}.")
    if maximum is not None and number > maximum:
        raise ValueError(f"{label} cannot exceed {maximum}.")
    return number


def validate_student_id(value):
    text = required_text(value, "Student ID", max_length=50)
    if not _STUDENT_ID.fullmatch(text):
        raise ValueError("Student ID may contain letters, numbers, hyphens, and underscores only.")
    return text


def validate_username(value):
    text = required_text(value, "Username", max_length=50)
    if len(text) < 3 or not _USERNAME.fullmatch(text):
        raise ValueError("Username must be 3–50 characters using letters, numbers, dots, hyphens, or underscores.")
    return text


def validate_password(value):
    if not isinstance(value, str) or len(value) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if len(value.encode("utf-8")) > 72:
        raise ValueError("Password must be no more than 72 UTF-8 bytes.")
    return value


def validate_room_number(value):
    text = required_text(value, "Room number", max_length=50)
    if not _ROOM_NUMBER.fullmatch(text):
        raise ValueError("Room number contains unsupported characters.")
    return text


def validate_rating(value):
    if isinstance(value, bool):
        raise ValueError("Rating must be a whole number from 1 to 5.")
    text = str(value or "").strip()
    if text not in {"1", "2", "3", "4", "5"}:
        raise ValueError("Rating must be a whole number from 1 to 5.")
    return int(text)


def validate_positive_amount(value, label="Amount"):
    try:
        amount = Decimal(str(value).strip()).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError, AttributeError) as error:
        raise ValueError(f"{label} must be a valid number.") from error
    if not amount.is_finite() or amount <= 0:
        raise ValueError(f"{label} must be greater than zero.")
    return amount
