# ============================================================
# ROLE BASED ACCESS CONTROL
# ============================================================


# ------------------------------------------------------------
# Admin Menu
# ------------------------------------------------------------

ADMIN_MENU = [
    "Dashboard",
    "Students",
    "Rooms",
    "Fees",
    "Complaints",
    "Attendance",
    "Feedback",
    "Notifications",
    "Quality Dashboard",
    "Reports",
    "Profile",
    "Settings"
]


# ------------------------------------------------------------
# Student Menu
# ------------------------------------------------------------

STUDENT_MENU = [
    "Dashboard",
    "Rooms",
    "Fees",
    "Complaints",
    "Attendance",
    "Feedback",
    "Notifications",
    "Profile",
    "Settings"
]


# ------------------------------------------------------------
# Get Menu According to Role
# ------------------------------------------------------------

def get_menu_for_role(role):
    """
    Return sidebar menu according to user's role.
    """

    if not role:
        return []

    role = role.lower().strip()

    if role == "admin":
        return ADMIN_MENU.copy()

    elif role == "student":
        return STUDENT_MENU.copy()

    return []


# ------------------------------------------------------------
# Check Admin Access
# ------------------------------------------------------------

def is_admin(role):
    """
    Check whether user is an admin.
    """

    if not role:
        return False

    return role.lower().strip() == "admin"


# ------------------------------------------------------------
# Check Student Access
# ------------------------------------------------------------

def is_student(role):
    """
    Check whether user is a student.
    """

    if not role:
        return False

    return role.lower().strip() == "student"


# ------------------------------------------------------------
# Check Specific Menu Access
# ------------------------------------------------------------

def has_menu_access(role, menu_name):
    """
    Check whether a role has access to a specific menu.
    """

    allowed_menu = get_menu_for_role(role)

    return menu_name in allowed_menu


# ------------------------------------------------------------
# Direct Test
# ------------------------------------------------------------

if __name__ == "__main__":

    print("ADMIN MENU")
    print(get_menu_for_role("admin"))

    print("\nSTUDENT MENU")
    print(get_menu_for_role("student"))

    print("\nUNKNOWN ROLE")
    print(get_menu_for_role("unknown"))

    print("\nACCESS TESTS")

    print(
        "Admin -> Reports:",
        has_menu_access("admin", "Reports")
    )

    print(
        "Student -> Reports:",
        has_menu_access("student", "Reports")
    )

    print(
        "Student -> Feedback:",
        has_menu_access("student", "Feedback")
    )

    print(
        "Admin is admin:",
        is_admin("admin")
    )

    print(
        "Student is admin:",
        is_admin("student")
    )