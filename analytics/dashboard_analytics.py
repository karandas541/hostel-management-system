"""Role-scoped summary metrics and recent activity for the home dashboard."""

from database import get_connection
from utils.authorization import require_role, resolve_student


def get_dashboard_statistics(actor=None):
    """Return global admin metrics or data limited to the logged-in student."""
    verified = require_role(actor, "admin", "student")
    is_admin = verified["role"] == "admin"
    student_db_id = None
    if not is_admin:
        student_db_id, _ = resolve_student(verified)

    connection = get_connection()
    try:
        cursor = connection.cursor()
        if is_admin:
            total_students = cursor.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        else:
            total_students = 1

        student_room = None
        if is_admin:
            total_rooms = cursor.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]
            total_beds = cursor.execute("SELECT COALESCE(SUM(capacity), 0) FROM rooms").fetchone()[0]
            occupied_beds = cursor.execute(
                "SELECT COUNT(*) FROM room_allocations WHERE vacated_at IS NULL"
            ).fetchone()[0]
            available_beds = max(0, total_beds - occupied_beds)
            occupancy_rate = round(occupied_beds / total_beds * 100, 2) if total_beds else 0
        else:
            total_rooms = total_beds = occupied_beds = available_beds = occupancy_rate = None
            student_room = cursor.execute(
                """SELECT rooms.room_number, room_allocations.bed_number,
                          rooms.capacity,
                          (SELECT COUNT(*) FROM room_allocations active
                           WHERE active.room_id = rooms.id AND active.vacated_at IS NULL)
                   FROM room_allocations JOIN rooms ON rooms.id = room_allocations.room_id
                   WHERE room_allocations.student_id = ? AND room_allocations.vacated_at IS NULL
                   ORDER BY room_allocations.id DESC LIMIT 1""",
                (student_db_id,),
            ).fetchone()

        fee_clause = " WHERE fees.student_id = ?" if student_db_id is not None else ""
        fee_params = (student_db_id,) if student_db_id is not None else ()
        cursor.execute(
            """SELECT COALESCE(SUM(fees.amount), 0),
                      COALESCE(SUM(COALESCE(paid.total_paid, 0)), 0),
                      COALESCE(SUM(MAX(fees.amount - COALESCE(paid.total_paid, 0), 0)), 0)
               FROM fees LEFT JOIN (
                   SELECT fee_id, SUM(amount) AS total_paid FROM payments GROUP BY fee_id
               ) paid ON paid.fee_id = fees.id""" + fee_clause,
            fee_params,
        )
        total_fees_amount, collected_fees, pending_fees = cursor.fetchone()
        fee_payment_completion_rate = (
            round(min(100, collected_fees / total_fees_amount * 100), 2)
            if total_fees_amount else None
        )

        complaint_clause = " WHERE student_id = ?" if student_db_id is not None else ""
        complaint_params = (student_db_id,) if student_db_id is not None else ()
        total_complaints = cursor.execute(
            "SELECT COUNT(*) FROM complaints" + complaint_clause,
            complaint_params,
        ).fetchone()[0]
        pending_complaints = cursor.execute(
            "SELECT COUNT(*) FROM complaints WHERE status NOT IN ('Resolved', 'Closed')" +
            (" AND student_id = ?" if student_db_id is not None else ""),
            complaint_params,
        ).fetchone()[0]
        resolved_complaints = cursor.execute(
            "SELECT COUNT(*) FROM complaints WHERE status IN ('Resolved', 'Closed')" +
            (" AND student_id = ?" if student_db_id is not None else ""),
            complaint_params,
        ).fetchone()[0]
        complaint_resolution_rate = (
            round(resolved_complaints / total_complaints * 100, 2) if total_complaints else 0
        )

        feedback_clause = " WHERE student_id = ?" if student_db_id is not None else ""
        feedback_params = (student_db_id,) if student_db_id is not None else ()
        feedback_count, average_satisfaction = cursor.execute(
            "SELECT COUNT(*), AVG(overall_experience) FROM feedback" + feedback_clause,
            feedback_params,
        ).fetchone()
        average_satisfaction = round(average_satisfaction, 2) if average_satisfaction is not None else None

        complaint_filter = "WHERE complaints.student_id = ? AND " if student_db_id is not None else "WHERE "
        recent_complaints = cursor.execute(
            """SELECT complaints.id, students.student_id, students.name,
                      complaints.category, complaints.status, complaints.priority,
                      complaints.created_at
               FROM complaints JOIN students ON students.id = complaints.student_id
               """ + complaint_filter + "1 = 1 ORDER BY complaints.id DESC LIMIT 5",
            complaint_params,
        ).fetchall()

        payment_filter = "WHERE fees.student_id = ? AND " if student_db_id is not None else "WHERE "
        recent_payments = cursor.execute(
            """SELECT payments.id, students.student_id, students.name, payments.fee_id,
                      payments.amount, payments.payment_mode, payments.payment_date,
                      payments.receipt_number
               FROM payments JOIN fees ON fees.id = payments.fee_id
               JOIN students ON students.id = fees.student_id
               """ + payment_filter + "1 = 1 ORDER BY payments.id DESC LIMIT 5",
            fee_params,
        ).fetchall()

        if is_admin:
            recent_students = cursor.execute(
                "SELECT student_id, name, created_at FROM students ORDER BY id DESC LIMIT 5"
            ).fetchall()
        else:
            recent_students = []

        status_filter = " WHERE student_id = ?" if student_db_id is not None else ""
        complaint_status_counts = cursor.execute(
            "SELECT status, COUNT(*) FROM complaints" + status_filter + " GROUP BY status",
            complaint_params,
        ).fetchall()

        return {
            "total_students": total_students,
            "total_rooms": total_rooms,
            "total_beds": total_beds,
            "occupied_beds": occupied_beds,
            "available_beds": available_beds,
            "occupancy_rate": occupancy_rate,
            "student_room_number": student_room[0] if student_room else None,
            "student_bed_number": student_room[1] if student_room else None,
            "student_room_capacity": student_room[2] if student_room else None,
            "student_room_occupied_beds": student_room[3] if student_room else None,
            "total_fees_amount": total_fees_amount or 0,
            "collected_fees": collected_fees or 0,
            "pending_fees": pending_fees or 0,
            "fee_payment_completion_rate": fee_payment_completion_rate,
            "total_complaints": total_complaints,
            "pending_complaints": pending_complaints,
            "resolved_complaints": resolved_complaints,
            "complaint_resolution_rate": complaint_resolution_rate,
            "feedback_count": feedback_count,
            "average_satisfaction": average_satisfaction,
            "recent_complaints": recent_complaints,
            "recent_payments": recent_payments,
            "recent_students": recent_students,
            "complaint_status_counts": complaint_status_counts,
        }
    finally:
        connection.close()
