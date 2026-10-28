"""Modern SaaS Login View built with Flet for unified portal access."""

import flet as ft
from services.auth_service import login_user
from flet_views.theme import build_theme, get_colors


class LoginView(ft.Container):
    def __init__(self, page: ft.Page, on_login_success):
        super().__init__()
        self.app_page = page
        self.on_login_success = on_login_success
        self.expand = True
        self.alignment = ft.Alignment.CENTER

        self.remember_me = True

        # Unified Username Input
        self.username_input = ft.TextField(
            label="Username",
            hint_text="Username",
            prefix_icon=ft.Icons.PERSON_OUTLINE_ROUNDED,
            border_radius=12,
            filled=True,
            autofocus=True,
            text_size=13,
            on_submit=self._handle_submit,
        )

        # Password Input
        self.password_input = ft.TextField(
            label="Password",
            hint_text="••••••••",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK_ROUNDED,
            border_radius=12,
            filled=True,
            text_size=13,
            on_submit=self._handle_submit,
        )

        # Error banner text & container
        self.error_text = ft.Text(
            value="",
            color=ft.Colors.RED_600,
            size=12,
            weight=ft.FontWeight.W_500,
            expand=True,
        )

        self.error_banner = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, color=ft.Colors.RED_500, size=18),
                    self.error_text,
                    ft.IconButton(
                        icon=ft.Icons.CLOSE_ROUNDED,
                        icon_size=16,
                        icon_color=ft.Colors.RED_500,
                        tooltip="Dismiss",
                        on_click=lambda _: self._clear_error(),
                    ),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            border_radius=10,
            visible=False,
        )

        # Loading indicator
        self.loading_indicator = ft.ProgressRing(
            width=18,
            height=18,
            stroke_width=2.5,
            color=ft.Colors.WHITE,
            visible=False,
        )

        # Login button contents
        self.login_btn_icon = ft.Icon(
            ft.Icons.LOGIN_ROUNDED,
            size=18,
            color=ft.Colors.WHITE,
        )
        self.login_btn_text = ft.Text(
            "Sign In to Dashboard",
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE,
            size=13,
        )

        self.login_btn = ft.FilledButton(
            content=ft.Row(
                controls=[
                    self.login_btn_icon,
                    self.loading_indicator,
                    self.login_btn_text,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=12),
                bgcolor=ft.Colors.INDIGO_600,
                padding=ft.Padding.symmetric(vertical=14),
            ),
            height=46,
            on_click=self._do_login,
        )

        # Initial UI render
        self._build_ui()

    def _build_ui(self):
        is_dark = self.app_page.theme_mode == ft.ThemeMode.DARK
        colors = get_colors(is_dark)

        # Update input theme colors
        self.username_input.bgcolor = colors["surface_alt"]
        self.password_input.bgcolor = colors["surface_alt"]

        self.error_banner.bgcolor = colors["danger_soft"]
        self.error_banner.border = ft.Border.all(1, colors["danger"])
        self.error_text.color = colors["danger"]

        left_hero = self._build_left_hero(colors)
        right_form = self._build_right_form(colors, is_dark)

        # Bounded Split Card centered in LoginView
        card = ft.Container(
            content=ft.Row(
                controls=[left_hero, right_form],
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            width=880,
            height=530,
            border_radius=20,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            bgcolor=colors["surface"],
            border=ft.Border.all(1, colors["border"]),
            shadow=ft.BoxShadow(
                blur_radius=28,
                spread_radius=1,
                color=ft.Colors.with_opacity(0.12 if not is_dark else 0.45, ft.Colors.BLACK),
                offset=ft.Offset(0, 12),
            ),
        )

        self.content = card

    def _build_left_hero(self, colors: dict) -> ft.Container:
        def _make_feature_row(icon, title: str, subtitle: str, icon_color: str):
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Icon(icon, size=18, color=icon_color),
                            width=36,
                            height=36,
                            border_radius=10,
                            bgcolor=ft.Colors.with_opacity(0.15, icon_color),
                            alignment=ft.Alignment.CENTER,
                        ),
                        ft.Column(
                            controls=[
                                ft.Text(title, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                ft.Text(subtitle, size=11, color="#94A3B8"),
                            ],
                            spacing=1,
                            expand=True,
                        ),
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                border_radius=12,
                bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
                border=ft.Border.all(1, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)),
            )

        # Top Brand Row
        brand_row = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Icon(ft.Icons.HOLIDAY_VILLAGE_ROUNDED, size=20, color=ft.Colors.WHITE),
                    width=38,
                    height=38,
                    border_radius=10,
                    bgcolor=ft.Colors.INDIGO_600,
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Column(
                    controls=[
                        ft.Text("HOSTEL HUB", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.Text("Enterprise Suite", size=10, color="#94A3B8"),
                    ],
                    spacing=0,
                ),
                ft.Container(expand=True),
                # Live status indicator
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(width=7, height=7, border_radius=4, bgcolor="#10B981"),
                            ft.Text("Active v2.4", size=10, weight=ft.FontWeight.BOLD, color="#34D399"),
                        ],
                        spacing=5,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                    border_radius=12,
                    bgcolor=ft.Colors.with_opacity(0.15, "#064E3B"),
                    border=ft.Border.all(1, ft.Colors.with_opacity(0.35, "#10B981")),
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        hero_text = ft.Column(
            controls=[
                ft.Text(
                    "Smart Campus Living,\nSimplified.",
                    size=22,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                ),
                ft.Text(
                    "A centralized digital platform for student room allocations, automated fee clearances, and real-time grievance tracking.",
                    size=12,
                    color="#94A3B8",
                ),
            ],
            spacing=8,
        )

        features = ft.Column(
            controls=[
                _make_feature_row(
                    ft.Icons.MEETING_ROOM_ROUNDED,
                    "Smart Room Allocations",
                    "Live occupancy tracking & room inventory",
                    "#818CF8",
                ),
                _make_feature_row(
                    ft.Icons.PAYMENTS_ROUNDED,
                    "Automated Dues & Receipts",
                    "Track balances, dues alerts & digital receipts",
                    "#10B981",
                ),
                _make_feature_row(
                    ft.Icons.SUPPORT_AGENT_ROUNDED,
                    "24/7 Grievance Desk",
                    "Direct complaint ticketing with live updates",
                    "#F59E0B",
                ),
            ],
            spacing=10,
        )

        footer = ft.Row(
            controls=[
                ft.Icon(ft.Icons.LOCK_OUTLINE_ROUNDED, size=13, color="#64748B"),
                ft.Text("256-Bit Encrypted • Role-Based Access Control", size=10, color="#64748B"),
            ],
            spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    brand_row,
                    ft.Container(height=4),
                    hero_text,
                    features,
                    ft.Container(height=4),
                    footer,
                ],
                spacing=16,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            width=380,
            padding=28,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=["#0A0F1D", "#1E1B4B", "#0F172A"],
            ),
        )

    def _build_right_form(self, colors: dict, is_dark: bool) -> ft.Container:
        # Theme toggle button
        theme_btn = ft.IconButton(
            icon=ft.Icons.DARK_MODE_OUTLINED if not is_dark else ft.Icons.LIGHT_MODE_ROUNDED,
            icon_size=18,
            icon_color=colors["text_muted"],
            tooltip="Switch Dark / Light theme",
            on_click=self._toggle_theme,
        )

        # Top Bar
        top_bar = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.SECURITY_ROUNDED, size=13, color=colors["accent"]),
                            ft.Text("SECURE GATEWAY", size=10, weight=ft.FontWeight.BOLD, color=colors["accent"]),
                        ],
                        spacing=4,
                    ),
                    padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                    border_radius=8,
                    bgcolor=colors["accent_soft"],
                ),
                ft.Container(expand=True),
                theme_btn,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Welcome heading
        heading = ft.Column(
            controls=[
                ft.Text("Welcome Back", size=24, weight=ft.FontWeight.BOLD, color=colors["text"]),
                ft.Text(
                    "Sign in to your account to access your workspace",
                    size=12,
                    color=colors["text_muted"],
                ),
            ],
            spacing=3,
        )

        # Options Row (Remember me & Need Help)
        options_row = ft.Row(
            controls=[
                ft.Checkbox(
                    label="Remember me",
                    value=self.remember_me,
                    on_change=lambda e: setattr(self, "remember_me", e.control.value),
                    fill_color=colors["accent"],
                ),
                ft.Container(expand=True),
                ft.TextButton(
                    "Need Help?",
                    on_click=self._show_help_dialog,
                    style=ft.ButtonStyle(color=colors["accent"]),
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Security footer caption
        security_note = ft.Text(
            "Authorized personnel only. All access attempts are monitored.",
            size=10,
            color=colors["text_muted"],
            text_align=ft.TextAlign.CENTER,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    top_bar,
                    ft.Container(height=6),
                    heading,
                    ft.Container(height=8),
                    self.username_input,
                    self.password_input,
                    self.error_banner,
                    options_row,
                    ft.Container(height=4),
                    self.login_btn,
                    ft.Container(height=4),
                    security_note,
                ],
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            width=500,
            padding=ft.Padding.symmetric(horizontal=38, vertical=28),
            bgcolor=colors["surface"],
        )

    def _toggle_theme(self, _):
        is_dark = self.app_page.theme_mode == ft.ThemeMode.DARK
        new_dark = not is_dark
        self.app_page.theme_mode = ft.ThemeMode.DARK if new_dark else ft.ThemeMode.LIGHT
        self.app_page.theme = build_theme(is_dark=new_dark)
        self.app_page.bgcolor = get_colors(is_dark=new_dark)["page"]
        self._build_ui()
        self.app_page.update()

    def _show_help_dialog(self, _):
        is_dark = self.app_page.theme_mode == ft.ThemeMode.DARK
        colors = get_colors(is_dark)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.HELP_OUTLINE_ROUNDED, color=colors["accent"], size=22),
                    ft.Text("Portal Access Guidelines", weight=ft.FontWeight.BOLD, size=16),
                ],
                spacing=10,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "Sign-in Information & Support",
                            weight=ft.FontWeight.BOLD,
                            size=13,
                            color=colors["text"],
                        ),
                        ft.Text(
                            "Please enter the unique username and password assigned to your portal account.",
                            size=12,
                            color=colors["text_muted"],
                        ),
                        ft.Divider(height=16, color=colors["border"]),
                        ft.Text(
                            "Forgot Password or Locked Out?",
                            weight=ft.FontWeight.BOLD,
                            size=13,
                            color=colors["text"],
                        ),
                        ft.Text(
                            "For security, password resets must be requested directly through the hostel administration office or warden.",
                            size=12,
                            color=colors["text_muted"],
                        ),
                    ],
                    spacing=10,
                    tight=True,
                ),
                width=420,
            ),
            actions=[
                ft.FilledButton(
                    "Understood",
                    style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_600),
                    on_click=lambda _: self._close_dialog(dlg),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.app_page.show_dialog(dlg)

    def _close_dialog(self, dlg):
        dlg.open = False
        self.app_page.update()

    def _handle_submit(self, _):
        self._do_login(None)

    def _clear_error(self):
        self.error_text.value = ""
        self.error_banner.visible = False
        self.app_page.update()

    def _set_error(self, message: str):
        self.error_text.value = message
        self.error_banner.visible = True
        self.app_page.update()

    def _do_login(self, _):
        username = (self.username_input.value or "").strip()
        password = self.password_input.value or ""

        if not username:
            self._set_error("Please enter your username.")
            return
        if not password:
            self._set_error("Please enter your password.")
            return

        self.error_banner.visible = False
        self.login_btn.disabled = True
        self.loading_indicator.visible = True
        self.login_btn_icon.visible = False
        self.app_page.update()

        success, result = login_user(username, password)

        if not success:
            self._set_error(str(result) if result else "Invalid credentials.")
            self.login_btn.disabled = False
            self.loading_indicator.visible = False
            self.login_btn_icon.visible = True
            self.app_page.update()
            return

        # Login succeeded
        self.login_btn.disabled = False
        self.loading_indicator.visible = False
        self.login_btn_icon.visible = True
        self.on_login_success(result)
