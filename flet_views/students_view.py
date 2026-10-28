from datetime import datetime
import re
"""Modern SaaS Students Management View built with Flet."""

import secrets
import flet as ft
from services.student_service import get_all_students, add_student, delete_student
from services.room_service import get_all_rooms, allocate_room, deallocate_room
from services.auth_service import get_student_credentials, create_or_update_student_credentials
from flet_views.theme import get_colors, attach_date_picker


class StudentsSubView(ft.Column):
    def __init__(self, page: ft.Page, user: dict):
        super().__init__()
        self.app_page = page
        self.user = user
        self.expand = True
        self.spacing = 16

        self.search_field = ft.TextField(
            hint_text="Search students by name, ID, or course...",
            prefix_icon=ft.Icons.SEARCH_ROUNDED,
            border_radius=10,
            expand=True,
            on_change=self._filter_students,
        )

        self.table_container = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
        self.all_students = []

        self.controls = [
            self._build_header(),
            ft.Container(
                content=self.table_container,
                expand=True,
                padding=16,
                border_radius=14,
                bgcolor=get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)["surface"],
                border=ft.Border.all(1, get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)["border"]),
            ),
        ]

        self.load_data()

    def _build_header(self) -> ft.Control:
        is_admin = self.user.get("role") == "admin"
        return ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("Student Directory", size=22, weight=ft.FontWeight.BOLD),
                        ft.Text("Manage enrolled students, room assignments, and student login accounts", size=12, color=get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)["text_muted"]),
                    ],
                    spacing=2,
                    expand=True,
                ),
                self.search_field,
                ft.FilledButton(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.PERSON_ADD_ROUNDED, size=16, color=ft.Colors.WHITE),
                            ft.Text("Add Student", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ],
                        spacing=6,
                    ),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.INDIGO_600,
                        shape=ft.RoundedRectangleBorder(radius=10),
                        padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                    ),
                    visible=is_admin,
                    on_click=self._open_add_dialog,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=16,
        )

    def load_data(self):
        try:
            self.all_students = get_all_students(actor=self.user)
            self._render_table(self.all_students)
        except Exception as err:
            self.table_container.controls = [ft.Text(f"Error loading students: {err}", color=ft.Colors.RED_400)]
            self.app_page.update()

    def _filter_students(self, _):
        query = (self.search_field.value or "").strip().lower()
        if not query:
            self._render_table(self.all_students)
            return

        filtered = [
            s for s in self.all_students
            if query in (s.get("name") or "").lower()
            or query in (s.get("student_id") or "").lower()
            or query in (s.get("course") or "").lower()
            or query in (s.get("room_number") or "").lower()
        ]
        self._render_table(filtered)

    def _render_table(self, students: list):
        colors = get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)

        if not students:
            self.table_container.controls = [
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.SEARCH_OFF_ROUNDED, size=40, color=colors["text_muted"]),
                            ft.Text("No students found matching your criteria.", color=colors["text_muted"]),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    alignment=ft.Alignment.CENTER,
                    padding=40,
                )
            ]
            self.app_page.update()
            return

        rows = []
        for s in students:
            is_active = (s.get("status") or "").lower() == "active"
            status_chip = ft.Container(
                content=ft.Text(
                    s.get("status") or "Active",
                    size=10,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREEN_500 if is_active else ft.Colors.RED_400,
                ),
                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                border_radius=12,
                bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.GREEN_500 if is_active else ft.Colors.RED_400),
            )

            actions = []
            sid_str = s.get("student_id") or ""
            sname_str = s.get("name") or ""
            has_room = bool(s.get("room_number"))

            if self.user.get("role") == "admin":
                # View details
                actions.append(
                    ft.IconButton(
                        icon=ft.Icons.BADGE_OUTLINED,
                        icon_size=18,
                        icon_color=ft.Colors.BLUE_400,
                        tooltip="View Student Details",
                        on_click=lambda e, stu=s: self._open_student_details_dialog(stu),
                    )
                )

                # Credentials / Login creation button
                actions.append(
                    ft.IconButton(
                        icon=ft.Icons.KEY_ROUNDED,
                        icon_size=18,
                        icon_color=ft.Colors.GREEN_400,
                        tooltip="Manage Login ID & Password",
                        on_click=lambda e, sid=sid_str, sname=sname_str: self._open_credentials_dialog(sid, sname),
                    )
                )

                if has_room:
                    actions.append(
                        ft.IconButton(
                            icon=ft.Icons.DOOR_BACK_DOOR_OUTLINED,
                            icon_size=18,
                            icon_color=ft.Colors.AMBER_500,
                            tooltip=f"Vacate Room {s['room_number']}",
                            on_click=lambda e, sid=sid_str, sname=sname_str: self._confirm_vacate_room(sid, sname),
                        )
                    )
                else:
                    actions.append(
                        ft.IconButton(
                            icon=ft.Icons.BED_ROUNDED,
                            icon_size=18,
                            icon_color=ft.Colors.INDIGO_400,
                            tooltip="Assign Room & Bed",
                            on_click=lambda e, sid=sid_str, sname=sname_str: self._open_allocate_dialog(sid, sname),
                        )
                    )

                actions.append(
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                        icon_size=18,
                        icon_color=ft.Colors.RED_400,
                        tooltip="Delete Student",
                        on_click=lambda e, sid=sid_str, sname=sname_str: self._confirm_delete_student(sid, sname),
                    )
                )

            if s.get("room_number"):
                room_cell = ft.Row(
                    controls=[
                        ft.Text(f"Room {s['room_number']}", weight=ft.FontWeight.BOLD),
                        ft.Container(
                            content=ft.Text(f"Bed #{s['bed_number']}", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_400),
                            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                            border_radius=6,
                            bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.INDIGO_400),
                        ),
                    ],
                    spacing=6,
                )
            else:
                room_cell = ft.Text("Unassigned", color=colors["text_muted"])

            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(s.get("student_id") or "—", weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(s.get("name") or "—", weight=ft.FontWeight.W_500)),
                        ft.DataCell(ft.Text(f"{s.get('course') or '—'} ({s.get('branch') or '—'})")),
                        ft.DataCell(room_cell),
                        ft.DataCell(ft.Text(s.get("phone") or "—")),
                        ft.DataCell(status_chip),
                        ft.DataCell(ft.Row(actions, spacing=2) if actions else ft.Text("—")),
                    ]
                )
            )

        table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("STUDENT ID", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
                ft.DataColumn(ft.Text("NAME", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
                ft.DataColumn(ft.Text("COURSE / BRANCH", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
                ft.DataColumn(ft.Text("ROOM ALLOCATION", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
                ft.DataColumn(ft.Text("PHONE", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
                ft.DataColumn(ft.Text("STATUS", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
                ft.DataColumn(ft.Text("ACTIONS", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
            ],
            rows=rows,
            border_radius=10,
            heading_row_color=colors["surface_alt"],
            column_spacing=18,
        )

        self.table_container.controls = [table]
        self.app_page.update()

    def _open_credentials_dialog(self, student_id: str, student_name: str):
        colors = get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)
        status_ok, creds = get_student_credentials(student_id, actor=self.user)
        if not status_ok:
            self._show_toast(f"Failed to fetch credentials: {creds}", is_err=True)
            return

        has_account = creds.get("has_account", False)
        curr_user = creds.get("username") or student_id
        curr_active = creds.get("is_active", True)

        username_field = ft.TextField(
            label="Student Login ID / Username",
            value=curr_user,
            border_radius=8,
            prefix_icon=ft.Icons.BADGE_ROUNDED,
            hint_text="e.g. STU100 or student username",
        )

        password_field = ft.TextField(
            label="Password (min 8 chars)",
            value="Student@123" if not has_account else "",
            hint_text="Enter password" if not has_account else "Enter new password to reset",
            password=True,
            can_reveal_password=True,
            border_radius=8,
            prefix_icon=ft.Icons.LOCK_ROUNDED,
        )

        active_switch = ft.Switch(
            label="Account Active (Can log in)",
            value=curr_active,
        )

        def generate_random_pass(_):
            new_pass = f"Student@{secrets.randbelow(9000) + 1000}"
            password_field.value = new_pass
            password_field.password = False
            self.app_page.update()

        gen_btn = ft.OutlinedButton(
            content=ft.Row([ft.Icon(ft.Icons.AUTO_FIX_HIGH_ROUNDED, size=14), ft.Text("Generate Password", size=11)], spacing=4),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            on_click=generate_random_pass,
        )

        status_badge = ft.Container(
            content=ft.Text(
                "Account Active: Student Can Login" if has_account else "No Login Created Yet",
                size=11,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.GREEN_400 if has_account else ft.Colors.AMBER_400,
            ),
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            border_radius=8,
            bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.GREEN_400 if has_account else ft.Colors.AMBER_400),
        )

        def save_creds(_):
            uname = (username_field.value or "").strip()
            pwd = password_field.value or ""
            if not uname:
                self._show_toast("Username / Login ID is required.", is_err=True)
                return
            if not pwd:
                self._show_toast("Please enter a password for this student.", is_err=True)
                return
            if len(pwd) < 8:
                self._show_toast("Password must be at least 8 characters long.", is_err=True)
                return

            dlg.open = False
            self.app_page.update()

            ok, res_msg = create_or_update_student_credentials(
                student_id=student_id,
                username=uname,
                password=pwd,
                actor=self.user,
                is_active=active_switch.value,
            )
            if ok:
                self._show_toast(f"Credentials saved! Username: {uname} | Password: {pwd}")
            else:
                self._show_toast(f"Failed: {res_msg}", is_err=True)

        dlg = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.KEY_ROUNDED, color=ft.Colors.GREEN_400, size=24),
                    ft.Text("Student Login Credentials", weight=ft.FontWeight.BOLD, size=18),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(f"Student: {student_name} ({student_id})", size=13, weight=ft.FontWeight.BOLD),
                                status_badge,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Text(
                            "Both Admin and Students sign in through the same login page. Admin creates the ID and password for the student.",
                            size=11,
                            color=colors["text_muted"],
                        ),
                        ft.Container(height=4),
                        username_field,
                        password_field,
                        ft.Row([gen_btn], alignment=ft.MainAxisAlignment.END),
                        active_switch,
                    ],
                    spacing=8,
                ),
                width=440,
                height=320,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self._close_dialog(dlg)),
                ft.FilledButton("Save Credentials", bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE, on_click=save_creds),
            ],
        )
        self.app_page.overlay.append(dlg)
        dlg.open = True
        self.app_page.update()

    def _open_student_details_dialog(self, student: dict):
        colors = get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)

        items = [
            ("Student ID", student.get("student_id")),
            ("Full Name", student.get("name")),
            ("Course", student.get("course")),
            ("Branch", student.get("branch")),
            ("Academic Year", f"Year {student.get('year')}" if student.get("year") else "—"),
            ("Room Number", f"Room {student.get('room_number')}" if student.get("room_number") else "Not Assigned"),
            ("Bed Number", f"Bed #{student.get('bed_number')}" if student.get("bed_number") else "—"),
            ("Phone", student.get("phone")),
            ("Email", student.get("email")),
            ("Parent/Guardian", student.get("parent_name")),
            ("Status", student.get("status") or "Active"),
        ]

        rows = []
        for label, val in items:
            rows.append(
                ft.Row(
                    controls=[
                        ft.Text(label, size=12, color=colors["text_muted"], width=130),
                        ft.Text(str(val or "—"), size=12, weight=ft.FontWeight.W_600, expand=True),
                    ],
                )
            )

        dlg = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.BADGE_ROUNDED, color=ft.Colors.INDIGO_400),
                    ft.Text(f"Student: {student.get('name')}", weight=ft.FontWeight.BOLD, size=18),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=ft.Column(controls=rows, spacing=8),
                width=400,
                height=300,
            ),
            actions=[
                ft.FilledButton("Close", on_click=lambda _: self._close_dialog(dlg)),
            ],
        )
        self.app_page.overlay.append(dlg)
        dlg.open = True
        self.app_page.update()

    def _open_allocate_dialog(self, student_id: str, student_name: str):
        colors = get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)

        rooms = get_all_rooms(actor=self.user)
        avail_rooms = [r for r in rooms if r[5] > 0]
        room_opts = [
            ft.dropdown.Option(
                key=str(r[1]),
                text=f"Room {r[1]} (Floor {r[2]} · {r[5]} beds free)",
            )
            for r in avail_rooms
        ]

        if not room_opts:
            self._show_toast("No rooms with available beds found. Please add or vacate a room first.", is_err=True)
            return

        room_dropdown = ft.Dropdown(
            label="Select Room (with free beds)",
            options=room_opts,
            value=room_opts[0].key if room_opts else None,
            border_radius=8,
            expand=True,
        )

        dlg = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.BED_ROUNDED, color=ft.Colors.INDIGO_600, size=24),
                    ft.Text("Assign Room & Bed", weight=ft.FontWeight.BOLD, size=18),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(f"Assigning room for: {student_name} ({student_id})", size=13, weight=ft.FontWeight.BOLD),
                        room_dropdown,
                        ft.Text("Bed number will be automatically allocated to the lowest free bed in the room.", size=11, color=colors["text_muted"]),
                    ],
                    spacing=12,
                ),
                width=380,
                height=160,
            ),
            actions=[
                ft.TextButton(content="Cancel", on_click=lambda _: self._close_dialog(dlg)),
                ft.FilledButton(
                    content="Assign Bed",
                    bgcolor=ft.Colors.INDIGO_600,
                    color=ft.Colors.WHITE,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=lambda _: self._submit_allocation(dlg, student_id, room_dropdown.value),
                ),
            ],
        )
        self.app_page.overlay.append(dlg)
        dlg.open = True
        self.app_page.update()

    def _submit_allocation(self, dlg, sid, rnum):
        if not rnum:
            self._show_toast("Please select a room.", is_err=True)
            return
        try:
            success, msg = allocate_room(student_id=sid, room_number=rnum, actor=self.user)
            if success:
                dlg.open = False
                self.load_data()
                self._show_toast(msg)
            else:
                self._show_toast(f"Failed: {msg}", is_err=True)
        except Exception as e:
            self._show_toast(f"Error: {e}", is_err=True)

    def _confirm_vacate_room(self, student_id: str, student_name: str):
        def do_vacate(_):
            dlg.open = False
            try:
                success, msg = deallocate_room(student_id=student_id, actor=self.user)
                if success:
                    self.load_data()
                    self._show_toast(f"Room vacated successfully for {student_name}.")
                else:
                    self._show_toast(f"Vacate Failed: {msg}", is_err=True)
            except Exception as e:
                self._show_toast(f"Error: {e}", is_err=True)

        dlg = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.DOOR_BACK_DOOR_OUTLINED, color=ft.Colors.AMBER_500, size=24),
                    ft.Text("Confirm Room Vacate", weight=ft.FontWeight.BOLD, size=18),
                ],
                spacing=8,
            ),
            content=ft.Text(f"Are you sure you want to vacate the room for {student_name} ({student_id})?"),
            actions=[
                ft.OutlinedButton("Cancel", on_click=lambda _: self._close_dialog(dlg)),
                ft.FilledButton("Yes, Vacate", bgcolor=ft.Colors.AMBER_600, color=ft.Colors.WHITE, on_click=do_vacate),
            ],
        )
        self.app_page.overlay.append(dlg)
        dlg.open = True
        self.app_page.update()

    def _confirm_delete_student(self, student_id: str, student_name: str):
        content_text = ft.Text(f"Are you sure you want to delete student {student_name} ({student_id})?", size=14)

        def do_delete(cascade=False):
            dlg.open = False
            self.app_page.update()
            success, msg = delete_student(student_id, actor=self.user, cascade=cascade)
            if success:
                self.load_data()
                self._show_toast(f"Student {student_name} deleted successfully.")
            else:
                if "linked" in msg.lower() and not cascade:
                    self._confirm_force_delete(student_id, student_name, msg)
                else:
                    self._show_toast(f"Delete Failed: {msg}", is_err=True)

        dlg = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.DELETE_OUTLINE_ROUNDED, color=ft.Colors.RED_500, size=24),
                    ft.Text("Confirm Delete Student", weight=ft.FontWeight.BOLD, size=18),
                ],
                spacing=8,
            ),
            content=content_text,
            actions=[
                ft.OutlinedButton("Cancel", on_click=lambda _: self._close_dialog(dlg)),
                ft.FilledButton(
                    "Yes, Delete",
                    bgcolor=ft.Colors.RED_600,
                    color=ft.Colors.WHITE,
                    on_click=lambda _: do_delete(cascade=False),
                ),
            ],
        )
        self.app_page.overlay.append(dlg)
        dlg.open = True
        self.app_page.update()

    def _confirm_force_delete(self, student_id: str, student_name: str, reason: str):
        def do_force_delete(_):
            dlg.open = False
            self.app_page.update()
            success, msg = delete_student(student_id, actor=self.user, cascade=True)
            if success:
                self.load_data()
                self._show_toast(f"Student {student_name} and all linked records deleted.")
            else:
                self._show_toast(f"Force Delete Failed: {msg}", is_err=True)

        dlg = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.AMBER_600, size=24),
                    ft.Text("Linked Records Found", weight=ft.FontWeight.BOLD, size=18),
                ],
                spacing=8,
            ),
            content=ft.Column(
                controls=[
                    ft.Text(f"{student_name} ({student_id}) has existing records in the system:", size=13),
                    ft.Container(
                        content=ft.Text(reason, size=12, color=ft.Colors.RED_400, weight=ft.FontWeight.W_500),
                        padding=10,
                        border_radius=8,
                        bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.RED_400),
                    ),
                    ft.Text("Do you want to permanently delete this student along with all their linked records?", size=13),
                ],
                spacing=10,
                tight=True,
            ),
            actions=[
                ft.OutlinedButton("Cancel", on_click=lambda _: self._close_dialog(dlg)),
                ft.FilledButton(
                    "Force Delete All Records",
                    bgcolor=ft.Colors.RED_700,
                    color=ft.Colors.WHITE,
                    on_click=do_force_delete,
                ),
            ],
        )
        self.app_page.overlay.append(dlg)
        dlg.open = True
        self.app_page.update()

    def _open_add_dialog(self, _):
        # 1. Student Identity & Contact
        sid_field = ft.TextField(label="Student ID (e.g. STU100)", border_radius=8, expand=True)
        name_field = ft.TextField(label="Full Name", border_radius=8, expand=True)
        phone_field = ft.TextField(
            label="Phone Number (10 digits)",
            hint_text="e.g. 9876543210",
            max_length=10,
            border_radius=8,
            expand=True,
        )
        email_field = ft.TextField(
            label="Email Address (@gmail.com)",
            hint_text="name@gmail.com",
            border_radius=8,
            expand=True,
        )

        # 2. Academic Credentials
        course_field = ft.TextField(label="Course (e.g. B.Tech, HM, BCA)", border_radius=8, expand=True)
        branch_field = ft.TextField(label="Branch / Specialization (e.g. CSE, BHM)", border_radius=8, expand=True)
        year_dropdown = ft.Dropdown(
            label="Current Academic Year",
            value="1",
            options=[
                ft.dropdown.Option("1", "Year 1"),
                ft.dropdown.Option("2", "Year 2"),
                ft.dropdown.Option("3", "Year 3"),
                ft.dropdown.Option("4", "Year 4"),
            ],
            border_radius=8,
            expand=True,
        )
        admission_date_field = ft.TextField(
            label="Admission Date (YYYY-MM-DD)",
            value=datetime.now().strftime("%Y-%m-%d"),
            hint_text="YYYY-MM-DD",
            prefix_icon=ft.Icons.CALENDAR_MONTH_ROUNDED,
            border_radius=8,
            expand=True,
        )
        attach_date_picker(admission_date_field, self.app_page, first_date=datetime(2015, 1, 1), last_date=datetime(2035, 12, 31))

        # 3. Guardian & Emergency Information
        parent_name_field = ft.TextField(
            label="Parent / Guardian Name",
            hint_text="e.g. Mr. Sharma / Legal Guardian",
            border_radius=8,
            expand=True,
        )

        # 4. Student Login Credentials
        create_login_chk = ft.Checkbox(label="Create Student Login ID & Password now", value=True)
        login_pass_field = ft.TextField(
            label="Student Password (Min 8 chars)",
            value="Student@123",
            password=True,
            can_reveal_password=True,
            border_radius=8,
        )

        dlg = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.PERSON_ADD_ALT_1_ROUNDED, color=ft.Colors.INDIGO_500, size=24),
                    ft.Text("Add New Student", weight=ft.FontWeight.BOLD, size=18),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        # Section: Student Identity & Contact
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.BADGE_ROUNDED, size=16, color=ft.Colors.PURPLE_400),
                                ft.Text("Student Identity & Contact", weight=ft.FontWeight.BOLD, size=13),
                            ],
                            spacing=6,
                        ),
                        ft.Row(controls=[sid_field, name_field], spacing=10),
                        ft.Row(controls=[phone_field, email_field], spacing=10),
                        ft.Divider(height=16),

                        # Section: Academic Credentials
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.SCHOOL_ROUNDED, size=16, color=ft.Colors.INDIGO_400),
                                ft.Text("Academic Credentials", weight=ft.FontWeight.BOLD, size=13),
                            ],
                            spacing=6,
                        ),
                        ft.Row(controls=[course_field, branch_field], spacing=10),
                        ft.Row(controls=[year_dropdown, admission_date_field], spacing=10),
                        ft.Divider(height=16),

                        # Section: Guardian & Emergency Information
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.FAMILY_RESTROOM_ROUNDED, size=16, color=ft.Colors.GREEN_500),
                                ft.Text("Guardian & Emergency Information", weight=ft.FontWeight.BOLD, size=13),
                            ],
                            spacing=6,
                        ),
                        ft.Row(controls=[parent_name_field], spacing=10),
                        ft.Divider(height=16),

                        # Section: Login Account
                        create_login_chk,
                        login_pass_field,
                    ],
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=500,
                height=480,
            ),
            actions=[
                ft.TextButton(content="Cancel", on_click=lambda _: self._close_dialog(dlg)),
                ft.FilledButton(
                    "Save Student",
                    bgcolor=ft.Colors.INDIGO_600,
                    color=ft.Colors.WHITE,
                    on_click=lambda _: self._save_new_student(
                        dlg,
                        sid_field.value,
                        name_field.value,
                        course_field.value,
                        branch_field.value,
                        year_dropdown.value,
                        admission_date_field.value,
                        parent_name_field.value,
                        phone_field.value,
                        email_field.value,
                        create_login_chk.value,
                        login_pass_field.value,
                    ),
                ),
            ],
        )
        self.app_page.overlay.append(dlg)
        dlg.open = True
        self.app_page.update()

    def _close_dialog(self, dlg):
        dlg.open = False
        self.app_page.update()

    def _show_invalid_phone_dialog(self, reason: str):
        err_dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.PHONE_ANDROID_ROUNDED, color=ft.Colors.RED_500, size=24),
                    ft.Text("Invalid Phone Number", weight=ft.FontWeight.BOLD, size=16),
                ],
                spacing=10,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "Mobile number validation failed!",
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.RED_600,
                        ),
                        ft.Text(
                            reason,
                            size=12,
                        ),
                    ],
                    spacing=8,
                    tight=True,
                ),
                width=380,
            ),
            actions=[
                ft.FilledButton(
                    "OK",
                    bgcolor=ft.Colors.INDIGO_600,
                    on_click=lambda _: self._close_dialog(err_dlg),
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.app_page.overlay.append(err_dlg)
        err_dlg.open = True
        self.app_page.update()

    def _show_invalid_email_dialog(self, reason: str):
        err_dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.MAIL_OUTLINE_ROUNDED, color=ft.Colors.RED_500, size=24),
                    ft.Text("Invalid Gmail Address", weight=ft.FontWeight.BOLD, size=16),
                ],
                spacing=10,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "Real Gmail address validation failed!",
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.RED_600,
                        ),
                        ft.Text(
                            reason,
                            size=12,
                        ),
                    ],
                    spacing=8,
                    tight=True,
                ),
                width=380,
            ),
            actions=[
                ft.FilledButton(
                    "OK",
                    bgcolor=ft.Colors.INDIGO_600,
                    on_click=lambda _: self._close_dialog(err_dlg),
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.app_page.overlay.append(err_dlg)
        err_dlg.open = True
        self.app_page.update()

    def _validate_real_gmail(self, email_val: str) -> tuple[bool, str]:
        from utils.validators import validate_real_gmail
        try:
            val = validate_real_gmail(email_val)
            return True, val
        except ValueError as e:
            return False, str(e)

    def _validate_phone_10_digits(self, phone_val: str) -> tuple[bool, str]:
        from utils.validators import validate_real_mobile_phone
        try:
            val = validate_real_mobile_phone(phone_val)
            return True, val
        except ValueError as e:
            return False, str(e)

    def _save_new_student(
        self, dlg, sid, name, course, branch, year, adm_date, parent_name,
        phone, email, create_login, login_password
    ):
        # 1. Strict 10-digit Phone Validation
        phone_ok, phone_err = self._validate_phone_10_digits(phone)
        if not phone_ok:
            self._show_invalid_phone_dialog(phone_err)
            return

        # 2. Strict Real Gmail Format Validation
        email_ok, email_err = self._validate_real_gmail(email)
        if not email_ok:
            self._show_invalid_email_dialog(email_err)
            return

        email_val = str(email or "").strip().lower()

        # Parse year and admission date
        parsed_year = int(year) if year and str(year).isdigit() else 1
        parsed_adm_date = str(adm_date or "").strip() or None
        parsed_parent = str(parent_name or "").strip() or None

        try:
            success, msg = add_student(
                student_id=sid,
                name=name,
                course=course,
                branch=branch,
                year=parsed_year,
                admission_date=parsed_adm_date,
                parent_name=parsed_parent,
                phone=str(phone).strip(),
                email=email_val,
                actor=self.user,
            )
        except Exception as e:
            self._show_toast(f"Failed: {e}", is_err=True)
            return

        if success:
            extra_msg = ""
            if create_login and login_password:
                try:
                    ok, c_msg = create_or_update_student_credentials(
                        student_id=sid,
                        username=sid,
                        password=login_password,
                        actor=self.user,
                    )
                    if ok:
                        extra_msg = f" Login created: ID={sid}, Pass={login_password}."
                    else:
                        extra_msg = f" (Login account warning: {c_msg})"
                except Exception as c_err:
                    extra_msg = f" (Login account error: {c_err})"

            dlg.open = False
            self.load_data()
            self._show_toast(f"Student added successfully!{extra_msg}")
        else:
            self._show_toast(f"Failed: {msg}", is_err=True)

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
