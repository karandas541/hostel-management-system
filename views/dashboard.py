import customtkinter as ctk
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from views.fees import FeeManagement
from views.rooms import RoomsWindow
from views.students import StudentsWindow
from views.complaints import ComplaintManagement
from views.attendance import AttendanceManagement
from views.feedback import FeedbackManagement
from views.quality_dashboard import QualityDashboardWindow
from views.reports import ReportsWindow
from views.profile import ProfileWindow
from views.settings import SettingsWindow
from views.notifications import NotificationsWindow

from analytics.dashboard_analytics import get_dashboard_statistics
from services.notification_service import get_unread_count

from utils.shortcuts import ShortcutManager
from utils.role_access import get_menu_for_role
from utils.authorization import load_actor, require_menu_access, AuthorizationError
from utils.authorization import revoke_session
from utils.ui_theme import COLORS, get_palette, apply_professional_style
from utils.theme_manager import ThemeManager


class DashboardWindow(ctk.CTk):

    def __init__(self, user):
        user = load_actor(user)
        super().__init__()

        self.user = user
        ThemeManager.set_theme(ThemeManager.load_user_theme(self.user["id"]))

        self.title("Hostel Management System - Dashboard")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.state("zoomed")
        self.configure(fg_color=COLORS["page"])

        ctk.set_default_color_theme("blue")

        # =====================================================
        # Keep references to opened windows
        # =====================================================

        self.students_window = None
        self.rooms_window = None
        self.fees_window = None
        self.complaints_window = None
        self.attendance_window = None
        self.feedback_window = None
        self.quality_window = None
        self.reports_window = None
        self.profile_window = None
        self.settings_window = None
        self.notifications_window = None
        self._active_feature_window = None

        # =====================================================
        # Main area reference
        # =====================================================

        self.main_area = None
        self.dashboard_scroll = None
        self.dashboard_figure = None
        self.dashboard_canvas = None

        # =====================================================
        # Create UI
        # =====================================================

        self.create_sidebar()
        self.create_dashboard()

        self.update_notification_count()

        # =====================================================
        # Keyboard Shortcuts
        # =====================================================

        self.shortcut_manager = ShortcutManager(
            self,
            home_callback=self.go_home,
            students_callback=(lambda: self.menu_clicked("Students"))
            if self.user["role"] == "admin" else None,
            fees_callback=lambda: self.menu_clicked("Fees"),
            refresh_callback=self.refresh_active_page,
            notifications_callback=lambda: self.menu_clicked("Notifications"),
            logout_callback=self.logout,
            theme_callback=self.toggle_theme,
            exit_callback=self.exit_application
        )

    # =========================================================
    # SIDEBAR
    # =========================================================

    def create_sidebar(self):

        self.sidebar = ctk.CTkFrame(
            self,
            width=220,
            corner_radius=0,
            fg_color=COLORS["nav"]
        )

        self.sidebar.pack(
            side="left",
            fill="y"
        )

        self.sidebar.pack_propagate(False)

        # =====================================================
        # Sidebar Title
        # =====================================================

        title = ctk.CTkLabel(
            self.sidebar,
            text="HOSTEL\nMANAGEMENT",
            text_color="#FFFFFF",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        )

        title.pack(
            pady=(30, 20)
        )

        ctk.CTkLabel(
            self.sidebar,
            text=f"{self.user['username']}  ·  {self.user['role'].title()}",
            text_color="#AFC1D5",
            font=ctk.CTkFont(size=12),
        ).pack(pady=(0, 16))

        # =====================================================
        # Scrollable Menu
        # =====================================================

        self.menu_frame = ctk.CTkScrollableFrame(
            self.sidebar,
            width=190,
            corner_radius=0,
            fg_color="transparent"
        )

        self.menu_frame.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )

        # =====================================================
        # Sidebar Buttons
        # =====================================================

        buttons = get_menu_for_role(self.user["role"])
        icons = {
            "Dashboard": "⌂", "Students": "♙", "Rooms": "▦", "Fees": "₹",
            "Complaints": "◇", "Attendance": "◷", "Feedback": "☆",
            "Quality Dashboard": "◈", "Reports": "▤", "Profile": "●",
            "Settings": "⚙", "Notifications": "♧",
        }

        for button_name in buttons:

            if button_name == "Notifications":

                self.notifications_button = ctk.CTkButton(
                    self.menu_frame,
                    text=f"{icons.get(button_name, '•')}   Notifications",
                    width=180,
                    height=40,
                    anchor="w", fg_color="transparent", hover_color=COLORS["nav_hover"],
                    text_color="#E5EEF8", corner_radius=10, font=ctk.CTkFont(size=14, weight="bold"),
                    command=lambda name=button_name:
                    self.menu_clicked(name)
                )

                self.notifications_button.pack(
                    pady=6
                )

            else:

                button = ctk.CTkButton(
                    self.menu_frame,
                    text=f"{icons.get(button_name, '•')}   {button_name}",
                    width=180,
                    height=40,
                    anchor="w", fg_color="transparent", hover_color=COLORS["nav_hover"],
                    text_color="#E5EEF8", corner_radius=10, font=ctk.CTkFont(size=14, weight="bold"),
                    command=lambda name=button_name:
                    self.menu_clicked(name)
                )

                button.pack(
                    pady=6
                )

        # =====================================================
        # Logout Button
        # =====================================================

        logout_button = ctk.CTkButton(
            self.sidebar,
            text="Logout",
            width=180,
            height=40,
            fg_color="#A94442",
            hover_color="#893735",
            corner_radius=10,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.logout
        )

        logout_button.pack(
            side="bottom",
            pady=20
        )

    # =========================================================
    # DASHBOARD
    # =========================================================

    def create_dashboard(self):

        # IMPORTANT:
        # Create main_area only once.
        # This prevents Ctrl + R from creating duplicate
        # dashboard frames.

        if self.main_area is None:

            self.main_area = ctk.CTkFrame(
                self,
                corner_radius=0,
                fg_color=COLORS["page"]
            )

            self.main_area.pack(
                side="right",
                fill="both",
                expand=True
            )

        if self.dashboard_scroll is None or not self.dashboard_scroll.winfo_exists():
            self.dashboard_scroll = ctk.CTkScrollableFrame(
                self.main_area,
                corner_radius=0,
                fg_color="transparent",
                scrollbar_button_color="#7B8CA3",
                scrollbar_button_hover_color="#53677F",
            )
            self.dashboard_scroll.pack(fill="both", expand=True)

        if self.dashboard_figure is not None:
            plt.close(self.dashboard_figure)
            self.dashboard_figure = None
            self.dashboard_canvas = None

        # =====================================================
        # Header
        # =====================================================

        header = ctk.CTkFrame(
            self.dashboard_scroll,
            height=86,
            fg_color=COLORS["surface"], border_color=COLORS["border"],
            border_width=1, corner_radius=14
        )

        header.pack(
            fill="x",
            padx=20,
            pady=20
        )

        welcome = ctk.CTkLabel(
            header,
            text=f"Welcome, {self.user['username']} 👋",
            font=ctk.CTkFont(
                size=26,
                weight="bold"
            )
        )

        welcome.pack(
            side="left",
            padx=20,
            pady=20
        )

        role = ctk.CTkLabel(
            header,
            text=f"Role: {self.user['role'].upper()}",
            font=ctk.CTkFont(
                size=14
            ), text_color=COLORS["accent"]
        )

        role.pack(
            side="right",
            padx=20
        )

        # =====================================================
        # Statistics
        # =====================================================

        stats = get_dashboard_statistics(actor=self.user)

        cards_frame = ctk.CTkFrame(
            self.dashboard_scroll,
            fg_color="transparent"
        )

        cards_frame.pack(
            fill="x",
            padx=20,
            pady=10
        )

        for column in range(4):
            cards_frame.grid_columnconfigure(column, weight=1, uniform="dashboard_cards")
        if self.user["role"] == "admin":
            satisfaction = (
                f"{stats['average_satisfaction']}/5"
                if stats["average_satisfaction"] is not None else "No feedback"
            )
            cards = [
                ("Total Students", str(stats["total_students"])),
                ("Rooms", str(stats["total_rooms"])),
                ("Total Beds", str(stats["total_beds"])),
                ("Occupied Beds", str(stats["occupied_beds"])),
                ("Available Beds", str(stats["available_beds"])),
                ("Occupancy Rate", f"{stats['occupancy_rate']:.1f}%"),
                ("Fees Collected", f"₹{stats['collected_fees']:,.2f}"),
                ("Fees Pending", f"₹{stats['pending_fees']:,.2f}"),
                ("Open Complaints", str(stats["pending_complaints"])),
                ("Avg. Satisfaction", satisfaction),
            ]
        else:
            room = stats["student_room_number"] or "Not assigned"
            bed = str(stats["student_bed_number"]) if stats["student_bed_number"] is not None else "—"
            satisfaction = (
                f"{stats['average_satisfaction']}/5"
                if stats["average_satisfaction"] is not None else "No feedback"
            )
            cards = [
                ("Your Room", room),
                ("Your Bed", bed),
                ("Fees Paid", f"₹{stats['collected_fees']:,.2f}"),
                ("Fees Outstanding", f"₹{stats['pending_fees']:,.2f}"),
                ("Your Complaints", str(stats["total_complaints"])),
                ("Open Complaints", str(stats["pending_complaints"])),
                ("Your Satisfaction", satisfaction),
            ]

        for index, (title, value) in enumerate(cards):
            self.create_card(cards_frame, title, value, index % 4, index // 4)

        # =====================================================
        # Quality Summary
        # =====================================================

        quality_frame = ctk.CTkFrame(self.dashboard_scroll, fg_color=COLORS["surface"],
                                      border_color=COLORS["border"], border_width=1, corner_radius=14)

        quality_frame.pack(fill="x", padx=20, pady=(10, 12))

        quality_title_text = (
            "Q08 — Improve User Satisfaction"
            if self.user["role"] == "admin"
            else "Your Hostel Overview"
        )
        quality_title = ctk.CTkLabel(
            quality_frame,
            text=quality_title_text,
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        )

        quality_title.pack(
            pady=(30, 10)
        )

        if self.user["role"] == "admin":
            fee_completion = (
                f"{stats['fee_payment_completion_rate']}%"
                if stats["fee_payment_completion_rate"] is not None else "No fees recorded"
            )
            summary = (
                f"Feedback responses: {stats['feedback_count']}    •    "
                f"Complaint resolution: {stats['complaint_resolution_rate']}%    •    "
                f"Fee completion: {fee_completion}"
            )
        else:
            room_summary = (
                f"Room {stats['student_room_number']} · Bed {stats['student_bed_number']}"
                if stats["student_room_number"] else "No active room allocation"
            )
            summary = (
                f"{room_summary}    •    "
                f"Your open complaints: {stats['pending_complaints']}    •    "
                f"Your outstanding fees: ₹{stats['pending_fees']:,.2f}"
            )

        quality_text = ctk.CTkLabel(
            quality_frame,
            text=summary,
            font=ctk.CTkFont(
                size=16
            ),
            justify="left"
        )

        quality_text.pack(pady=(4, 24), padx=24)

        if self.user["role"] == "admin":
            self.create_dashboard_charts(stats)

        activity_frame = ctk.CTkFrame(self.dashboard_scroll, fg_color="transparent")
        activity_frame.pack(fill="x", padx=12, pady=(0, 20))
        activity_columns = 3 if self.user["role"] == "admin" else 2
        for column in range(activity_columns):
            activity_frame.grid_columnconfigure(column, weight=1, uniform="activity")
        self.create_activity_panel(
            activity_frame, "Recent Complaints", stats["recent_complaints"],
            lambda row: f"{row[1]} · {row[3]}\n{row[4]}  ·  {row[6] or 'Date unavailable'}",
            0,
        )
        self.create_activity_panel(
            activity_frame, "Recent Payments", stats["recent_payments"],
            lambda row: f"{row[1]} · ₹{float(row[4]):,.2f}\n{row[5] or 'Payment'}  ·  {row[6] or 'Date unavailable'}",
            1,
        )
        if self.user["role"] == "admin":
            self.create_activity_panel(
                activity_frame, "Recent Registrations", stats["recent_students"],
                lambda row: f"{row[1]} · {row[0]}\n{row[2] or 'Date unavailable'}",
                2,
            )
        self.apply_visual_theme()

    def create_dashboard_charts(self, stats):
        """Show concise admin-only occupancy, fee, and complaint charts."""
        colors = get_palette()
        section = ctk.CTkFrame(
            self.dashboard_scroll, fg_color=colors["surface"],
            border_color=colors["border"], border_width=1, corner_radius=14,
        )
        section.pack(fill="x", padx=20, pady=(0, 18))
        ctk.CTkLabel(
            section, text="Operations Overview",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(16, 4))

        self.dashboard_figure, axes = plt.subplots(2, 2, figsize=(12, 6.0))
        axes = axes.flatten()
        self.dashboard_figure.patch.set_facecolor(colors["surface"])
        complaint_statuses = stats["complaint_status_counts"]
        complaint_labels = [str(row[0]) for row in complaint_statuses]
        complaint_values = [row[1] for row in complaint_statuses]
        chart_specs = [
            ("Bed Occupancy", [stats["occupied_beds"], stats["available_beds"]], ["Occupied", "Available"]),
            ("Fee Collection", [stats["collected_fees"], stats["pending_fees"]], ["Collected", "Pending"]),
            ("Complaints by Status", complaint_values, complaint_labels),
        ]
        chart_colors = [colors["accent"], "#91A4BA"]
        for axis, (title, values, labels) in zip(axes[:3], chart_specs):
            axis.set_facecolor(colors["surface"])
            if sum(values) > 0:
                bars = axis.bar(labels, values, color=chart_colors, width=0.58)
                axis.bar_label(bars, fmt="%.0f" if max(values) >= 1 else "%.2f", padding=3,
                               color=colors["text"], fontsize=9)
                axis.margins(y=0.2)
            else:
                axis.text(0.5, 0.5, "No data yet", ha="center", va="center",
                          transform=axis.transAxes, color=colors["muted"])
                axis.set_xticks([])
            axis.set_title(title, color=colors["text"], fontsize=11, pad=12)
            axis.tick_params(axis="x", colors=colors["muted"], labelsize=9)
            axis.tick_params(axis="y", colors=colors["muted"], labelsize=8)
            axis.spines["top"].set_visible(False)
            axis.spines["right"].set_visible(False)
            axis.spines["left"].set_color(colors["border"])
            axis.spines["bottom"].set_color(colors["border"])
            axis.grid(axis="y", color=colors["border"], alpha=0.55, linewidth=0.6)
            axis.set_axisbelow(True)
        satisfaction_axis = axes[3]
        satisfaction_axis.set_facecolor(colors["surface"])
        satisfaction = stats["average_satisfaction"]
        if satisfaction is not None:
            satisfaction_axis.barh(["Average score"], [satisfaction], color=colors["accent"], height=0.48)
            satisfaction_axis.set_xlim(0, 5)
            satisfaction_axis.set_xticks(range(0, 6))
            satisfaction_axis.text(
                min(satisfaction + 0.12, 4.65), 0, f"{satisfaction:.2f}/5",
                va="center", color=colors["text"], fontsize=10,
            )
            satisfaction_axis.margins(y=0.7)
        else:
            satisfaction_axis.text(0.5, 0.5, "No feedback yet", ha="center", va="center",
                                   transform=satisfaction_axis.transAxes, color=colors["muted"])
            satisfaction_axis.set_xticks([])
        satisfaction_axis.set_title("User Satisfaction", color=colors["text"], fontsize=11, pad=12)
        satisfaction_axis.tick_params(colors=colors["muted"], labelsize=9)
        satisfaction_axis.spines["top"].set_visible(False)
        satisfaction_axis.spines["right"].set_visible(False)
        satisfaction_axis.spines["left"].set_color(colors["border"])
        satisfaction_axis.spines["bottom"].set_color(colors["border"])
        satisfaction_axis.grid(axis="x", color=colors["border"], alpha=0.55, linewidth=0.6)
        satisfaction_axis.set_axisbelow(True)
        self.dashboard_figure.tight_layout(pad=2.2)
        self.dashboard_canvas = FigureCanvasTkAgg(self.dashboard_figure, master=section)
        self.dashboard_canvas.draw()
        self.dashboard_canvas.get_tk_widget().pack(fill="x", expand=True, padx=14, pady=(0, 14))

    def create_activity_panel(self, parent, title, records, formatter, column):
        """Render a small, role-scoped activity list."""
        colors = get_palette()
        panel = ctk.CTkFrame(
            parent, fg_color=colors["surface"], border_color=colors["border"],
            border_width=1, corner_radius=12,
        )
        panel.grid(row=0, column=column, padx=8, sticky="nsew")
        ctk.CTkLabel(
            panel, text=title, font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=15, pady=(14, 8))
        if not records:
            ctk.CTkLabel(
                panel, text="Nothing to show yet", text_color=colors["muted"],
            ).pack(anchor="w", padx=15, pady=(2, 16))
            return
        for index, row in enumerate(records):
            ctk.CTkLabel(
                panel, text=formatter(row), justify="left", anchor="w",
                text_color=colors["text"], wraplength=300,
            ).pack(fill="x", padx=15, pady=(2, 8))

    # =========================================================
    # DASHBOARD CARDS
    # =========================================================

    def create_card(
        self,
        parent,
        title,
        value,
        column,
        row=0,
    ):

        card = ctk.CTkFrame(
            parent,
            width=190,
            height=130, fg_color=COLORS["surface"], border_color=COLORS["border"],
            border_width=1, corner_radius=14
        )

        card.grid(
            row=row,
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
            font=ctk.CTkFont(
                size=13
            )
        )

        title_label.pack(
            pady=(20, 5)
        )

        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(
                size=25,
                weight="bold"
            )
        )

        value_label.pack()

        colors = get_palette()
        title_label.configure(text_color=colors["muted"])
        value_label.configure(text_color=colors["accent"])

    # =========================================================
    # NOTIFICATION COUNT
    # =========================================================

    def update_notification_count(self):

        try:

            unread_count = get_unread_count(self.user["id"], actor=self.user)

            if unread_count > 0:

                self.notifications_button.configure(
                    text=f"🔔 Notifications ({unread_count})"
                )

            else:

                self.notifications_button.configure(
                    text="🔔 Notifications"
                )

        except Exception as error:

            print(
                "Notification count error:",
                error
            )

    # =========================================================
    # MENU
    # =========================================================

    def menu_clicked(self, name):

        try:
            require_menu_access(self.user, name)
        except AuthorizationError as error:
            messagebox.showwarning("Access denied", str(error), parent=self)
            return

        print(f"{name} clicked")

        # =====================================================
        # Dashboard
        # =====================================================

        if name == "Dashboard":

            self.go_home()

            return

        # =====================================================
        # Students
        # =====================================================

        elif name == "Students":

            if (
                self.students_window is None
                or not self.students_window.winfo_exists()
            ):

                self.students_window = StudentsWindow(self)

            else:

                self.students_window.lift()

            self._raise_feature_window(self.students_window)

            return

        # =====================================================
        # Rooms
        # =====================================================

        elif name == "Rooms":

            if (
                self.rooms_window is None
                or not self.rooms_window.winfo_exists()
            ):

                self.rooms_window = RoomsWindow(self)

            else:

                self.rooms_window.lift()

            self._raise_feature_window(self.rooms_window)

            return

        # =====================================================
        # Fees
        # =====================================================

        elif name == "Fees":

            if (
                self.fees_window is None
                or not self.fees_window.winfo_exists()
            ):

                self.fees_window = FeeManagement(self)

            else:

                self.fees_window.lift()

            self._raise_feature_window(self.fees_window)

            return

        # =====================================================
        # Complaints
        # =====================================================

        elif name == "Complaints":

            if (
                self.complaints_window is None
                or not self.complaints_window.winfo_exists()
            ):

                self.complaints_window = ComplaintManagement(self)

            else:

                self.complaints_window.lift()

            self._raise_feature_window(self.complaints_window)

            return

        # =====================================================
        # Attendance
        # =====================================================

        elif name == "Attendance":

            if (
                self.attendance_window is None
                or not self.attendance_window.winfo_exists()
            ):

                self.attendance_window = AttendanceManagement(self)

            else:

                self.attendance_window.lift()

            self._raise_feature_window(self.attendance_window)

            return

        # =====================================================
        # Feedback
        # =====================================================

        elif name == "Feedback":

            if (
                self.feedback_window is None
                or not self.feedback_window.winfo_exists()
            ):

                self.feedback_window = FeedbackManagement(self)

            else:

                self.feedback_window.lift()

            self._raise_feature_window(self.feedback_window)

            return

        # =====================================================
        # Notifications
        # =====================================================

        elif name == "Notifications":

            if (
                self.notifications_window is None
                or not self.notifications_window.winfo_exists()
            ):

                self.notifications_window = NotificationsWindow(
                    self,
                    self.user
                )

            else:

                self.notifications_window.lift()

            self._raise_feature_window(self.notifications_window)

            self.update_notification_count()

            return

        # =====================================================
        # Quality Dashboard
        # =====================================================

        elif name == "Quality Dashboard":

            if (
                self.quality_window is None
                or not self.quality_window.winfo_exists()
            ):

                self.quality_window = QualityDashboardWindow(self)

            else:

                self.quality_window.lift()

            self._raise_feature_window(self.quality_window)

            return

        # =====================================================
        # Reports
        # =====================================================

        elif name == "Reports":

            print("Opening Reports Window...")

            if (
                self.reports_window is None
                or not self.reports_window.winfo_exists()
            ):

                self.reports_window = ReportsWindow(self)

            else:

                self.reports_window.lift()

            self._raise_feature_window(self.reports_window)

            print("Reports Window Opened")

            return

        # =====================================================
        # Profile
        # =====================================================

        elif name == "Profile":

            if (
                self.profile_window is None
                or not self.profile_window.winfo_exists()
            ):

                self.profile_window = ProfileWindow(
                    self,
                    self.user
                )

            else:

                self.profile_window.lift()

            self._raise_feature_window(self.profile_window)

            return

        # =====================================================
        # Settings
        # =====================================================

        elif name == "Settings":

            if (
                self.settings_window is None
                or not self.settings_window.winfo_exists()
            ):

                self.settings_window = SettingsWindow(
                    self,
                    self.user
                )

            else:

                self.settings_window.lift()

            self._raise_feature_window(self.settings_window)

            return

    def _raise_feature_window(self, window):
        """Keep feature windows owned by and stacked above the dashboard."""
        if window is None or not window.winfo_exists():
            return

        try:
            self._active_feature_window = window
            self.shortcut_manager.attach_window(window)
            window.transient(self)
            window.state("zoomed")
            window.deiconify()
            window.lift()
            window.focus_force()
            # Windows can process focus before the native window is mapped.
            window.after(80, lambda target=window: self._finish_raise(target))
        except Exception:
            pass

    def _finish_raise(self, window):
        if window.winfo_exists():
            window.lift()
            window.focus_force()

    # =========================================================
    # KEYBOARD SHORTCUTS
    # =========================================================

    def go_home(self):

        """
        Ctrl + H

        Return to dashboard without creating
        another dashboard frame.
        """

        active = self._active_feature_window
        self._active_feature_window = None
        if active is not None and active.winfo_exists():
            active.withdraw()
        self.lift()
        self.focus_force()

    def refresh_active_page(self):
        """Refresh the window currently holding keyboard focus."""
        active = self._active_feature_window
        focused = self.focus_get()
        if focused is not None:
            top = focused.winfo_toplevel()
            if top is self:
                active = None
            else:
                active = top

        refreshers = {
            self.students_window: "load_students",
            self.rooms_window: "refresh_all",
            self.fees_window: "load_fees",
            self.complaints_window: "load_complaints",
            self.attendance_window: "load_attendance",
            self.feedback_window: "load_feedback",
            self.notifications_window: "load_notifications",
            self.reports_window: "refresh_reports",
            self.settings_window: "load_settings",
        }
        method_name = refreshers.get(active)
        if active is None:
            self.refresh_dashboard()
        elif method_name and active.winfo_exists():
            getattr(active, method_name)()
        elif active in (self.quality_window, self.profile_window) and active.winfo_exists():
            if active is self.quality_window:
                self.quality_window = None
                feature_name = "Quality Dashboard"
            else:
                self.profile_window = None
                feature_name = "Profile"
            active.destroy()
            self.menu_clicked(feature_name)

    # =========================================================

    def refresh_dashboard(self):

        """
        Ctrl + R

        Refresh only the contents inside main_area.

        The main_area itself is NOT destroyed.
        Therefore the sidebar and layout remain correct.
        """

        if self.main_area is None:
            return

        # Remove existing dashboard content
        if self.dashboard_figure is not None:
            plt.close(self.dashboard_figure)
            self.dashboard_figure = None
            self.dashboard_canvas = None
        if self.dashboard_scroll is not None and self.dashboard_scroll.winfo_exists():
            self.dashboard_scroll.destroy()
        self.dashboard_scroll = None

        # Recreate dashboard content
        # using the SAME main_area
        self.create_dashboard()

        # Update notification badge
        self.update_notification_count()

    # =========================================================

    def apply_visual_theme(self):
        """Refresh dashboard and open feature windows for the active theme."""
        colors = get_palette()
        self.configure(fg_color=colors["page"])
        self.sidebar.configure(fg_color=colors["nav"])

        for widget in self.sidebar.winfo_children():
            if isinstance(widget, ctk.CTkLabel):
                label = str(widget.cget("text"))
                widget.configure(
                    text_color="#FFFFFF" if label.startswith("HOSTEL") else "#B8C7D8"
                )
            elif isinstance(widget, ctk.CTkScrollableFrame):
                widget.configure(
                    fg_color="transparent",
                    scrollbar_button_color="#40536C",
                    scrollbar_button_hover_color="#637991",
                )

        for widget in self.menu_frame.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                if str(widget.cget("text")).startswith("Logout"):
                    widget.configure(fg_color=colors["danger"], hover_color="#963B3B")
                else:
                    widget.configure(
                        fg_color="transparent",
                        hover_color=colors["nav_hover"],
                        text_color="#E7EEF7",
                    )

        if self.main_area is not None:
            apply_professional_style(self.main_area)
        self.apply_dashboard_chart_theme()

        for attr in (
            "students_window", "rooms_window", "fees_window", "complaints_window",
            "attendance_window", "feedback_window", "quality_window", "reports_window",
            "profile_window", "settings_window", "notifications_window",
        ):
            window = getattr(self, attr, None)
            if window is not None and window.winfo_exists():
                apply_professional_style(window)
                if hasattr(window, "refresh_theme_display"):
                    window.refresh_theme_display()
                if attr == "settings_window" and hasattr(window, "theme_menu"):
                    window.theme_menu.set(ThemeManager.get_current_theme().capitalize())

    def apply_dashboard_chart_theme(self):
        """Keep the embedded Matplotlib charts in sync with light/dark mode."""
        if self.dashboard_figure is None:
            return
        colors = get_palette()
        self.dashboard_figure.patch.set_facecolor(colors["surface"])
        for axis in self.dashboard_figure.axes:
            axis.set_facecolor(colors["surface"])
            axis.title.set_color(colors["text"])
            axis.xaxis.label.set_color(colors["text"])
            axis.yaxis.label.set_color(colors["text"])
            axis.tick_params(colors=colors["muted"])
            for spine in axis.spines.values():
                if spine.get_visible():
                    spine.set_color(colors["border"])
            for index, bar in enumerate(axis.patches):
                bar.set_facecolor(colors["accent"] if index % 2 == 0 else "#91A4BA")
            for label in axis.texts:
                label.set_color(colors["text"] if label.get_text() != "No data yet" else colors["muted"])
            axis.yaxis.grid(True, color=colors["border"], alpha=0.55, linewidth=0.6)
        if self.dashboard_canvas is not None:
            self.dashboard_canvas.draw_idle()

    def toggle_theme(self):

        """
        Ctrl + D

        Toggle between Light and Dark mode.
        """

        current_mode = ctk.get_appearance_mode()

        if current_mode == "Light":

            new_theme = ThemeManager.DARK_MODE

        else:

            new_theme = ThemeManager.LIGHT_MODE

        ThemeManager.set_theme(new_theme)
        self.apply_visual_theme()
        try:
            ThemeManager.save_user_theme(self.user["id"], new_theme)
        except Exception:
            messagebox.showerror(
                "Theme",
                "Theme changed for this session but could not be saved. Please try again.",
                parent=self,
            )

    # =========================================================

    def exit_application(self):

        """
        Ctrl + Q

        Exit application after confirmation.
        """

        result = messagebox.askyesno(
            "Exit Application",
            "Are you sure you want to exit the application?"
        )

        if result:
            revoke_session(self.user.get("session_token"))
            self.destroy()

    # =========================================================
    # LOGOUT
    # =========================================================

    def logout(self):

        result = messagebox.askyesno(
            "Logout",
            "Are you sure you want to logout?"
        )

        if result:

            self.destroy()


# =============================================================
# DIRECT TEST
# =============================================================

if __name__ == "__main__":

    test_user = {
        "id": 1,
        "username": "admin",
        "email": "admin@hostel.com",
        "role": "admin"
    }

    app = DashboardWindow(
        test_user
    )

    app.mainloop()
