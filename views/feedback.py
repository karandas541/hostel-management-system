import customtkinter as ctk
from tkinter import messagebox
from utils.authorization import require_menu_access, guard_authorization_errors
from utils.authorization import resolve_student
from utils.ui_theme import apply_professional_style


from services.feedback_service import (
    add_feedback,
    get_all_feedback,
    get_overall_satisfaction
)


class FeedbackManagement(ctk.CTkToplevel):

    def __init__(self, parent):
        require_menu_access(parent.user, "Feedback")
        super().__init__(parent)
        self.actor = parent.user

        self.title("Feedback & Satisfaction")
        self.geometry("1250x850")
        self.minsize(1100, 700)

        self.create_ui()
        if self.actor["role"] == "student":
            _, student_id = resolve_student(self.actor)
            self.student_id_entry.insert(0, student_id)
            self.student_id_entry.configure(state="disabled")
        self.load_feedback()
        apply_professional_style(self)

    # ========================================================
    # CREATE UI
    # ========================================================

    def create_ui(self):

        # ====================================================
        # HEADER
        # ====================================================

        header = ctk.CTkFrame(
            self,
            corner_radius=0
        )

        header.pack(
            fill="x"
        )

        title = ctk.CTkLabel(
            header,
            text="Feedback & Satisfaction",
            font=ctk.CTkFont(
                size=28,
                weight="bold"
            )
        )

        title.pack(
            side="left",
            padx=25,
            pady=20
        )

        ctk.CTkButton(
            header,
            text="Refresh",
            width=100,
            command=self.load_feedback
        ).pack(
            side="right",
            padx=25
        )

        # ====================================================
        # SCROLLABLE MAIN AREA
        # ====================================================

        self.scrollable_frame = ctk.CTkScrollableFrame(
            self,
            corner_radius=0
        )

        self.scrollable_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        # ====================================================
        # FEEDBACK FORM
        # ====================================================

        form_frame = ctk.CTkFrame(
            self.scrollable_frame
        )

        form_frame.pack(
            fill="x",
            padx=15,
            pady=10
        )

        ctk.CTkLabel(
            form_frame,
            text="Submit Feedback",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        ).grid(
            row=0,
            column=0,
            columnspan=6,
            pady=15,
            padx=15,
            sticky="w"
        )

        # ====================================================
        # STUDENT ID
        # ====================================================

        ctk.CTkLabel(
            form_frame,
            text="Student ID"
        ).grid(
            row=1,
            column=0,
            padx=10,
            pady=10,
            sticky="e"
        )

        self.student_id_entry = ctk.CTkEntry(
            form_frame,
            width=180,
            placeholder_text="STU001"
        )

        self.student_id_entry.grid(
            row=1,
            column=1,
            padx=10,
            pady=10
        )

        # ====================================================
        # EVALUATION PERIOD
        # ====================================================

        ctk.CTkLabel(
            form_frame,
            text="Evaluation Period"
        ).grid(
            row=1,
            column=2,
            padx=10,
            pady=10,
            sticky="e"
        )

        self.period_box = ctk.CTkComboBox(
            form_frame,
            width=180,
            values=[
                "Weekly",
                "Monthly",
                "Quarterly",
                "Yearly"
            ]
        )

        self.period_box.set(
            "Monthly"
        )

        self.period_box.grid(
            row=1,
            column=3,
            padx=10,
            pady=10
        )

        # ====================================================
        # RATING FIELDS
        # ====================================================

        rating_fields = [
            ("Room Quality", "room_quality"),
            ("Cleanliness", "cleanliness"),
            ("Food Quality", "food_quality"),
            ("Maintenance", "maintenance"),
            ("Wi-Fi", "wifi"),
            ("Security", "security"),
            ("Hostel Staff", "hostel_staff"),
            ("Common Facilities", "common_facilities"),
            ("Overall Experience", "overall_experience")
        ]

        self.rating_boxes = {}

        for index, (label, key) in enumerate(rating_fields):

            row = (index // 3) + 2
            column = (index % 3) * 2

            ctk.CTkLabel(
                form_frame,
                text=label
            ).grid(
                row=row,
                column=column,
                padx=10,
                pady=8,
                sticky="e"
            )

            rating_box = ctk.CTkComboBox(
                form_frame,
                width=100,
                values=[
                    "1",
                    "2",
                    "3",
                    "4",
                    "5"
                ]
            )

            rating_box.set(
                "5"
            )

            rating_box.grid(
                row=row,
                column=column + 1,
                padx=10,
                pady=8
            )

            self.rating_boxes[key] = rating_box

        # ====================================================
        # COMMENTS
        # ====================================================

        comments_row = 5

        ctk.CTkLabel(
            form_frame,
            text="Comments"
        ).grid(
            row=comments_row,
            column=0,
            padx=10,
            pady=10,
            sticky="e"
        )

        self.comments_entry = ctk.CTkEntry(
            form_frame,
            width=650,
            placeholder_text="Write your feedback..."
        )

        self.comments_entry.grid(
            row=comments_row,
            column=1,
            columnspan=5,
            padx=10,
            pady=10,
            sticky="w"
        )

        # ====================================================
        # SUBMIT BUTTON
        # ====================================================

        ctk.CTkButton(
            form_frame,
            text="Submit Feedback",
            width=180,
            command=self.submit_feedback
        ).grid(
            row=6,
            column=0,
            columnspan=6,
            pady=15
        )

        # ====================================================
        # SATISFACTION SUMMARY
        # ====================================================

        summary_frame = ctk.CTkFrame(
            self.scrollable_frame
        )

        summary_frame.pack(
            fill="x",
            padx=15,
            pady=10
        )

        ctk.CTkLabel(
            summary_frame,
            text="Satisfaction Summary",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        ).pack(
            pady=(15, 5)
        )

        self.score_label = ctk.CTkLabel(
            summary_frame,
            text="Overall Satisfaction: 0.00 / 5",
            font=ctk.CTkFont(
                size=22,
                weight="bold"
            )
        )

        self.score_label.pack(
            pady=8
        )

        self.category_score_label = ctk.CTkLabel(
            summary_frame,
            text="Category averages will appear here.",
            justify="left",
            font=ctk.CTkFont(
                size=14
            )
        )

        self.category_score_label.pack(
            pady=(5, 15)
        )

        # ====================================================
        # SEARCH / FILTER
        # ====================================================

        filter_frame = ctk.CTkFrame(
            self.scrollable_frame
        )

        filter_frame.pack(
            fill="x",
            padx=15,
            pady=10
        )

        ctk.CTkLabel(
            filter_frame,
            text="Search / Filter Feedback",
            font=ctk.CTkFont(
                size=18,
                weight="bold"
            )
        ).grid(
            row=0,
            column=0,
            columnspan=5,
            padx=15,
            pady=(15, 10),
            sticky="w"
        )

        # Search

        self.search_entry = ctk.CTkEntry(
            filter_frame,
            width=300,
            placeholder_text="Search Student ID or Name"
        )

        self.search_entry.grid(
            row=1,
            column=0,
            padx=10,
            pady=10
        )

        self.search_entry.bind(
            "<Return>",
            self.search_feedback
        )

        # Period Filter

        self.period_filter = ctk.CTkComboBox(
            filter_frame,
            width=180,
            values=[
                "All",
                "Weekly",
                "Monthly",
                "Quarterly",
                "Yearly"
            ],
            command=self.period_filter_changed
        )

        self.period_filter.set(
            "All"
        )

        self.period_filter.grid(
            row=1,
            column=1,
            padx=10,
            pady=10
        )

        # Search Button

        ctk.CTkButton(
            filter_frame,
            text="Search",
            width=100,
            command=self.search_feedback
        ).grid(
            row=1,
            column=2,
            padx=10,
            pady=10
        )

        # Clear Button

        ctk.CTkButton(
            filter_frame,
            text="Clear",
            width=100,
            command=self.clear_filter
        ).grid(
            row=1,
            column=3,
            padx=10,
            pady=10
        )

        # ====================================================
        # FEEDBACK RECORDS
        # ====================================================

        ctk.CTkLabel(
            self.scrollable_frame,
            text="Feedback Records",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        ).pack(
            anchor="w",
            padx=15,
            pady=(15, 5)
        )

        self.records_textbox = ctk.CTkTextbox(
            self.scrollable_frame,
            height=350,
            font=ctk.CTkFont(
                size=12
            )
        )

        self.records_textbox.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=10
        )

        # ====================================================
        # BOTTOM REFRESH
        # ====================================================

        ctk.CTkButton(
            self.scrollable_frame,
            text="Refresh Feedback Records",
            width=180,
            command=self.load_feedback
        ).pack(
            pady=10
        )

        ctk.CTkLabel(
            self.scrollable_frame,
            text=""
        ).pack(
            pady=20
        )

    # ========================================================
    # SUBMIT FEEDBACK
    # ========================================================

    @guard_authorization_errors
    def submit_feedback(self):

        student_id = (
            self.student_id_entry
            .get()
            .strip()
        )

        period = (
            self.period_box
            .get()
            .strip()
        )

        comments = (
            self.comments_entry
            .get()
            .strip()
        )

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not student_id:

            messagebox.showwarning(
                "Validation",
                "Please enter Student ID."
            )

            return

        ratings = {}

        try:

            for key, box in self.rating_boxes.items():

                value = int(
                    box.get()
                )

                if value < 1 or value > 5:

                    messagebox.showwarning(
                        "Invalid Rating",
                        "Rating must be between 1 and 5."
                    )

                    return

                ratings[key] = value

        except ValueError:

            messagebox.showwarning(
                "Invalid Rating",
                "Please select valid ratings between 1 and 5."
            )

            return

        # ----------------------------------------------------
        # ADD FEEDBACK
        # ----------------------------------------------------

        success, message = add_feedback(
            student_id,
            ratings["room_quality"],
            ratings["cleanliness"],
            ratings["food_quality"],
            ratings["maintenance"],
            ratings["wifi"],
            ratings["security"],
            ratings["hostel_staff"],
            ratings["common_facilities"],
            ratings["overall_experience"],
            comments,
            period,
            actor=self.actor
        )

        if success:

            messagebox.showinfo(
                "Success",
                message
            )

            # Clear form

            if self.actor["role"] == "admin":
                self.student_id_entry.delete(0, "end")

            self.comments_entry.delete(
                0,
                "end"
            )

            self.period_box.set(
                "Monthly"
            )

            for box in self.rating_boxes.values():

                box.set(
                    "5"
                )

            self.load_feedback()

        else:

            messagebox.showerror(
                "Error",
                message
            )

    # ========================================================
    # LOAD FEEDBACK
    # ========================================================

    @guard_authorization_errors
    def load_feedback(self):

        feedback = get_all_feedback(actor=self.actor)

        self.display_feedback(
            feedback
        )

        self.update_summary(
            feedback
        )
        apply_professional_style(self)

    # ========================================================
    # DISPLAY FEEDBACK
    # ========================================================

    def display_feedback(self, feedback):

        self.records_textbox.delete(
            "1.0",
            "end"
        )

        if not feedback:

            self.records_textbox.insert(
                "end",
                "No feedback records found."
            )

            return

        header = (
            f"{'ID':<5}"
            f"{'Student':<12}"
            f"{'Name':<20}"
            f"{'Room':<6}"
            f"{'Clean':<7}"
            f"{'Food':<6}"
            f"{'Maint.':<7}"
            f"{'WiFi':<6}"
            f"{'Security':<9}"
            f"{'Staff':<7}"
            f"{'Facilities':<11}"
            f"{'Overall':<8}"
            f"{'Period':<12}\n"
        )

        self.records_textbox.insert(
            "end",
            header
        )

        self.records_textbox.insert(
            "end",
            "-" * 130 + "\n"
        )

        for record in feedback:

            (
                feedback_id,
                student_id,
                name,
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
                evaluation_period,
                created_at
            ) = record

            row = (
                f"{feedback_id:<5}"
                f"{str(student_id):<12}"
                f"{str(name):<20}"
                f"{room_quality:<6}"
                f"{cleanliness:<7}"
                f"{food_quality:<6}"
                f"{maintenance:<7}"
                f"{wifi:<6}"
                f"{security:<9}"
                f"{hostel_staff:<7}"
                f"{common_facilities:<11}"
                f"{overall_experience:<8}"
                f"{str(evaluation_period):<12}\n"
            )

            self.records_textbox.insert(
                "end",
                row
            )

            # Comments and date

            self.records_textbox.insert(
                "end",
                f"    Comment: {comments or '-'}"
                f"    | Date: {created_at}\n"
            )

            self.records_textbox.insert(
                "end",
                "\n"
            )

    # ========================================================
    # UPDATE SUMMARY
    # ========================================================

    def update_summary(self, feedback):

        # Overall score from service

        score = get_overall_satisfaction(actor=self.actor)

        self.score_label.configure(
            text=f"Overall Satisfaction: {score:.2f} / 5"
        )

        # ----------------------------------------------------
        # No feedback
        # ----------------------------------------------------

        if not feedback:

            self.category_score_label.configure(
                text="No feedback available for category analysis."
            )

            return

        # ----------------------------------------------------
        # Category totals
        # ----------------------------------------------------

        category_indexes = {
            "Room Quality": 3,
            "Cleanliness": 4,
            "Food Quality": 5,
            "Maintenance": 6,
            "Wi-Fi": 7,
            "Security": 8,
            "Hostel Staff": 9,
            "Common Facilities": 10,
            "Overall Experience": 11
        }

        category_totals = {}
        category_counts = {}

        for category in category_indexes:

            category_totals[category] = 0
            category_counts[category] = 0

        for record in feedback:

            for category, index in category_indexes.items():

                value = record[index]

                if value is not None:

                    category_totals[category] += float(
                        value
                    )

                    category_counts[category] += 1

        # ----------------------------------------------------
        # Create summary text
        # ----------------------------------------------------

        summary_lines = []

        for category in category_indexes:

            count = category_counts[category]

            if count > 0:

                average = (
                    category_totals[category]
                    / count
                )

                summary_lines.append(
                    f"{category}: {average:.2f} / 5"
                )

        summary_text = "\n".join(
            summary_lines
        )

        self.category_score_label.configure(
            text=summary_text
        )

    # ========================================================
    # SEARCH FEEDBACK
    # ========================================================

    @guard_authorization_errors
    def search_feedback(self, event=None):

        query = (
            self.search_entry
            .get()
            .strip()
            .lower()
        )

        selected_period = (
            self.period_filter
            .get()
            .strip()
            .lower()
        )

        feedback = get_all_feedback(actor=self.actor)

        filtered_feedback = []

        for record in feedback:

            (
                feedback_id,
                student_id,
                name,
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
                evaluation_period,
                created_at
            ) = record

            student_id_text = str(
                student_id
            ).lower()

            name_text = str(
                name
            ).lower()

            period_text = str(
                evaluation_period
            ).lower()

            # Search condition

            search_match = (
                not query
                or query in student_id_text
                or query in name_text
            )

            # Period condition

            if selected_period == "all":

                period_match = True

            else:

                period_match = (
                    period_text
                    == selected_period
                )

            if search_match and period_match:

                filtered_feedback.append(
                    record
                )

        self.display_feedback(
            filtered_feedback
        )

    # ========================================================
    # PERIOD FILTER
    # ========================================================

    def period_filter_changed(self, selected_value):

        self.search_feedback()

    # ========================================================
    # CLEAR FILTER
    # ========================================================

    @guard_authorization_errors
    def clear_filter(self):

        self.search_entry.delete(
            0,
            "end"
        )

        self.period_filter.set(
            "All"
        )

        self.load_feedback()


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    print(
        "FeedbackManagement must be opened from the main application."
    )
