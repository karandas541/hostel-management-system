import customtkinter as ctk
from tkinter import messagebox

from services.student_service import (
    add_student,
    delete_student,
    get_all_students,
    get_student,
    update_student,
)
from utils.authorization import guard_authorization_errors, require_menu_access
from utils.ui_theme import apply_professional_style, get_palette


class StudentsWindow(ctk.CTkToplevel):
    """Scrollable student directory and admin record editor."""

    FIELD_DEFINITIONS = (
        ("student_id", "Student ID", "e.g. STU001", "entry"),
        ("name", "Full name", "Student name", "entry"),
        ("parent_name", "Parent / guardian", "Parent or guardian name", "entry"),
        ("gender", "Gender", None, "gender"),
        ("date_of_birth", "Date of birth", "YYYY-MM-DD", "entry"),
        ("phone", "Phone", "Contact number", "entry"),
        ("email", "Email", "name@example.com", "entry"),
        ("course", "Course", "Course / program", "entry"),
        ("branch", "Branch", "Department / branch", "entry"),
        ("year", "Year", "e.g. 1", "entry"),
        ("admission_date", "Admission date", "YYYY-MM-DD", "entry"),
        ("room_number", "Room number", "Assigned room", "entry"),
        ("bed_number", "Bed number", "Assigned bed", "entry"),
        ("status", "Status", None, "status"),
    )

    def __init__(self, parent):
        require_menu_access(parent.user, "Students")
        super().__init__(parent)
        self.actor = parent.user
        self._selected_student_id = None
        self._student_records = []

        self.title("Hostel Management System - Students")
        self.geometry("1200x800")
        self.minsize(950, 650)

        self.create_ui()
        self.load_students()
        apply_professional_style(self)

    def create_ui(self):
        self.main_frame = ctk.CTkScrollableFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=16)

        header = ctk.CTkFrame(self.main_frame, corner_radius=14)
        header.pack(fill="x", padx=4, pady=(4, 16))
        ctk.CTkLabel(
            header, text="Student Management",
            font=ctk.CTkFont(size=27, weight="bold"),
        ).pack(side="left", padx=22, pady=(16, 2))
        ctk.CTkLabel(
            header, text="Maintain student profiles and academic details",
            font=ctk.CTkFont(size=13), text_color=get_palette()["muted"],
        ).pack(side="left", padx=(0, 12), pady=(20, 16))
        ctk.CTkButton(
            header, text="Refresh", width=110, command=self.load_students,
        ).pack(side="right", padx=18, pady=16)

        self.form_frame = ctk.CTkFrame(self.main_frame, corner_radius=14)
        self.form_frame.pack(fill="x", padx=4, pady=(0, 16))
        self.form_title = ctk.CTkLabel(
            self.form_frame, text="Add a student",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self.form_title.grid(row=0, column=0, columnspan=3, sticky="w", padx=18, pady=(16, 8))

        for column in range(3):
            self.form_frame.grid_columnconfigure(column, weight=1, uniform="student-fields")

        self.fields = {}
        for index, (key, label, placeholder, kind) in enumerate(self.FIELD_DEFINITIONS):
            row, column = divmod(index, 3)
            ctk.CTkLabel(
                self.form_frame, text=label, anchor="w",
                font=ctk.CTkFont(size=12, weight="bold"),
            ).grid(row=1 + row * 2, column=column, sticky="ew", padx=12, pady=(6, 2))
            if kind == "gender":
                widget = ctk.CTkOptionMenu(
                    self.form_frame,
                    values=["Select", "Female", "Male", "Other", "Prefer not to say"],
                    height=36,
                )
                widget.set("Select")
            elif kind == "status":
                widget = ctk.CTkOptionMenu(
                    self.form_frame,
                    values=["Active", "Inactive", "Graduated", "Withdrawn"],
                    height=36,
                )
                widget.set("Active")
            else:
                widget = ctk.CTkEntry(
                    self.form_frame, placeholder_text=placeholder, height=36,
                )
            widget.grid(row=2 + row * 2, column=column, sticky="ew", padx=12, pady=(0, 4))
            self.fields[key] = widget

        address_row = 1 + ((len(self.FIELD_DEFINITIONS) + 2) // 3) * 2
        ctk.CTkLabel(
            self.form_frame, text="Address", anchor="w",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=address_row, column=0, columnspan=3, sticky="ew", padx=12, pady=(6, 2))
        self.address = ctk.CTkTextbox(self.form_frame, height=72, wrap="word")
        self.address.grid(row=address_row + 1, column=0, columnspan=3, sticky="ew", padx=12, pady=(0, 8))

        actions = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        actions.grid(row=address_row + 2, column=0, columnspan=3, sticky="ew", padx=8, pady=(4, 14))
        ctk.CTkButton(actions, text="Add Student", width=140, command=self.add_student).pack(side="left", padx=5)
        self.update_button = ctk.CTkButton(
            actions, text="Update Selected", width=150, state="disabled",
            command=self.update_selected_student,
        )
        self.update_button.pack(side="left", padx=5)
        ctk.CTkButton(
            actions, text="Clear Form", width=120, fg_color="#68788A",
            hover_color="#526173", command=self.clear_form,
        ).pack(side="left", padx=5)
        self.selection_hint = ctk.CTkLabel(
            actions, text="Choose Edit on a student card to update a record.",
            font=ctk.CTkFont(size=12), text_color=get_palette()["muted"],
        )
        self.selection_hint.pack(side="left", padx=12)

        directory = ctk.CTkFrame(self.main_frame, corner_radius=14)
        directory.pack(fill="both", expand=True, padx=4, pady=(0, 6))
        directory_header = ctk.CTkFrame(directory, fg_color="transparent")
        directory_header.pack(fill="x", padx=16, pady=(14, 4))
        ctk.CTkLabel(
            directory_header, text="Student Directory",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left")
        self.record_count = ctk.CTkLabel(
            directory_header, text="0 records", font=ctk.CTkFont(size=12),
            text_color=get_palette()["muted"],
        )
        self.record_count.pack(side="right")

        search_row = ctk.CTkFrame(directory, fg_color="transparent")
        search_row.pack(fill="x", padx=12, pady=(2, 10))
        self.search_entry = ctk.CTkEntry(
            search_row, placeholder_text="Search student ID, name, email or course", width=420,
        )
        self.search_entry.pack(side="left", padx=5, pady=5)
        self.search_entry.bind("<Return>", self.search_students)
        ctk.CTkButton(search_row, text="Search", width=100, command=self.search_students).pack(side="left", padx=5)
        ctk.CTkButton(
            search_row, text="Clear Search", width=120, fg_color="#68788A",
            hover_color="#526173", command=self.clear_search,
        ).pack(side="left", padx=5)

        self.students_list = ctk.CTkFrame(directory, fg_color="transparent")
        self.students_list.pack(fill="x", padx=10, pady=(0, 12))

    def _form_data(self):
        data = {key: widget.get().strip() for key, widget in self.fields.items()}
        if data["gender"] == "Select":
            data["gender"] = ""
        data["address"] = self.address.get("1.0", "end").strip()
        return data

    @guard_authorization_errors
    def add_student(self):
        data = self._form_data()
        try:
            success, message = add_student(
                data.pop("student_id"), data.pop("name"), data.pop("email"),
                data.pop("phone"), data.pop("course"), data.pop("year"),
                data.pop("gender"), actor=self.actor, **data,
            )
        except ValueError as error:
            messagebox.showwarning("Check student details", str(error), parent=self)
            return
        if not success:
            messagebox.showerror("Could not add student", message, parent=self)
            return
        messagebox.showinfo("Student added", message, parent=self)
        self.clear_form()
        self.load_students()

    @guard_authorization_errors
    def update_selected_student(self):
        if not self._selected_student_id:
            messagebox.showwarning("Select a student", "Choose Edit on a student record first.", parent=self)
            return
        try:
            success, message = update_student(
                self._selected_student_id, self._form_data(), actor=self.actor,
            )
        except ValueError as error:
            messagebox.showwarning("Check student details", str(error), parent=self)
            return
        if not success:
            messagebox.showerror("Could not update student", message, parent=self)
            return
        messagebox.showinfo("Student updated", message, parent=self)
        self.clear_form()
        self.load_students()

    @guard_authorization_errors
    @guard_authorization_errors
    def load_students(self):
        try:
            self._student_records = get_all_students(actor=self.actor)
        except Exception:
            messagebox.showerror(
                "Could not load students",
                "Student records could not be loaded. Check the database and try again.",
                parent=self,
            )
            return
        self.display_students()

    @guard_authorization_errors
    def search_students(self, event=None):
        self.display_students()
        return "break" if event is not None else None

    def display_students(self):
        query = self.search_entry.get().strip().casefold()
        for widget in self.students_list.winfo_children():
            widget.destroy()

        records = self._student_records
        if query:
            records = [
                student for student in records
                if query in " ".join(str(student.get(key) or "") for key in (
                    "student_id", "name", "email", "course", "branch",
                )).casefold()
            ]

        count = len(records)
        self.record_count.configure(text=f"{count} student{'s' if count != 1 else ''}")
        if not records:
            ctk.CTkLabel(
                self.students_list,
                text="No matching students. Try another search or add a new student.",
                text_color=get_palette()["muted"],
            ).pack(fill="x", padx=14, pady=26)
            apply_professional_style(self)
            return

        for student in records:
            self._create_student_card(student)
        apply_professional_style(self)

    def _create_student_card(self, student):
        colors = get_palette()
        card = ctk.CTkFrame(
            self.students_list, corner_radius=12,
            border_width=1, border_color=colors["border"],
        )
        card.pack(fill="x", padx=6, pady=5)

        detail = ctk.CTkFrame(card, fg_color="transparent")
        detail.pack(side="left", fill="both", expand=True, padx=14, pady=10)
        ctk.CTkLabel(
            detail, text=student.get("name") or "Unnamed student", anchor="w",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w")
        line = "  ·  ".join(value for value in (
            student.get("student_id"), student.get("course"), student.get("branch"),
            f"Year {student['year']}" if student.get("year") else None,
        ) if value)
        ctk.CTkLabel(
            detail, text=line or "Student details not provided", anchor="w",
            font=ctk.CTkFont(size=12), text_color=colors["muted"],
        ).pack(anchor="w", pady=(2, 0))

        room = student.get("room_number")
        bed = student.get("bed_number")
        contact = "  ·  ".join(value for value in (
            student.get("email"), student.get("phone"),
            f"Room {room}" + (f", Bed {bed}" if bed else "") if room else None,
        ) if value)
        if contact:
            ctk.CTkLabel(
                detail, text=contact, anchor="w", font=ctk.CTkFont(size=11),
                text_color=colors["muted"],
            ).pack(anchor="w", pady=(2, 0))

        status = student.get("status") or "Active"
        ctk.CTkLabel(
            card, text=status, corner_radius=8,
            fg_color=colors["surface_alt"], text_color=colors["accent"],
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(side="left", padx=8, ipadx=8, ipady=5)
        ctk.CTkButton(
            card, text="Details", width=80, command=lambda record=student: self.view_student(record["student_id"]),
        ).pack(side="right", padx=(5, 10), pady=10)
        ctk.CTkButton(
            card, text="Edit", width=70, fg_color="#536C82", hover_color="#40566A",
            command=lambda record=student: self.select_student(record),
        ).pack(side="right", padx=5, pady=10)
        ctk.CTkButton(
            card, text="Delete", width=78, fg_color=colors["danger"], hover_color="#963B3B",
            command=lambda record=student: self.delete_student_record(record["student_id"]),
        ).pack(side="right", padx=5, pady=10)

    def select_student(self, student):
        self.clear_form()
        self._selected_student_id = student["student_id"]
        for key, widget in self.fields.items():
            value = student.get(key)
            if isinstance(widget, ctk.CTkOptionMenu):
                widget.set(str(value) if value else ("Select" if key == "gender" else "Active"))
            else:
                widget.insert(0, str(value) if value is not None else "")
        self.address.insert("1.0", student.get("address") or "")
        self.form_title.configure(text=f"Edit student · {self._selected_student_id}")
        self.update_button.configure(state="normal")
        self.selection_hint.configure(text="Update Selected saves the changes to this record.")

    @guard_authorization_errors
    def view_student(self, student_id):
        try:
            student = get_student(student_id, actor=self.actor)
        except Exception:
            messagebox.showerror(
                "Could not load student",
                "Student details could not be loaded. Please try again.",
                parent=self,
            )
            return
        if student is None:
            messagebox.showwarning("Student not found", "Refresh the directory and try again.", parent=self)
            self.load_students()
            return

        detail_window = ctk.CTkToplevel(self)
        detail_window.title(f"Student Details · {student_id}")
        detail_window.geometry("700x760")
        detail_window.minsize(550, 500)
        detail_window.transient(self)
        body = ctk.CTkScrollableFrame(detail_window, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(
            body, text=student.get("name") or "Student Details",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(anchor="w", padx=8, pady=(8, 2))
        ctk.CTkLabel(
            body, text=f"Student ID  ·  {student['student_id']}",
            text_color=get_palette()["muted"],
        ).pack(anchor="w", padx=8, pady=(0, 16))

        labels = (
            ("Parent / guardian", "parent_name"), ("Gender", "gender"),
            ("Date of birth", "date_of_birth"), ("Phone", "phone"),
            ("Email", "email"), ("Address", "address"), ("Course", "course"),
            ("Branch", "branch"), ("Year", "year"), ("Admission date", "admission_date"),
            ("Room number", "room_number"), ("Bed number", "bed_number"),
            ("Status", "status"), ("Created", "created_at"),
        )
        for label, key in labels:
            value = student.get(key)
            row = ctk.CTkFrame(body, corner_radius=9)
            row.pack(fill="x", padx=6, pady=4)
            ctk.CTkLabel(
                row, text=label, width=175, anchor="w",
                font=ctk.CTkFont(size=12, weight="bold"),
            ).pack(side="left", padx=12, pady=10)
            ctk.CTkLabel(
                row, text=str(value) if value not in (None, "") else "—",
                anchor="w", justify="left", wraplength=420,
            ).pack(side="left", fill="x", expand=True, padx=8, pady=10)
        ctk.CTkButton(body, text="Close", width=110, command=detail_window.destroy).pack(pady=14)
        apply_professional_style(detail_window)
        detail_window.transient(self)
        detail_window.lift()

    @guard_authorization_errors
    def delete_student_record(self, student_id):
        if not messagebox.askyesno(
            "Delete student", f"Permanently delete student {student_id}?",
            detail="Deletion is blocked when the student has linked history or a login account.",
            parent=self,
        ):
            return
        success, message = delete_student(student_id, actor=self.actor)
        if success:
            if self._selected_student_id == student_id:
                self.clear_form()
            self.load_students()
            messagebox.showinfo("Student deleted", message, parent=self)
        else:
            messagebox.showwarning("Student kept", message, parent=self)

    def clear_form(self):
        for key, widget in self.fields.items():
            if isinstance(widget, ctk.CTkOptionMenu):
                widget.set("Select" if key == "gender" else "Active")
            else:
                widget.delete(0, "end")
        self.address.delete("1.0", "end")
        self._selected_student_id = None
        self.form_title.configure(text="Add a student")
        self.update_button.configure(state="disabled")
        self.selection_hint.configure(text="Choose Edit on a student card to update a record.")

    def clear_search(self):
        self.search_entry.delete(0, "end")
        self.display_students()


if __name__ == "__main__":
    print("StudentsWindow must be opened from the main application.")
