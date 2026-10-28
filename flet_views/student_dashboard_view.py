"""Modern SaaS Student Dashboard View for Hostel Management System."""

import flet as ft
from datetime import datetime
from services.student_service import get_student_dashboard_data, update_student_contact
from services.complaint_service import add_complaint
from services.attendance_service import mark_entry, mark_exit
from utils.validators import validate_real_mobile_phone, validate_real_gmail
from flet_views.theme import get_colors, attach_date_picker


class StudentDashboardSubView(ft.Column):
    def __init__(self, page: ft.Page, user: dict, on_navigate=None, toggle_theme_fn=None):
        super().__init__()
        self.app_page = page
        self.user = user
        self.on_navigate = on_navigate
        self.toggle_theme_fn = toggle_theme_fn
        self.expand = True
        self.spacing = 16
        self.scroll = ft.ScrollMode.AUTO

        self.data = {}
        self.selected_tab_idx = 0
        self.tab_buttons = []
        self.tab_content_area = ft.Container(expand=True)
        self.content_container = ft.Column(spacing=16)

        self.controls = [self.content_container]
        self.load_data()

    def load_data(self):
        try:
            self.data = get_student_dashboard_data(actor=self.user)
            self._render_view()
        except Exception as e:
            self.content_container.controls = [
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, size=48, color=ft.Colors.RED_400),
                            ft.Text("Could not load student dashboard.", size=16, weight=ft.FontWeight.BOLD),
                            ft.Text(str(e), size=12, color=ft.Colors.RED_300),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    padding=40,
                    alignment=ft.Alignment.CENTER,
                )
            ]
            self.app_page.update()

    def _render_view(self):
        is_dark = self.app_page.theme_mode == ft.ThemeMode.DARK
        colors = get_colors(is_dark)

        if not self.data:
            self.content_container.controls = [
                ft.Text("No student record found linked to your account.", size=14, color=colors["text_muted"])
            ]
            self.app_page.update()
            return

        student = self.data.get("student") or {}
        room = self.data.get("room")
        roommates = self.data.get("roommates", [])
        fees = self.data.get("fees", {})
        attendance = self.data.get("attendance", {})
        complaints = self.data.get("complaints", {})
        announcements = self.data.get("announcements", [])

        # Build UI Elements
        header_banner = self._build_header_banner(student, room, colors)
        stat_cards = self._build_stat_cards(room, fees, attendance, complaints, colors)
        tabs_section = self._build_tabs_wrapper(student, room, roommates, fees, attendance, complaints, announcements, colors)

        self.content_container.controls = [
            header_banner,
            ft.Container(height=2),
            stat_cards,
            ft.Container(height=4),
            tabs_section,
            ft.Container(height=24),
        ]
        self.app_page.update()

    # ── Header Banner ──────────────────────────────────────────────────────────
    def _build_header_banner(self, student: dict, room: dict, colors: dict) -> ft.Control:
        name = student.get("name") or self.user.get("full_name") or self.user.get("username")
        student_id = student.get("student_id") or "STU"
        course = student.get("course") or "Undergraduate"
        branch = student.get("branch") or ""
        year = f"Year {student['year']}" if student.get("year") else ""
        course_str = " · ".join([p for p in (course, branch, year) if p])

        hour = datetime.now().hour
        greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"
        initials = "".join([part[0] for part in name.split()[:2]]).upper() or "ST"

        room_str = f"Room {room['room_number']} · Bed #{room['bed_number']}" if room else "Room Not Assigned"

        left_info = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text(initials, size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    width=52,
                    height=52,
                    border_radius=14,
                    bgcolor=ft.Colors.INDIGO_600,
                    alignment=ft.Alignment.CENTER,
                    shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.25, ft.Colors.INDIGO_700)),
                ),
                ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(f"{greeting}, {name} 👋", size=18, weight=ft.FontWeight.BOLD, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Container(
                                    content=ft.Text("STUDENT", size=9, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_300),
                                    padding=ft.Padding.symmetric(horizontal=7, vertical=2),
                                    border_radius=10,
                                    bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.INDIGO_400),
                                ),
                                ft.Container(
                                    content=ft.Text(student.get("status") or "Active", size=9, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400),
                                    padding=ft.Padding.symmetric(horizontal=7, vertical=2),
                                    border_radius=10,
                                    bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.GREEN_400),
                                ),
                            ],
                            spacing=6,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Text(f"Student ID: {student_id}  |  {course_str}", size=11, color=colors["text_muted"], no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.MEETING_ROOM_ROUNDED, size=13, color=ft.Colors.INDIGO_400),
                                ft.Text(room_str, size=11, weight=ft.FontWeight.W_500, color=ft.Colors.INDIGO_300),
                            ],
                            spacing=4,
                        ),
                    ],
                    spacing=2,
                    expand=True,
                ),
            ],
            spacing=14,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        )

        is_dark = self.app_page.theme_mode == ft.ThemeMode.DARK
        theme_icon = ft.Icons.LIGHT_MODE_ROUNDED if is_dark else ft.Icons.DARK_MODE_ROUNDED
        theme_label = "Light Mode" if is_dark else "Dark Mode"

        right_actions = ft.Row(
            controls=[
                ft.FilledButton(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.REPORT_PROBLEM_ROUNDED, size=14, color=ft.Colors.WHITE),
                            ft.Text("Grievance", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ],
                        spacing=4,
                    ),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.AMBER_700,
                        shape=ft.RoundedRectangleBorder(radius=8),
                        padding=ft.Padding.symmetric(horizontal=10, vertical=8),
                    ),
                    tooltip="Log a complaint or maintenance request",
                    on_click=lambda _: self._open_new_complaint_dialog(student.get("student_id")),
                ),
                ft.OutlinedButton(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.STAR_ROUNDED, size=14),
                            ft.Text("Feedback", size=11),
                        ],
                        spacing=4,
                    ),
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8),
                        padding=ft.Padding.symmetric(horizontal=10, vertical=8),
                    ),
                    tooltip="Submit hostel facility feedback",
                    on_click=lambda _: self._nav_to("Feedback"),
                ),
                ft.OutlinedButton(
                    content=ft.Row(
                        controls=[
                            ft.Icon(theme_icon, size=14),
                            ft.Text(theme_label, size=11),
                        ],
                        spacing=4,
                    ),
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8),
                        padding=ft.Padding.symmetric(horizontal=10, vertical=8),
                    ),
                    tooltip=f"Switch to {'Light' if is_dark else 'Dark'} Mode",
                    on_click=lambda _: self._toggle_theme(),
                ),
                ft.IconButton(
                    icon=ft.Icons.REFRESH_ROUNDED,
                    icon_size=18,
                    tooltip="Refresh Dashboard",
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=lambda _: self.load_data(),
                ),
            ],
            spacing=6,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        return ft.Container(
            content=ft.Row(
                controls=[left_info, right_actions],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
            padding=ft.Padding.symmetric(horizontal=18, vertical=16),
            border_radius=16,
            bgcolor=colors["surface"],
            border=ft.Border.all(1, colors["border"]),
            shadow=ft.BoxShadow(blur_radius=12, color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK)),
        )

    # ── Quick Stat Cards ───────────────────────────────────────────────────────
    def _build_stat_cards(self, room: dict, fees: dict, attendance: dict, complaints: dict, colors: dict) -> ft.Control:
        # Card 1: Room & Bed
        room_title = f"Room {room['room_number']}" if room else "Unallocated"
        room_sub = f"Bed #{room['bed_number']} (Floor {room['floor']})" if room else "Contact Warden"
        card1 = self._stat_card(
            title="MY ALLOCATION",
            val=room_title,
            sub=room_sub,
            icon=ft.Icons.HOTEL_ROUNDED,
            accent=ft.Colors.INDIGO_500,
            colors=colors,
        )

        # Card 2: Fee Balance
        bal = fees.get("balance", 0.0)
        paid = fees.get("paid", 0.0)
        bal_text = f"₹{bal:,.0f} Due" if bal > 0 else "Fully Paid"
        bal_color = ft.Colors.RED_400 if bal > 0 else ft.Colors.GREEN_500
        card2 = self._stat_card(
            title="FEE STATUS",
            val=bal_text,
            sub=f"₹{paid:,.0f} paid so far",
            icon=ft.Icons.PAYMENTS_ROUNDED,
            accent=bal_color,
            colors=colors,
        )

        # Card 3: Today's Attendance
        today = attendance.get("today", {})
        if today.get("entry") and today.get("exit"):
            att_val = "Completed"
            att_sub = f"In: {today['entry'][-8:]} · Out: {today['exit'][-8:]}"
            att_accent = ft.Colors.BLUE_500
        elif today.get("entry"):
            att_val = "Checked In"
            att_sub = f"In at: {today['entry'][-8:]}"
            att_accent = ft.Colors.GREEN_500
        else:
            att_val = "Not Logged"
            att_sub = "No gate punch today"
            att_accent = ft.Colors.AMBER_500

        card3 = self._stat_card(
            title="TODAY'S ATTENDANCE",
            val=att_val,
            sub=att_sub,
            icon=ft.Icons.CHECKLIST_ROUNDED,
            accent=att_accent,
            colors=colors,
        )

        # Card 4: Complaints
        comp_summary = complaints.get("summary", {})
        open_count = comp_summary.get("pending", 0)
        tot_count = comp_summary.get("total", 0)
        comp_text = f"{open_count} Pending" if open_count > 0 else "All Resolved"
        comp_accent = ft.Colors.AMBER_600 if open_count > 0 else ft.Colors.GREEN_500
        card4 = self._stat_card(
            title="GRIEVANCES",
            val=comp_text,
            sub=f"{tot_count} complaints logged",
            icon=ft.Icons.CHAT_BUBBLE_ROUNDED,
            accent=comp_accent,
            colors=colors,
        )

        return ft.Row(
            controls=[card1, card2, card3, card4],
            spacing=14,
        )

    def _stat_card(self, title: str, val: str, sub: str, icon: str, accent: str, colors: dict) -> ft.Control:
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(width=4, height=48, border_radius=2, bgcolor=accent),
                    ft.Column(
                        controls=[
                            ft.Text(title, size=10, weight=ft.FontWeight.BOLD, color=colors["text_muted"]),
                            ft.Text(val, size=18, weight=ft.FontWeight.BOLD, color=colors["text"]),
                            ft.Text(sub, size=11, color=colors["text_muted"], no_wrap=True),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Container(
                        content=ft.Icon(icon, size=22, color=accent),
                        width=42,
                        height=42,
                        border_radius=10,
                        bgcolor=ft.Colors.with_opacity(0.12, accent),
                        alignment=ft.Alignment.CENTER,
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            expand=True,
            padding=16,
            border_radius=14,
            bgcolor=colors["surface"],
            border=ft.Border.all(1, colors["border"]),
        )

    # ── Custom Modern Pill Navigation Bar ─────────────────────────────────────
    def _build_tabs_wrapper(self, student, room, roommates, fees, attendance, complaints, announcements, colors) -> ft.Control:
        tab_defs = [
            ("Profile Details", ft.Icons.PERSON_PIN_ROUNDED),
            ("Room & Roommates", ft.Icons.MEETING_ROOM_ROUNDED),
            ("Fees & Receipts", ft.Icons.RECEIPT_LONG_ROUNDED),
            ("Attendance & Punches", ft.Icons.ACCESS_TIME_ROUNDED),
            ("Complaints Tracker", ft.Icons.REPORT_PROBLEM_OUTLINED),
            ("Weekly Mess Menu", ft.Icons.RESTAURANT_MENU_ROUNDED),
            ("Notices & Rules", ft.Icons.CAMPAIGN_ROUNDED),
        ]

        def get_tab_content(idx: int):
            if idx == 0:
                return self._tab_profile(student, colors)
            elif idx == 1:
                return self._tab_roommates(room, roommates, colors)
            elif idx == 2:
                return self._tab_fees(fees, student, room, colors)
            elif idx == 3:
                return self._tab_attendance(attendance, student.get("student_id"), colors)
            elif idx == 4:
                return self._tab_complaints(complaints, student.get("student_id"), colors)
            elif idx == 5:
                return self._tab_mess_menu(colors)
            elif idx == 6:
                return self._tab_notices_and_rules(announcements, colors)
            return ft.Text("View under construction.")

        self.tab_buttons = []
        tab_pills = []

        def on_tab_click(new_idx):
            self.selected_tab_idx = new_idx
            self._update_tab_bar_state(colors)
            self.tab_content_area.content = get_tab_content(new_idx)
            self.app_page.update()

        for idx, (label, icon) in enumerate(tab_defs):
            is_active = (idx == self.selected_tab_idx)
            btn = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(icon, size=15, color=ft.Colors.WHITE if is_active else colors["text_muted"]),
                        ft.Text(
                            label,
                            size=12,
                            weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.W_500,
                            color=ft.Colors.WHITE if is_active else colors["text_muted"],
                        ),
                    ],
                    spacing=6,
                ),
                padding=ft.Padding.symmetric(horizontal=14, vertical=8),
                border_radius=20,
                bgcolor=ft.Colors.INDIGO_600 if is_active else colors["surface_alt"],
                ink=True,
                on_click=lambda e, i=idx: on_tab_click(i),
            )
            self.tab_buttons.append(btn)
            tab_pills.append(btn)

        tab_bar = ft.Container(
            content=ft.Row(
                controls=tab_pills,
                spacing=8,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=ft.Padding.symmetric(vertical=4),
        )

        self.tab_content_area.content = get_tab_content(self.selected_tab_idx)

        return ft.Container(
            content=ft.Column(
                controls=[
                    tab_bar,
                    ft.Divider(height=1, color=colors["border"]),
                    self.tab_content_area,
                ],
                spacing=12,
            ),
            expand=True,
            border_radius=16,
            bgcolor=colors["surface"],
            border=ft.Border.all(1, colors["border"]),
            padding=16,
        )

    def _update_tab_bar_state(self, colors: dict):
        for idx, btn in enumerate(self.tab_buttons):
            is_active = (idx == self.selected_tab_idx)
            row = btn.content
            row.controls[0].color = ft.Colors.WHITE if is_active else colors["text_muted"]
            row.controls[1].color = ft.Colors.WHITE if is_active else colors["text_muted"]
            row.controls[1].weight = ft.FontWeight.BOLD if is_active else ft.FontWeight.W_500
            btn.bgcolor = ft.Colors.INDIGO_600 if is_active else colors["surface_alt"]

    # ── Tab 0: Profile Details ────────────────────────────────────────────────
    def _tab_profile(self, student: dict, colors: dict) -> ft.Control:
        academic_items = [
            ("Student ID / Roll No", student.get("student_id")),
            ("Course Enrolled", student.get("course")),
            ("Specialization / Branch", student.get("branch")),
            ("Current Academic Year", f"Year {student.get('year')}" if student.get("year") else None),
            ("Admission Date", student.get("admission_date")),
            ("Enrollment Status", student.get("status") or "Active"),
        ]

        personal_items = [
            ("Full Name", student.get("name")),
            ("Gender", student.get("gender")),
            ("Date of Birth", student.get("date_of_birth")),
            ("Contact Phone", student.get("phone")),
            ("Contact Email", student.get("email")),
            ("Permanent Address", student.get("address")),
        ]

        guardian_items = [
            ("Parent / Guardian Name", student.get("parent_name")),
            ("Relationship", "Parent / Legal Guardian"),
            ("Emergency Contact", student.get("phone")),
        ]

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("Complete Student Profile", size=16, weight=ft.FontWeight.BOLD),
                                    ft.Text("Official academic, personal, and guardian credentials registered in system", size=12, color=colors["text_muted"]),
                                ],
                                spacing=2,
                            ),
                            ft.OutlinedButton(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.EDIT_ROUNDED, size=14),
                                        ft.Text("Update Personal & Contact Details", size=12),
                                    ],
                                    spacing=6,
                                ),
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                                on_click=lambda _: self._open_edit_contact_dialog(student),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(height=12, color=colors["border"]),
                    ft.Row(
                        controls=[
                            self._detail_box("Academic Credentials", ft.Icons.SCHOOL_ROUNDED, academic_items, ft.Colors.INDIGO_500, colors),
                            self._detail_box("Personal & Contact Details", ft.Icons.PERSON_OUTLINE_ROUNDED, personal_items, ft.Colors.PURPLE_500, colors),
                        ],
                        spacing=16,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    ft.Container(height=8),
                    ft.Row(
                        controls=[
                            self._detail_box("Guardian & Emergency Information", ft.Icons.FAMILY_RESTROOM_ROUNDED, guardian_items, ft.Colors.GREEN_500, colors),
                        ],
                        spacing=16,
                    ),
                    ft.Container(height=12),
                ],
                spacing=4,
            ),
        )

    def _detail_box(self, section_title: str, icon: str, items: list, accent: str, colors: dict) -> ft.Control:
        rows = []
        for label, val in items:
            val_str = str(val) if val else "—"
            rows.append(
                ft.Row(
                    controls=[
                        ft.Text(label, size=12, color=colors["text_muted"], width=160),
                        ft.Text(val_str, size=12, weight=ft.FontWeight.W_600, color=colors["text"], expand=True),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(icon, size=18, color=accent),
                            ft.Text(section_title, size=14, weight=ft.FontWeight.BOLD),
                        ],
                        spacing=8,
                    ),
                    ft.Divider(height=10, color=colors["border"]),
                    ft.Column(controls=rows, spacing=8),
                ],
                spacing=4,
            ),
            expand=True,
            padding=16,
            border_radius=12,
            bgcolor=colors["surface_alt"],
            border=ft.Border.all(1, colors["border"]),
        )

    # ── Tab 1: Room & Roommates ───────────────────────────────────────────────
    def _tab_roommates(self, room: dict, roommates: list, colors: dict) -> ft.Control:
        if not room:
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Container(height=24),
                        ft.Icon(ft.Icons.BED_OUTLINED, size=48, color=colors["text_muted"]),
                        ft.Text("No Room Allocated Yet", size=16, weight=ft.FontWeight.BOLD),
                        ft.Text("Please contact the warden or admin to allocate a room and bed.", size=12, color=colors["text_muted"]),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
                padding=40,
                alignment=ft.Alignment.CENTER,
            )

        room_card = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text(f"Room {room['room_number']}", size=20, weight=ft.FontWeight.BOLD),
                            ft.Text(f"Type: {room['room_type']}  ·  Floor {room['floor']}", size=12, color=colors["text_muted"]),
                            ft.Container(height=4),
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        content=ft.Text(f"Your Bed: #{room['bed_number']}", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                                        border_radius=8,
                                        bgcolor=ft.Colors.INDIGO_600,
                                    ),
                                    ft.Container(
                                        content=ft.Text(f"Capacity: {room['occupied_beds']}/{room['capacity']} Beds Occupied", size=11, weight=ft.FontWeight.W_500, color=colors["text"]),
                                        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                                        border_radius=8,
                                        bgcolor=colors["surface"],
                                        border=ft.Border.all(1, colors["border"]),
                                    ),
                                ],
                                spacing=8,
                            ),
                        ],
                        spacing=2,
                    ),
                    ft.Icon(ft.Icons.MEETING_ROOM_ROUNDED, size=52, color=ft.Colors.INDIGO_400),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=18,
            border_radius=14,
            bgcolor=colors["surface_alt"],
            border=ft.Border.all(1, colors["border"]),
        )

        mate_cards = []
        if roommates:
            for m in roommates:
                m_init = "".join([p[0] for p in m["name"].split()[:2]]).upper() or "RM"
                mate_cards.append(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Text(m_init, size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                    width=42,
                                    height=42,
                                    border_radius=12,
                                    bgcolor=ft.Colors.PURPLE_600,
                                    alignment=ft.Alignment.CENTER,
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(m["name"], size=13, weight=ft.FontWeight.BOLD),
                                        ft.Text(f"Bed #{m['bed_number']}  ·  {m['course']} ({m['branch']})", size=11, color=colors["text_muted"]),
                                        ft.Row(
                                            controls=[
                                                ft.Icon(ft.Icons.PHONE_ROUNDED, size=13, color=ft.Colors.GREEN_400),
                                                ft.Text(m["phone"], size=11, color=ft.Colors.GREEN_400, weight=ft.FontWeight.W_500),
                                            ],
                                            spacing=4,
                                        ),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                            ],
                            spacing=12,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=12,
                        border_radius=10,
                        bgcolor=colors["surface_alt"],
                        border=ft.Border.all(1, colors["border"]),
                    )
                )
        else:
            mate_cards.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, size=20, color=colors["text_muted"]),
                            ft.Text("No other roommates currently assigned to this room.", size=12, color=colors["text_muted"]),
                        ],
                        spacing=8,
                    ),
                    padding=16,
                )
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    room_card,
                    ft.Container(height=8),
                    ft.Text("Roommates Sharing This Room", size=15, weight=ft.FontWeight.BOLD),
                    ft.Text("Contact details of your fellow residents allocated to this room", size=11, color=colors["text_muted"]),
                    ft.Divider(height=10, color=colors["border"]),
                    ft.Column(controls=mate_cards, spacing=10),
                    ft.Container(height=12),
                ],
                spacing=4,
            ),
        )

    # ── Tab 2: Fees & Receipts ────────────────────────────────────────────────
    def _tab_fees(self, fees: dict, student: dict, room: dict, colors: dict) -> ft.Control:
        tot = fees.get("total", 0.0)
        paid = fees.get("paid", 0.0)
        bal = fees.get("balance", 0.0)
        payments = fees.get("recent_payments", [])

        summary_box = ft.Row(
            controls=[
                self._mini_stat("Total Billed", f"₹{tot:,.0f}", ft.Colors.INDIGO_500, colors),
                self._mini_stat("Total Paid", f"₹{paid:,.0f}", ft.Colors.GREEN_500, colors),
                self._mini_stat("Outstanding Balance", f"₹{bal:,.0f}", ft.Colors.RED_400 if bal > 0 else ft.Colors.GREEN_500, colors),
            ],
            spacing=14,
        )

        rows = []
        if payments:
            for p in payments:
                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(p["receipt"], weight=ft.FontWeight.BOLD)),
                            ft.DataCell(ft.Text(p["date"])),
                            ft.DataCell(ft.Text(p["mode"])),
                            ft.DataCell(ft.Text(f"₹{p['amount']:,.2f}", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_500)),
                            ft.DataCell(
                                ft.OutlinedButton(
                                    content=ft.Row([ft.Icon(ft.Icons.RECEIPT_ROUNDED, size=13), ft.Text("View Receipt", size=11)], spacing=4),
                                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
                                    on_click=lambda e, item=p: self._open_receipt_dialog(item, student, room),
                                )
                            ),
                        ]
                    )
                )
            table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("RECEIPT NO.", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
                    ft.DataColumn(ft.Text("PAYMENT DATE", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
                    ft.DataColumn(ft.Text("MODE", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
                    ft.DataColumn(ft.Text("AMOUNT", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
                    ft.DataColumn(ft.Text("ACTION / RECEIPT", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
                ],
                rows=rows,
                border_radius=10,
                heading_row_color=colors["surface_alt"],
                column_spacing=24,
            )
            pay_display = ft.Container(content=table, border_radius=10, border=ft.Border.all(1, colors["border"]))
        else:
            pay_display = ft.Container(
                content=ft.Text("No payment receipts recorded yet.", size=12, color=colors["text_muted"]),
                padding=20,
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    summary_box,
                    ft.Container(height=12),
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("Payment Receipts & Transactions", size=15, weight=ft.FontWeight.BOLD),
                                    ft.Text("Official record of fee payments credited to your account", size=11, color=colors["text_muted"]),
                                ],
                                spacing=2,
                            ),
                            ft.FilledButton(
                                content=ft.Row([ft.Icon(ft.Icons.PAYMENTS_ROUNDED, size=14), ft.Text("Full Fee Ledger", size=12)], spacing=6),
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                                on_click=lambda _: self._nav_to("Fees"),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(height=10, color=colors["border"]),
                    pay_display,
                    ft.Container(height=12),
                ],
                spacing=4,
            ),
        )

    def _mini_stat(self, title: str, val: str, accent: str, colors: dict) -> ft.Control:
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(title, size=11, color=colors["text_muted"]),
                    ft.Text(val, size=18, weight=ft.FontWeight.BOLD, color=accent),
                ],
                spacing=2,
            ),
            expand=True,
            padding=14,
            border_radius=12,
            bgcolor=colors["surface_alt"],
            border=ft.Border.all(1, colors["border"]),
        )

    def _open_receipt_dialog(self, payment: dict, student: dict, room: dict):
        colors = get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)
        room_str = f"Room {room['room_number']} (Bed #{room['bed_number']})" if room else "Not Assigned"

        content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("HOSTEL PAYMENT RECEIPT", weight=ft.FontWeight.BOLD, size=16),
                            ft.Container(
                                content=ft.Text("VERIFIED & PAID", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400),
                                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                                border_radius=8,
                                bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.GREEN_400),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(height=12, color=colors["border"]),
                    self._rcpt_row("Receipt Number:", payment.get("receipt", "—"), is_bold=True),
                    self._rcpt_row("Student Name:", student.get("name", "—")),
                    self._rcpt_row("Student ID:", student.get("student_id", "—")),
                    self._rcpt_row("Course / Branch:", f"{student.get('course')} ({student.get('branch')})"),
                    self._rcpt_row("Room Allocation:", room_str),
                    self._rcpt_row("Payment Date:", payment.get("date", "—")),
                    self._rcpt_row("Payment Mode:", payment.get("mode", "Online")),
                    ft.Divider(height=12, color=colors["border"]),
                    ft.Row(
                        controls=[
                            ft.Text("Total Amount Paid:", size=14, weight=ft.FontWeight.BOLD),
                            ft.Text(f"₹{float(payment.get('amount', 0)):,.2f}", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_500),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(height=4),
                    ft.Text("This is an official system-generated receipt for hostel accommodation dues.", size=10, color=colors["text_muted"], text_align=ft.TextAlign.CENTER),
                ],
                spacing=8,
                tight=True,
            ),
            width=420,
            padding=16,
        )

        dlg = ft.AlertDialog(
            content=content,
            actions=[
                ft.FilledButton("Close", on_click=lambda _: self._close_dlg(dlg)),
            ],
        )
        self.app_page.overlay.append(dlg)
        dlg.open = True
        self.app_page.update()

    def _rcpt_row(self, label: str, val: str, is_bold: bool = False):
        return ft.Row(
            controls=[
                ft.Text(label, size=12, color=ft.Colors.GREY_500, width=130),
                ft.Text(str(val or "—"), size=12, weight=ft.FontWeight.BOLD if is_bold else ft.FontWeight.W_500, expand=True),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    # ── Tab 3: Attendance & Punches ───────────────────────────────────────────
    def _tab_attendance(self, attendance: dict, student_id: str, colors: dict) -> ft.Control:
        today = attendance.get("today", {})
        history = attendance.get("history", [])

        in_time = today.get("entry") or "—"
        out_time = today.get("exit") or "—"

        status_text = "Checked In" if today.get("entry") and not today.get("exit") else "Completed" if today.get("exit") else "No punch yet"
        status_color = ft.Colors.GREEN_500 if today.get("entry") and not today.get("exit") else ft.Colors.BLUE_500 if today.get("exit") else ft.Colors.AMBER_500

        def do_punch(is_entry: bool):
            if is_entry:
                ok, msg = mark_entry(student_id=student_id, actor=self.user)
            else:
                ok, msg = mark_exit(student_id=student_id, actor=self.user)
            if ok:
                self.load_data()
                self._show_toast(f"Gate punch recorded: {msg}")
            else:
                self._show_toast(f"Punch failed: {msg}", is_err=True)

        today_card = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text("Today's Gate Status", size=15, weight=ft.FontWeight.BOLD),
                                    ft.Container(
                                        content=ft.Text(status_text, size=10, weight=ft.FontWeight.BOLD, color=status_color),
                                        padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                                        border_radius=8,
                                        bgcolor=ft.Colors.with_opacity(0.12, status_color),
                                    ),
                                ],
                                spacing=8,
                            ),
                            ft.Text(f"Date: {datetime.now().strftime('%A, %d %b %Y')}", size=11, color=colors["text_muted"]),
                            ft.Container(height=4),
                            ft.Row(
                                controls=[
                                    ft.Text("Check-In: ", size=12, color=colors["text_muted"]),
                                    ft.Text(in_time[-8:] if in_time != "—" else "—", size=12, weight=ft.FontWeight.BOLD),
                                    ft.Container(width=16),
                                    ft.Text("Check-Out: ", size=12, color=colors["text_muted"]),
                                    ft.Text(out_time[-8:] if out_time != "—" else "—", size=12, weight=ft.FontWeight.BOLD),
                                ],
                            ),
                        ],
                        spacing=2,
                    ),
                    # Interactive Punch buttons
                    ft.Row(
                        controls=[
                            ft.FilledButton(
                                content=ft.Row([ft.Icon(ft.Icons.LOGIN_ROUNDED, size=14), ft.Text("Punch IN", size=12)], spacing=4),
                                style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, shape=ft.RoundedRectangleBorder(radius=8)),
                                on_click=lambda _: do_punch(True),
                            ),
                            ft.FilledButton(
                                content=ft.Row([ft.Icon(ft.Icons.LOGOUT_ROUNDED, size=14), ft.Text("Punch OUT", size=12)], spacing=4),
                                style=ft.ButtonStyle(bgcolor=ft.Colors.AMBER_800, shape=ft.RoundedRectangleBorder(radius=8)),
                                on_click=lambda _: do_punch(False),
                            ),
                        ],
                        spacing=8,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=16,
            border_radius=12,
            bgcolor=colors["surface_alt"],
            border=ft.Border.all(1, colors["border"]),
        )

        rows = []
        if history:
            for a in history:
                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(a["date"], weight=ft.FontWeight.W_500)),
                            ft.DataCell(ft.Text(a["entry"][-8:] if a["entry"] != "—" else "—")),
                            ft.DataCell(ft.Text(a["exit"][-8:] if a["exit"] != "—" else "—")),
                            ft.DataCell(
                                ft.Container(
                                    content=ft.Text("Present", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400),
                                    padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                                    border_radius=8,
                                    bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.GREEN_400),
                                )
                            ),
                        ]
                    )
                )
            table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("DATE", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
                    ft.DataColumn(ft.Text("GATE IN", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
                    ft.DataColumn(ft.Text("GATE OUT", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
                    ft.DataColumn(ft.Text("STATUS", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
                ],
                rows=rows,
                border_radius=10,
                heading_row_color=colors["surface_alt"],
                column_spacing=24,
            )
            hist_display = ft.Container(content=table, border_radius=10, border=ft.Border.all(1, colors["border"]))
        else:
            hist_display = ft.Container(
                content=ft.Text("No attendance punch history logged yet.", size=12, color=colors["text_muted"]),
                padding=20,
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    today_card,
                    ft.Container(height=12),
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("Recent Attendance Logs", size=15, weight=ft.FontWeight.BOLD),
                                    ft.Text("Gate entry and exit timestamps recorded by guard biometric scanner", size=11, color=colors["text_muted"]),
                                ],
                                spacing=2,
                            ),
                            ft.FilledButton(
                                content=ft.Row([ft.Icon(ft.Icons.CHECKLIST_ROUNDED, size=14), ft.Text("View Full Attendance", size=12)], spacing=6),
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                                on_click=lambda _: self._nav_to("Attendance"),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(height=10, color=colors["border"]),
                    hist_display,
                    ft.Container(height=12),
                ],
                spacing=4,
            ),
        )

    # ── Tab 4: Complaints Tracker ─────────────────────────────────────────────
    def _tab_complaints(self, complaints: dict, student_id: str, colors: dict) -> ft.Control:
        recent = complaints.get("recent", [])

        cards = []
        if recent:
            for c in recent:
                st = c["status"] or "Submitted"
                is_res = (st.lower() in ("resolved", "closed"))
                chip_color = ft.Colors.GREEN_400 if is_res else ft.Colors.AMBER_500 if st.lower() == "in progress" else ft.Colors.BLUE_400

                cards.append(
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Row(
                                            controls=[
                                                ft.Icon(ft.Icons.REPORT_PROBLEM_ROUNDED, size=16, color=chip_color),
                                                ft.Text(f"#{c['id']} · Category: {c['category']}", size=13, weight=ft.FontWeight.BOLD),
                                            ],
                                            spacing=6,
                                        ),
                                        ft.Container(
                                            content=ft.Text(st, size=10, weight=ft.FontWeight.BOLD, color=chip_color),
                                            padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                                            border_radius=8,
                                            bgcolor=ft.Colors.with_opacity(0.12, chip_color),
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                ft.Text(c["description"], size=12, color=colors["text"]),
                                ft.Row(
                                    controls=[
                                        ft.Text(f"Priority: {c['priority']}  ·  Logged: {c['created_at'][:10] if c.get('created_at') else '—'}", size=11, color=colors["text_muted"]),
                                        ft.Text(f"Resolution Remarks: {c['remarks']}", size=11, color=ft.Colors.INDIGO_300 if c.get("remarks") != "—" else colors["text_muted"]),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                            ],
                            spacing=6,
                        ),
                        padding=14,
                        border_radius=10,
                        bgcolor=colors["surface_alt"],
                        border=ft.Border.all(1, colors["border"]),
                    )
                )
        else:
            cards.append(
                ft.Container(
                    content=ft.Text("You have not logged any complaints yet.", size=12, color=colors["text_muted"]),
                    padding=20,
                )
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("Grievances & Maintenance Requests", size=15, weight=ft.FontWeight.BOLD),
                                    ft.Text("Track progress on issues reported for room, electrical, mess, or cleanliness", size=11, color=colors["text_muted"]),
                                ],
                                spacing=2,
                            ),
                            ft.FilledButton(
                                content=ft.Row([ft.Icon(ft.Icons.ADD_ROUNDED, size=15), ft.Text("Log New Grievance", size=12)], spacing=6),
                                style=ft.ButtonStyle(bgcolor=ft.Colors.AMBER_700, shape=ft.RoundedRectangleBorder(radius=8)),
                                on_click=lambda _: self._open_new_complaint_dialog(student_id),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(height=10, color=colors["border"]),
                    ft.Column(controls=cards, spacing=10),
                    ft.Container(height=12),
                ],
                spacing=4,
            ),
        )

    # ── Tab 5: Weekly Mess Menu ───────────────────────────────────────────────
    def _tab_mess_menu(self, colors: dict) -> ft.Control:
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        today_name = datetime.now().strftime("%A")

        weekly_menu = {
            "Monday": {"b": "Aloo Paratha, Curd, Tea / Coffee", "l": "Dal Makhani, Rice, Roti, Seasonal Veg, Salad", "s": "Samosa, Masala Chai", "d": "Paneer Butter Masala, Roti, Jeera Rice, Gulab Jamun"},
            "Tuesday": {"b": "Idli Sambhar, Coconut Chutney, Tea", "l": "Rajma Masala, Steamed Rice, Roti, Boondi Raita", "s": "Veg Sandwich, Tea", "d": "Mix Veg Curry, Dal Tadka, Roti, Rice, Kheer"},
            "Wednesday": {"b": "Poha, Boiled Egg / Sprouts, Tea", "l": "Chole Bhature / Rice, Kadhi Pakora, Salad", "s": "Biscuits, Tea / Milk", "d": "Butter Chicken / Shahi Paneer, Naan, Rice"},
            "Thursday": {"b": "Uttapam, Sambhar, Green Chutney", "l": "Dal Fry, Jeera Aloo, Roti, Rice, Curd", "s": "Patties, Hot Coffee", "d": "Egg Curry / Malai Kofta, Roti, Rice, Halwa"},
            "Friday": {"b": "Puri Bhaji, Banana, Tea / Coffee", "l": "Veg Biryani, Mirchi Salan, Raita, Papad", "s": "Bread Pakora, Tea", "d": "Dal Tadka, Bhindi Masala, Roti, Pulao, Custard"},
            "Saturday": {"b": "Methi Thepla, Pickle, Curd, Tea", "l": "Khichdi, Kadhi, Aloo Chokha, Papad", "s": "Maggi Noodles, Coffee", "d": "Palak Paneer, Phulka, Steamed Rice, Sweet"},
            "Sunday": {"b": "Masala Dosa, Sambhar, Chutney", "l": "Special Veg Thali / Chicken Curry, Pulao, Roti", "s": "Cake, Masala Tea", "d": "Matar Paneer, Tandoori Roti, Veg Pulao, Ice Cream"},
        }

        cards = []
        for d in days:
            is_today = (d.lower() == today_name.lower())
            m = weekly_menu[d]

            header_badge = ft.Container(
                content=ft.Text("TODAY'S MENU", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                border_radius=6,
                bgcolor=ft.Colors.INDIGO_600,
            ) if is_today else ft.Container()

            cards.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(d, size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_400 if is_today else colors["text"]),
                                    header_badge,
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Divider(height=6, color=colors["border"]),
                            self._meal_line("Breakfast (7:30 - 9:30 AM):", m["b"], colors),
                            self._meal_line("Lunch (12:30 - 2:30 PM):", m["l"], colors),
                            self._meal_line("Evening Snacks (5:00 - 6:30 PM):", m["s"], colors),
                            self._meal_line("Dinner (8:00 - 10:00 PM):", m["d"], colors),
                        ],
                        spacing=4,
                    ),
                    padding=14,
                    border_radius=12,
                    bgcolor=colors["surface_alt"] if not is_today else ft.Colors.with_opacity(0.08, ft.Colors.INDIGO_400),
                    border=ft.Border.all(1.5 if is_today else 1, ft.Colors.INDIGO_400 if is_today else colors["border"]),
                )
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Weekly Mess Meal Schedule", size=15, weight=ft.FontWeight.BOLD),
                    ft.Text("Dietary menu served across breakfast, lunch, snacks, and dinner", size=11, color=colors["text_muted"]),
                    ft.Divider(height=10, color=colors["border"]),
                    ft.Column(controls=cards, spacing=10),
                    ft.Container(height=12),
                ],
                spacing=4,
            ),
        )

    def _meal_line(self, meal_label: str, menu_text: str, colors: dict):
        return ft.Row(
            controls=[
                ft.Text(meal_label, size=11, weight=ft.FontWeight.BOLD, color=colors["text_muted"], width=180),
                ft.Text(menu_text, size=12, weight=ft.FontWeight.W_500, expand=True),
            ],
        )

    # ── Tab 6: Notices & Rules ────────────────────────────────────────────────
    def _tab_notices_and_rules(self, announcements: list, colors: dict) -> ft.Control:
        notice_items = []
        if announcements:
            for ann in announcements:
                notice_items.append(
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Text(ann["title"], size=13, weight=ft.FontWeight.BOLD),
                                        ft.Text(ann["created_at"][:10] if ann.get("created_at") else "", size=11, color=colors["text_muted"]),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                ft.Text(ann["message"], size=12, color=colors["text_muted"]),
                            ],
                            spacing=4,
                        ),
                        padding=12,
                        border_radius=10,
                        bgcolor=colors["surface_alt"],
                        border=ft.Border.all(1, colors["border"]),
                    )
                )
        else:
            notice_items.append(
                ft.Container(
                    content=ft.Text("No announcements posted currently.", size=12, color=colors["text_muted"]),
                    padding=16,
                )
            )

        hostel_rules = [
            ("Main Gate Curfew", "10:00 PM (Strict gate closure; late entries require warden's approval slip)"),
            ("Night Silence Hours", "11:00 PM – 06:00 AM (Maintain quietness in corridors, rooms, and balconies)"),
            ("Visitor Hours", "04:00 PM – 07:00 PM (Visitors permitted in Common Lounge area only)"),
            ("Prohibited Items", "Heaters, induction coils, unauthorized electric appliances, and smoking/alcohol"),
        ]

        rule_rows = []
        for r_title, r_desc in hostel_rules:
            rule_rows.append(
                ft.Column(
                    controls=[
                        ft.Text(r_title, size=12, weight=ft.FontWeight.BOLD),
                        ft.Text(r_desc, size=11, color=colors["text_muted"]),
                    ],
                    spacing=1,
                )
            )

        helpline_items = [
            ("Hostel Warden Office", "+91 98765 43210 (Warden Cabin / Admin Block)"),
            ("Chief Security Desk", "+91 98765 43211 (Main Gate 24x7 Helpline)"),
            ("Campus Ambulance / Medical", "108 / +91 98765 43212 (Health Centre)"),
            ("Hostel Electrician & Plumber", "+91 98765 43213 (Maintenance Desk)"),
        ]

        helpline_rows = []
        for h_role, h_num in helpline_items:
            helpline_rows.append(
                ft.Row(
                    controls=[
                        ft.Text(h_role, size=12, weight=ft.FontWeight.BOLD, width=180),
                        ft.Text(h_num, size=12, color=ft.Colors.GREEN_400),
                    ],
                )
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Hostel Notice Board & Announcements", size=15, weight=ft.FontWeight.BOLD),
                    ft.Text("Official circulars and notices broadcasted by administration", size=11, color=colors["text_muted"]),
                    ft.Divider(height=10, color=colors["border"]),
                    ft.Column(controls=notice_items, spacing=8),
                    ft.Container(height=12),
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Row([ft.Icon(ft.Icons.RULE_ROUNDED, size=16, color=ft.Colors.INDIGO_400), ft.Text("Hostel Rules & Curfew Guidelines", size=13, weight=ft.FontWeight.BOLD)], spacing=6),
                                        ft.Divider(height=8, color=colors["border"]),
                                        ft.Column(controls=rule_rows, spacing=8),
                                    ],
                                ),
                                expand=True,
                                padding=14,
                                border_radius=10,
                                bgcolor=colors["surface_alt"],
                                border=ft.Border.all(1, colors["border"]),
                            ),
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Row([ft.Icon(ft.Icons.PHONE_IN_TALK_ROUNDED, size=16, color=ft.Colors.GREEN_400), ft.Text("24x7 Emergency & Staff Contacts", size=13, weight=ft.FontWeight.BOLD)], spacing=6),
                                        ft.Divider(height=8, color=colors["border"]),
                                        ft.Column(controls=helpline_rows, spacing=8),
                                    ],
                                ),
                                expand=True,
                                padding=14,
                                border_radius=10,
                                bgcolor=colors["surface_alt"],
                                border=ft.Border.all(1, colors["border"]),
                            ),
                        ],
                        spacing=16,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    ft.Container(height=12),
                ],
                spacing=4,
            ),
        )

    # ── Helpers & Modals ───────────────────────────────────────────────────────
    def _toggle_theme(self):
        if self.toggle_theme_fn:
            self.toggle_theme_fn()
        else:
            new_mode = ft.ThemeMode.LIGHT if self.app_page.theme_mode == ft.ThemeMode.DARK else ft.ThemeMode.DARK
            self.app_page.theme_mode = new_mode
            colors = get_colors(new_mode == ft.ThemeMode.DARK)
            self.app_page.bgcolor = colors["page"]
            self._render_view()

    def _nav_to(self, target: str):
        if self.on_navigate:
            self.on_navigate(target)

    def _open_edit_contact_dialog(self, student: dict):
        sid = student.get("student_id")
        phone_field = ft.TextField(
            label="Phone Number (10 digits)",
            value=student.get("phone") or "",
            border_radius=8,
            max_length=10,
            prefix_icon=ft.Icons.PHONE_ROUNDED,
            expand=True,
        )
        email_field = ft.TextField(
            label="Email Address (@gmail.com)",
            value=student.get("email") or "",
            border_radius=8,
            prefix_icon=ft.Icons.EMAIL_ROUNDED,
            expand=True,
        )
        gender_field = ft.Dropdown(
            label="Gender",
            value=student.get("gender") or "Male",
            options=[
                ft.dropdown.Option("Male"),
                ft.dropdown.Option("Female"),
                ft.dropdown.Option("Other"),
            ],
            border_radius=8,
            expand=True,
        )
        dob_field = ft.TextField(
            label="Date of Birth (YYYY-MM-DD)",
            value=student.get("date_of_birth") or "",
            hint_text="e.g. 2004-05-15",
            border_radius=8,
            prefix_icon=ft.Icons.CALENDAR_MONTH_ROUNDED,
            expand=True,
        )
        attach_date_picker(dob_field, self.app_page, first_date=datetime(1970, 1, 1), last_date=datetime(2025, 12, 31))
        address_field = ft.TextField(
            label="Permanent Address",
            value=student.get("address") or "",
            hint_text="e.g. 123 Main Street, City",
            border_radius=8,
            multiline=True,
            min_lines=2,
            max_lines=3,
            prefix_icon=ft.Icons.HOME_ROUNDED,
        )
        parent_field = ft.TextField(
            label="Parent / Guardian Name",
            value=student.get("parent_name") or "",
            hint_text="e.g. Mr. Sharma",
            border_radius=8,
            prefix_icon=ft.Icons.FAMILY_RESTROOM_ROUNDED,
        )

        def do_save(_):
            new_phone = (phone_field.value or "").strip()
            new_email = (email_field.value or "").strip()
            new_gender = (gender_field.value or "").strip() or None
            new_dob = (dob_field.value or "").strip() or None
            new_addr = (address_field.value or "").strip() or None
            new_parent = (parent_field.value or "").strip() or None

            if not new_phone:
                self._show_toast("Phone number cannot be blank! Please provide a valid 10-digit number.", is_err=True)
                return
            if not new_email:
                self._show_toast("Email address cannot be blank! Please provide a valid @gmail.com address.", is_err=True)
                return

            try:
                valid_phone = validate_real_mobile_phone(new_phone)
            except ValueError as e:
                self._show_toast(str(e), is_err=True)
                return

            try:
                valid_email = validate_real_gmail(new_email)
            except ValueError as e:
                self._show_toast(str(e), is_err=True)
                return

            if new_dob:
                try:
                    from utils.validators import validate_iso_date
                    validate_iso_date(new_dob, "Date of birth")
                except ValueError as e:
                    self._show_toast(str(e), is_err=True)
                    return

            from database import get_connection
            conn = get_connection()
            try:
                conn.execute(
                    """UPDATE students 
                       SET phone = ?, email = ?, gender = ?, date_of_birth = ?, address = ?, parent_name = COALESCE(?, parent_name)
                       WHERE student_id = ?""",
                    (valid_phone, valid_email, new_gender, new_dob, new_addr, new_parent, sid),
                )
                conn.execute(
                    "UPDATE users SET phone = ?, email = ? WHERE username = ? OR student_id = ?",
                    (valid_phone, valid_email, sid, sid),
                )
                conn.commit()
                dlg.open = False
                self.app_page.update()
                self.load_data()
                self._show_toast("Personal & Contact details updated successfully!")
            except Exception as e:
                self._show_toast(f"Update failed: {e}", is_err=True)
            finally:
                conn.close()

        dlg = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.EDIT_NOTE_ROUNDED, color=ft.Colors.INDIGO_400),
                    ft.Text("Update Personal & Contact Details", weight=ft.FontWeight.BOLD, size=18),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Keep your identity, address, and contact details up-to-date in hostel records.", size=12, color=ft.Colors.GREY_500),
                        ft.Row(controls=[phone_field, email_field], spacing=10),
                        ft.Row(controls=[gender_field, dob_field], spacing=10),
                        parent_field,
                        address_field,
                    ],
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=460,
                height=380,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self._close_dlg(dlg)),
                ft.FilledButton("Save Changes", on_click=do_save),
            ],
        )
        self.app_page.overlay.append(dlg)
        dlg.open = True
        self.app_page.update()

    def _open_new_complaint_dialog(self, student_id: str):
        cat_drop = ft.Dropdown(
            label="Category",
            options=[
                ft.dropdown.Option("Electrical"),
                ft.dropdown.Option("Plumbing"),
                ft.dropdown.Option("Cleanliness"),
                ft.dropdown.Option("Furniture"),
                ft.dropdown.Option("WiFi / Internet"),
                ft.dropdown.Option("Mess / Food"),
                ft.dropdown.Option("Other"),
            ],
            value="Electrical",
            border_radius=8,
        )
        prio_drop = ft.Dropdown(
            label="Priority",
            options=[
                ft.dropdown.Option("Low"),
                ft.dropdown.Option("Medium"),
                ft.dropdown.Option("High"),
            ],
            value="Medium",
            border_radius=8,
        )
        desc_field = ft.TextField(
            label="Description",
            hint_text="Describe the issue in detail...",
            multiline=True,
            min_lines=3,
            max_lines=5,
            border_radius=8,
        )

        def do_submit(_):
            desc = (desc_field.value or "").strip()
            if not desc:
                self._show_toast("Please enter a description of your issue.", is_err=True)
                return
            dlg.open = False
            self.app_page.update()
            success, msg = add_complaint(
                student_id=student_id,
                category=cat_drop.value,
                description=desc,
                priority=prio_drop.value,
                actor=self.user,
            )
            if success:
                self.load_data()
                self._show_toast("Complaint logged successfully! Warden/staff notified.")
            else:
                self._show_toast(f"Failed to log complaint: {msg}", is_err=True)

        dlg = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.REPORT_PROBLEM_ROUNDED, color=ft.Colors.AMBER_600),
                    ft.Text("Log New Grievance", weight=ft.FontWeight.BOLD),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[cat_drop, prio_drop, desc_field],
                    spacing=12,
                ),
                width=400,
                height=260,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self._close_dlg(dlg)),
                ft.FilledButton("Submit Grievance", bgcolor=ft.Colors.AMBER_700, color=ft.Colors.WHITE, on_click=do_submit),
            ],
        )
        self.app_page.overlay.append(dlg)
        dlg.open = True
        self.app_page.update()

    def _close_dlg(self, dlg):
        dlg.open = False
        self.app_page.update()

    def _show_toast(self, message: str, is_err: bool = False):
        try:
            sb = ft.SnackBar(
                content=ft.Text(message, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.RED_600 if is_err else ft.Colors.GREEN_600,
                behavior=ft.SnackBarBehavior.FLOATING,
                shape=ft.RoundedRectangleBorder(radius=10),
                duration=ft.Duration(seconds=4),
                show_close_icon=True,
            )
            self.app_page.show_dialog(sb)
        except Exception:
            pass
