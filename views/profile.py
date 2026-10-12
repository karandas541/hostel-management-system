import customtkinter as ctk
from tkinter import messagebox
from utils.authorization import require_menu_access, guard_authorization_errors
from utils.authorization import load_actor, resolve_student
from utils.ui_theme import apply_professional_style
from utils.validators import required_text, validate_email, validate_password, validate_phone
from utils.theme_manager import ThemeManager

from database import get_connection


class ProfileWindow(ctk.CTkToplevel):

    def __init__(self, parent, user_data):
        require_menu_access(user_data, "Profile")
        super().__init__(parent)

        self.parent = parent
        self.user_data = load_actor(user_data)

        self.title("Hostel Management System - Profile")
        self.geometry("750x800")
        self.minsize(650, 650)

        self.protocol(
            "WM_DELETE_WINDOW",
            self.destroy
        )

        self.create_interface()
        apply_professional_style(self)

    # =========================================================
    # MAIN INTERFACE
    # =========================================================

    def create_interface(self):

        self.main_frame = ctk.CTkScrollableFrame(self)

        self.main_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )

        # =====================================================
        # HEADER
        # =====================================================

        title = ctk.CTkLabel(
            self.main_frame,
            text="My Profile",
            font=ctk.CTkFont(
                size=28,
                weight="bold"
            )
        )

        title.pack(
            pady=(10, 5)
        )

        subtitle = ctk.CTkLabel(
            self.main_frame,
            text="View and manage your account information",
            font=ctk.CTkFont(size=14)
        )

        subtitle.pack(
            pady=(0, 25)
        )

        # =====================================================
        # ACCOUNT INFORMATION
        # =====================================================

        account_card = ctk.CTkFrame(
            self.main_frame
        )

        account_card.pack(
            fill="x",
            padx=20,
            pady=10
        )

        ctk.CTkLabel(
            account_card,
            text="Account Information",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        ).pack(
            anchor="w",
            padx=25,
            pady=(20, 15)
        )

        self.name_summary = self.create_info_row(
            account_card,
            "Name",
            self.user_data.get("full_name") or self.user_data.get("username", "N/A"),
        )

        self.email_summary = self.create_info_row(
            account_card,
            "Email",
            self.user_data.get(
                "email",
                "Not provided"
            )
        )

        self.phone_summary = self.create_info_row(
            account_card,
            "Phone",
            self.user_data.get("phone") or "Not provided",
        )

        self.create_info_row(
            account_card,
            "Role",
            self.user_data.get(
                "role",
                "N/A"
            ).title()
        )

        self.create_info_row(
            account_card,
            "User ID",
            str(
                self.user_data.get(
                    "id",
                    "N/A"
                )
            )
        )
        self.theme_summary = self.create_info_row(
            account_card,
            "Theme",
            ThemeManager.get_current_theme().title(),
        )

        # =====================================================
        # PERSONAL INFORMATION
        # =====================================================

        self.personal_card = ctk.CTkFrame(
            self.main_frame
        )

        self.personal_card.pack(
            fill="x",
            padx=20,
            pady=20
        )

        ctk.CTkLabel(
            self.personal_card,
            text="Personal Information",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        ).pack(
            anchor="w",
            padx=25,
            pady=(20, 15)
        )

        # Name

        ctk.CTkLabel(
            self.personal_card,
            text=("Account Name" if self.user_data.get("role") == "admin" else "Full Name")
        ).pack(
            anchor="w",
            padx=25,
            pady=(5, 5)
        )

        self.name_entry = ctk.CTkEntry(
            self.personal_card,
            width=450,
            placeholder_text="Enter your name"
        )

        self.name_entry.pack(
            padx=25,
            pady=(0, 10)
        )

        role = self.user_data.get("role", "").lower().strip()
        self.name_entry.insert(
            0,
            self.user_data.get("full_name") or self.user_data.get("username", ""),
        )

        # Email

        ctk.CTkLabel(
            self.personal_card,
            text="Email"
        ).pack(
            anchor="w",
            padx=25,
            pady=(5, 5)
        )

        self.email_entry = ctk.CTkEntry(
            self.personal_card,
            width=450,
            placeholder_text="Enter email"
        )

        self.email_entry.pack(
            padx=25,
            pady=(0, 10)
        )
        self.email_entry.insert(0, self.user_data.get("email", ""))

        # Phone

        ctk.CTkLabel(
            self.personal_card,
            text="Phone Number"
        ).pack(
            anchor="w",
            padx=25,
            pady=(5, 5)
        )

        self.phone_entry = ctk.CTkEntry(
            self.personal_card,
            width=450,
            placeholder_text="Enter phone number"
        )

        self.phone_entry.pack(
            padx=25,
            pady=(0, 15)
        )
        self.phone_entry.insert(0, self.user_data.get("phone") or "")

        ctk.CTkButton(
            self.personal_card,
            text="Update Personal Information",
            width=240,
            height=40,
            command=self.update_personal_information
        ).pack(
            pady=(5, 20)
        )

        # =====================================================
        # STUDENT INFORMATION
        # =====================================================

        self.student_card = ctk.CTkFrame(
            self.main_frame
        )

        # Only show student information for student role

        if role == "student":

            self.student_card.pack(
                fill="x",
                padx=20,
                pady=10
            )

            ctk.CTkLabel(
                self.student_card,
                text="Student Information",
                font=ctk.CTkFont(
                    size=20,
                    weight="bold"
                )
            ).pack(
                anchor="w",
                padx=25,
                pady=(20, 15)
            )

            self.student_info_frame = ctk.CTkFrame(
                self.student_card,
                fg_color="transparent"
            )

            self.student_info_frame.pack(
                fill="x",
                padx=25,
                pady=(0, 20)
            )

            self.load_student_information()

        # =====================================================
        # CHANGE PASSWORD
        # =====================================================

        password_card = ctk.CTkFrame(
            self.main_frame
        )

        password_card.pack(
            fill="x",
            padx=20,
            pady=20
        )

        ctk.CTkLabel(
            password_card,
            text="Change Password",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        ).pack(
            anchor="w",
            padx=25,
            pady=(20, 15)
        )

        # Current password

        ctk.CTkLabel(
            password_card,
            text="Current Password"
        ).pack(
            anchor="w",
            padx=25,
            pady=(5, 5)
        )

        self.current_password = ctk.CTkEntry(
            password_card,
            width=450,
            show="*"
        )

        self.current_password.pack(
            padx=25,
            pady=(0, 10)
        )

        # New password

        ctk.CTkLabel(
            password_card,
            text="New Password"
        ).pack(
            anchor="w",
            padx=25,
            pady=(5, 5)
        )

        self.new_password = ctk.CTkEntry(
            password_card,
            width=450,
            show="*"
        )

        self.new_password.pack(
            padx=25,
            pady=(0, 10)
        )

        # Confirm password

        ctk.CTkLabel(
            password_card,
            text="Confirm New Password"
        ).pack(
            anchor="w",
            padx=25,
            pady=(5, 5)
        )

        self.confirm_password = ctk.CTkEntry(
            password_card,
            width=450,
            show="*"
        )

        self.confirm_password.pack(
            padx=25,
            pady=(0, 15)
        )

        ctk.CTkButton(
            password_card,
            text="Change Password",
            width=220,
            height=40,
            command=self.change_password
        ).pack(
            pady=(5, 20)
        )

    # =========================================================
    # INFORMATION ROW
    # =========================================================

    def create_info_row(
        self,
        parent,
        label_text,
        value_text
    ):

        row = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )

        row.pack(
            fill="x",
            padx=25,
            pady=7
        )

        label = ctk.CTkLabel(
            row,
            text=label_text,
            width=150,
            anchor="w",
            font=ctk.CTkFont(
                weight="bold"
            )
        )

        label.pack(
            side="left"
        )

        value = ctk.CTkLabel(
            row,
            text=str(value_text),
            anchor="w"
        )

        value.pack(
            side="left",
            padx=20
        )
        return value

    def refresh_theme_display(self):
        """Keep the profile's theme summary current after settings changes."""
        if hasattr(self, "theme_summary") and self.theme_summary.winfo_exists():
            self.theme_summary.configure(text=ThemeManager.get_current_theme().title())

    # =========================================================
    # LOAD STUDENT INFORMATION
    # =========================================================

    def load_student_information(self):

        connection = None
        try:

            connection = get_connection()
            cursor = connection.cursor()

            # -------------------------------------------------
            # Resolve only the uniquely linked student record.
            student_db_id, _ = resolve_student(self.user_data)
            # -------------------------------------------------

            cursor.execute(
                """
                SELECT
                    id,
                    student_id,
                    name,
                    email,
                    phone,
                    course,
                    branch,
                    year,
                    gender
                FROM students
                WHERE id = ?
                """,
                (student_db_id,)
            )

            student = cursor.fetchone()

            if student is None:

                self.create_info_row(
                    self.student_info_frame,
                    "Student ID",
                    "Student record not found"
                )

                return

            (
                student_db_id,
                student_id,
                name,
                email,
                phone,
                course,
                branch,
                year,
                gender
            ) = student

            # Save student database ID for updates

            self.student_db_id = student_db_id
            self.student_id = student_id

            # -------------------------------------------------
            # Fill editable fields
            # -------------------------------------------------

            self.name_entry.delete(0, "end")
            self.name_entry.insert(0, name or "")

            self.email_entry.delete(
                0,
                "end"
            )

            self.email_entry.insert(
                0,
                email or self.user_data.get(
                    "email",
                    ""
                )
            )

            self.phone_entry.delete(0, "end")
            self.phone_entry.insert(0, phone or "")

            self.name_summary.configure(text=name or self.user_data.get("username", "N/A"))
            self.phone_summary.configure(text=phone or "Not provided")

            # -------------------------------------------------
            # Room information
            # -------------------------------------------------

            cursor.execute(
                """
                SELECT
                    rooms.room_number,
                    room_allocations.bed_number
                FROM room_allocations

                JOIN rooms
                    ON room_allocations.room_id = rooms.id

                WHERE room_allocations.student_id = ?

                AND room_allocations.vacated_at IS NULL

                LIMIT 1
                """,
                (
                    student_db_id,
                )
            )

            room = cursor.fetchone()

            if room:

                room_number = room[0]
                bed_number = room[1]

                room_text = (
                    f"Room {room_number} | "
                    f"Bed {bed_number}"
                )

            else:

                room_text = "Not allocated"

            # -------------------------------------------------
            # Fee status
            # -------------------------------------------------

            cursor.execute(
                """
                SELECT
                    COUNT(*),
                    SUM(
                        CASE
                            WHEN status = 'Pending'
                            THEN 1
                            ELSE 0
                        END
                    ),
                    SUM(
                        CASE
                            WHEN status = 'Partial'
                            THEN 1
                            ELSE 0
                        END
                    ),
                    SUM(
                        CASE
                            WHEN status = 'Paid'
                            THEN 1
                            ELSE 0
                        END
                    )
                FROM fees
                WHERE student_id = ?
                """,
                (
                    student_db_id,
                )
            )

            fee_data = cursor.fetchone()

            total_fees = fee_data[0] or 0
            pending_fees = fee_data[1] or 0
            partial_fees = fee_data[2] or 0
            paid_fees = fee_data[3] or 0

            if total_fees == 0:

                fee_status = "No fee records"

            elif pending_fees > 0:

                fee_status = f"Pending ({pending_fees})"

            elif partial_fees > 0:

                fee_status = f"Partial ({partial_fees})"

            elif paid_fees == total_fees:

                fee_status = "All Paid"

            else:

                fee_status = "Pending"

            # -------------------------------------------------
            # Complaint status
            # -------------------------------------------------

            cursor.execute(
                """
                SELECT
                    COUNT(*),
                    SUM(
                        CASE
                            WHEN status IN ('Submitted', 'Assigned', 'In Progress')
                            THEN 1
                            ELSE 0
                        END
                    ),
                    SUM(
                        CASE
                            WHEN status = 'Resolved'
                            THEN 1
                            ELSE 0
                        END
                    ),
                    SUM(
                        CASE
                            WHEN status = 'Closed'
                            THEN 1
                            ELSE 0
                        END
                    )
                FROM complaints
                WHERE student_id = ?
                """,
                (
                    student_db_id,
                )
            )

            complaint_data = cursor.fetchone()

            total_complaints = complaint_data[0] or 0
            active_complaints = complaint_data[1] or 0
            resolved_complaints = complaint_data[2] or 0
            closed_complaints = complaint_data[3] or 0

            if total_complaints == 0:

                complaint_status = "No complaints"

            else:
                complaint_status = (
                    f"Open: {active_complaints} · "
                    f"Resolved: {resolved_complaints} · "
                    f"Closed: {closed_complaints}"
                )

            # -------------------------------------------------
            # Display student details
            # -------------------------------------------------

            self.create_info_row(
                self.student_info_frame,
                "Student ID",
                student_id
            )

            self.create_info_row(
                self.student_info_frame,
                "Course",
                course or "Not provided"
            )

            self.create_info_row(
                self.student_info_frame,
                "Branch",
                branch or "Not provided"
            )

            self.create_info_row(
                self.student_info_frame,
                "Year",
                year if year else "Not provided"
            )

            self.create_info_row(
                self.student_info_frame,
                "Gender",
                gender or "Not provided"
            )

            self.student_contact_summary = self.create_info_row(
                self.student_info_frame,
                "Contact",
                phone or "Not provided",
            )

            self.create_info_row(
                self.student_info_frame,
                "Room",
                room_text
            )

            self.create_info_row(
                self.student_info_frame,
                "Fee Status",
                fee_status
            )

            self.create_info_row(
                self.student_info_frame,
                "Complaint Status",
                complaint_status
            )

        except Exception:

            messagebox.showerror(
                "Error",
                "Unable to load student information. Please try again.",
                parent=self,
            )
        finally:
            if connection:
                try:
                    connection.close()
                except Exception:
                    pass

    # =========================================================
    # UPDATE PERSONAL INFORMATION
    # =========================================================

    @guard_authorization_errors
    def update_personal_information(self):
        verified_user = load_actor(self.user_data)
        role = verified_user["role"]
        student_db_id = None

        if role == "student":
            student_db_id, _ = resolve_student(verified_user)
            if student_db_id != getattr(self, "student_db_id", None):
                messagebox.showerror(
                    "Access denied",
                    "Student profile ownership could not be verified.",
                    parent=self,
                )
                return

        try:
            email = validate_email(self.email_entry.get())
            if not email:
                raise ValueError("Email is required.")
            name = required_text(self.name_entry.get(), "Name", max_length=100)
            phone = validate_phone(self.phone_entry.get()) or ""
        except ValueError as error:
            messagebox.showwarning("Validation Error", str(error), parent=self)
            return

        connection = None
        try:
            connection = get_connection()
            cursor = connection.cursor()

            duplicate_user = cursor.execute(
                "SELECT id FROM users WHERE lower(email) = lower(?) AND id != ?",
                (email, verified_user["id"]),
            ).fetchone()
            if duplicate_user:
                messagebox.showwarning(
                    "Email Already Exists",
                    "This email is already used by another account.",
                    parent=self,
                )
                return

            if role == "student":
                duplicate_student = cursor.execute(
                    "SELECT id FROM students WHERE lower(email) = lower(?) AND id != ?",
                    (email, student_db_id),
                ).fetchone()
                if duplicate_student:
                    messagebox.showwarning(
                        "Email Already Exists",
                        "This email is already used by another student.",
                        parent=self,
                    )
                    return

                cursor.execute(
                    "UPDATE students SET name = ?, email = ?, phone = ? WHERE id = ?",
                    (name, email, phone, student_db_id),
                )
                if cursor.rowcount != 1:
                    raise ValueError("Student profile could not be found.")

            cursor.execute(
                "UPDATE users SET full_name = ?, email = ?, phone = ? WHERE id = ?",
                (name, email, phone, verified_user["id"]),
            )
            if cursor.rowcount != 1:
                raise ValueError("User account could not be found.")

            connection.commit()
            self.user_data["full_name"] = name
            self.user_data["email"] = email
            self.user_data["phone"] = phone
            if hasattr(self.parent, "user"):
                self.parent.user["full_name"] = name
                self.parent.user["email"] = email
                self.parent.user["phone"] = phone
            self.name_summary.configure(text=name)
            self.email_summary.configure(text=email)
            self.phone_summary.configure(text=phone or "Not provided")
            if role == "student" and hasattr(self, "student_contact_summary"):
                self.student_contact_summary.configure(text=phone or "Not provided")

            messagebox.showinfo(
                "Success",
                "Personal information updated successfully.",
                parent=self,
            )
        except ValueError as error:
            if connection:
                connection.rollback()
            messagebox.showwarning("Profile", str(error), parent=self)
        except Exception:
            if connection:
                connection.rollback()
            messagebox.showerror(
                "Error",
                "Unable to update information. Check the fields and try again.",
                parent=self,
            )
        finally:
            if connection:
                connection.close()

    # =========================================================
    # CHANGE PASSWORD
    # =========================================================

    @guard_authorization_errors
    def change_password(self):

        self.user_data = load_actor(self.user_data)

        current = self.current_password.get()
        new = self.new_password.get()
        confirm = self.confirm_password.get()

        # -----------------------------------------------------
        # Empty fields
        # -----------------------------------------------------

        if not current or not new or not confirm:

            messagebox.showwarning(
                "Validation Error",
                "Please fill all password fields."
            )

            return

        # -----------------------------------------------------
        # Password length
        # -----------------------------------------------------

        try:
            validate_password(new)
        except ValueError as error:
            messagebox.showwarning("Validation Error", str(error), parent=self)
            return

        # -----------------------------------------------------
        # Password confirmation
        # -----------------------------------------------------

        if new != confirm:

            messagebox.showwarning(
                "Validation Error",
                "New password and confirmation do not match."
            )

            return

        connection = None

        try:

            from utils.security import (
                verify_password,
                hash_password
            )

            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT password_hash
                FROM users
                WHERE id = ?
                """,
                (
                    self.user_data["id"],
                )
            )

            result = cursor.fetchone()

            if result is None:

                messagebox.showerror(
                    "Error",
                    "User account was not found."
                )

                return

            current_hash = result[0]

            # -------------------------------------------------
            # Verify current password
            # -------------------------------------------------

            if not verify_password(
                current,
                current_hash
            ):

                messagebox.showerror(
                    "Incorrect Password",
                    "Current password is incorrect."
                )

                return

            # -------------------------------------------------
            # Prevent same password
            # -------------------------------------------------

            if verify_password(
                new,
                current_hash
            ):

                messagebox.showwarning(
                    "Password Error",
                    "New password must be different from the current password."
                )

                return

            # -------------------------------------------------
            # Hash new password
            # -------------------------------------------------

            new_hash = hash_password(
                new
            )

            cursor.execute(
                """
                UPDATE users
                SET password_hash = ?
                WHERE id = ?
                """,
                (
                    new_hash,
                    self.user_data["id"]
                )
            )

            connection.commit()

            # -------------------------------------------------
            # Clear fields
            # -------------------------------------------------

            self.current_password.delete(
                0,
                "end"
            )

            self.new_password.delete(
                0,
                "end"
            )

            self.confirm_password.delete(
                0,
                "end"
            )

            messagebox.showinfo(
                "Success",
                "Password changed successfully."
            )

        except Exception:

            if connection:

                try:
                    connection.rollback()
                except:
                    pass

            messagebox.showerror(
                "Error",
                "Unable to change password. Check the current password and try again.",
                parent=self,
            )

        finally:

            if connection:

                try:
                    connection.close()
                except:
                    pass


# =============================================================
# STANDALONE TEST
# =============================================================

if __name__ == "__main__":

    root = ctk.CTk()

    root.withdraw()

    test_user = {
        "id": 1,
        "username": "admin",
        "email": "admin@hostel.com",
        "role": "admin"
    }

    app = ProfileWindow(
        root,
        test_user
    )

    app.mainloop()
