"""Modern SaaS Dashboard built with Flet."""

import flet as ft
from datetime import datetime
from analytics.dashboard_analytics import get_dashboard_statistics
from services.notification_service import get_unread_count
from utils.role_access import get_menu_for_role
from flet_views.theme import get_colors

MENU_ICONS = {
    "Dashboard": ft.Icons.DASHBOARD_ROUNDED,
    "Students": ft.Icons.PEOPLE_ALT_ROUNDED,
    "Rooms": ft.Icons.MEETING_ROOM_ROUNDED,
    "Fees": ft.Icons.PAYMENTS_ROUNDED,
    "Complaints": ft.Icons.CHAT_BUBBLE_OUTLINE_ROUNDED,
    "Attendance": ft.Icons.CHECKLIST_ROUNDED,
    "Feedback": ft.Icons.STAR_BORDER_ROUNDED,
    "Quality Dashboard": ft.Icons.ANALYTICS_ROUNDED,
    "Reports": ft.Icons.SUMMARIZE_ROUNDED,
    "Profile": ft.Icons.ACCOUNT_CIRCLE_ROUNDED,
    "Settings": ft.Icons.SETTINGS_ROUNDED,
    "Notifications": ft.Icons.NOTIFICATIONS_ROUNDED,
}


class DashboardView(ft.Row):
    def __init__(self, page: ft.Page, user: dict, on_logout):
        super().__init__()
        self.app_page = page
        self.user = user
        self.on_logout = on_logout
        self.expand = True
        self.spacing = 0

        self.current_menu = "Dashboard"
        self.sidebar_buttons = {}

        # Content container where active view renders
        self.content_area = ft.Container(
            expand=True,
            padding=ft.Padding.only(left=28, right=28, top=20, bottom=24),
        )

        self.sidebar = self._build_sidebar()
        self.controls = [self.sidebar, self.content_area]

        self.load_view("Dashboard")

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self) -> ft.Container:
        is_dark = self.app_page.theme_mode == ft.ThemeMode.DARK
        colors = get_colors(is_dark)

        # Brand Logo Pill
        logo = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text("H", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        width=38,
                        height=38,
                        border_radius=10,
                        bgcolor=ft.Colors.INDIGO_600,
                        alignment=ft.Alignment.CENTER,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text("Hostel", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            ft.Text("Management", size=10, color=colors["sidebar_sub"]),
                        ],
                        spacing=0,
                    ),
                ],
                spacing=12,
            ),
            padding=ft.Padding.symmetric(horizontal=16, vertical=18),
        )

        # Navigation items
        menu_items = get_menu_for_role(self.user["role"])
        nav_buttons = []
        for name in menu_items:
            icon = MENU_ICONS.get(name, ft.Icons.CIRCLE)
            is_active = (name == self.current_menu)

            item_controls = [
                ft.Icon(
                    icon,
                    size=18,
                    color=ft.Colors.WHITE if is_active else colors["sidebar_sub"],
                ),
                ft.Text(
                    name,
                    size=13,
                    weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL,
                    color=ft.Colors.WHITE if is_active else colors["sidebar_sub"],
                    expand=True,
                ),
            ]

            if name == "Notifications":
                try:
                    unread = get_unread_count(self.user["id"], actor=self.user)
                except Exception:
                    unread = 0
                if unread > 0:
                    badge_dot = ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Container(
                                    width=7,
                                    height=7,
                                    border_radius=4,
                                    bgcolor=ft.Colors.WHITE,
                                ),
                                ft.Text(
                                    str(unread) if unread < 100 else "99+",
                                    size=10,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                ),
                            ],
                            spacing=3,
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        bgcolor=ft.Colors.RED_500,
                        border_radius=10,
                        padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                        alignment=ft.Alignment.CENTER,
                    )
                    item_controls.append(badge_dot)

            btn = ft.Container(
                content=ft.Row(
                    controls=item_controls,
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding.symmetric(horizontal=14, vertical=10),
                border_radius=10,
                bgcolor=colors["sidebar_active"] if is_active else ft.Colors.TRANSPARENT,
                ink=True,
                on_click=lambda e, n=name: self._menu_item_clicked(n),
            )
            self.sidebar_buttons[name] = btn
            nav_buttons.append(btn)

        nav_col = ft.Column(
            controls=nav_buttons,
            spacing=3,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        # User Profile badge at bottom (links to Settings)
        initials = (self.user.get("full_name") or self.user.get("username") or "?")[:2].upper()
        display_name = self.user.get("full_name") or self.user["username"]
        self.user_badge = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(initials, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        width=32,
                        height=32,
                        border_radius=16,
                        bgcolor=ft.Colors.INDIGO_500,
                        alignment=ft.Alignment.CENTER,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(display_name, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, no_wrap=True),
                            ft.Text(self.user["role"].title(), size=10, color=colors["sidebar_sub"]),
                        ],
                        spacing=0,
                        expand=True,
                    ),
                ],
                spacing=10,
            ),
            padding=ft.Padding.all(10),
            border_radius=10,
            bgcolor=colors["sidebar_active"],
            ink=True,
            tooltip="View Settings & Profile",
            on_click=lambda _: self.load_view("Settings"),
        )
        user_badge = self.user_badge

        sidebar_container = ft.Container(
            content=ft.Column(
                controls=[
                    logo,
                    ft.Divider(height=1, color=colors["border"]),
                    ft.Container(height=6),
                    nav_col,
                    ft.Divider(height=1, color=colors["border"]),
                    user_badge,
                ],
                spacing=8,
            ),
            width=240,
            bgcolor=colors["sidebar"],
            padding=ft.Padding.only(left=12, right=12, top=4, bottom=16),
        )

        return sidebar_container

    def _menu_item_clicked(self, name: str):
        self.load_view(name)

    def _update_sidebar_active_state(self):
        is_dark = self.app_page.theme_mode == ft.ThemeMode.DARK
        colors = get_colors(is_dark)

        for name, btn in self.sidebar_buttons.items():
            is_active = (name == self.current_menu)
            row = btn.content
            row.controls[0].color = ft.Colors.WHITE if is_active else colors["sidebar_sub"]
            row.controls[1].color = ft.Colors.WHITE if is_active else colors["sidebar_sub"]
            row.controls[1].weight = ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL
            btn.bgcolor = colors["sidebar_active"] if is_active else ft.Colors.TRANSPARENT
        self.app_page.update()

    # ── View Routing ──────────────────────────────────────────────────────────
    def load_view(self, view_name: str):
        self.current_menu = view_name
        self._update_sidebar_active_state()
        self.update_sidebar_badges()

        if view_name == "Dashboard":
            if self.user.get("role") == "student":
                from flet_views.student_dashboard_view import StudentDashboardSubView
                self.content_area.content = StudentDashboardSubView(self.app_page, self.user, on_navigate=self.load_view, toggle_theme_fn=self.toggle_theme)
            else:
                self.content_area.content = self._build_dashboard_content()
        elif view_name == "Students":
            from flet_views.students_view import StudentsSubView
            self.content_area.content = StudentsSubView(self.app_page, self.user)
        elif view_name == "Rooms":
            from flet_views.rooms_view import RoomsSubView
            self.content_area.content = RoomsSubView(self.app_page, self.user)
        elif view_name == "Fees":
            from flet_views.fees_view import FeesSubView
            self.content_area.content = FeesSubView(self.app_page, self.user)
        elif view_name == "Complaints":
            from flet_views.complaints_view import ComplaintsSubView
            self.content_area.content = ComplaintsSubView(self.app_page, self.user)
        elif view_name == "Attendance":
            from flet_views.attendance_view import AttendanceSubView
            self.content_area.content = AttendanceSubView(self.app_page, self.user)
        elif view_name == "Feedback":
            from flet_views.feedback_view import FeedbackSubView
            self.content_area.content = FeedbackSubView(self.app_page, self.user)
        elif view_name == "Reports":
            from flet_views.reports_view import ReportsSubView
            self.content_area.content = ReportsSubView(self.app_page, self.user)
        elif view_name == "Notifications":
            from flet_views.notifications_view import NotificationsSubView
            self.content_area.content = NotificationsSubView(self.app_page, self.user)
        elif view_name == "Quality Dashboard":
            from flet_views.quality_dashboard_view import QualityDashboardSubView
            self.content_area.content = QualityDashboardSubView(self.app_page, self.user)
        elif view_name in ("Profile", "Settings"):
            from flet_views.settings_view import SettingsSubView
            self.content_area.content = SettingsSubView(self.app_page, self.user, self.toggle_theme, on_logout=self.on_logout)
        else:
            self.content_area.content = ft.Text(f"{view_name} page under active development.")

        self.app_page.update()

    def update_sidebar_badges(self):
        btn = self.sidebar_buttons.get("Notifications")
        if not btn:
            return
        is_dark = self.app_page.theme_mode == ft.ThemeMode.DARK
        colors = get_colors(is_dark)
        is_active = (self.current_menu == "Notifications")
        try:
            unread = get_unread_count(self.user["id"], actor=self.user)
        except Exception:
            unread = 0

        item_controls = [
            ft.Icon(
                MENU_ICONS.get("Notifications", ft.Icons.NOTIFICATIONS_ROUNDED),
                size=18,
                color=ft.Colors.WHITE if is_active else colors["sidebar_sub"],
            ),
            ft.Text(
                "Notifications",
                size=13,
                weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL,
                color=ft.Colors.WHITE if is_active else colors["sidebar_sub"],
                expand=True,
            ),
        ]
        if unread > 0:
            item_controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                width=7,
                                height=7,
                                border_radius=4,
                                bgcolor=ft.Colors.WHITE,
                            ),
                            ft.Text(
                                str(unread) if unread < 100 else "99+",
                                size=10,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.WHITE,
                            ),
                        ],
                        spacing=3,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    bgcolor=ft.Colors.RED_500,
                    border_radius=10,
                    padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                    alignment=ft.Alignment.CENTER,
                )
            )

        btn.content = ft.Row(
            controls=item_controls,
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.app_page.update()

    def update_user_badge(self):
        if not hasattr(self, "user_badge") or not self.user_badge:
            return
        is_dark = self.app_page.theme_mode == ft.ThemeMode.DARK
        colors = get_colors(is_dark)
        display_name = self.user.get("full_name") or self.user.get("username", "")
        words = [w for w in display_name.split() if w]
        if len(words) >= 2:
            initials = (words[0][0] + words[1][0]).upper()
        elif len(words) == 1:
            initials = words[0][:2].upper()
        else:
            initials = (self.user.get("username") or "?")[:2].upper()

        self.user_badge.content = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text(initials, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    width=32,
                    height=32,
                    border_radius=16,
                    bgcolor=ft.Colors.INDIGO_500,
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Column(
                    controls=[
                        ft.Text(display_name, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, no_wrap=True),
                        ft.Text(self.user["role"].title(), size=10, color=colors["sidebar_sub"]),
                    ],
                    spacing=0,
                    expand=True,
                ),
            ],
            spacing=10,
        )
        self.app_page.update()

        # ── Top Header ────────────────────────────────────────────────────────────
    def _build_header(self, colors: dict) -> ft.Container:
        hour = datetime.now().hour
        greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"

        is_dark = self.app_page.theme_mode == ft.ThemeMode.DARK
        theme_icon = ft.Icons.LIGHT_MODE_ROUNDED if is_dark else ft.Icons.DARK_MODE_ROUNDED
        theme_label = "Light Mode" if is_dark else "Dark Mode"

        unread = get_unread_count(self.user["id"], actor=self.user)

        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text(f"{greeting}, {self.user['username']} 👋", size=22, weight=ft.FontWeight.BOLD),
                            ft.Text("Overview and operational statistics for your hostel", size=12, color=colors["text_muted"]),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Container(
                        content=ft.Text(
                            self.user["role"].upper(),
                            size=10,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.INDIGO_600 if not is_dark else ft.Colors.INDIGO_400,
                        ),
                        padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                        border_radius=20,
                        bgcolor=colors["accent_soft"],
                        border=ft.Border.all(1, colors["accent"]),
                    ),
                    ft.OutlinedButton(
                        content=ft.Row(
                            controls=[
                                ft.Icon(theme_icon, size=15),
                                ft.Text(theme_label, size=12),
                            ],
                            spacing=6,
                        ),
                        on_click=lambda _: self.toggle_theme(),
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    ),
                    ft.OutlinedButton(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.REFRESH_ROUNDED, size=15),
                                ft.Text("Refresh", size=12),
                            ],
                            spacing=6,
                        ),
                        on_click=lambda _: self.load_view(self.current_menu),
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(vertical=10),
        )
        return header

    # ── Dashboard Content ─────────────────────────────────────────────────────
    def _build_dashboard_content(self) -> ft.Control:
        is_dark = self.app_page.theme_mode == ft.ThemeMode.DARK
        colors = get_colors(is_dark)

        stats = get_dashboard_statistics(actor=self.user)

        header = self._build_header(colors)
        stat_cards = self._build_stat_cards(stats, colors)
        operations = self._build_operations_meters(stats, colors)
        activity = self._build_recent_activity(stats, colors)

        scrollable_content = ft.Column(
            controls=[
                header,
                ft.Container(height=12),
                stat_cards,
                ft.Container(height=18),
                operations,
                ft.Container(height=18),
                activity,
                ft.Container(height=30),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=0,
        )
        return scrollable_content

    # ── Stat Cards ────────────────────────────────────────────────────────────
    def _build_stat_cards(self, stats: dict, colors: dict) -> ft.Control:
        if self.user["role"] == "admin":
            sat = f"{stats['average_satisfaction']:.1f}/5" if stats["average_satisfaction"] is not None else "—"
            items = [
                ("Total Students", str(stats["total_students"]), ft.Icons.PEOPLE_ALT_ROUNDED, ft.Colors.INDIGO_500),
                ("Total Rooms", str(stats["total_rooms"]), ft.Icons.MEETING_ROOM_ROUNDED, ft.Colors.PURPLE_500),
                ("Available Beds", str(stats["available_beds"]), ft.Icons.HOTEL_ROUNDED, ft.Colors.GREEN_500),
                ("Occupancy Rate", f"{stats['occupancy_rate']:.0f}%", ft.Icons.DONUT_LARGE_ROUNDED, ft.Colors.BLUE_500),
                ("Fees Collected", f"₹{stats['collected_fees']:,.0f}", ft.Icons.ACCOUNT_BALANCE_WALLET_ROUNDED, ft.Colors.GREEN_600),
                ("Fees Pending", f"₹{stats['pending_fees']:,.0f}", ft.Icons.PENDING_ACTIONS_ROUNDED, ft.Colors.RED_500),
                ("Open Complaints", str(stats["pending_complaints"]), ft.Icons.REPORT_PROBLEM_ROUNDED, ft.Colors.AMBER_500),
                ("User Satisfaction", sat, ft.Icons.STAR_ROUNDED, ft.Colors.INDIGO_500),
            ]
        else:
            room = stats["student_room_number"] or "Not assigned"
            bed = str(stats["student_bed_number"]) if stats["student_bed_number"] is not None else "—"
            items = [
                ("Assigned Room", f"Room {room}", ft.Icons.MEETING_ROOM_ROUNDED, ft.Colors.INDIGO_500),
                ("Assigned Bed", f"Bed #{bed}", ft.Icons.HOTEL_ROUNDED, ft.Colors.PURPLE_500),
                ("Fees Paid", f"₹{stats['collected_fees']:,.0f}", ft.Icons.ACCOUNT_BALANCE_WALLET_ROUNDED, ft.Colors.GREEN_500),
                ("Fees Outstanding", f"₹{stats['pending_fees']:,.0f}", ft.Icons.PENDING_ACTIONS_ROUNDED, ft.Colors.RED_500),
                ("Your Complaints", str(stats["total_complaints"]), ft.Icons.CHAT_BUBBLE_ROUNDED, ft.Colors.AMBER_500),
                ("Open Complaints", str(stats["pending_complaints"]), ft.Icons.REPORT_PROBLEM_ROUNDED, ft.Colors.RED_500),
            ]

        # Render responsive grid of cards
        row1_cards = []
        row2_cards = []
        for idx, (title, value, icon, accent) in enumerate(items):
            card = self._create_card(title, value, icon, accent, colors)
            if idx < 4:
                row1_cards.append(card)
            else:
                row2_cards.append(card)

        controls = [ft.Row(controls=row1_cards, spacing=14)]
        if row2_cards:
            controls.append(ft.Container(height=14))
            controls.append(ft.Row(controls=row2_cards, spacing=14))

        return ft.Column(controls=controls, spacing=0)

    def _create_card(self, title: str, value: str, icon: str, accent: str, colors: dict) -> ft.Control:
        card = ft.Container(
            content=ft.Row(
                controls=[
                    # Left accent bar
                    ft.Container(width=4, height=44, border_radius=2, bgcolor=accent),
                    ft.Column(
                        controls=[
                            ft.Text(title.upper(), size=10, weight=ft.FontWeight.BOLD, color=colors["text_muted"]),
                            ft.Text(value, size=24, weight=ft.FontWeight.BOLD, color=colors["text"]),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Container(
                        content=ft.Icon(icon, size=22, color=accent),
                        width=40,
                        height=40,
                        border_radius=10,
                        bgcolor=ft.Colors.with_opacity(0.12, accent),
                        alignment=ft.Alignment.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
            expand=True,
            padding=ft.Padding.symmetric(horizontal=16, vertical=16),
            border_radius=14,
            bgcolor=colors["surface"],
            border=ft.Border.all(1, colors["border"]),
        )
        return card

    # ── Operations Visual Meters ──────────────────────────────────────────────
    def _build_operations_meters(self, stats: dict, colors: dict) -> ft.Control:
        if self.user["role"] != "admin":
            return ft.Container()

        # Occupancy meter
        total_beds = stats["total_beds"] or 1
        occ_ratio = min(1.0, max(0.0, (stats["occupied_beds"] or 0) / total_beds))

        # Fee collection meter
        total_fee = stats["total_fees_amount"] or 1
        fee_ratio = min(1.0, max(0.0, (stats["collected_fees"] or 0) / total_fee))

        # Complaint resolution meter
        total_comp = stats["total_complaints"] or 1
        comp_ratio = min(1.0, max(0.0, (stats["resolved_complaints"] or 0) / total_comp))

        card1 = self._meter_card(
            title="Bed Occupancy",
            subtitle=f"{stats['occupied_beds']} occupied of {stats['total_beds']} beds",
            ratio=occ_ratio,
            color=ft.Colors.INDIGO_500,
            colors=colors,
        )
        card2 = self._meter_card(
            title="Fee Collection Rate",
            subtitle=f"₹{stats['collected_fees']:,.0f} of ₹{stats['total_fees_amount']:,.0f}",
            ratio=fee_ratio,
            color=ft.Colors.GREEN_500,
            colors=colors,
        )
        card3 = self._meter_card(
            title="Complaint Resolution",
            subtitle=f"{stats['resolved_complaints']} resolved of {stats['total_complaints']} complaints",
            ratio=comp_ratio,
            color=ft.Colors.AMBER_500,
            colors=colors,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Operations Health", size=16, weight=ft.FontWeight.BOLD),
                    ft.Container(height=8),
                    ft.Row(controls=[card1, card2, card3], spacing=14),
                ],
            ),
        )

    def _meter_card(self, title: str, subtitle: str, ratio: float, color: str, colors: dict) -> ft.Control:
        percentage = int(ratio * 100)
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(title, size=13, weight=ft.FontWeight.BOLD),
                            ft.Text(f"{percentage}%", size=13, weight=ft.FontWeight.BOLD, color=color),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(height=4),
                    ft.ProgressBar(value=ratio, color=color, bgcolor=colors["border"], height=8, border_radius=4),
                    ft.Container(height=4),
                    ft.Text(subtitle, size=11, color=colors["text_muted"]),
                ],
                spacing=2,
            ),
            expand=True,
            padding=ft.Padding.all(16),
            border_radius=14,
            bgcolor=colors["surface"],
            border=ft.Border.all(1, colors["border"]),
        )

    # ── Recent Activity ───────────────────────────────────────────────────────
    def _build_recent_activity(self, stats: dict, colors: dict) -> ft.Control:
        cols = []

        # Complaints list
        comp_items = []
        for r in stats.get("recent_complaints", [])[:5]:
            comp_items.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.REPORT_ROUNDED, size=18, color=ft.Colors.AMBER_500),
                            ft.Column(
                                controls=[
                                    ft.Text(f"{r[1]} · {r[3]}", size=12, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"{r[4]} · {r[6] or 'Pending'}", size=10, color=colors["text_muted"]),
                                ],
                                spacing=1,
                                expand=True,
                            ),
                        ],
                        spacing=10,
                    ),
                    padding=ft.Padding.symmetric(vertical=6, horizontal=8),
                    border_radius=8,
                    bgcolor=colors["surface_alt"],
                )
            )
        cols.append(self._activity_box("Recent Complaints", comp_items or [ft.Text("No complaints logged", size=11, color=colors["text_muted"])], colors))

        # Payments list
        pay_items = []
        for r in stats.get("recent_payments", [])[:5]:
            pay_items.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.PAYMENTS_ROUNDED, size=18, color=ft.Colors.GREEN_500),
                            ft.Column(
                                controls=[
                                    ft.Text(f"{r[1]} · ₹{float(r[4]):,.2f}", size=12, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"{r[5] or 'Payment'} · {r[6] or '—'}", size=10, color=colors["text_muted"]),
                                ],
                                spacing=1,
                                expand=True,
                            ),
                        ],
                        spacing=10,
                    ),
                    padding=ft.Padding.symmetric(vertical=6, horizontal=8),
                    border_radius=8,
                    bgcolor=colors["surface_alt"],
                )
            )
        cols.append(self._activity_box("Recent Payments", pay_items or [ft.Text("No payments recorded", size=11, color=colors["text_muted"])], colors))

        if self.user["role"] == "admin":
            stu_items = []
            for r in stats.get("recent_students", [])[:5]:
                stu_items.append(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.PERSON_ADD_ROUNDED, size=18, color=ft.Colors.INDIGO_500),
                                ft.Column(
                                    controls=[
                                        ft.Text(f"{r[1]} · {r[0]}", size=12, weight=ft.FontWeight.BOLD),
                                        ft.Text(f"Registered {r[2] or '—'}", size=10, color=colors["text_muted"]),
                                    ],
                                    spacing=1,
                                    expand=True,
                                ),
                            ],
                            spacing=10,
                        ),
                        padding=ft.Padding.symmetric(vertical=6, horizontal=8),
                        border_radius=8,
                        bgcolor=colors["surface_alt"],
                    )
                )
            cols.append(self._activity_box("Recent Registrations", stu_items or [ft.Text("No new registrations", size=11, color=colors["text_muted"])], colors))

        return ft.Row(controls=cols, spacing=14)

    def _activity_box(self, title: str, items: list, colors: dict) -> ft.Control:
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(title, size=14, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=1, color=colors["border"]),
                    ft.Column(controls=items, spacing=6),
                ],
                spacing=8,
            ),
            expand=True,
            padding=ft.Padding.all(16),
            border_radius=14,
            bgcolor=colors["surface"],
            border=ft.Border.all(1, colors["border"]),
        )

    # ── Theme Toggle ──────────────────────────────────────────────────────────
    def toggle_theme(self):
        new_mode = ft.ThemeMode.LIGHT if self.app_page.theme_mode == ft.ThemeMode.DARK else ft.ThemeMode.DARK
        self.app_page.theme_mode = new_mode
        colors = get_colors(new_mode == ft.ThemeMode.DARK)
        self.app_page.bgcolor = colors["page"]

        # Rebuild sidebar & active view
        self.sidebar = self._build_sidebar()
        self.controls[0] = self.sidebar
        self.load_view(self.current_menu)
        self.app_page.update()
