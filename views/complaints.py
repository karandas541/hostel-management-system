import customtkinter as ctk
from tkinter import messagebox
from utils.authorization import require_menu_access, resolve_student, guard_authorization_errors
from utils.ui_theme import apply_professional_style

from services.complaint_service import (
    add_complaint,
    get_all_complaints,
    assign_complaint,
    update_complaint_status,
    resolve_complaint,
    close_complaint
)


class ComplaintManagement(ctk.CTkToplevel):

    def __init__(self, parent):
        require_menu_access(parent.user, "Complaints")
        super().__init__(parent)
        self.actor = parent.user

        self.title("Complaint Management")
        self.geometry("1200x750")
        self.minsize(1000, 650)

        # =========================================================
        # MAIN SCROLLABLE FRAME
        # =========================================================

        self.main_scroll = ctk.CTkScrollableFrame(
            self,
            corner_radius=0
        )
        self.main_scroll.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )
        self.configure(fg_color="#F3F6FB")

        # =========================================================
        # TITLE
        # =========================================================

        title = ctk.CTkLabel(
            self.main_scroll,
            text="Complaint Management",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(pady=20)

        # =========================================================
        # SUBMIT COMPLAINT
        # =========================================================

        submit_frame = ctk.CTkFrame(self.main_scroll)
        submit_frame.pack(
            fill="x",
            padx=20,
            pady=10
        )

        ctk.CTkLabel(
            submit_frame,
            text="Submit Complaint",
            font=ctk.CTkFont(size=20, weight="bold")
        ).grid(
            row=0,
            column=0,
            columnspan=8,
            pady=15
        )

        ctk.CTkLabel(
            submit_frame,
            text="Student ID"
        ).grid(
            row=1,
            column=0,
            padx=8,
            pady=8
        )

        self.student_id_entry = ctk.CTkEntry(
            submit_frame,
            placeholder_text="STU001"
        )
        self.student_id_entry.grid(
            row=1,
            column=1,
            padx=8,
            pady=8
        )

        ctk.CTkLabel(
            submit_frame,
            text="Category"
        ).grid(
            row=1,
            column=2,
            padx=8,
            pady=8
        )

        self.category_entry = ctk.CTkEntry(
            submit_frame,
            placeholder_text="Wi-Fi"
        )
        self.category_entry.grid(
            row=1,
            column=3,
            padx=8,
            pady=8
        )

        ctk.CTkLabel(
            submit_frame,
            text="Priority"
        ).grid(
            row=1,
            column=4,
            padx=8,
            pady=8
        )

        self.priority_box = ctk.CTkComboBox(
            submit_frame,
            values=[
                "Low",
                "Medium",
                "High",
                "Urgent"
            ]
        )
        self.priority_box.set("Medium")
        self.priority_box.grid(
            row=1,
            column=5,
            padx=8,
            pady=8
        )

        ctk.CTkLabel(
            submit_frame,
            text="Description"
        ).grid(
            row=2,
            column=0,
            padx=8,
            pady=8
        )

        self.description_entry = ctk.CTkEntry(
            submit_frame,
            width=500,
            placeholder_text="Describe your complaint"
        )
        self.description_entry.grid(
            row=2,
            column=1,
            columnspan=5,
            padx=8,
            pady=8
        )

        ctk.CTkButton(
            submit_frame,
            text="Submit Complaint",
            command=self.submit_complaint
        ).grid(
            row=3,
            column=0,
            columnspan=8,
            pady=15
        )

        # =========================================================
        # ASSIGN COMPLAINT
        # =========================================================

        assign_frame = self.assign_frame = ctk.CTkFrame(self.main_scroll)
        assign_frame.pack(
            fill="x",
            padx=20,
            pady=10
        )

        ctk.CTkLabel(
            assign_frame,
            text="Assign Complaint",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(
            row=0,
            column=0,
            columnspan=6,
            pady=10
        )

        ctk.CTkLabel(
            assign_frame,
            text="Complaint ID"
        ).grid(
            row=1,
            column=0,
            padx=8,
            pady=8
        )

        self.assign_id_entry = ctk.CTkEntry(
            assign_frame,
            placeholder_text="1"
        )
        self.assign_id_entry.grid(
            row=1,
            column=1,
            padx=8,
            pady=8
        )

        ctk.CTkLabel(
            assign_frame,
            text="Staff"
        ).grid(
            row=1,
            column=2,
            padx=8,
            pady=8
        )

        self.staff_entry = ctk.CTkEntry(
            assign_frame,
            placeholder_text="Maintenance Staff"
        )
        self.staff_entry.grid(
            row=1,
            column=3,
            padx=8,
            pady=8
        )

        ctk.CTkButton(
            assign_frame,
            text="Assign",
            command=self.assign_complaint_gui
        ).grid(
            row=1,
            column=4,
            padx=8,
            pady=8
        )

        # =========================================================
        # STATUS UPDATE
        # =========================================================

        status_frame = self.status_frame = ctk.CTkFrame(self.main_scroll)
        status_frame.pack(
            fill="x",
            padx=20,
            pady=10
        )

        ctk.CTkLabel(
            status_frame,
            text="Update Status",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(
            row=0,
            column=0,
            columnspan=6,
            pady=10
        )

        ctk.CTkLabel(
            status_frame,
            text="Complaint ID"
        ).grid(
            row=1,
            column=0,
            padx=8,
            pady=8
        )

        self.status_id_entry = ctk.CTkEntry(
            status_frame,
            placeholder_text="1"
        )
        self.status_id_entry.grid(
            row=1,
            column=1,
            padx=8,
            pady=8
        )

        self.status_box = ctk.CTkComboBox(
            status_frame,
            values=[
                "Submitted",
                "Assigned",
                "In Progress",
                "Resolved",
                "Closed"
            ]
        )
        self.status_box.set("In Progress")
        self.status_box.grid(
            row=1,
            column=2,
            padx=8,
            pady=8
        )

        ctk.CTkButton(
            status_frame,
            text="Update Status",
            command=self.update_status_gui
        ).grid(
            row=1,
            column=3,
            padx=8,
            pady=8
        )

        # =========================================================
        # RESOLVE COMPLAINT
        # =========================================================

        resolve_frame = self.resolve_frame = ctk.CTkFrame(self.main_scroll)
        resolve_frame.pack(
            fill="x",
            padx=20,
            pady=10
        )

        ctk.CTkLabel(
            resolve_frame,
            text="Resolve Complaint",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(
            row=0,
            column=0,
            columnspan=6,
            pady=10
        )

        ctk.CTkLabel(
            resolve_frame,
            text="Complaint ID"
        ).grid(
            row=1,
            column=0,
            padx=8,
            pady=8
        )

        self.resolve_id_entry = ctk.CTkEntry(
            resolve_frame,
            placeholder_text="1"
        )
        self.resolve_id_entry.grid(
            row=1,
            column=1,
            padx=8,
            pady=8
        )

        ctk.CTkLabel(
            resolve_frame,
            text="Remarks"
        ).grid(
            row=1,
            column=2,
            padx=8,
            pady=8
        )

        self.remarks_entry = ctk.CTkEntry(
            resolve_frame,
            width=450,
            placeholder_text="Problem fixed..."
        )
        self.remarks_entry.grid(
            row=1,
            column=3,
            padx=8,
            pady=8
        )

        ctk.CTkButton(
            resolve_frame,
            text="Resolve",
            command=self.resolve_complaint_gui
        ).grid(
            row=1,
            column=4,
            padx=8,
            pady=8
        )

        # =========================================================
        # SEARCH & FILTER
        # =========================================================

        filter_frame = ctk.CTkFrame(self.main_scroll)
        filter_frame.pack(
            fill="x",
            padx=20,
            pady=10
        )

        ctk.CTkLabel(
            filter_frame,
            text="Search & Filter Complaints",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(
            row=0,
            column=0,
            columnspan=8,
            pady=15
        )

        # Search
        ctk.CTkLabel(
            filter_frame,
            text="Search"
        ).grid(
            row=1,
            column=0,
            padx=8,
            pady=8
        )

        self.search_entry = ctk.CTkEntry(
            filter_frame,
            width=400,
            placeholder_text="Complaint ID / Student ID / Name / Category"
        )
        self.search_entry.grid(
            row=1,
            column=1,
            columnspan=2,
            padx=8,
            pady=8
        )

        # Status Filter
        ctk.CTkLabel(
            filter_frame,
            text="Status"
        ).grid(
            row=1,
            column=3,
            padx=8,
            pady=8
        )

        self.status_filter_box = ctk.CTkComboBox(
            filter_frame,
            values=[
                "All",
                "Submitted",
                "Assigned",
                "In Progress",
                "Resolved",
                "Closed"
            ],
            width=170
        )
        self.status_filter_box.set("All")
        self.status_filter_box.grid(
            row=1,
            column=4,
            padx=8,
            pady=8
        )

        # Priority Filter
        ctk.CTkLabel(
            filter_frame,
            text="Priority"
        ).grid(
            row=2,
            column=0,
            padx=8,
            pady=8
        )

        self.priority_filter_box = ctk.CTkComboBox(
            filter_frame,
            values=[
                "All",
                "Low",
                "Medium",
                "High",
                "Urgent"
            ],
            width=170
        )
        self.priority_filter_box.set("All")
        self.priority_filter_box.grid(
            row=2,
            column=1,
            padx=8,
            pady=8
        )

        # Buttons
        ctk.CTkButton(
            filter_frame,
            text="Search",
            width=120,
            command=self.load_complaints
        ).grid(
            row=2,
            column=2,
            padx=8,
            pady=8
        )

        ctk.CTkButton(
            filter_frame,
            text="Clear",
            width=120,
            command=self.clear_filters
        ).grid(
            row=2,
            column=3,
            padx=8,
            pady=8
        )

        ctk.CTkButton(
            filter_frame,
            text="Refresh",
            width=120,
            command=self.load_complaints
        ).grid(
            row=2,
            column=4,
            padx=8,
            pady=8
        )

        # Enter key = Search
        self.search_entry.bind(
            "<Return>",
            lambda event: self.load_complaints()
        )

        # =========================================================
        # COMPLAINT RECORDS
        # =========================================================

        records_frame = ctk.CTkFrame(self.main_scroll)
        records_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        ctk.CTkLabel(
            records_frame,
            text="Complaint Records",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(
            pady=10
        )

        self.records_textbox = ctk.CTkTextbox(
            records_frame,
            height=350
        )
        self.records_textbox.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=10
        )

        if self.actor["role"] == "student":
            _, student_id = resolve_student(self.actor)
            self.student_id_entry.insert(0, student_id)
            self.student_id_entry.configure(state="disabled")
            self.assign_frame.pack_forget()
            self.status_frame.pack_forget()
            self.resolve_frame.pack_forget()
        self.load_complaints()
        apply_professional_style(self)

    # =========================================================
    # SUBMIT
    # =========================================================

    @guard_authorization_errors
    def submit_complaint(self):

        student_id = self.student_id_entry.get().strip()
        category = self.category_entry.get().strip()
        description = self.description_entry.get().strip()
        priority = self.priority_box.get()

        if not student_id or not category or not description:
            messagebox.showwarning(
                "Validation",
                "Please fill all complaint fields."
            )
            return

        success, message = add_complaint(
            student_id,
            category,
            description,
            priority,
            actor=self.actor
        )

        if success:

            messagebox.showinfo(
                "Success",
                message
            )

            if self.actor["role"] == "admin":
                self.student_id_entry.delete(0, "end")
            self.category_entry.delete(0, "end")
            self.description_entry.delete(0, "end")

            self.priority_box.set("Medium")

            self.load_complaints()

        else:

            messagebox.showerror(
                "Error",
                message
            )

    # =========================================================
    # ASSIGN
    # =========================================================

    @guard_authorization_errors
    def assign_complaint_gui(self):

        complaint_id = self.assign_id_entry.get().strip()
        staff = self.staff_entry.get().strip()

        if not complaint_id or not staff:
            messagebox.showwarning(
                "Validation",
                "Complaint ID and staff are required."
            )
            return

        try:
            complaint_id = int(complaint_id)

        except ValueError:
            messagebox.showerror(
                "Error",
                "Complaint ID must be a number."
            )
            return

        success, message = assign_complaint(
            complaint_id,
            staff,
            actor=self.actor
        )

        if success:

            messagebox.showinfo(
                "Success",
                message
            )

            self.assign_id_entry.delete(0, "end")
            self.staff_entry.delete(0, "end")

            self.load_complaints()

        else:

            messagebox.showerror(
                "Error",
                message
            )

    # =========================================================
    # STATUS
    # =========================================================

    @guard_authorization_errors
    def update_status_gui(self):

        complaint_id = self.status_id_entry.get().strip()
        status = self.status_box.get()

        if not complaint_id:
            messagebox.showwarning(
                "Validation",
                "Complaint ID is required."
            )
            return

        try:
            complaint_id = int(complaint_id)

        except ValueError:
            messagebox.showerror(
                "Error",
                "Complaint ID must be a number."
            )
            return

        success, message = update_complaint_status(
            complaint_id,
            status,
            actor=self.actor
        )

        if success:

            messagebox.showinfo(
                "Success",
                message
            )

            self.status_id_entry.delete(0, "end")
            self.status_box.set("In Progress")

            self.load_complaints()

        else:

            messagebox.showerror(
                "Error",
                message
            )

    # =========================================================
    # RESOLVE
    # =========================================================

    @guard_authorization_errors
    def resolve_complaint_gui(self):

        complaint_id = self.resolve_id_entry.get().strip()
        remarks = self.remarks_entry.get().strip()

        if not complaint_id or not remarks:
            messagebox.showwarning(
                "Validation",
                "Complaint ID and remarks are required."
            )
            return

        try:
            complaint_id = int(complaint_id)

        except ValueError:
            messagebox.showerror(
                "Error",
                "Complaint ID must be a number."
            )
            return

        success, message = resolve_complaint(
            complaint_id,
            remarks,
            actor=self.actor
        )

        if success:

            messagebox.showinfo(
                "Success",
                message
            )

            self.resolve_id_entry.delete(0, "end")
            self.remarks_entry.delete(0, "end")

            self.load_complaints()

        else:

            messagebox.showerror(
                "Error",
                message
            )

    # =========================================================
    # LOAD / SEARCH / FILTER RECORDS
    # =========================================================

    @guard_authorization_errors
    def load_complaints(self):

        complaints = get_all_complaints(actor=self.actor)

        search_text = (
            self.search_entry.get()
            .strip()
            .lower()
        )

        status_filter = self.status_filter_box.get()
        priority_filter = self.priority_filter_box.get()

        self.records_textbox.delete(
            "1.0",
            "end"
        )

        header = (
            f"{'ID':<5}"
            f"{'Student':<12}"
            f"{'Name':<22}"
            f"{'Category':<15}"
            f"{'Priority':<10}"
            f"{'Status':<15}"
            f"{'Staff':<20}\n"
        )

        self.records_textbox.insert(
            "end",
            header
        )

        self.records_textbox.insert(
            "end",
            "-" * 100 + "\n"
        )

        found_count = 0

        for complaint in complaints:

            (
                complaint_id,
                student_id,
                name,
                category,
                description,
                priority,
                status,
                assigned_staff,
                created_at,
                resolved_at,
                resolution_remarks
            ) = complaint

            # -----------------------------------------------------
            # SEARCH
            # -----------------------------------------------------

            searchable_text = (
                f"{complaint_id} "
                f"{student_id} "
                f"{name or ''} "
                f"{category or ''}"
            ).lower()

            if search_text:
                if search_text not in searchable_text:
                    continue

            # -----------------------------------------------------
            # STATUS FILTER
            # -----------------------------------------------------

            if status_filter != "All":

                if status != status_filter:
                    continue

            # -----------------------------------------------------
            # PRIORITY FILTER
            # -----------------------------------------------------

            if priority_filter != "All":

                if priority != priority_filter:
                    continue

            # -----------------------------------------------------
            # DISPLAY
            # -----------------------------------------------------

            staff = (
                assigned_staff
                if assigned_staff
                else "-"
            )

            name_display = (
                name
                if name
                else "-"
            )

            category_display = (
                category
                if category
                else "-"
            )

            priority_display = (
                priority
                if priority
                else "-"
            )

            status_display = (
                status
                if status
                else "-"
            )

            row = (
                f"{str(complaint_id):<5}"
                f"{str(student_id):<12}"
                f"{str(name_display)[:20]:<22}"
                f"{str(category_display)[:13]:<15}"
                f"{str(priority_display)[:8]:<10}"
                f"{str(status_display)[:13]:<15}"
                f"{str(staff)[:18]:<20}\n"
            )

            self.records_textbox.insert(
                "end",
                row
            )

            found_count += 1

        # =========================================================
        # NO RECORDS
        # =========================================================

        if found_count == 0:

            self.records_textbox.insert(
                "end",
                "\nNo complaint records found."
            )

        # =========================================================
        # RECORD COUNT
        # =========================================================

        self.records_textbox.insert(
            "end",
            f"\n\nTotal Records: {found_count}"
        )
        apply_professional_style(self)

    # =========================================================
    # CLEAR FILTERS
    # =========================================================

    def clear_filters(self):

        self.search_entry.delete(
            0,
            "end"
        )

        self.status_filter_box.set(
            "All"
        )

        self.priority_filter_box.set(
            "All"
        )

        self.load_complaints()
