import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import csv
import os
import tempfile

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image
)
from utils.authorization import require_menu_access
from utils.ui_theme import apply_professional_style

from analytics.dashboard_analytics import get_dashboard_statistics
from analytics.satisfaction_analysis import get_satisfaction_analysis


class ReportsWindow(ctk.CTkToplevel):

    def __init__(self, parent):
        require_menu_access(parent.user, "Reports")
        super().__init__(parent)
        self.actor = parent.user

        self.title("Hostel Management System - Reports")
        self.geometry("1150x850")
        self.minsize(950, 700)

        self.stats = get_dashboard_statistics(actor=self.actor)
        self.satisfaction = get_satisfaction_analysis(actor=self.actor)

        self.protocol(
            "WM_DELETE_WINDOW",
            self.close_window
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
            padx=10,
            pady=10
        )

        self.create_header()
        self.create_summary()
        self.create_quality_metrics()
        self.create_satisfaction_report()
        self.create_improvement_areas()
        self.create_satisfaction_chart()

    # =========================================================
    # HEADER
    # =========================================================

    def create_header(self):

        header = ctk.CTkFrame(self.main_frame)

        header.pack(
            fill="x",
            padx=10,
            pady=10
        )

        title = ctk.CTkLabel(
            header,
            text="Reports & Analytics",
            font=ctk.CTkFont(
                size=26,
                weight="bold"
            )
        )

        title.pack(
            side="left",
            padx=20,
            pady=20
        )

        button_frame = ctk.CTkFrame(
            header,
            fg_color="transparent"
        )

        button_frame.pack(
            side="right",
            padx=20
        )

        refresh_button = ctk.CTkButton(
            button_frame,
            text="Refresh",
            width=110,
            command=self.refresh_reports
        )

        refresh_button.pack(
            side="left",
            padx=5
        )

        csv_button = ctk.CTkButton(
            button_frame,
            text="Export CSV",
            width=110,
            command=self.export_csv
        )

        csv_button.pack(
            side="left",
            padx=5
        )

        pdf_button = ctk.CTkButton(
            button_frame,
            text="Export PDF",
            width=110,
            command=self.export_pdf
        )

        pdf_button.pack(
            side="left",
            padx=5
        )

    # =========================================================
    # HOSTEL SUMMARY
    # =========================================================

    def create_summary(self):

        section = ctk.CTkFrame(
            self.main_frame
        )

        section.pack(
            fill="x",
            padx=10,
            pady=10
        )

        title = ctk.CTkLabel(
            section,
            text="Hostel Summary Report",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        )

        title.pack(
            pady=(20, 15)
        )

        summary_frame = ctk.CTkFrame(
            section,
            fg_color="transparent"
        )

        summary_frame.pack(
            fill="x",
            padx=20,
            pady=10
        )

        summary_data = [

            (
                "Total Students",
                self.stats.get("total_students", 0)
            ),

            (
                "Total Rooms",
                self.stats.get("total_rooms", 0)
            ),

            (
                "Total Beds",
                self.stats.get("total_beds", 0)
            ),

            (
                "Occupied Beds",
                self.stats.get("occupied_beds", 0)
            ),

            (
                "Available Beds",
                self.stats.get("available_beds", 0)
            ),

            (
                "Pending Fees",
                f"INR {self.stats.get('pending_fees', 0):.2f}"
            ),

            (
                "Total Complaints",
                self.stats.get("total_complaints", 0)
            ),

            (
                "Pending Complaints",
                self.stats.get("pending_complaints", 0)
            )
        ]

        for index, (title_text, value) in enumerate(
            summary_data
        ):

            self.create_summary_item(
                summary_frame,
                title_text,
                value,
                index
            )

    def create_summary_item(
        self,
        parent,
        title,
        value,
        column
    ):

        card = ctk.CTkFrame(
            parent,
            width=130,
            height=90
        )

        card.grid(
            row=0,
            column=column,
            padx=5,
            pady=5,
            sticky="nsew"
        )

        parent.grid_columnconfigure(
            column,
            weight=1
        )

        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(
                size=11
            )
        )

        title_label.pack(
            pady=(15, 5)
        )

        value_label = ctk.CTkLabel(
            card,
            text=str(value),
            font=ctk.CTkFont(
                size=18,
                weight="bold"
            )
        )

        value_label.pack()

    # =========================================================
    # QUALITY METRICS
    # =========================================================

    def create_quality_metrics(self):

        section = ctk.CTkFrame(
            self.main_frame
        )

        section.pack(
            fill="x",
            padx=10,
            pady=10
        )

        title = ctk.CTkLabel(
            section,
            text="TQM Quality Metrics",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        )

        title.pack(
            pady=(20, 5)
        )

        description = ctk.CTkLabel(
            section,
            text=(
                "Key indicators used to monitor hostel service quality "
                "and user satisfaction."
            ),
            font=ctk.CTkFont(size=12)
        )

        description.pack(
            pady=(0, 15)
        )

        metrics_frame = ctk.CTkFrame(
            section,
            fg_color="transparent"
        )

        metrics_frame.pack(
            fill="x",
            padx=20,
            pady=10
        )

        occupancy_rate = self.stats.get(
            "occupancy_rate",
            0
        )

        resolution_rate = self.stats.get(
            "complaint_resolution_rate",
            0
        )

        satisfaction_score = self.stats.get(
            "average_satisfaction",
            0
        )

        total_complaints = self.stats.get(
            "total_complaints",
            0
        )

        pending_complaints = self.stats.get(
            "pending_complaints",
            0
        )

        resolved_complaints = self.stats.get(
            "resolved_complaints",
            0
        )

        metrics = [

            (
                "Occupancy Rate",
                f"{occupancy_rate:.2f}%"
            ),

            (
                "Complaint Resolution Rate",
                f"{resolution_rate:.2f}%"
            ),

            (
                "Average Satisfaction",
                f"{satisfaction_score:.2f}/5" if satisfaction_score else "No feedback"
            ),

            (
                "Resolved Complaints",
                resolved_complaints
            ),

            (
                "Pending Complaints",
                pending_complaints
            ),

            (
                "Total Complaints",
                total_complaints
            )
        ]

        for index, (name, value) in enumerate(metrics):

            row = index // 3
            column = index % 3

            self.create_metric_card(
                metrics_frame,
                name,
                value,
                row,
                column
            )

    def create_metric_card(
        self,
        parent,
        title,
        value,
        row,
        column
    ):

        card = ctk.CTkFrame(
            parent,
            height=100
        )

        card.grid(
            row=row,
            column=column,
            padx=8,
            pady=8,
            sticky="nsew"
        )

        parent.grid_columnconfigure(
            column,
            weight=1
        )

        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(
                size=12
            )
        )

        title_label.pack(
            pady=(15, 5)
        )

        value_label = ctk.CTkLabel(
            card,
            text=str(value),
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        )

        value_label.pack()

    # =========================================================
    # SATISFACTION TABLE
    # =========================================================

    def create_satisfaction_report(self):

        section = ctk.CTkFrame(
            self.main_frame
        )

        section.pack(
            fill="x",
            padx=10,
            pady=10
        )

        title = ctk.CTkLabel(
            section,
            text="Student Satisfaction Report",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        )

        title.pack(
            pady=(20, 10)
        )

        table_frame = ctk.CTkFrame(
            section
        )

        table_frame.pack(
            fill="x",
            padx=20,
            pady=10
        )

        columns = (
            "Quality Area",
            "Score",
            "Status"
        )

        self.table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=9
        )

        self.table.heading(
            "Quality Area",
            text="Quality Area"
        )

        self.table.heading(
            "Score",
            text="Score"
        )

        self.table.heading(
            "Status",
            text="Status"
        )

        self.table.column(
            "Quality Area",
            width=300
        )

        self.table.column(
            "Score",
            width=150
        )

        self.table.column(
            "Status",
            width=250
        )

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.table.yview
        )

        self.table.configure(
            yscrollcommand=scrollbar.set
        )

        self.table.pack(
            side="left",
            fill="x",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.load_satisfaction_data()

    def get_satisfaction_status(self, score):

        if score is None:
            return "No feedback yet"

        if score < 3.0:

            return "Critical Improvement"

        elif score < 4.0:

            return "Needs Improvement"

        else:

            return "Good Performance"

    def load_satisfaction_data(self):

        for item in self.table.get_children():

            self.table.delete(item)

        for category, score in self.satisfaction.items():

            status = self.get_satisfaction_status(
                score
            )

            self.table.insert(
                "",
                "end",
                values=(
                    category,
                    f"{score:.2f}/5" if score is not None else "No data",
                    status
                )
            )

    # =========================================================
    # IMPROVEMENT AREAS
    # =========================================================

    def create_improvement_areas(self):

        section = ctk.CTkFrame(
            self.main_frame
        )

        section.pack(
            fill="x",
            padx=10,
            pady=10
        )

        title = ctk.CTkLabel(
            section,
            text="TQM Improvement Areas",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        )

        title.pack(
            pady=(20, 5)
        )

        description = ctk.CTkLabel(
            section,
            text=(
                "Categories below 4/5 should receive attention "
                "under the continuous improvement process."
            ),
            font=ctk.CTkFont(size=12)
        )

        description.pack(
            pady=(0, 15)
        )

        improvement_frame = ctk.CTkFrame(
            section
        )

        improvement_frame.pack(
            fill="x",
            padx=20,
            pady=10
        )

        improvement_found = False

        sorted_categories = sorted(
            self.satisfaction.items(),
            key=lambda item: (item[1] is not None, item[1] if item[1] is not None else -1)
        )

        for category, score in sorted_categories:

            if score is not None and score < 4.0:

                improvement_found = True

                row = ctk.CTkFrame(
                    improvement_frame
                )

                row.pack(
                    fill="x",
                    padx=10,
                    pady=5
                )

                category_label = ctk.CTkLabel(
                    row,
                    text=category,
                    anchor="w",
                    font=ctk.CTkFont(
                        size=13,
                        weight="bold"
                    )
                )

                category_label.pack(
                    side="left",
                    padx=10,
                    pady=10
                )

                score_label = ctk.CTkLabel(
                    row,
                    text=f"{score:.2f}/5 - Needs Improvement",
                    anchor="e"
                )

                score_label.pack(
                    side="right",
                    padx=10,
                    pady=10
                )

        if not improvement_found:

            if not any(score is not None for score in self.satisfaction.values()):
                message_text = "No feedback has been submitted yet."
            elif any(score is None for score in self.satisfaction.values()):
                message_text = (
                    "Rated categories are at 4/5 or above. Some areas still need feedback."
                )
            else:
                message_text = (
                    "All satisfaction categories are currently performing at 4/5 or above."
                )

            message = ctk.CTkLabel(
                improvement_frame,
                text=message_text,
                font=ctk.CTkFont(
                    size=13,
                    weight="bold"
                )
            )

            message.pack(
                pady=20
            )

    # =========================================================
    # SATISFACTION CHART
    # =========================================================

    def create_satisfaction_chart(self):

        self.current_figure = None

        section = ctk.CTkFrame(
            self.main_frame
        )

        section.pack(
            fill="x",
            padx=10,
            pady=20
        )

        title = ctk.CTkLabel(
            section,
            text="Satisfaction Analysis Chart",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        )

        title.pack(
            pady=(20, 10)
        )

        chart_frame = ctk.CTkFrame(
            section,
            height=500
        )

        chart_frame.pack(
            fill="x",
            padx=20,
            pady=10
        )

        observed = [(category, score) for category, score in self.satisfaction.items() if score is not None]
        if not observed:
            ctk.CTkLabel(chart_frame, text="No feedback has been submitted yet.").pack(pady=30)
            return
        categories, scores = zip(*observed)

        figure = plt.Figure(
            figsize=(10, 6),
            dpi=100
        )

        axis = figure.add_subplot(111)

        axis.barh(
            categories,
            scores
        )

        axis.set_title(
            "Student Satisfaction by Quality Area"
        )

        axis.set_xlabel(
            "Satisfaction Score"
        )

        axis.set_xlim(
            0,
            5
        )

        axis.grid(
            axis="x",
            alpha=0.3
        )

        figure.tight_layout()

        self.chart_canvas = FigureCanvasTkAgg(
            figure,
            master=chart_frame
        )

        self.chart_canvas.draw()

        canvas_widget = (
            self.chart_canvas.get_tk_widget()
        )

        canvas_widget.pack(
            fill="both",
            expand=True
        )

        self.current_figure = figure

    # =========================================================
    # EXPORT CSV
    # =========================================================

    def export_csv(self):

        file_path = filedialog.asksaveasfilename(
            parent=self,
            title="Save Reports",
            defaultextension=".csv",
            filetypes=[
                (
                    "CSV Files",
                    "*.csv"
                ),
                (
                    "All Files",
                    "*.*"
                )
            ]
        )

        if not file_path:

            return

        try:

            with open(
                file_path,
                "w",
                newline="",
                encoding="utf-8"
            ) as file:

                writer = csv.writer(file)

                # -------------------------------------------------
                # TITLE
                # -------------------------------------------------

                writer.writerow(
                    ["HOSTEL MANAGEMENT SYSTEM"]
                )

                writer.writerow(
                    ["Reports & Analytics"]
                )

                writer.writerow([])

                # -------------------------------------------------
                # HOSTEL SUMMARY
                # -------------------------------------------------

                writer.writerow(
                    ["HOSTEL SUMMARY"]
                )

                writer.writerow(
                    ["Metric", "Value"]
                )

                writer.writerow(
                    [
                        "Total Students",
                        self.stats.get(
                            "total_students",
                            0
                        )
                    ]
                )

                writer.writerow(
                    [
                        "Total Rooms",
                        self.stats.get(
                            "total_rooms",
                            0
                        )
                    ]
                )

                writer.writerow(
                    [
                        "Total Beds",
                        self.stats.get(
                            "total_beds",
                            0
                        )
                    ]
                )

                writer.writerow(
                    [
                        "Occupied Beds",
                        self.stats.get(
                            "occupied_beds",
                            0
                        )
                    ]
                )

                writer.writerow(
                    [
                        "Available Beds",
                        self.stats.get(
                            "available_beds",
                            0
                        )
                    ]
                )

                writer.writerow(
                    [
                        "Pending Fees",
                        self.stats.get(
                            "pending_fees",
                            0
                        )
                    ]
                )

                writer.writerow(
                    [
                        "Total Complaints",
                        self.stats.get(
                            "total_complaints",
                            0
                        )
                    ]
                )

                writer.writerow(
                    [
                        "Pending Complaints",
                        self.stats.get(
                            "pending_complaints",
                            0
                        )
                    ]
                )

                writer.writerow([])

                # -------------------------------------------------
                # QUALITY METRICS
                # -------------------------------------------------

                writer.writerow(
                    ["TQM QUALITY METRICS"]
                )

                writer.writerow(
                    ["Metric", "Value"]
                )

                writer.writerow(
                    [
                        "Occupancy Rate",
                        f"{self.stats.get('occupancy_rate', 0):.2f}%"
                    ]
                )

                writer.writerow(
                    [
                        "Complaint Resolution Rate",
                        f"{self.stats.get('complaint_resolution_rate', 0):.2f}%"
                    ]
                )

                writer.writerow(
                    [
                        "Average Satisfaction",
                        (f"{self.stats.get('average_satisfaction', 0):.2f}/5"
                         if self.stats.get("average_satisfaction") else "No feedback")
                    ]
                )

                writer.writerow(
                    [
                        "Resolved Complaints",
                        self.stats.get(
                            "resolved_complaints",
                            0
                        )
                    ]
                )

                writer.writerow(
                    [
                        "Pending Complaints",
                        self.stats.get(
                            "pending_complaints",
                            0
                        )
                    ]
                )

                writer.writerow([])

                # -------------------------------------------------
                # SATISFACTION REPORT
                # -------------------------------------------------

                writer.writerow(
                    ["SATISFACTION REPORT"]
                )

                writer.writerow(
                    [
                        "Quality Area",
                        "Score",
                        "Status"
                    ]
                )

                for category, score in self.satisfaction.items():

                    status = self.get_satisfaction_status(
                        score
                    )

                    writer.writerow(
                        [
                            category,
                            f"{score:.2f}" if score is not None else "No data",
                            status
                        ]
                    )

                writer.writerow([])

                # -------------------------------------------------
                # IMPROVEMENT AREAS
                # -------------------------------------------------

                writer.writerow(
                    ["IMPROVEMENT AREAS"]
                )

                writer.writerow(
                    [
                        "Quality Area",
                        "Score",
                        "Recommendation"
                    ]
                )

                for category, score in sorted(
                    self.satisfaction.items(),
                    key=lambda item: (item[1] is not None, item[1] if item[1] is not None else -1)
                ):

                    if score is None:
                        recommendation = "Collect feedback before assessing this area"

                    elif score < 3.0:

                        recommendation = (
                            "Critical improvement required"
                        )

                    elif score < 4.0:

                        recommendation = (
                            "Needs improvement"
                        )

                    else:

                        recommendation = (
                            "Maintain performance"
                        )

                    writer.writerow(
                        [
                            category,
                            f"{score:.2f}" if score is not None else "No data",
                            recommendation
                        ]
                    )

            messagebox.showinfo(
                "Export Successful",
                "CSV report exported successfully."
            )

        except Exception:

            messagebox.showerror(
                "Export Error",
                "Could not export the CSV file. Check the destination and try again.",
                parent=self,
            )

    # =========================================================
    # EXPORT PDF
    # =========================================================

    def export_pdf(self):

        file_path = filedialog.asksaveasfilename(
            parent=self,
            title="Save PDF Report",
            defaultextension=".pdf",
            filetypes=[
                (
                    "PDF Files",
                    "*.pdf"
                ),
                (
                    "All Files",
                    "*.*"
                )
            ]
        )

        if not file_path:

            return

        chart_path = None

        try:

            # -------------------------------------------------
            # SAVE CHART TEMPORARILY
            # -------------------------------------------------

            if self.current_figure is not None:
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_chart:
                    chart_path = temp_chart.name
                self.current_figure.savefig(chart_path, dpi=150, bbox_inches="tight")

            # -------------------------------------------------
            # CREATE PDF
            # -------------------------------------------------

            document = SimpleDocTemplate(
                file_path,
                pagesize=A4,
                rightMargin=30,
                leftMargin=30,
                topMargin=30,
                bottomMargin=30
            )

            styles = getSampleStyleSheet()

            elements = []

            elements.append(
                Paragraph(
                    "Hostel Management System",
                    styles["Title"]
                )
            )

            elements.append(
                Paragraph(
                    "Reports & Analytics",
                    styles["Heading2"]
                )
            )

            elements.append(
                Spacer(
                    1,
                    15
                )
            )

            # -------------------------------------------------
            # HOSTEL SUMMARY
            # -------------------------------------------------

            elements.append(
                Paragraph(
                    "Hostel Summary",
                    styles["Heading2"]
                )
            )

            summary_data = [

                ["Metric", "Value"],

                [
                    "Total Students",
                    str(
                        self.stats.get(
                            "total_students",
                            0
                        )
                    )
                ],

                [
                    "Total Rooms",
                    str(
                        self.stats.get(
                            "total_rooms",
                            0
                        )
                    )
                ],

                [
                    "Total Beds",
                    str(
                        self.stats.get(
                            "total_beds",
                            0
                        )
                    )
                ],

                [
                    "Occupied Beds",
                    str(
                        self.stats.get(
                            "occupied_beds",
                            0
                        )
                    )
                ],

                [
                    "Available Beds",
                    str(
                        self.stats.get(
                            "available_beds",
                            0
                        )
                    )
                ],

                [
                    "Pending Fees",
                    f"INR {self.stats.get('pending_fees', 0):.2f}"
                ],

                [
                    "Total Complaints",
                    str(
                        self.stats.get(
                            "total_complaints",
                            0
                        )
                    )
                ],

                [
                    "Pending Complaints",
                    str(
                        self.stats.get(
                            "pending_complaints",
                            0
                        )
                    )
                ]
            ]

            summary_table = Table(
                summary_data,
                colWidths=[
                    250,
                    150
                ]
            )

            summary_table.setStyle(
                TableStyle([
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.lightgrey
                    ),

                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey
                    ),

                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold"
                    ),

                    (
                        "ALIGN",
                        (1, 1),
                        (1, -1),
                        "CENTER"
                    )
                ])
            )

            elements.append(
                summary_table
            )

            elements.append(
                Spacer(
                    1,
                    20
                )
            )

            # -------------------------------------------------
            # QUALITY METRICS
            # -------------------------------------------------

            elements.append(
                Paragraph(
                    "TQM Quality Metrics",
                    styles["Heading2"]
                )
            )

            quality_data = [

                ["Metric", "Value"],

                [
                    "Occupancy Rate",
                    f"{self.stats.get('occupancy_rate', 0):.2f}%"
                ],

                [
                    "Complaint Resolution Rate",
                    f"{self.stats.get('complaint_resolution_rate', 0):.2f}%"
                ],

                [
                    "Average Satisfaction",
                    (f"{self.stats.get('average_satisfaction', 0):.2f}/5"
                     if self.stats.get("average_satisfaction") else "No feedback")
                ],

                [
                    "Resolved Complaints",
                    str(
                        self.stats.get(
                            "resolved_complaints",
                            0
                        )
                    )
                ],

                [
                    "Pending Complaints",
                    str(
                        self.stats.get(
                            "pending_complaints",
                            0
                        )
                    )
                ],

                [
                    "Total Complaints",
                    str(
                        self.stats.get(
                            "total_complaints",
                            0
                        )
                    )
                ]
            ]

            quality_table = Table(
                quality_data,
                colWidths=[
                    250,
                    150
                ]
            )

            quality_table.setStyle(
                TableStyle([
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.lightgrey
                    ),

                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey
                    ),

                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold"
                    ),

                    (
                        "ALIGN",
                        (1, 1),
                        (1, -1),
                        "CENTER"
                    )
                ])
            )

            elements.append(
                quality_table
            )

            elements.append(
                Spacer(
                    1,
                    20
                )
            )

            # -------------------------------------------------
            # SATISFACTION REPORT
            # -------------------------------------------------

            elements.append(
                Paragraph(
                    "Student Satisfaction Report",
                    styles["Heading2"]
                )
            )

            satisfaction_data = [
                [
                    "Quality Area",
                    "Score",
                    "Status"
                ]
            ]

            for category, score in self.satisfaction.items():

                status = self.get_satisfaction_status(
                    score
                )

                satisfaction_data.append(
                    [
                        category,
                        f"{score:.2f}/5" if score is not None else "No data",
                        status
                    ]
                )

            satisfaction_table = Table(
                satisfaction_data,
                colWidths=[
                    200,
                    100,
                    180
                ]
            )

            satisfaction_table.setStyle(
                TableStyle([
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.lightgrey
                    ),

                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey
                    ),

                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold"
                    ),

                    (
                        "ALIGN",
                        (1, 1),
                        (1, -1),
                        "CENTER"
                    )
                ])
            )

            elements.append(
                satisfaction_table
            )

            elements.append(
                Spacer(
                    1,
                    20
                )
            )

            # -------------------------------------------------
            # IMPROVEMENT AREAS
            # -------------------------------------------------

            elements.append(
                Paragraph(
                    "TQM Improvement Areas",
                    styles["Heading2"]
                )
            )

            improvement_data = [
                [
                    "Quality Area",
                    "Score",
                    "Recommendation"
                ]
            ]

            for category, score in sorted(
                self.satisfaction.items(),
                key=lambda item: (item[1] is not None, item[1] if item[1] is not None else -1)
            ):

                if score is None:
                    recommendation = "Collect feedback before assessing this area"

                elif score < 3.0:

                    recommendation = (
                        "Critical improvement required"
                    )

                elif score < 4.0:

                    recommendation = (
                        "Needs improvement"
                    )

                else:

                    recommendation = (
                        "Maintain performance"
                    )

                improvement_data.append(
                    [
                        category,
                        f"{score:.2f}/5" if score is not None else "No data",
                        recommendation
                    ]
                )

            improvement_table = Table(
                improvement_data,
                colWidths=[
                    200,
                    100,
                    180
                ]
            )

            improvement_table.setStyle(
                TableStyle([
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.lightgrey
                    ),

                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey
                    ),

                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold"
                    ),

                    (
                        "ALIGN",
                        (1, 1),
                        (1, -1),
                        "CENTER"
                    )
                ])
            )

            elements.append(
                improvement_table
            )

            elements.append(
                Spacer(
                    1,
                    20
                )
            )

            # -------------------------------------------------
            # CHART
            # -------------------------------------------------

            elements.append(
                Paragraph(
                    "Satisfaction Analysis Chart",
                    styles["Heading2"]
                )
            )

            if chart_path:
                elements.append(Image(chart_path, width=500, height=300))
            else:
                elements.append(Paragraph("No feedback has been submitted yet.", styles["Normal"]))

            # -------------------------------------------------
            # BUILD PDF
            # -------------------------------------------------

            document.build(
                elements
            )

            messagebox.showinfo(
                "Export Successful",
                "PDF report exported successfully."
            )

        except Exception:

            messagebox.showerror(
                "PDF Export Error",
                "Could not export the PDF file. Check the destination and try again.",
                parent=self,
            )

        finally:

            if (
                chart_path
                and os.path.exists(chart_path)
            ):

                try:

                    os.remove(chart_path)

                except Exception:

                    pass

    # =========================================================
    # REFRESH
    # =========================================================

    def refresh_reports(self):

        try:

            self.stats = get_dashboard_statistics(actor=self.actor)

            self.satisfaction = get_satisfaction_analysis(actor=self.actor)

            if hasattr(
                self,
                "current_figure"
            ) and self.current_figure is not None:

                plt.close(
                    self.current_figure
                )

            self.main_frame.destroy()

            self.create_interface()
            apply_professional_style(self)

            messagebox.showinfo(
                "Reports",
                "Reports refreshed successfully."
            )

        except Exception:

            messagebox.showerror(
                "Refresh Error",
                "Could not refresh reports. Please try again.",
                parent=self,
            )

    # =========================================================
    # CLOSE
    # =========================================================

    def close_window(self):

        if hasattr(
            self,
            "current_figure"
        ) and self.current_figure is not None:

            plt.close(
                self.current_figure
            )

        self.destroy()


# =============================================================
# STANDALONE TEST
# =============================================================

if __name__ == "__main__":

    root = ctk.CTk()

    root.withdraw()

    app = ReportsWindow(root)

    app.mainloop()
