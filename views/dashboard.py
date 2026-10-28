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


# ─── sidebar menu items with emoji icons ────────────────────────────────────
_MENU_ICONS = {
    "Dashboard":        "⊞",
    "Students":         "👤",
    "Rooms":            "🛏",
    "Fees":             "💳",
    "Complaints":       "💬",
    "Attendance":       "📋",
    "Feedback":         "⭐",
    "Quality Dashboard":"📊",
    "Reports":          "📄",
    "Profile":          "🔘",
    "Settings":         "⚙",
    "Notifications":    "🔔",
}

# card accent colours (left-border stripe per metric category)
_CARD_ACCENTS = {
    "Total Students":    "#6366F1",
    "Rooms":             "#8B5CF6",
    "Total Beds":        "#06B6D4",
    "Occupied Beds":     "#F59E0B",
    "Available Beds":    "#10B981",
    "Occupancy Rate":    "#3B82F6",
    "Fees Collected":    "#10B981",
    "Fees Pending":      "#EF4444",
    "Open Complaints":   "#F59E0B",
    "Avg. Satisfaction": "#6366F1",
    # student cards
    "Your Room":         "#6366F1",
    "Your Bed":          "#8B5CF6",
    "Fees Paid":         "#10B981",
    "Fees Outstanding":  "#EF4444",
    "Your Complaints":   "#F59E0B",
    "Open Complaints ":  "#EF4444",
    "Your Satisfaction": "#6366F1",
}


