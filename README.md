# Hostel Management System

A desktop application for managing hostel operations and tracking service quality. The project uses a role-based workflow for administrators and students, with a Total Quality Management (TQM) focus on **Q08 — Improve User Satisfaction**.

**Project Name:** Hostel Management System

## TQM Goal

Use student feedback and complaint outcomes to identify service issues, prioritize improvements, and review whether hostel services are improving. The application displays measurements only when supported by saved records; see [TQM Q08 documentation](docs/TQM_Q08_Continuous_Improvement.md) for definitions and current limits.

## Objectives

- Keep student, room, fee, attendance, complaint, feedback, and notification records in one desktop application.
- Protect student records through role checks and student-to-login ownership checks.
- Track room capacity and active bed allocations.
- Record fees and partial or full payments, and show the remaining balance.
- Collect 1–5 ratings for hostel service areas and overall experience.
- Use feedback and complaint data to guide continuous improvement.

## Features

- **Role-specific access:** Admins manage hostel modules and access reports and the Quality Dashboard. Students see their own operational records and do not receive admin-only modules.
- **Students:** Create, search, view, update, and manage student records.
- **Rooms:** Maintain rooms and bed allocations, including occupied and available capacity.
- **Fees:** Create fees, record payments, and review fee/payment information.
- **Complaints:** Submit, assign, update, resolve, and close complaints.
- **Attendance:** Record and review attendance.
- **Feedback:** Collect student ratings and comments for hostel service areas.
- **Notifications:** Send targeted notifications and announcements, with per-account notification preferences.
- **Dashboard:** Show role-appropriate metrics and recent activity. Admin charts cover occupancy, fee collection, complaint status, and satisfaction.
- **Quality Dashboard and Reports:** Review feedback aggregates, recommendations, quality summaries, and exportable reports.
- **Profile and Settings:** Update account details, change password, select Light/Dark appearance, and save notification preferences.
- **Keyboard shortcuts:** Dashboard/home, refresh, logout, notifications, theme, exit, and role-appropriate Students/Fees shortcuts. Press **F1** for the in-app shortcut list.

## Modules

| Module | Admin | Student |
| --- | --- | --- |
| Dashboard | Hostel-wide overview | Personal overview |
| Students | Manage student records | Not available |
| Rooms | Manage rooms and allocations | View room information as permitted |
| Fees | Manage fees and payments | View own fee records |
| Complaints | Manage all complaints | Submit and view own complaints |
| Attendance | Manage attendance | View own attendance |
| Feedback | Review feedback | Submit and view own feedback |
| Notifications | Manage notifications and announcements | View own notifications |
| Quality Dashboard | Available | Not available |
| Reports | Available | Not available |
| Profile / Settings | Own account | Own account |

## Technologies

- Python (the current workspace uses Python 3.13)
- CustomTkinter for the desktop interface
- SQLite for local storage
- Matplotlib for charts
- ReportLab for PDF exports
- bcrypt for password hashing
- pandas, NumPy, and the libraries listed in `requirements.txt`

## Project Structure

```text
HostelManagementSystem/
├── analytics/       Dashboard and satisfaction analytics
├── assets/          Application assets
├── database/        Local SQLite database (`hostel.db`)
├── docs/            TQM documentation
├── models/          Data models
├── reports/         Report-related resources
├── services/        Authentication and business operations
├── utils/           Authorization, validation, themes, shortcuts, exports
├── views/           CustomTkinter screens
├── config.py        Database path configuration
├── database.py      Schema initialization and migrations
├── main.py          Application entry point
└── requirements.txt Python dependencies
```

## Database

The application uses SQLite at `database/hostel.db`, relative to the project directory. On startup, `main.py` initializes missing tables and applies additive migrations. Existing rows are retained. The database includes users, students, rooms, allocations, fees, payments, complaints, complaint updates, attendance, feedback, notifications, announcements, user settings, and audit records.

Keep the project directory as the working directory when starting the application so the relative database path resolves correctly. Back up `database/hostel.db` before manually editing or moving it.

## Installation

From the project root on Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks virtual-environment activation, open a new terminal with an appropriate local execution policy or call the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## How to Run

From the project root directory:

```powershell
.\.venv\Scripts\python.exe main.py
```

When `.venv` already exists, `python main.py` also detects it and relaunches the app with that project interpreter automatically. If the virtual environment has not been created yet, follow the setup commands above first.

The application initializes the SQLite schema before opening the login screen.

## Login Credentials

There are no hard-coded default usernames or passwords in the source code, and no demo password is documented. Use credentials provisioned for the local database by the project administrator. Passwords are stored as bcrypt hashes and cannot be read back from the database. A fresh database does not automatically create an administrator account; initial account provisioning must be performed by a trusted project administrator/setup process. The login screen's password-help action directs users to contact the administrator; self-service password reset is not implemented.

## TQM Metrics

The dashboard and Quality Dashboard calculate metrics from saved records, including:

- Average overall satisfaction and per-category feedback averages (1–5 scale).
- Feedback response count.
- Occupancy rate and available beds from room capacity and active room allocations.
- Collected fees, outstanding fees, and fee completion rate from fee and payment records.
- Total, open, and resolved/closed complaints and complaint resolution rate.
- Feedback-based improvement recommendations.

The application does not currently calculate average complaint resolution time, most common complaint category, or a separate room-occupancy accuracy score. Those values are not presented as measured metrics.

## Testing

Run the isolated database-backed workflow suite from the project root:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The suite creates and removes a temporary SQLite database inside the project workspace; it does not modify `database/hostel.db`. It covers authentication and role checks, student records, room capacity and allocation, fee payments, complaint resolution, attendance, feedback and TQM metrics, notification ownership and preferences, profile/password updates, settings persistence/reset, and CSV/PDF report exports. It also checks foreign-key enforcement and selected invalid-input cases.

The automated suite passed on 2026-10-08. Interactive GUI behavior across all screens and a packaged-build launch have not been manually smoke-tested.

## Screenshots

Screenshots can be added here after the final interface review.

```text
<!-- Example: ![Admin dashboard](docs/screenshots/admin-dashboard.png) -->
```

## Future Scope

- Add interactive GUI smoke tests for the complete role workflows and packaged-build launch.
- Provide a secure first-administrator setup flow and administrator-assisted password reset.
- Add complaint resolution time and complaint-category analytics.
- Track improvement actions and compare feedback before and after each action.
- Add practical date/status filters to reports where supported by the data model.

## Known Limitations

- A new empty database does not contain login accounts; there is no public sign-up or first-admin wizard.
- Password recovery is administrator-assisted; the app does not send reset links.
- TQM PDCA content is a guidance section. Improvement actions and their before/after outcomes are not recorded as a formal workflow.
- Some potentially useful measures (resolution time, most common complaint, and occupancy accuracy) are not currently calculated.
- The app is a local desktop application backed by SQLite; it is not a multi-hosted service.
