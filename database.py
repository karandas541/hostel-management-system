import sqlite3
from pathlib import Path


# Database folder
DATABASE_DIR = Path("database")
DATABASE_DIR.mkdir(exist_ok=True)

# Database file
DATABASE_PATH = DATABASE_DIR / "hostel.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)

    # Enable foreign keys
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    # =========================
    # USERS TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'student')),
            full_name TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    """)

    # Backward-compatible additive migration for existing installations.
    user_columns = {
        row[1] for row in cursor.execute("PRAGMA table_info(users)").fetchall()
    }
    if "full_name" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN full_name TEXT")
    if "phone" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")

    # =========================
    # STUDENTS TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            parent_name TEXT,
            gender TEXT,
            date_of_birth TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            course TEXT,
            branch TEXT,
            year INTEGER,
            admission_date TEXT,
            room_number TEXT,
            bed_number INTEGER,
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # =========================
    # ROOMS TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT NOT NULL UNIQUE,
            floor INTEGER NOT NULL,
            room_type TEXT,
            capacity INTEGER NOT NULL,
            occupied_beds INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Available'
        )
    """)

    # =========================
    # ROOM ALLOCATIONS TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS room_allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            bed_number INTEGER NOT NULL,
            allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            vacated_at TIMESTAMP,

            FOREIGN KEY(student_id)
                REFERENCES students(id),

            FOREIGN KEY(room_id)
                REFERENCES rooms(id)
        )
    """)

    # =========================
    # FEES TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            due_date TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(student_id)
                REFERENCES students(id)
        )
    """)

    # =========================
    # PAYMENTS TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fee_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_mode TEXT,
            payment_date TEXT,
            receipt_number TEXT UNIQUE,

            FOREIGN KEY(fee_id)
                REFERENCES fees(id)
        )
    """)

    # =========================
    # COMPLAINTS TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            priority TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'Submitted',
            assigned_staff TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP,
            resolution_remarks TEXT,

            FOREIGN KEY(student_id)
                REFERENCES students(id)
        )
    """)

    # =========================
    # COMPLAINT UPDATES TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaint_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            remarks TEXT,
            updated_by INTEGER,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(complaint_id)
                REFERENCES complaints(id),

            FOREIGN KEY(updated_by)
                REFERENCES users(id)
        )
    """)

    # =========================
    # ATTENDANCE TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            entry_time TEXT,
            exit_time TEXT,
            attendance_date TEXT NOT NULL,

            FOREIGN KEY(student_id)
                REFERENCES students(id)
        )
    """)

    # =========================
    # FEEDBACK TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,

            room_quality INTEGER
                CHECK(room_quality BETWEEN 1 AND 5),

            cleanliness INTEGER
                CHECK(cleanliness BETWEEN 1 AND 5),

            food_quality INTEGER
                CHECK(food_quality BETWEEN 1 AND 5),

            maintenance INTEGER
                CHECK(maintenance BETWEEN 1 AND 5),

            wifi INTEGER
                CHECK(wifi BETWEEN 1 AND 5),

            security INTEGER
                CHECK(security BETWEEN 1 AND 5),

            hostel_staff INTEGER
                CHECK(hostel_staff BETWEEN 1 AND 5),

            common_facilities INTEGER
                CHECK(common_facilities BETWEEN 1 AND 5),

            overall_experience INTEGER
                CHECK(overall_experience BETWEEN 1 AND 5),

            comments TEXT,
            evaluation_period TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(student_id)
                REFERENCES students(id)
        )
    """)

    # =========================
    # NOTIFICATIONS TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(user_id)
                REFERENCES users(id)
        )
    """)

    # =========================
    # ANNOUNCEMENTS TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(created_by)
                REFERENCES users(id)
        )
    """)

    # =========================
    # USER SETTINGS TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            theme TEXT DEFAULT 'light',
            notifications_enabled INTEGER DEFAULT 1,

            FOREIGN KEY(user_id)
                REFERENCES users(id)
        )
    """)

    # =========================
    # AUDIT LOG TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            module TEXT,
            record_id INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(user_id)
                REFERENCES users(id)
        )
    """)

    connection.commit()
    connection.close()

    print("Database initialized successfully.")


if __name__ == "__main__":
    initialize_database()