class DashboardWindow(ctk.CTk):

    def __init__(self, user):
        user = load_actor(user)
        super().__init__()

        self.user = user
        ThemeManager.set_theme(ThemeManager.load_user_theme(self.user["id"]))

        self.title("Hostel Management System — Dashboard")
        self.minsize(720, 480)
        colors = get_palette()
        self.configure(fg_color=colors["page"])

        ctk.set_default_color_theme("blue")

        # ── window references ────────────────────────────────────────────────
        self.students_window    = None
        self.rooms_window       = None
        self.fees_window        = None
        self.complaints_window  = None
        self.attendance_window  = None
        self.feedback_window    = None
        self.quality_window     = None
        self.reports_window     = None
        self.profile_window     = None
        self.settings_window    = None
        self.notifications_window = None
        self._active_feature_window = None

        # ── content area refs ────────────────────────────────────────────────
        self.main_area        = None
        self.dashboard_scroll = None
        self.dashboard_figure = None
        self.dashboard_canvas = None
        self._active_menu_btn = None   # currently highlighted sidebar button

        # ── build UI ─────────────────────────────────────────────────────────
        self.create_sidebar()
        self.create_dashboard()
        self.update_notification_count()

        # ── maximize on first launch, then allow free resize ─────────────────
        self.update_idletasks()   # force geometry to settle first
        self.state("zoomed")      # open maximized
        self.lift()
        self.focus_force()

        # ── keyboard shortcuts ───────────────────────────────────────────────
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
            exit_callback=self.exit_application,
        )

    # =========================================================================
    # SIDEBAR
    # =========================================================================

    def create_sidebar(self):
        colors = get_palette()

        self.sidebar = ctk.CTkFrame(
            self,
            width=258,
            corner_radius=0,
            fg_color=colors["nav"],
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # ── logo / brand area ────────────────────────────────────────────────
        brand_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent",
            height=72,
        )
        brand_frame.pack(fill="x", padx=16, pady=(22, 4))
        brand_frame.pack_propagate(False)

        logo_pill = ctk.CTkFrame(
            brand_frame,
            width=42,
            height=42,
            corner_radius=12,
            fg_color=colors["accent"],
        )
        logo_pill.place(x=0, y=15)
        logo_pill.pack_propagate(False)
        ctk.CTkLabel(
            logo_pill,
            text="H",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#FFFFFF",
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            brand_frame,
            text="Hostel",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#FFFFFF",
            anchor="w",
        ).place(x=54, y=17)
        ctk.CTkLabel(
            brand_frame,
            text="Management System",
            font=ctk.CTkFont(size=10),
            text_color=colors["muted"],
            anchor="w",
        ).place(x=54, y=40)

        # thin divider
        ctk.CTkFrame(
            self.sidebar,
            height=1,
            fg_color=colors["nav_hover"],
            corner_radius=0,
        ).pack(fill="x", padx=16, pady=(12, 8))

        # ── menu area ───────────────────────────────────────────────────────
        menu_label = ctk.CTkLabel(
            self.sidebar,
            text="NAVIGATION",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=colors["subtle"],
            anchor="w",
        )
        menu_label.pack(fill="x", padx=20, pady=(4, 6))

        self.menu_frame = ctk.CTkScrollableFrame(
            self.sidebar,
            corner_radius=0,
            fg_color="transparent",
            scrollbar_button_color=colors["nav_hover"],
            scrollbar_button_hover_color=colors["muted"],
        )
        self.menu_frame.pack(fill="both", expand=True, padx=10, pady=2)

        # ── sidebar buttons ──────────────────────────────────────────────────
        menu_items = get_menu_for_role(self.user["role"])
        self._menu_buttons = {}

        for name in menu_items:
            icon = _MENU_ICONS.get(name, "•")
            btn = ctk.CTkButton(
                self.menu_frame,
                text=f"  {icon}   {name}",
                height=40,
                anchor="w",
                corner_radius=10,
                fg_color="transparent",
                hover_color=colors["nav_hover"],
                text_color="#E2E8F0",
                font=ctk.CTkFont(size=13, weight="bold"),
                command=lambda n=name: self.menu_clicked(n),
            )
            btn.pack(fill="x", pady=2)
            self._menu_buttons[name] = btn

        # keep notification button accessible for badge update
        self.notifications_button = self._menu_buttons.get("Notifications")

        # ── divider before user section ──────────────────────────────────────
        ctk.CTkFrame(
            self.sidebar,
            height=1,
            fg_color=colors["nav_hover"],
            corner_radius=0,
        ).pack(fill="x", padx=16, pady=(8, 0))

        # ── user info pill (bottom) ──────────────────────────────────────────
        user_row = ctk.CTkFrame(
            self.sidebar,
            fg_color=colors["nav_surface"],
            corner_radius=12,
            height=58,
        )
        user_row.pack(fill="x", padx=12, pady=(10, 4))
        user_row.pack_propagate(False)

        # avatar circle
        initials = (self.user.get("username") or "?")[:2].upper()
        avatar = ctk.CTkFrame(
            user_row,
            width=36,
            height=36,
            corner_radius=18,
            fg_color=colors["accent"],
        )
        avatar.place(x=10, rely=0.5, anchor="w")
        avatar.pack_propagate(False)
        ctk.CTkLabel(
            avatar,
            text=initials,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#FFFFFF",
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            user_row,
            text=self.user["username"],
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#E2E8F0",
            anchor="w",
        ).place(x=56, y=10)
        ctk.CTkLabel(
            user_row,
            text=self.user["role"].title(),
            font=ctk.CTkFont(size=10),
            text_color=colors["muted"],
            anchor="w",
        ).place(x=56, y=30)

        # ── logout button ────────────────────────────────────────────────────
        ctk.CTkButton(
            self.sidebar,
            text="⏻   Logout",
            height=40,
            corner_radius=10,
            fg_color=colors["danger_soft"],
            hover_color=colors["danger"],
            text_color=colors["danger"],
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.logout,
        ).pack(fill="x", padx=12, pady=(6, 18))

    # =========================================================================
    # DASHBOARD CONTENT
    # =========================================================================

    def create_dashboard(self):
        colors = get_palette()

        # main_area created only once
        if self.main_area is None:
            self.main_area = ctk.CTkFrame(
                self,
                corner_radius=0,
                fg_color=colors["page"],
            )
            self.main_area.pack(side="right", fill="both", expand=True)

        # ── (re)create scroll frame ──────────────────────────────────────────
        if self.dashboard_scroll is None or not self.dashboard_scroll.winfo_exists():
            self.dashboard_scroll = ctk.CTkScrollableFrame(
                self.main_area,
                corner_radius=0,
                fg_color=colors["page"],      # explicit — prevents artifact
                scrollbar_button_color=colors["border"],
                scrollbar_button_hover_color=colors["muted"],
            )
            self.dashboard_scroll.pack(fill="both", expand=True)

        # close any previous matplotlib figure
        if self.dashboard_figure is not None:
            plt.close(self.dashboard_figure)
            self.dashboard_figure = None
            self.dashboard_canvas = None

        stats = get_dashboard_statistics(actor=self.user)

        self._build_header(colors)
        self._build_stat_cards(stats, colors)
        self._build_summary_bar(stats, colors)
        if self.user["role"] == "admin":
            self.create_dashboard_charts(stats)
        self._build_activity_panels(stats, colors)
        self.apply_visual_theme()

    # ─── header ──────────────────────────────────────────────────────────────

    def _build_header(self, colors):
        from datetime import datetime
        hour = datetime.now().hour
        greeting = (
            "Good morning" if hour < 12
            else "Good afternoon" if hour < 17
            else "Good evening"
        )

        header = ctk.CTkFrame(
            self.dashboard_scroll,
            height=80,
            fg_color=colors["surface"],
            border_color=colors["border"],
            border_width=1,
            corner_radius=16,
        )
        header.pack(fill="x", padx=24, pady=(20, 8))
        header.pack_propagate(False)

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", padx=20, pady=0, fill="y")

        ctk.CTkLabel(
            left,
            text=f"{greeting}, {self.user['username']} 👋",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=colors["text"],
            anchor="w",
        ).pack(anchor="w", pady=(16, 0))

        ctk.CTkLabel(
            left,
            text="Here's what's happening in your hostel today.",
            font=ctk.CTkFont(size=12),
            text_color=colors["muted"],
            anchor="w",
        ).pack(anchor="w")

        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right", padx=20, fill="y")

        # role pill
        role_color = colors["accent_soft"]
        ctk.CTkFrame(
            right,
            width=90, height=28,
            corner_radius=14,
            fg_color=role_color,
            border_color=colors["accent"],
            border_width=1,
        ).place(relx=1.0, rely=0.5, anchor="e", x=-10)

        ctk.CTkLabel(
            right,
            text=f"  {self.user['role'].upper()}  ",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=colors["accent"],
            corner_radius=14,
            fg_color=role_color,
            width=90,
            height=28,
        ).pack(anchor="e", pady=(26, 0))

        # quick-action buttons
        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.pack(side="right", padx=6, fill="y")

        ctk.CTkButton(
            actions,
            text="⟳  Refresh",
            width=96,
            height=32,
            corner_radius=8,
            fg_color=colors["surface_alt"],
            hover_color=colors["border"],
            text_color=colors["text_2"],
            font=ctk.CTkFont(size=12),
            command=self.refresh_dashboard,
        ).pack(anchor="e", pady=(24, 4))

    # ─── stat cards ──────────────────────────────────────────────────────────

    def _build_stat_cards(self, stats, colors):
        if self.user["role"] == "admin":
            satisfaction = (
                f"{stats['average_satisfaction']:.1f}/5"
                if stats["average_satisfaction"] is not None else "—"
            )
            cards = [
                ("Total Students",  str(stats["total_students"])),
                ("Rooms",           str(stats["total_rooms"])),
                ("Available Beds",  str(stats["available_beds"])),
                ("Occupancy Rate",  f"{stats['occupancy_rate']:.0f}%"),
                ("Fees Collected",  f"₹{stats['collected_fees']:,.0f}"),
                ("Fees Pending",    f"₹{stats['pending_fees']:,.0f}"),
                ("Open Complaints", str(stats["pending_complaints"])),
                ("Avg. Satisfaction", satisfaction),
            ]
        else:
            room = stats["student_room_number"] or "Not assigned"
            bed  = str(stats["student_bed_number"]) if stats["student_bed_number"] is not None else "—"
            satisfaction = (
                f"{stats['average_satisfaction']:.1f}/5"
                if stats["average_satisfaction"] is not None else "—"
            )
            cards = [
                ("Your Room",        room),
                ("Your Bed",         bed),
                ("Fees Paid",        f"₹{stats['collected_fees']:,.0f}"),
                ("Fees Outstanding", f"₹{stats['pending_fees']:,.0f}"),
                ("Your Complaints",  str(stats["total_complaints"])),
                ("Open Complaints",  str(stats["pending_complaints"])),
                ("Your Satisfaction",satisfaction),
            ]

        grid = ctk.CTkFrame(self.dashboard_scroll, fg_color="transparent")
        grid.pack(fill="x", padx=24, pady=(8, 4))

        cols = 4
        for c in range(cols):
            grid.grid_columnconfigure(c, weight=1, uniform="cards")

        for idx, (title, value) in enumerate(cards):
            self._create_card(grid, title, value, idx % cols, idx // cols, colors)

    def _create_card(self, parent, title, value, col, row, colors):
        accent = _CARD_ACCENTS.get(title, colors["accent"])

        # outer card frame
        card = ctk.CTkFrame(
            parent,
            height=104,
            fg_color=colors["surface"],
            border_color=colors["border"],
            border_width=1,
            corner_radius=14,
        )
        card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
        card.grid_propagate(False)

        # coloured left accent bar
        bar = ctk.CTkFrame(
            card,
            width=4,
            corner_radius=2,
            fg_color=accent,
        )
        bar.place(x=0, rely=0.15, relheight=0.7)
        # title
        ctk.CTkLabel(
            card,
            text=title.upper(),
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=colors["muted"],
            anchor="w",
        ).place(x=20, y=20)

        # value
        ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=accent,
            anchor="w",
        ).place(x=20, y=44)

    # ─── summary bar ─────────────────────────────────────────────────────────

    def _build_summary_bar(self, stats, colors):
        bar = ctk.CTkFrame(
            self.dashboard_scroll,
            fg_color=colors["surface"],
            border_color=colors["border"],
            border_width=1,
            corner_radius=14,
            height=58,
        )
        bar.pack(fill="x", padx=24, pady=(6, 10))
        bar.pack_propagate(False)

        if self.user["role"] == "admin":
            fee_completion = (
                f"{stats['fee_payment_completion_rate']}%"
                if stats["fee_payment_completion_rate"] is not None
                else "No fees"
            )
            parts = [
                ("📁 Feedback responses", str(stats["feedback_count"])),
                ("✅ Resolution rate", f"{stats['complaint_resolution_rate']}%"),
                ("💳 Fee completion", fee_completion),
            ]
        else:
            room_text = (
                f"Room {stats['student_room_number']} · Bed {stats['student_bed_number']}"
                if stats["student_room_number"] else "No allocation"
            )
            parts = [
                ("🛏 Your room", room_text),
                ("⚠ Open complaints", str(stats["pending_complaints"])),
                ("💳 Outstanding fees", f"₹{stats['pending_fees']:,.0f}"),
            ]

        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20)

        for i, (label, val) in enumerate(parts):
            seg = ctk.CTkFrame(inner, fg_color="transparent")
            seg.pack(side="left", expand=True, fill="both")

            ctk.CTkLabel(
                seg,
                text=label,
                font=ctk.CTkFont(size=10),
                text_color=colors["muted"],
            ).pack(anchor="w", pady=(8, 0))

            ctk.CTkLabel(
                seg,
                text=val,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=colors["text"],
            ).pack(anchor="w")

            # vertical separator between segments
            if i < len(parts) - 1:
                ctk.CTkFrame(
                    inner,
                    width=1,
                    fg_color=colors["border"],
                    corner_radius=0,
                ).pack(side="left", fill="y", pady=10)

    # ─── charts ──────────────────────────────────────────────────────────────

    def create_dashboard_charts(self, stats):
        """Admin-only 2×2 Matplotlib chart grid — DPI-corrected for sharpness."""
        colors = get_palette()

        section = ctk.CTkFrame(
            self.dashboard_scroll,
            fg_color=colors["surface"],
            border_color=colors["border"],
            border_width=1,
            corner_radius=16,
        )
        section.pack(fill="x", padx=24, pady=(4, 10))

        ctk.CTkLabel(
            section,
            text="Operations Overview",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=colors["text"],
        ).pack(anchor="w", padx=20, pady=(16, 4))

        # ── DPI-aware figure ─────────────────────────────────────────────────
        try:
            # winfo_fpixels("1i") returns pixels per inch → actual screen DPI
            screen_dpi = self.winfo_fpixels("1i")
            fig_dpi = min(max(int(screen_dpi), 72), 150)
        except Exception:
            fig_dpi = 100

        bg = colors["surface"]
        self.dashboard_figure, axes = plt.subplots(
            2, 2,
            figsize=(12, 5.6),
            dpi=fig_dpi,
        )
        axes = axes.flatten()
        self.dashboard_figure.patch.set_facecolor(bg)
        self.dashboard_figure.subplots_adjust(
            left=0.06, right=0.97, top=0.92, bottom=0.10,
            hspace=0.55, wspace=0.32,
        )

        complaint_statuses = stats["complaint_status_counts"]
        complaint_labels   = [str(r[0]) for r in complaint_statuses]
        complaint_values   = [r[1] for r in complaint_statuses]

        bar_color   = colors["accent"]
        alt_color   = colors["border"]

        chart_specs = [
            ("Bed Occupancy",      [stats["occupied_beds"],    stats["available_beds"]],  ["Occupied",  "Available"]),
            ("Fee Collection",     [stats["collected_fees"],   stats["pending_fees"]],    ["Collected", "Pending"]),
            ("Complaints by Status", complaint_values, complaint_labels),
        ]

        for axis, (title, values, labels) in zip(axes[:3], chart_specs):
            axis.set_facecolor(bg)
            if sum(v for v in values if v) > 0:
                bar_colors = [bar_color, alt_color] * (len(values) // 2 + 1)
                bars = axis.bar(labels, values, color=bar_colors[:len(values)], width=0.52, zorder=3)
                axis.bar_label(bars, fmt="%.0f", padding=4,
                               color=colors["text"], fontsize=8, fontweight="bold")
                axis.margins(y=0.25)
            else:
                axis.text(0.5, 0.5, "No data yet", ha="center", va="center",
                          transform=axis.transAxes, color=colors["muted"], fontsize=9)
                axis.set_xticks([])

            axis.set_title(title, color=colors["text"], fontsize=10,
                           fontweight="bold", pad=10)
            axis.tick_params(axis="x", colors=colors["muted"], labelsize=8)
            axis.tick_params(axis="y", colors=colors["muted"], labelsize=7)
            axis.spines["top"].set_visible(False)
            axis.spines["right"].set_visible(False)
            axis.spines["left"].set_color(colors["border"])
            axis.spines["bottom"].set_color(colors["border"])
            axis.grid(axis="y", color=colors["border"], alpha=0.6, linewidth=0.7, zorder=0)
            axis.set_axisbelow(True)

        # satisfaction horizontal bar
        sat_ax = axes[3]
        sat_ax.set_facecolor(bg)
        satisfaction = stats["average_satisfaction"]
        if satisfaction is not None:
            sat_ax.barh(["Avg. Score"], [satisfaction],
                        color=bar_color, height=0.42, zorder=3)
            sat_ax.set_xlim(0, 5)
            sat_ax.set_xticks([0, 1, 2, 3, 4, 5])
            sat_ax.text(
                min(satisfaction + 0.1, 4.55), 0,
                f"  {satisfaction:.2f}/5",
                va="center", color=colors["text"], fontsize=9, fontweight="bold",
            )
            sat_ax.margins(y=0.7)
        else:
            sat_ax.text(0.5, 0.5, "No feedback yet", ha="center", va="center",
                        transform=sat_ax.transAxes, color=colors["muted"], fontsize=9)
            sat_ax.set_xticks([])

        sat_ax.set_title("User Satisfaction", color=colors["text"], fontsize=10,
                         fontweight="bold", pad=10)
        sat_ax.tick_params(colors=colors["muted"], labelsize=8)
        sat_ax.spines["top"].set_visible(False)
        sat_ax.spines["right"].set_visible(False)
        sat_ax.spines["left"].set_color(colors["border"])
        sat_ax.spines["bottom"].set_color(colors["border"])
        sat_ax.grid(axis="x", color=colors["border"], alpha=0.6, linewidth=0.7, zorder=0)
        sat_ax.set_axisbelow(True)

        # ── embed canvas ─────────────────────────────────────────────────────
        self.dashboard_canvas = FigureCanvasTkAgg(self.dashboard_figure, master=section)
        self.dashboard_canvas.draw()
        tk_widget = self.dashboard_canvas.get_tk_widget()
        tk_widget.configure(highlightthickness=0, bd=0)   # remove ugly border
        tk_widget.pack(fill="x", expand=True, padx=16, pady=(0, 16))

    # ─── activity panels ─────────────────────────────────────────────────────

    def _build_activity_panels(self, stats, colors):
        cols = 3 if self.user["role"] == "admin" else 2
        frame = ctk.CTkFrame(self.dashboard_scroll, fg_color="transparent")
        frame.pack(fill="x", padx=18, pady=(4, 24))

        for c in range(cols):
            frame.grid_columnconfigure(c, weight=1, uniform="activity")

        self._activity_panel(
            frame, "Recent Complaints", stats["recent_complaints"],
            lambda r: (f"{r[1]} · {r[3]}", f"{r[4]}  ·  {r[6] or 'Pending'}"),
            0, colors,
        )
        self._activity_panel(
            frame, "Recent Payments", stats["recent_payments"],
            lambda r: (f"{r[1]} · ₹{float(r[4]):,.2f}", f"{r[5] or 'Payment'}  ·  {r[6] or '—'}"),
            1, colors,
        )
        if self.user["role"] == "admin":
            self._activity_panel(
                frame, "Recent Registrations", stats["recent_students"],
                lambda r: (f"{r[1]} · {r[0]}", r[2] or "—"),
                2, colors,
            )

    def _activity_panel(self, parent, title, records, formatter, col, colors):
        panel = ctk.CTkFrame(
            parent,
            fg_color=colors["surface"],
            border_color=colors["border"],
            border_width=1,
            corner_radius=14,
        )
        panel.grid(row=0, column=col, padx=6, sticky="nsew")

        ctk.CTkLabel(
            panel,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=colors["text"],
            anchor="w",
        ).pack(anchor="w", padx=16, pady=(14, 6))

        # thin accent line under title
        ctk.CTkFrame(
            panel,
            height=2,
            corner_radius=1,
            fg_color=colors["accent"],
        ).pack(fill="x", padx=16, pady=(0, 8))

        if not records:
            ctk.CTkLabel(
                panel,
                text="Nothing to show yet",
                text_color=colors["muted"],
                font=ctk.CTkFont(size=12),
            ).pack(anchor="w", padx=16, pady=(4, 16))
            return

        for row in records:
            main_text, sub_text = formatter(row)

            row_frame = ctk.CTkFrame(
                panel,
                fg_color=colors["surface_alt"],
                corner_radius=8,
            )
            row_frame.pack(fill="x", padx=12, pady=3)

            ctk.CTkLabel(
                row_frame,
                text=main_text,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=colors["text"],
                anchor="w",
                wraplength=280,
            ).pack(anchor="w", padx=10, pady=(6, 0))

            ctk.CTkLabel(
                row_frame,
                text=sub_text,
                font=ctk.CTkFont(size=10),
                text_color=colors["muted"],
                anchor="w",
                wraplength=280,
            ).pack(anchor="w", padx=10, pady=(0, 6))

        ctk.CTkFrame(panel, height=10, fg_color="transparent").pack()

    # =========================================================================
    # NOTIFICATION BADGE
    # =========================================================================

    def update_notification_count(self):
        try:
            unread = get_unread_count(self.user["id"], actor=self.user)
            btn = self._menu_buttons.get("Notifications")
            if btn is None:
                return
            if unread > 0:
                btn.configure(text=f"  🔔   Notifications ({unread})")
            else:
                btn.configure(text="  🔔   Notifications")
        except Exception as err:
            print("Notification count error:", err)

    # =========================================================================
    # SIDEBAR ACTIVE STATE
    # =========================================================================

    def _set_active_menu(self, name):
        """Highlight the active sidebar button."""
        colors = get_palette()
        for btn_name, btn in self._menu_buttons.items():
            if btn_name == name:
                btn.configure(
                    fg_color=colors["nav_active"],
                    text_color="#FFFFFF",
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color="#E2E8F0",
                )

    # =========================================================================
    # MENU ROUTING
    # =========================================================================

    def menu_clicked(self, name):
        try:
            require_menu_access(self.user, name)
        except AuthorizationError as error:
            messagebox.showwarning("Access denied", str(error), parent=self)
            return

        if name == "Dashboard":
            self._set_active_menu("Dashboard")
            self.go_home()
            return

        window_map = {
            "Students":         ("students_window",     StudentsWindow,          [self]),
            "Rooms":            ("rooms_window",         RoomsWindow,             [self]),
            "Fees":             ("fees_window",          FeeManagement,           [self]),
            "Complaints":       ("complaints_window",    ComplaintManagement,     [self]),
            "Attendance":       ("attendance_window",    AttendanceManagement,    [self]),
            "Feedback":         ("feedback_window",      FeedbackManagement,      [self]),
            "Quality Dashboard":("quality_window",       QualityDashboardWindow,  [self]),
            "Reports":          ("reports_window",       ReportsWindow,           [self]),
            "Notifications":    ("notifications_window", NotificationsWindow,     [self, self.user]),
            "Profile":          ("profile_window",       ProfileWindow,           [self, self.user]),
            "Settings":         ("settings_window",      SettingsWindow,          [self, self.user]),
        }

        if name not in window_map:
            return

        attr, cls, args = window_map[name]
        win = getattr(self, attr, None)

        if win is None or not win.winfo_exists():
            win = cls(*args)
            setattr(self, attr, win)
        else:
            win.lift()

        self._set_active_menu(name)
        self._raise_feature_window(win)

        if name == "Notifications":
            self.update_notification_count()

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
            window.after(80, lambda w=window: (w.lift(), w.focus_force()) if w.winfo_exists() else None)
        except Exception:
            pass

    # =========================================================================
    # KEYBOARD SHORTCUT HANDLERS
    # =========================================================================

    def go_home(self):
        """Ctrl+H — return to dashboard without recreating it."""
        active = self._active_feature_window
        self._active_feature_window = None
        if active is not None and active.winfo_exists():
            active.withdraw()
        self._set_active_menu("Dashboard")
        self.lift()
        self.focus_force()

    def refresh_active_page(self):
        """Ctrl+R — refresh whichever window has focus."""
        active = self._active_feature_window
        focused = self.focus_get()
        if focused is not None:
            top = focused.winfo_toplevel()
            active = None if top is self else top

        refreshers = {
            self.students_window:     "load_students",
            self.rooms_window:        "refresh_all",
            self.fees_window:         "load_fees",
            self.complaints_window:   "load_complaints",
            self.attendance_window:   "load_attendance",
            self.feedback_window:     "load_feedback",
            self.notifications_window:"load_notifications",
            self.reports_window:      "refresh_reports",
            self.settings_window:     "load_settings",
        }
        method_name = refreshers.get(active)
        if active is None:
            self.refresh_dashboard()
        elif method_name and active.winfo_exists():
            getattr(active, method_name)()
        elif active in (self.quality_window, self.profile_window) and active.winfo_exists():
            feature_name = (
                "Quality Dashboard" if active is self.quality_window else "Profile"
            )
            if active is self.quality_window:
                self.quality_window = None
            else:
                self.profile_window = None
            active.destroy()
            self.menu_clicked(feature_name)

    def refresh_dashboard(self):
        """Ctrl+R on dashboard — rebuild scroll content, keep sidebar."""
        if self.main_area is None:
            return
        if self.dashboard_figure is not None:
            plt.close(self.dashboard_figure)
            self.dashboard_figure = None
            self.dashboard_canvas = None
        if self.dashboard_scroll is not None and self.dashboard_scroll.winfo_exists():
            self.dashboard_scroll.destroy()
        self.dashboard_scroll = None
        self.create_dashboard()
        self.update_notification_count()

    # =========================================================================
    # THEMING
    # =========================================================================

    def apply_visual_theme(self):
        """Refresh every open window to match the active light/dark palette."""
        colors = get_palette()
        self.configure(fg_color=colors["page"])

        # ── sidebar ──────────────────────────────────────────────────────────
        self.sidebar.configure(fg_color=colors["nav"])
        for widget in self.sidebar.winfo_children():
            kind = widget.__class__.__name__
            if kind == "CTkScrollableFrame":
                widget.configure(
                    fg_color="transparent",
                    scrollbar_button_color=colors["nav_hover"],
                    scrollbar_button_hover_color=colors["muted"],
                )
            elif kind == "CTkFrame":
                widget.configure(fg_color="transparent")
            elif kind == "CTkLabel":
                text = str(widget.cget("text"))
                if text == "NAVIGATION":
                    widget.configure(text_color=colors["subtle"])

        # sidebar menu buttons
        for btn in self._menu_buttons.values():
            current_fg = btn.cget("fg_color")
            if current_fg == "transparent":
                btn.configure(
                    fg_color="transparent",
                    hover_color=colors["nav_hover"],
                    text_color="#E2E8F0",
                )

        # ── main area ────────────────────────────────────────────────────────
        if self.main_area is not None:
            self.main_area.configure(fg_color=colors["page"])
        if self.dashboard_scroll is not None and self.dashboard_scroll.winfo_exists():
            self.dashboard_scroll.configure(fg_color=colors["page"])
            apply_professional_style(self.dashboard_scroll)

        self.apply_dashboard_chart_theme()

        # ── open feature windows ─────────────────────────────────────────────
        for attr in (
            "students_window", "rooms_window", "fees_window", "complaints_window",
            "attendance_window", "feedback_window", "quality_window", "reports_window",
            "profile_window", "settings_window", "notifications_window",
        ):
            win = getattr(self, attr, None)
            if win is not None and win.winfo_exists():
                apply_professional_style(win)
                if hasattr(win, "refresh_theme_display"):
                    win.refresh_theme_display()
                if attr == "settings_window" and hasattr(win, "theme_menu"):
                    win.theme_menu.set(ThemeManager.get_current_theme().capitalize())

    def apply_dashboard_chart_theme(self):
        """Sync embedded Matplotlib charts with the active light/dark palette."""
        if self.dashboard_figure is None:
            return
        colors = get_palette()
        bg = colors["surface"]
        self.dashboard_figure.patch.set_facecolor(bg)
        for axis in self.dashboard_figure.axes:
            axis.set_facecolor(bg)
            axis.title.set_color(colors["text"])
            axis.tick_params(colors=colors["muted"])
            for spine in axis.spines.values():
                if spine.get_visible():
                    spine.set_color(colors["border"])
            for idx, patch in enumerate(axis.patches):
                patch.set_facecolor(colors["accent"] if idx % 2 == 0 else colors["border"])
            for txt in axis.texts:
                txt.set_color(colors["text"] if txt.get_text() not in ("No data yet", "No feedback yet") else colors["muted"])
            axis.yaxis.grid(True, color=colors["border"], alpha=0.55, linewidth=0.7)
        if self.dashboard_canvas is not None:
            self.dashboard_canvas.draw_idle()

    def toggle_theme(self):
        """Ctrl+D — toggle light / dark."""
        current = ctk.get_appearance_mode()
        new_theme = ThemeManager.DARK_MODE if current == "Light" else ThemeManager.LIGHT_MODE
        ThemeManager.set_theme(new_theme)
        self.apply_visual_theme()
        try:
            ThemeManager.save_user_theme(self.user["id"], new_theme)
        except Exception:
            messagebox.showerror(
                "Theme",
                "Theme changed for this session but could not be saved.",
                parent=self,
            )

    # =========================================================================
    # EXIT / LOGOUT
    # =========================================================================

    def exit_application(self):
        """Ctrl+Q — exit after confirmation."""
        if messagebox.askyesno("Exit", "Are you sure you want to exit?", parent=self):
            revoke_session(self.user.get("session_token"))
            self.destroy()

    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?", parent=self):
            self.destroy()


# =============================================================================
# DIRECT TEST
# =============================================================================

if __name__ == "__main__":
    test_user = {
        "id": 1,
        "username": "admin",
        "email": "admin@hostel.com",
        "role": "admin",
    }
    app = DashboardWindow(test_user)
    app.mainloop()
