import customtkinter as ctk
from tkinter import messagebox
from utils.authorization import require_menu_access, guard_authorization_errors
from utils.authorization import resolve_student
from utils.ui_theme import apply_professional_style

from services.fee_service import (
    add_fee,
    get_all_fees,
    make_payment,
    get_fee_summary
)


class FeeManagement(ctk.CTkToplevel):

    def __init__(self, parent):
        require_menu_access(parent.user, "Fees")
        super().__init__(parent)
        self.actor = parent.user

        self.title("Fee Management")
        self.geometry("1100x750")
        self.minsize(1000, 650)

        self.create_ui()
        if self.actor["role"] == "student":
            self.add_frame.pack_forget()
            self.payment_frame.pack_forget()
        self.load_fees()
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
            text="Fee Management",
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

        refresh_button = ctk.CTkButton(
            header,
            text="Refresh",
            width=100,
            command=self.load_fees
        )

        refresh_button.pack(
            side="right",
            padx=25
        )

        # ====================================================
        # SCROLLABLE AREA
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
        # ADD FEE
        # ====================================================

        add_frame = self.add_frame = ctk.CTkFrame(
            self.scrollable_frame
        )

        add_frame.pack(
            fill="x",
            padx=15,
            pady=15
        )

        ctk.CTkLabel(
            add_frame,
            text="Add New Fee",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        ).grid(
            row=0,
            column=0,
            columnspan=6,
            pady=15,
            sticky="w",
            padx=15
        )

        ctk.CTkLabel(
            add_frame,
            text="Student ID"
        ).grid(
            row=1,
            column=0,
            padx=10,
            pady=10
        )

        self.student_id_entry = ctk.CTkEntry(
            add_frame,
            placeholder_text="STU001"
        )

        self.student_id_entry.grid(
            row=1,
            column=1,
            padx=10,
            pady=10
        )

        ctk.CTkLabel(
            add_frame,
            text="Amount"
        ).grid(
            row=1,
            column=2,
            padx=10,
            pady=10
        )

        self.amount_entry = ctk.CTkEntry(
            add_frame,
            placeholder_text="5000"
        )

        self.amount_entry.grid(
            row=1,
            column=3,
            padx=10,
            pady=10
        )

        ctk.CTkLabel(
            add_frame,
            text="Due Date"
        ).grid(
            row=1,
            column=4,
            padx=10,
            pady=10
        )

        self.due_date_entry = ctk.CTkEntry(
            add_frame,
            placeholder_text="YYYY-MM-DD"
        )

        self.due_date_entry.grid(
            row=1,
            column=5,
            padx=10,
            pady=10
        )

        ctk.CTkButton(
            add_frame,
            text="Add Fee",
            width=150,
            command=self.add_fee_gui
        ).grid(
            row=2,
            column=0,
            columnspan=6,
            pady=15
        )

        # ====================================================
        # PAYMENT
        # ====================================================

        payment_frame = self.payment_frame = ctk.CTkFrame(
            self.scrollable_frame
        )

        payment_frame.pack(
            fill="x",
            padx=15,
            pady=10
        )

        ctk.CTkLabel(
            payment_frame,
            text="Make Payment",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        ).grid(
            row=0,
            column=0,
            columnspan=8,
            pady=15,
            sticky="w",
            padx=15
        )

        ctk.CTkLabel(
            payment_frame,
            text="Fee ID"
        ).grid(
            row=1,
            column=0,
            padx=10,
            pady=10
        )

        self.fee_id_entry = ctk.CTkEntry(
            payment_frame,
            placeholder_text="1"
        )

        self.fee_id_entry.grid(
            row=1,
            column=1,
            padx=10,
            pady=10
        )

        ctk.CTkLabel(
            payment_frame,
            text="Payment Amount"
        ).grid(
            row=1,
            column=2,
            padx=10,
            pady=10
        )

        self.payment_amount_entry = ctk.CTkEntry(
            payment_frame,
            placeholder_text="2000"
        )

        self.payment_amount_entry.grid(
            row=1,
            column=3,
            padx=10,
            pady=10
        )

        ctk.CTkLabel(
            payment_frame,
            text="Payment Mode"
        ).grid(
            row=1,
            column=4,
            padx=10,
            pady=10
        )

        self.payment_mode = ctk.CTkComboBox(
            payment_frame,
            values=[
                "Cash",
                "UPI",
                "Bank Transfer"
            ]
        )

        self.payment_mode.set(
            "UPI"
        )

        self.payment_mode.grid(
            row=1,
            column=5,
            padx=10,
            pady=10
        )

        ctk.CTkLabel(
            payment_frame,
            text="Receipt No."
        ).grid(
            row=1,
            column=6,
            padx=10,
            pady=10
        )

        self.receipt_entry = ctk.CTkEntry(
            payment_frame,
            placeholder_text="REC001"
        )

        self.receipt_entry.grid(
            row=1,
            column=7,
            padx=10,
            pady=10
        )

        ctk.CTkButton(
            payment_frame,
            text="Make Payment",
            width=170,
            command=self.make_payment_gui
        ).grid(
            row=2,
            column=0,
            columnspan=8,
            pady=15
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
            text="Search / Filter Fees",
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
            width=280,
            placeholder_text="Search Student ID or Name"
        )

        self.search_entry.grid(
            row=1,
            column=0,
            padx=10,
            pady=10
        )

        # Enter key

        self.search_entry.bind(
            "<Return>",
            self.search_fees
        )

        # Status

        self.status_filter = ctk.CTkComboBox(
            filter_frame,
            width=170,
            values=[
                "All",
                "Paid",
                "Pending",
                "Partial"
            ],
            command=self.status_filter_changed
        )

        self.status_filter.set(
            "All"
        )

        self.status_filter.grid(
            row=1,
            column=1,
            padx=10,
            pady=10
        )

        # Search button

        ctk.CTkButton(
            filter_frame,
            text="Search",
            width=100,
            command=self.search_fees
        ).grid(
            row=1,
            column=2,
            padx=10,
            pady=10
        )

        # Clear button

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
        # FEE RECORDS
        # ====================================================

        ctk.CTkLabel(
            self.scrollable_frame,
            text="Fee Records",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        ).pack(
            anchor="w",
            padx=15,
            pady=(10, 5)
        )

        self.fee_textbox = ctk.CTkTextbox(
            self.scrollable_frame,
            height=300,
            font=ctk.CTkFont(
                size=13
            )
        )

        self.fee_textbox.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=10
        )

        ctk.CTkButton(
            self.scrollable_frame,
            text="Refresh Fee Records",
            width=160,
            command=self.load_fees
        ).pack(
            pady=10
        )

        # Bottom space

        ctk.CTkLabel(
            self.scrollable_frame,
            text=""
        ).pack(
            pady=20
        )

    # ========================================================
    # ADD FEE
    # ========================================================

    @guard_authorization_errors
    def add_fee_gui(self):

        student_id = (
            self.student_id_entry
            .get()
            .strip()
        )

        amount_text = (
            self.amount_entry
            .get()
            .strip()
        )

        due_date = (
            self.due_date_entry
            .get()
            .strip()
        )

        if not student_id or not amount_text or not due_date:

            messagebox.showwarning(
                "Validation",
                "Please fill all fields."
            )

            return

        try:

            amount = float(
                amount_text
            )

            if amount <= 0:

                messagebox.showerror(
                    "Invalid Amount",
                    "Amount must be greater than 0."
                )

                return

        except ValueError:

            messagebox.showerror(
                "Invalid Amount",
                "Amount must be a number."
            )

            return

        success, message = add_fee(
            student_id,
            amount,
            due_date,
            actor=self.actor
        )

        if success:

            messagebox.showinfo(
                "Success",
                message
            )

            self.student_id_entry.delete(
                0,
                "end"
            )

            self.amount_entry.delete(
                0,
                "end"
            )

            self.due_date_entry.delete(
                0,
                "end"
            )

            self.load_fees()

        else:

            messagebox.showerror(
                "Error",
                message
            )

    # ========================================================
    # MAKE PAYMENT
    # ========================================================

    @guard_authorization_errors
    def make_payment_gui(self):

        fee_id_text = (
            self.fee_id_entry
            .get()
            .strip()
        )

        amount_text = (
            self.payment_amount_entry
            .get()
            .strip()
        )

        payment_mode = (
            self.payment_mode
            .get()
        )

        receipt_number = (
            self.receipt_entry
            .get()
            .strip()
        )

        if not fee_id_text or not amount_text:

            messagebox.showwarning(
                "Validation",
                "Fee ID and payment amount are required."
            )

            return

        try:

            fee_id = int(
                fee_id_text
            )

            amount = float(
                amount_text
            )

            if amount <= 0:

                messagebox.showerror(
                    "Invalid Amount",
                    "Payment amount must be greater than 0."
                )

                return

        except ValueError:

            messagebox.showerror(
                "Invalid Input",
                "Fee ID must be integer and amount must be number."
            )

            return

        summary = get_fee_summary(
            fee_id,
            actor=self.actor
        )

        if summary is None:

            messagebox.showerror(
                "Error",
                "Fee record not found."
            )

            return

        total, paid, pending = summary

        if pending <= 0:

            messagebox.showinfo(
                "Already Paid",
                "This fee is already fully paid."
            )

            return

        if amount > pending:

            messagebox.showwarning(
                "Invalid Payment",
                f"Pending amount is only ₹{pending:.2f}."
            )

            return

        success, message = make_payment(
            fee_id,
            amount,
            payment_mode,
            receipt_number,
            actor=self.actor
        )

        if success:

            messagebox.showinfo(
                "Success",
                message
            )

            self.fee_id_entry.delete(
                0,
                "end"
            )

            self.payment_amount_entry.delete(
                0,
                "end"
            )

            self.receipt_entry.delete(
                0,
                "end"
            )

            self.load_fees()

        else:

            messagebox.showerror(
                "Payment Error",
                message
            )

    # ========================================================
    # LOAD FEES
    # ========================================================

    @guard_authorization_errors
    def load_fees(self):

        fees = get_all_fees(actor=self.actor)

        self.display_fees(
            fees
        )
        apply_professional_style(self)

    # ========================================================
    # DISPLAY FEES
    # ========================================================

    def display_fees(self, fees):

        self.fee_textbox.delete(
            "1.0",
            "end"
        )

        if not fees:

            self.fee_textbox.insert(
                "end",
                "No fee records found."
            )

            return

        header = (
            f"{'ID':<5}{'Student ID':<14}{'Name':<22}"
            f"{'Total':<12}{'Paid':<12}{'Pending':<12}"
            f"{'Due Date':<13}{'Status':<10}\n"
        )

        self.fee_textbox.insert(
            "end",
            header
        )

        self.fee_textbox.insert("end", "-" * 100 + "\n")

        for fee in fees:

            (
                fee_id,
                student_id,
                name,
                amount,
                due_date,
                status,
                paid_amount,
                pending_amount
            ) = fee

            row = (
                f"{fee_id:<5}"
                f"{student_id:<14}"
                f"{name[:20]:<22}"
                f"{amount:<12.2f}"
                f"{paid_amount:<12.2f}"
                f"{pending_amount:<12.2f}"
                f"{str(due_date or ''):<13}"
                f"{status:<10}\n"
            )

            self.fee_textbox.insert(
                "end",
                row
            )

    # ========================================================
    # SEARCH FEES
    # ========================================================

    @guard_authorization_errors
    def search_fees(self, event=None):

        query = (
            self.search_entry
            .get()
            .strip()
            .lower()
        )

        selected_status = (
            self.status_filter
            .get()
            .strip()
            .lower()
        )

        fees = get_all_fees(actor=self.actor)

        filtered_fees = []

        for fee in fees:

            (
                fee_id,
                student_id,
                name,
                amount,
                due_date,
                status,
                _paid_amount,
                _pending_amount
            ) = fee

            student_id_text = str(
                student_id
            ).lower()

            name_text = str(
                name
            ).lower()

            status_text = str(
                status
            ).lower()

            # Search condition

            search_match = (
                not query
                or query in student_id_text
                or query in name_text
            )

            # Status condition

            if selected_status == "all":

                status_match = True

            else:

                status_match = (
                    status_text
                    == selected_status
                )

            if search_match and status_match:

                filtered_fees.append(
                    fee
                )

        self.display_fees(
            filtered_fees
        )

    # ========================================================
    # STATUS FILTER
    # ========================================================

    def status_filter_changed(self, selected_value):

        self.search_fees()

    # ========================================================
    # CLEAR FILTER
    # ========================================================

    @guard_authorization_errors
    def clear_filter(self):

        self.search_entry.delete(
            0,
            "end"
        )

        self.status_filter.set(
            "All"
        )

        self.load_fees()


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    print(
        "FeeManagement must be opened from the main application."
    )
