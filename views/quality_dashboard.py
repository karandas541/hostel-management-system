import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from analytics.dashboard_analytics import get_dashboard_statistics
from analytics.satisfaction_analysis import get_satisfaction_analysis
from analytics.quality_metrics import get_quality_recommendations
from utils.authorization import guard_authorization_errors, require_menu_access
from utils.ui_theme import apply_professional_style, get_palette


class QualityDashboardWindow(ctk.CTkToplevel):

    def __init__(self, parent):
        require_menu_access(parent.user, "Quality Dashboard")
        super().__init__(parent)
        self.actor = parent.user

        self.title("Q08 - Quality Dashboard")
        self.geometry("1000x800")
        self.minsize(850, 650)

        # Scrollable main area
        self.content_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )

        self.content_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        self.refresh_dashboard()

    # ---------------------------------------------------------
    # HEADER
    # ---------------------------------------------------------

    def create_header(self):

        header = ctk.CTkFrame(
            self.content_frame,
            height=80
        )

        header.pack(
            fill="x",
            padx=10,
            pady=10
        )

        title = ctk.CTkLabel(
            header,
            text="Q08 — Improve User Satisfaction",
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

        ctk.CTkButton(
            header,
            text="Refresh",
            width=105,
            command=self.refresh_dashboard,
        ).pack(side="right", padx=18)

    @guard_authorization_errors
    def refresh_dashboard(self):
        if hasattr(self, "figure"):
            plt.close(self.figure)
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.stats = get_dashboard_statistics(actor=self.actor)
        self.satisfaction = get_satisfaction_analysis(actor=self.actor)
        self.create_header()
        self.create_metrics()
        self.create_satisfaction_section()
        self.create_satisfaction_chart()
        self.create_recommendations()
        self.create_pdca_section()
        apply_professional_style(self)

    # ---------------------------------------------------------
    # QUALITY METRICS
    # ---------------------------------------------------------

    def create_metrics(self):

        metrics_frame = ctk.CTkFrame(
            self.content_frame,
            fg_color="transparent"
        )

        metrics_frame.pack(
            fill="x",
            padx=10,
            pady=10
        )

        self.create_metric_card(
            metrics_frame,
            "Average Satisfaction",
            (f"{self.stats['average_satisfaction']}/5"
             if self.stats["average_satisfaction"] else "No feedback"),
            0
        )

        if self.actor["role"] == "admin":
            room_metric_title = "Occupancy Rate"
            room_metric_value = f"{self.stats['occupancy_rate']}%"
        else:
            room_metric_title = "Your Room"
            room_metric_value = self.stats["student_room_number"] or "Not assigned"

        self.create_metric_card(
            metrics_frame,
            room_metric_title,
            room_metric_value,
            1
        )

        self.create_metric_card(
            metrics_frame,
            "Pending Complaints",
            str(self.stats["pending_complaints"]),
            2
        )

        self.create_metric_card(
            metrics_frame,
            "Resolution Rate",
            f"{self.stats['complaint_resolution_rate']}%",
            3
        )

    def create_metric_card(
        self,
        parent,
        title,
        value,
        column
    ):

        card = ctk.CTkFrame(
            parent,
            width=210,
            height=110
        )

        card.grid(
            row=0,
            column=column,
            padx=8,
            sticky="nsew"
        )

        parent.grid_columnconfigure(
            column,
            weight=1
        )

        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=13)
        )

        title_label.pack(
            pady=(18, 5)
        )

        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(
                size=24,
                weight="bold"
            )
        )

        value_label.pack()

    # ---------------------------------------------------------
    # SATISFACTION BY QUALITY AREA
    # ---------------------------------------------------------

    def create_satisfaction_section(self):

        section = ctk.CTkFrame(
            self.content_frame
        )

        section.pack(
            fill="x",
            padx=10,
            pady=10
        )

        title = ctk.CTkLabel(
            section,
            text="Satisfaction by Quality Area",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        )

        title.pack(
            pady=(20, 15)
        )

        for category, score in self.satisfaction.items():

            row = ctk.CTkFrame(
                section,
                fg_color="transparent"
            )

            row.pack(
                fill="x",
                padx=30,
                pady=5
            )

            label = ctk.CTkLabel(
                row,
                text=category,
                width=180,
                anchor="w"
            )

            label.pack(
                side="left"
            )

            progress = ctk.CTkProgressBar(
                row,
                width=500
            )

            progress.pack(
                side="left",
                padx=15,
                fill="x",
                expand=True
            )

            progress.set(score / 5 if score is not None else 0)

            score_label = ctk.CTkLabel(
                row,
                text=f"{score}/5" if score is not None else "No data",
                width=60
            )

            score_label.pack(
                side="right"
            )

    # ---------------------------------------------------------
    # SATISFACTION CHART
    # ---------------------------------------------------------

    def create_satisfaction_chart(self):

        section = ctk.CTkFrame(
            self.content_frame
        )

        section.pack(
            fill="x",
            padx=10,
            pady=10
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

        observed = [(name, score) for name, score in self.satisfaction.items() if score is not None]
        if not observed:
            ctk.CTkLabel(
                section,
                text="No feedback has been submitted yet.",
            ).pack(padx=20, pady=24)
            return

        categories, scores = zip(*observed)

        self.figure, axis = plt.subplots(figsize=(9, 5))
        colors = get_palette()
        self.figure.patch.set_facecolor(colors["surface"])

        axis.barh(categories, scores, color=colors["accent"])

        axis.set_xlabel(
            "Satisfaction Score"
        )

        axis.set_xlim(
            0,
            5
        )

        axis.set_title(
            "User Satisfaction by Quality Area"
        )
        axis.set_facecolor(colors["surface"])
        axis.tick_params(colors=colors["text"])
        axis.xaxis.label.set_color(colors["text"])
        axis.title.set_color(colors["text"])
        for spine in axis.spines.values():
            spine.set_color(colors["border"])

        self.figure.tight_layout()

        canvas = FigureCanvasTkAgg(
            self.figure,
            master=section
        )

        canvas.draw()

        canvas.get_tk_widget().pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )

    # ---------------------------------------------------------
    # CONTINUOUS IMPROVEMENT RECOMMENDATIONS
    # ---------------------------------------------------------

    def create_recommendations(self):

        recommendations = get_quality_recommendations(actor=self.actor)

        section = ctk.CTkFrame(
            self.content_frame
        )

        section.pack(
            fill="x",
            padx=10,
            pady=10
        )

        title = ctk.CTkLabel(
            section,
            text="Continuous Improvement Recommendations",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        )

        title.pack(
            pady=(20, 15)
        )

        for item in recommendations:

            row = ctk.CTkFrame(
                section
            )

            row.pack(
                fill="x",
                padx=30,
                pady=5
            )

            text = (
                f"{item['category']} — "
                f"{item['score']}/5\n" if item["score"] is not None else
                f"{item['category']}\n"
            ) + (
                f"{item['status']}\n"
                f"{item['recommendation']}"
            )

            recommendation_label = ctk.CTkLabel(
                row,
                text=text,
                font=ctk.CTkFont(size=14),
                justify="left",
                anchor="w"
            )

            recommendation_label.pack(
                fill="x",
                padx=15,
                pady=10
            )

    # ---------------------------------------------------------
    # PDCA CYCLE
    # ---------------------------------------------------------

    def create_pdca_section(self):

        section = ctk.CTkFrame(
            self.content_frame
        )

        section.pack(
            fill="x",
            padx=10,
            pady=10
        )

        title = ctk.CTkLabel(
            section,
            text="TQM — PDCA Continuous Improvement Cycle",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        )

        title.pack(
            pady=(20, 15)
        )

        steps = [
            (
                "PLAN",
                "Identify low satisfaction areas and "
                "plan improvement actions."
            ),
            (
                "DO",
                "Implement corrective actions to improve "
                "the selected quality area."
            ),
            (
                "CHECK",
                "Collect student feedback and compare "
                "new satisfaction scores."
            ),
            (
                "ACT",
                "Standardize successful improvements and "
                "start the next improvement cycle."
            )
        ]

        for step, description in steps:

            row = ctk.CTkFrame(
                section
            )

            row.pack(
                fill="x",
                padx=30,
                pady=5
            )

            step_label = ctk.CTkLabel(
                row,
                text=step,
                width=100,
                font=ctk.CTkFont(
                    size=15,
                    weight="bold"
                )
            )

            step_label.pack(
                side="left",
                padx=10,
                pady=15
            )

            description_label = ctk.CTkLabel(
                row,
                text=description,
                anchor="w",
                justify="left",
                font=ctk.CTkFont(size=14)
            )

            description_label.pack(
                side="left",
                fill="x",
                expand=True,
                padx=10
            )


# ---------------------------------------------------------
# DIRECT TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    root = ctk.CTk()

    root.withdraw()

    app = QualityDashboardWindow(root)

    app.mainloop()
