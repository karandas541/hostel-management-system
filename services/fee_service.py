"""Fee creation, payment recording, and student-scoped fee queries."""

from decimal import Decimal
import sqlite3

from database import get_connection
from utils.authorization import require_role, resolve_student
from services.notification_service import notify_student_record
from utils.validators import validate_iso_date, validate_positive_amount, validate_student_id


PAYMENT_MODES = ("Cash", "UPI", "Card", "Net Banking", "Bank Transfer")


def _amount_in_cents(value, label="Amount"):
    amount = validate_positive_amount(value, label)
    return int(amount * 100)


def _amount_from_cents(cents):
    return (Decimal(cents) / 100).quantize(Decimal("0.01"))


def _validate_due_date(due_date):
    value = validate_iso_date(due_date, "Due date")
    if value is None:
        raise ValueError("Due date is required.")
    return value


def add_fee(student_id, amount, due_date, actor=None):
    require_role(actor, "admin")
    try:
        student_id = validate_student_id(student_id)
        cents = _amount_in_cents(amount, "Fee amount")
        normalized_date = _validate_due_date(due_date)
    except ValueError as error:
        return False, str(error)

    connection = get_connection()
    try:
        student = connection.execute("SELECT id, name FROM students WHERE student_id = ?", (student_id,)).fetchone()
        if student is None:
            return False, "Student not found."
        connection.execute(
            "INSERT INTO fees (student_id, amount, due_date, status) VALUES (?, ?, ?, 'Pending')",
            (student[0], float(_amount_from_cents(cents)), normalized_date),
        )
        connection.commit()
        try:
            notify_student_record(
                student[0],
                "Fee due",
                f"A fee of INR {_amount_from_cents(cents):.2f} is due by {normalized_date}.",
                actor=actor,
            )
        except Exception:
            pass
        return True, "Fee added successfully."
    except sqlite3.Error:
        connection.rollback()
        return False, "A database error prevented the fee from being added."
    finally:
        connection.close()


def get_all_fees(actor=None):
    verified = require_role(actor, "admin", "student")
    connection = get_connection()
    try:
        query = """SELECT fees.id, students.student_id, students.name, fees.amount,
                          fees.due_date, fees.status,
                          COALESCE(SUM(payments.amount), 0) AS paid_amount,
                          MAX(fees.amount - COALESCE(SUM(payments.amount), 0), 0) AS pending_amount
                   FROM fees
                   JOIN students ON fees.student_id = students.id
                   LEFT JOIN payments ON payments.fee_id = fees.id"""
        params = ()
        if verified["role"] == "student":
            own_id, _ = resolve_student(verified)
            query += " WHERE fees.student_id = ?"
            params = (own_id,)
        query += " GROUP BY fees.id ORDER BY fees.id DESC"
        return connection.execute(query, params).fetchall()
    finally:
        connection.close()


def get_fee(fee_id, actor=None):
    verified = require_role(actor, "admin", "student")
    connection = get_connection()
    try:
        query = "SELECT id, student_id, amount, due_date, status FROM fees WHERE id = ?"
        params = [fee_id]
        if verified["role"] == "student":
            own_id, _ = resolve_student(verified)
            query += " AND student_id = ?"
            params.append(own_id)
        return connection.execute(query, params).fetchone()
    finally:
        connection.close()


def _reconcile_fee_status(connection, fee_id):
    amounts = connection.execute(
        "SELECT amount FROM fees WHERE id = ?", (fee_id,),
    ).fetchone()
    if amounts is None:
        return
    total = _amount_in_cents(amounts[0], "Stored fee amount")
    paid_rows = connection.execute(
        "SELECT amount FROM payments WHERE fee_id = ?", (fee_id,),
    ).fetchall()
    paid = sum(_amount_in_cents(row[0], "Stored payment amount") for row in paid_rows)
    status = "Paid" if paid >= total else "Partial" if paid else "Pending"
    connection.execute("UPDATE fees SET status = ? WHERE id = ?", (status, fee_id))


def make_payment(fee_id, amount, payment_mode, receipt_number=None, actor=None):
    require_role(actor, "admin")
    try:
        payment_cents = _amount_in_cents(amount, "Payment amount")
    except ValueError as error:
        return False, str(error)
    payment_mode = str(payment_mode or "").strip()
    valid_modes = {m.lower(): m for m in PAYMENT_MODES}
    if payment_mode.lower() not in valid_modes:
        return False, "Choose Cash, UPI, Card, Net Banking, or Bank Transfer as the payment mode."
    payment_mode = valid_modes[payment_mode.lower()]
    receipt_number = str(receipt_number or "").strip() or None

    connection = get_connection()
    try:
        connection.execute("BEGIN IMMEDIATE")
        fee = connection.execute("SELECT amount FROM fees WHERE id = ?", (fee_id,)).fetchone()
        if fee is None:
            connection.rollback()
            return False, "Fee record not found."
        total_cents = _amount_in_cents(fee[0], "Stored fee amount")
        payments = connection.execute("SELECT amount FROM payments WHERE fee_id = ?", (fee_id,)).fetchall()
        paid_cents = sum(_amount_in_cents(row[0], "Stored payment amount") for row in payments)
        pending_cents = total_cents - paid_cents
        if pending_cents <= 0:
            _reconcile_fee_status(connection, fee_id)
            connection.commit()
            return False, "This fee is already fully paid."
        if payment_cents > pending_cents:
            connection.rollback()
            return False, f"Payment exceeds the pending amount of ₹{_amount_from_cents(pending_cents):.2f}."
        connection.execute(
            "INSERT INTO payments (fee_id, amount, payment_mode, payment_date, receipt_number) "
            "VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)",
            (fee_id, float(_amount_from_cents(payment_cents)), payment_mode, receipt_number),
        )
        _reconcile_fee_status(connection, fee_id)
        connection.commit()
        return True, "Payment recorded successfully."
    except sqlite3.IntegrityError as error:
        connection.rollback()
        if "receipt_number" in str(error).lower():
            return False, "That receipt number has already been used."
        return False, "Payment conflicts with an existing record. No changes were saved."
    except (sqlite3.Error, ValueError):
        connection.rollback()
        return False, "A database error prevented the payment. No changes were saved."
    finally:
        connection.close()


def get_fee_summary(fee_id, actor=None):
    fee = get_fee(fee_id, actor=actor)
    if fee is None:
        return None
    connection = get_connection()
    try:
        total_cents = _amount_in_cents(fee[2], "Stored fee amount")
        paid_cents = sum(
            _amount_in_cents(row[0], "Stored payment amount")
            for row in connection.execute("SELECT amount FROM payments WHERE fee_id = ?", (fee_id,)).fetchall()
        )
        return (
            _amount_from_cents(total_cents),
            _amount_from_cents(paid_cents),
            _amount_from_cents(max(0, total_cents - paid_cents)),
        )
    finally:
        connection.close()
