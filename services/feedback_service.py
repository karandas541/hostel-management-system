from database import get_connection
from utils.authorization import require_role, resolve_student, resolve_student_target
from utils.validators import validate_rating as _validated_rating, validate_student_id

EVALUATION_PERIODS = {"Weekly", "Monthly", "Quarterly", "Yearly"}


def validate_rating(rating):
    try:
        _validated_rating(rating)
        return True
    except ValueError:
        return False


def add_feedback(
    student_id,
    room_quality=5,
    cleanliness=5,
    food_quality=5,
    maintenance=5,
    wifi=5,
    security=5,
    hostel_staff=5,
    common_facilities=5,
    overall_experience=5,
    comments="",
    evaluation_period="Monthly",
    actor=None,
    **kwargs
):
    # Support alias keyword arguments passed by various UI dialogs
    if "room_maintenance" in kwargs:
        maintenance = kwargs["room_maintenance"]
    if "washroom_hygiene" in kwargs:
        cleanliness = kwargs["washroom_hygiene"]
    if "internet_wifi" in kwargs:
        wifi = kwargs["internet_wifi"]
    if "staff_behavior" in kwargs:
        hostel_staff = kwargs["staff_behavior"]
    if "study_environment" in kwargs:
        common_facilities = kwargs["study_environment"]
    if "suggestions" in kwargs:
        comments = kwargs["suggestions"] or comments

    try:
        student_id = validate_student_id(student_id)
    except ValueError as error:
        return False, str(error)
    student_db_id, _ = resolve_student_target(actor, student_id)

    evaluation_period = str(evaluation_period or "Monthly").strip()
    comments = str(comments or "").strip()
    if evaluation_period not in EVALUATION_PERIODS:
        return False, "Choose Weekly, Monthly, Quarterly, or Yearly as the evaluation period."
    if len(comments) > 2000:
        return False, "Feedback comments must be 2000 characters or fewer."

    connection = get_connection()
    cursor = connection.cursor()

    try:
        ratings = [
            room_quality,
            cleanliness,
            food_quality,
            maintenance,
            wifi,
            security,
            hostel_staff,
            common_facilities,
            overall_experience
        ]

        for rating in ratings:
            if not validate_rating(rating):
                return False, "All ratings must be between 1 and 5."

        # =========================
        # INSERT FEEDBACK
        # =========================
        cursor.execute(
            """
            INSERT INTO feedback
            (
                student_id,
                room_quality,
                cleanliness,
                food_quality,
                maintenance,
                wifi,
                security,
                hostel_staff,
                common_facilities,
                overall_experience,
                comments,
                evaluation_period
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                student_db_id,
                int(room_quality),
                int(cleanliness),
                int(food_quality),
                int(maintenance),
                int(wifi),
                int(security),
                int(hostel_staff),
                int(common_facilities),
                int(overall_experience),
                comments,
                evaluation_period
            )
        )

        connection.commit()
        return True, "Feedback submitted successfully."

    except Exception:
        connection.rollback()
        return False, "Feedback could not be saved. Please check the entries and try again."

    finally:
        connection.close()


def get_all_feedback(actor=None):
    verified = require_role(actor, "admin", "student")

    connection = get_connection()
    cursor = connection.cursor()

    query = """
        SELECT
            feedback.id,
            students.student_id,
            students.name,
            feedback.room_quality,
            feedback.cleanliness,
            feedback.food_quality,
            feedback.maintenance,
            feedback.wifi,
            feedback.security,
            feedback.hostel_staff,
            feedback.common_facilities,
            feedback.overall_experience,
            feedback.comments,
            feedback.evaluation_period,
            feedback.created_at
        FROM feedback
        JOIN students
            ON feedback.student_id = students.id
        """
    if verified["role"] == "student":
        own_id, _ = resolve_student(verified)
        query += " WHERE feedback.student_id = ?"
        cursor.execute(query + " ORDER BY feedback.id DESC", (own_id,))
    else:
        cursor.execute(query + " ORDER BY feedback.id DESC")

    feedback = cursor.fetchall()
    connection.close()
    return feedback


def get_average_satisfaction(actor=None):
    require_role(actor, "admin")

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            AVG(room_quality),
            AVG(cleanliness),
            AVG(food_quality),
            AVG(maintenance),
            AVG(wifi),
            AVG(security),
            AVG(hostel_staff),
            AVG(common_facilities),
            AVG(overall_experience)
        FROM feedback
        """
    )

    result = cursor.fetchone()
    connection.close()
    return result


def get_overall_satisfaction(actor=None):
    verified = require_role(actor, "admin", "student")

    connection = get_connection()
    cursor = connection.cursor()

    if verified["role"] == "student":
        own_id, _ = resolve_student(verified)
        cursor.execute(
            "SELECT AVG(overall_experience) FROM feedback WHERE student_id = ?",
            (own_id,),
        )
    else:
        cursor.execute(
        """
        SELECT AVG(overall_experience)
        FROM feedback
        """
        )

    result = cursor.fetchone()
    connection.close()

    if result[0] is None:
        return 0

    return round(result[0], 2)
