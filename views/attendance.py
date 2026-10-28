import customtkinter as ctk
from tkinter import messagebox
from utils.authorization import require_menu_access, guard_authorization_errors
from utils.authorization import resolve_student
from utils.ui_theme import apply_professional_style

from services.attendance_service import (
    mark_entry,
    mark_exit,
    get_all_attendance
)


class AttendanceManagement(ctk.CTkToplevel):

    def __init__(self, parent):
        require_menu_access(parent.user, "Attendance")
        super().__init__(parent)
        self.actor = parent.user

        self.title("Attendance Management")
        self.geometry("1150x750")

        # =========================
        # TITLE
        # =========================

        title = ctk.CTkLabel(
            self,
            text="Attendance Management",
            font=ctk.CTkFont(size=28, weight="bold")
        )

        title.pack(pady=20)

        # =========================
        # MAIN SCROLLABLE FRAME
        # =========================

        self.main_frame = ctk.CTkScrollableFrame(self)

        self.main_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        # =========================
        # ENTRY / EXIT FRAME
        # =========================

        action_frame = ctk.CTkFrame(self.main_frame)

        action_frame.pack(
            fill="x",
            padx=10,
            pady=10
        )

        ctk.CTkLabel(
            action_frame,
            text="Student Attendance",
            font=ctk.CTkFont(size=20, weight="bold")
        ).grid(
            row=0,
            column=0,
            columnspan=4,
            pady=15
        )

        # =========================
        # STUDENT ID
        # =========================

        ctk.CTkLabel(
            action_frame,
            text="Student ID"
        ).grid(
            row=1,
            column=0,
            padx=10,
            pady=10
        )

        self.student_id_entry = ctk.CTkEntry(
            action_frame,
            placeholder_text="STU001",
            width=180
        )

        self.student_id_entry.grid(
            row=1,
            column=1,
            padx=10,
            pady=10
        )

        # =========================
        # MARK ENTRY
        # =========================

        ctk.CTkButton(
            action_frame,
            text="Mark Entry",
            command=self.mark_entry_gui,
            width=120
        ).grid(
            row=1,
            column=2,
            padx=10,
            pady=10
        )

        # =========================
        # MARK EXIT
        # =========================

        ctk.CTkButton(
            action_frame,
            text="Mark Exit",
            command=self.mark_exit_gui,
            width=120
        ).grid(
            row=1,
            column=3,
            padx=10,
            pady=10
        )

        # =========================
        # SEARCH / FILTER FRAME
        # =========================

        search_frame = ctk.CTkFrame(self.main_frame)

        search_frame.pack(
            fill="x",
            padx=10,
            pady=10
        )

        ctk.CTkLabel(
            search_frame,
            text="Search Attendance",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(
            row=0,
            column=0,
            columnspan=5,
            pady=12
        )

        # Search Entry

        ctk.CTkLabel(
            search_frame,
            text="Search"
        ).grid(
            row=1,
            column=0,
            padx=10,
            pady=10
        )

        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Student ID, Name or Date",
            width=250
        )

        self.search_entry.grid(
            row=1,
            column=1,
            padx=10,
            pady=10
        )

        # Search Button

        ctk.CTkButton(
            search_frame,
            text="Search",
            command=self.search_attendance,
            width=100
        ).grid(
            row=1,
            column=2,
            padx=10,
            pady=10
        )

        # Status Filter

        ctk.CTkLabel(
            search_frame,
            text="Status"
        ).grid(
            row=1,
            column=3,
            padx=10,
            pady=10
        )

        self.status_filter = ctk.CTkComboBox(
            search_frame,
            values=[
                "All",
                "Inside",
                "Exited"
            ],
            width=130,
            command=lambda value: self.search_attendance()
        )

        self.status_filter.set("All")

        self.status_filter.grid(
            row=1,
            column=4,
            padx=10,
            pady=10
        )

        # Clear Button

        ctk.CTkButton(
            search_frame,
            text="Clear",
            command=self.clear_search,
            width=100
        ).grid(
            row=1,
            column=5,
            padx=10,
            pady=10
        )

        # Enter key search

        self.search_entry.bind(
            "<Return>",
            lambda event: self.search_attendance()
        )

        # =========================
        # RECORDS FRAME
        # =========================

        records_frame = ctk.CTkFrame(self.main_frame)

        records_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        ctk.CTkLabel(
            records_frame,
            text="Attendance Records",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(
            pady=10
        )

        # =========================
        # RECORDS TEXTBOX
        # =========================

        self.records_textbox = ctk.CTkTextbox(
            records_frame,
            height=350,
            font=ctk.CTkFont(
                family="Consolas",
                size=13
            )
        )

        self.records_textbox.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=10
        )

        # =========================
        # REFRESH BUTTON
        # =========================

        ctk.CTkButton(
            records_frame,
            text="Refresh",
            command=self.load_attendance,
            width=120
        ).pack(
            pady=10
        )

        # =========================
        # INITIAL LOAD
        # =========================

        if self.actor["role"] == "student":
            _, student_id = resolve_student(self.actor)
            self.student_id_entry.insert(0, student_id)
            self.student_id_entry.configure(state="disabled")
        self.load_attendance()
        apply_professional_style(self)

    # =====================================================
    # MARK ENTRY
    # =====================================================

    @guard_authorization_errors
    def mark_entry_gui(self):

        student_id = self.student_id_entry.get().strip()

        if not student_id:

            messagebox.showwarning(
                "Validation",
                "Please enter Student ID."
            )

            self.student_id_entry.focus()

            return

        success, message = mark_entry(student_id, actor=self.actor)

        if success:

            messagebox.showinfo(
                "Success",
                message
            )

            if self.actor["role"] == "admin":
                self.student_id_entry.delete(0, "end")

            self.load_attendance()

        else:

            messagebox.showerror(
                "Error",
                message
            )

    # =====================================================
    # MARK EXIT
    # =====================================================

    @guard_authorization_errors
    def mark_exit_gui(self):

        student_id = self.student_id_entry.get().strip()

        if not student_id:

            messagebox.showwarning(
                "Validation",
                "Please enter Student ID."
            )

            self.student_id_entry.focus()

            return

        success, message = mark_exit(student_id, actor=self.actor)

        if success:

            messagebox.showinfo(
                "Success",
                message
            )

            if self.actor["role"] == "admin":
                self.student_id_entry.delete(0, "end")

            self.load_attendance()

        else:

            messagebox.showerror(
                "Error",
                message
            )

    # =====================================================
    # SEARCH ATTENDANCE
    # =====================================================

    @guard_authorization_errors
    def search_attendance(self):

        search_text = self.search_entry.get().strip().lower()

        selected_status = self.status_filter.get()

        attendance = get_all_attendance(actor=self.actor)

        filtered_records = []

        for record in attendance:

            (
                attendance_id,
                student_id,
                name,
                entry_time,
                exit_time,
                attendance_date
            ) = record[:6]

            # Convert values to string safely

            student_id_text = str(student_id).lower()
            name_text = str(name).lower()
            date_text = str(attendance_date).lower()

            # Search condition

            matches_search = (
                not search_text
                or search_text in student_id_text
                or search_text in name_text
                or search_text in date_text
            )

            # Status condition

            if selected_status == "Inside":

                matches_status = not exit_time

            elif selected_status == "Exited":

                matches_status = bool(exit_time)

            else:

                matches_status = True

            if matches_search and matches_status:

                filtered_records.append(record)

        self.display_attendance(filtered_records)

    # =====================================================
    # CLEAR SEARCH
    # =====================================================

    @guard_authorization_errors
    def clear_search(self):

        self.search_entry.delete(
            0,
            "end"
        )

        self.status_filter.set("All")

        self.load_attendance()

    # =====================================================
    # LOAD ATTENDANCE
    # =====================================================

    @guard_authorization_errors
    def load_attendance(self):

        attendance = get_all_attendance(actor=self.actor)

        self.display_attendance(attendance)
        apply_professional_style(self)

    # =====================================================
    # DISPLAY ATTENDANCE
    # =====================================================

    def display_attendance(self, attendance):

        self.records_textbox.delete(
            "1.0",
            "end"
        )

        if not attendance:

            self.records_textbox.insert(
                "end",
                "No attendance records found."
            )

            return

        # =========================
        # HEADER
        # =========================

        header = (
            f"{'ID':<5}"
            f"{'Student ID':<15}"
            f"{'Name':<22}"
            f"{'Entry Time':<22}"
            f"{'Exit Time':<22}"
            f"{'Date':<15}"
            f"{'Status':<10}\n"
        )

        self.records_textbox.insert(
            "end",
            header
        )

        self.records_textbox.insert(
            "end",
            "-" * 115 + "\n"
        )

        # =========================
        # RECORDS
        # =========================

        for record in attendance:

            (
                attendance_id,
                student_id,
                name,
                entry_time,
                exit_time,
                attendance_date
            ) = record[:6]

            if exit_time:

                exit_time_display = str(exit_time)

                status = "Exited"

            else:

                exit_time_display = "-"

                status = "Inside"

            row = (
                f"{str(attendance_id):<5}"
                f"{str(student_id):<15}"
                f"{str(name):<22}"
                f"{str(entry_time):<22}"
                f"{exit_time_display:<22}"
                f"{str(attendance_date):<15}"
                f"{status:<10}\n"
            )

            self.records_textbox.insert(
                "end",
                row
            )
