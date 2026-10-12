"""Admin-only feedback aggregates used by the TQM dashboard."""

from database import get_connection
from utils.authorization import require_role


CATEGORIES = (
    ("Room Quality", "room_quality"),
    ("Cleanliness", "cleanliness"),
    ("Food Quality", "food_quality"),
    ("Maintenance", "maintenance"),
    ("Wi-Fi", "wifi"),
    ("Security", "security"),
    ("Hostel Staff", "hostel_staff"),
    ("Common Facilities", "common_facilities"),
    ("Overall Experience", "overall_experience"),
)


def get_satisfaction_analysis(actor=None):
    require_role(actor, "admin")
    columns = ", ".join(f"AVG({column})" for _, column in CATEGORIES)
    connection = get_connection()
    try:
        result = connection.execute(f"SELECT {columns} FROM feedback").fetchone()
        return {
            label: round(value, 2) if value is not None else None
            for (label, _), value in zip(CATEGORIES, result)
        }
    finally:
        connection.close()


def create_satisfaction_chart(actor=None):
    import matplotlib.pyplot as plt

    data = get_satisfaction_analysis(actor=actor)
    observed = [(category, score) for category, score in data.items() if score is not None]
    if not observed:
        return None
    categories, scores = zip(*observed)
    figure, axis = plt.subplots(figsize=(10, 6))
    axis.barh(categories, scores)
    axis.set_xlabel("Satisfaction Score")
    axis.set_ylabel("Quality Area")
    axis.set_title("Hostel User Satisfaction Analysis")
    axis.set_xlim(0, 5)
    figure.tight_layout()
    return figure
