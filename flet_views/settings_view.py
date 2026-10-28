"""Modern SaaS Settings & Profile Management View built with Flet."""

import flet as ft
from database import get_connection
from services.auth_service import hash_password, verify_password
from utils.validators import validate_email, validate_password, validate_real_mobile_phone, validate_real_gmail
from flet_views.theme import get_colors, attach_date_picker
from datetime import datetime


class SettingsSubView(ft.Column):
    def __init__(self, page: ft.Page, user: dict, toggle_theme_fn=None, on_logout=None):
        super().__init__()
        self.app_page = page
        self.user = user
        self.toggle_theme_fn = toggle_theme_fn
        self.on_logout = on_logout
        self.expand = True
        self.spacing = 16

        self.content_container = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=16)

        self.controls = [
            self._build_header(),
            ft.Container(
                content=self.content_container,
                expand=True,
                padding=24,
                border_radius=14,
                bgcolor=get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)["surface"],
                border=ft.Border.all(1, get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)["border"]),
            ),
        ]
        self._load_data()

    def _build_header(self) -> ft.Control:
        colors = get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)

        logout_button = ft.OutlinedButton(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.LOGOUT_ROUNDED, size=16, color=ft.Colors.RED_500),
                    ft.Text("Logout", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_500),
                ],
                spacing=6,
            ),
            style=ft.ButtonStyle(
                side=ft.BorderSide(1, ft.Colors.RED_400),
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding.symmetric(horizontal=16, vertical=10),
            ),
            tooltip="Sign out of your account",
            on_click=lambda _: self._confirm_logout(),
        )

        return ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("Account Settings & Profile", size=22, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            "Manage your personal details, credentials, and system preferences",
                            size=12,
                            color=colors["text_muted"],
                        ),
                    ],
                    spacing=2,
                    expand=True,
                ),
                logout_button,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _confirm_logout(self):
        """Shows a confirmation popup before logging the user out."""
        def do_logout(_):
            dlg.open = False
            self.app_page.update()
            if self.on_logout:
                self.on_logout()

        def cancel_logout(_):
            dlg.open = False
            self.app_page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.LOGOUT_ROUNDED, color=ft.Colors.RED_500, size=24),
                    ft.Text("Confirm Logout", weight=ft.FontWeight.BOLD, size=18),
                ],
                spacing=10,
            ),
            content=ft.Text(
                "Are you sure you want to logout?",
                size=14,
            ),
            actions=[
                ft.OutlinedButton(
                    "No",
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8),
                        padding=ft.Padding.symmetric(horizontal=16, vertical=8),
                    ),
                    on_click=cancel_logout,
                ),
                ft.FilledButton(
                    "Yes",
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.RED_600,
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=8),
                        padding=ft.Padding.symmetric(horizontal=16, vertical=8),
                    ),
                    on_click=do_logout,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.app_page.overlay.append(dlg)
        dlg.open = True
        self.app_page.update()

    def _load_data(self):
        is_dark = self.app_page.theme_mode == ft.ThemeMode.DARK
        colors = get_colors(is_dark)

        role = self.user.get("role", "student")

        # Fetch latest details from DB
        student_info = None
        conn = get_connection()
        try:
            curr_user = conn.execute(
                "SELECT username, email, full_name, phone FROM users WHERE id = ?", (self.user["id"],)
            ).fetchone()
            if curr_user:
                self.user["username"] = curr_user[0] or self.user.get("username", "")
                self.user["email"] = curr_user[1] or self.user.get("email", "")
                self.user["full_name"] = curr_user[2] or self.user.get("full_name", "")
                self.user["phone"] = curr_user[3] or self.user.get("phone", "")

            if role == "student":
                student_info = conn.execute(
                    """
                    SELECT student_id, name, course, branch, year, phone,
                           admission_date, status, room_number, bed_number,
                           gender, date_of_birth, address, parent_name
                    FROM students
                    WHERE lower(trim(email)) = lower(trim(?)) OR student_id = ?
                    LIMIT 1
                    """,
                    (self.user.get("email", ""), self.user.get("username", "")),
                ).fetchone()
        finally:
            conn.close()

        # ── 1. Hero Identity Card ──────────────────────────────────────────
        name_display = self.user.get("full_name") or self.user.get("username", "User")
        if student_info and student_info[1]:
            name_display = student_info[1]

        # Calculate initials from display name
        words = [w for w in name_display.split() if w]
        if len(words) >= 2:
            initials = (words[0][0] + words[1][0]).upper()
        elif len(words) == 1:
            initials = words[0][:2].upper()
        else:
            initials = (self.user.get("username") or "?")[:2].upper()

        hero_card = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(initials, size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        width=68,
                        height=68,
                        border_radius=34,
                        bgcolor=ft.Colors.INDIGO_600,
                        alignment=ft.Alignment.CENTER,
                    ),
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(name_display, size=20, weight=ft.FontWeight.BOLD),
                                    ft.Container(
                                        content=ft.Text(role.upper(), size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_400),
                                        padding=ft.Padding.symmetric(horizontal=10, vertical=3),
                                        border_radius=12,
                                        bgcolor=colors["accent_soft"],
                                    ),
                                ],
                                spacing=10,
                            ),
                            ft.Text(
                                f"Username: @{self.user['username']} · Email: {self.user.get('email', 'N/A')}",
                                size=12,
                                color=colors["text_muted"],
                            ),
                        ],
                        spacing=3,
                        expand=True,
                    ),
                ],
                spacing=18,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=20,
            border_radius=12,
            bgcolor=colors["surface_alt"],
        )

        # ── 2. Student Info Card (if student) ──────────────────────────────
        student_section = None
        if student_info:
            sid, sname, course, branch, yr, phone, adm_date, status, rnum, bnum = student_info[:10]
            room_text = f"Room {rnum} (Bed #{bnum})" if rnum else "No Room Assigned"

            student_section = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Academic & Hostel Allocation", size=15, weight=ft.FontWeight.BOLD),
                        ft.Row(
                            controls=[
                                self._info_box("Student ID", sid or "—", colors),
                                self._info_box("Course / Branch", f"{course or '—'} ({branch or '—'})", colors),
                                self._info_box("Year", f"Year {yr or 1}", colors),
                                self._info_box("Room & Bed", room_text, colors),
                            ],
                            spacing=12,
                        ),
                    ],
                    spacing=10,
                ),
                padding=18,
                border_radius=12,
                bgcolor=colors["surface_alt"],
            )

        # ── 3. Edit Personal & Contact Information ─────────────────────────
        card_title = "Admin Profile & Display Name" if role == "admin" else "Student Personal & Contact Details"
        btn_label = "Save Profile & Name" if role == "admin" else "Save Personal Details"

        self.name_input = ft.TextField(
            label="Admin Full Name" if role == "admin" else "Student Full Name",
            value=self.user.get("full_name") or (student_info[1] if student_info and student_info[1] else ""),
            hint_text="e.g. Karan Das",
            prefix_icon=ft.Icons.BADGE_ROUNDED if role == "admin" else ft.Icons.PERSON_ROUNDED,
            border_radius=8,
            expand=True,
        )
        self.email_input = ft.TextField(
            label="Email Address (@gmail.com)",
            value=self.user.get("email") or "",
            hint_text="name@gmail.com",
            prefix_icon=ft.Icons.EMAIL_ROUNDED,
            border_radius=8,
            expand=True,
        )
        self.phone_input = ft.TextField(
            label="Mobile Phone Number (10 digits)",
            value=self.user.get("phone") or (student_info[5] if student_info and student_info[5] else ""),
            hint_text="e.g. 9876543210",
            max_length=10,
            prefix_icon=ft.Icons.PHONE_ANDROID_ROUNDED,
            border_radius=8,
            expand=True,
        )

        edit_controls = [
            ft.Row(
                controls=[
                    ft.Icon(ft.Icons.MANAGE_ACCOUNTS_ROUNDED, color=ft.Colors.INDIGO_500, size=20),
                    ft.Text(card_title, size=15, weight=ft.FontWeight.BOLD),
                ],
                spacing=8,
            ),
            ft.Text(
                "Update your identity, contact information, and personal details.",
                size=11,
                color=colors["text_muted"],
            ),
            ft.Row(controls=[self.name_input, self.email_input], spacing=14),
            ft.Row(controls=[self.phone_input], spacing=14),
        ]

        if role == "student":
            gender_val = student_info[10] if (student_info and len(student_info) > 10 and student_info[10]) else "Male"
            dob_val = student_info[11] if (student_info and len(student_info) > 11 and student_info[11]) else ""
            addr_val = student_info[12] if (student_info and len(student_info) > 12 and student_info[12]) else ""
            parent_val = student_info[13] if (student_info and len(student_info) > 13 and student_info[13]) else ""

            self.gender_input = ft.Dropdown(
                label="Gender",
                value=gender_val,
                options=[
                    ft.dropdown.Option("Male"),
                    ft.dropdown.Option("Female"),
                    ft.dropdown.Option("Other"),
                ],
                border_radius=8,
                expand=True,
            )
            self.dob_input = ft.TextField(
                label="Date of Birth (YYYY-MM-DD)",
                value=dob_val,
                hint_text="e.g. 2004-05-15",
                prefix_icon=ft.Icons.CALENDAR_MONTH_ROUNDED,
                border_radius=8,
                expand=True,
            )
            attach_date_picker(self.dob_input, self.app_page, first_date=datetime(1970, 1, 1), last_date=datetime(2025, 12, 31))
            self.parent_input = ft.TextField(
                label="Parent / Guardian Name",
                value=parent_val,
                hint_text="e.g. Mr. Sharma",
                prefix_icon=ft.Icons.FAMILY_RESTROOM_ROUNDED,
                border_radius=8,
                expand=True,
            )
            self.address_input = ft.TextField(
                label="Permanent Address",
                value=addr_val,
                hint_text="e.g. 123 Main Street, City",
                prefix_icon=ft.Icons.HOME_ROUNDED,
                border_radius=8,
                multiline=True,
                min_lines=2,
                max_lines=3,
            )

            edit_controls.extend([
                ft.Row(controls=[self.gender_input, self.dob_input], spacing=14),
                ft.Row(controls=[self.parent_input], spacing=14),
                ft.Row(controls=[self.address_input], spacing=14),
            ])

        edit_controls.append(
            ft.FilledButton(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.SAVE_ROUNDED, size=16),
                        ft.Text(btn_label, size=13, weight=ft.FontWeight.BOLD),
                    ],
                    spacing=6,
                ),
                bgcolor=ft.Colors.INDIGO_600,
                color=ft.Colors.WHITE,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=8),
                    padding=ft.Padding.symmetric(horizontal=18, vertical=12),
                ),
                on_click=self._save_contact_info,
            )
        )

        personal_edit_card = ft.Container(
            content=ft.Column(controls=edit_controls, spacing=12),
            padding=20,
            border_radius=12,
            bgcolor=colors["surface_alt"],
        )

        # ── 4. Change Password Card ───────────────────────────────────────
        self.curr_pw = ft.TextField(label="Current Password", password=True, can_reveal_password=True, border_radius=8)
        self.new_pw = ft.TextField(label="New Password", password=True, can_reveal_password=True, border_radius=8)
        self.conf_pw = ft.TextField(label="Confirm New Password", password=True, can_reveal_password=True, border_radius=8)

        password_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Security & Password", size=15, weight=ft.FontWeight.BOLD),
                    self.curr_pw,
                    self.new_pw,
                    self.conf_pw,
                    ft.FilledButton(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.LOCK_RESET_ROUNDED, size=16),
                                ft.Text("Update Password", size=13, weight=ft.FontWeight.BOLD),
                            ],
                            spacing=6,
                        ),
                        bgcolor=ft.Colors.INDIGO_600,
                        color=ft.Colors.WHITE,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                        on_click=self._change_password,
                    ),
                ],
                spacing=12,
            ),
            padding=20,
            border_radius=12,
            bgcolor=colors["surface_alt"],
        )

        if role == "admin":
            password_card.expand = True
            self.curr_user_display = ft.TextField(
                label="Current Login Username",
                value=self.user.get("username", "admin"),
                read_only=True,
                border_radius=8,
                prefix_icon=ft.Icons.PERSON_ROUNDED,
            )
            self.new_user_input = ft.TextField(
                label="New Login Username",
                hint_text="e.g. admin_main (3-50 chars)",
                border_radius=8,
                prefix_icon=ft.Icons.BADGE_ROUNDED,
            )
            self.admin_user_pw = ft.TextField(
                label="Admin Password (to verify)",
                hint_text="Enter current admin password",
                helper="Enter current admin password to verify identity",
                password=True,
                can_reveal_password=True,
                border_radius=8,
                prefix_icon=ft.Icons.LOCK_ROUNDED,
            )
            username_card = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Admin Login Username", size=15, weight=ft.FontWeight.BOLD),
                        self.curr_user_display,
                        self.new_user_input,
                        self.admin_user_pw,
                        ft.FilledButton(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.CHANGE_CIRCLE_ROUNDED, size=16),
                                    ft.Text("Update Username", size=13, weight=ft.FontWeight.BOLD),
                                ],
                                spacing=6,
                            ),
                            bgcolor=ft.Colors.INDIGO_600,
                            color=ft.Colors.WHITE,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                            on_click=self._change_admin_username,
                        ),
                    ],
                    spacing=12,
                ),
                padding=20,
                border_radius=12,
                bgcolor=colors["surface_alt"],
                expand=True,
            )
            security_section = ft.Row(
                controls=[password_card, username_card],
                spacing=16,
                vertical_alignment=ft.CrossAxisAlignment.START,
            )
        else:
            security_section = password_card

        # ── 5. System Specs Card ──────────────────────────────────────────
        sys_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.INFO_ROUNDED, size=20, color=ft.Colors.BLUE_500),
                            ft.Text("About Hostel Management Desktop", size=14, weight=ft.FontWeight.BOLD),
                        ],
                        spacing=8,
                    ),
                    ft.Divider(height=1, color=colors["border"]),
                    ft.Text("UI Framework: Flet (Google Flutter Engine - Skia/Impeller)", size=12),
                    ft.Text("Database: SQLite with transaction isolation & role-based scoping", size=12),
                    ft.Text("Display: Hardware Accelerated 60-120 FPS · Zero Flicker", size=12),
                    ft.Text("Version: 2.0.0 (SaaS Edition)", size=12, color=colors["text_muted"]),
                ],
                spacing=8,
            ),
            padding=20,
            border_radius=12,
            bgcolor=colors["surface_alt"],
        )

        # Assemble all sections (Appearance switch removed since theme toggle is available on top dashboard)
        cards = [hero_card]
        if student_section:
            cards.append(student_section)
        cards.extend([personal_edit_card, security_section, sys_card])

        self.content_container.controls = cards
        self.app_page.update()

    def _change_admin_username(self, _):
        new_uname = (self.new_user_input.value or "").strip()
        pw = (self.admin_user_pw.value or "").strip()

        if not new_uname:
            self._show_toast("Please enter a new username.", is_err=True)
            return

        from utils.validators import validate_username
        try:
            new_uname = validate_username(new_uname)
        except ValueError as err:
            self._show_toast(str(err), is_err=True)
            return

        if not pw:
            self._show_toast("Please enter your current admin password to confirm.", is_err=True)
            return

        conn = get_connection()
        try:
            curr_row = conn.execute("SELECT password_hash FROM users WHERE id = ?", (self.user["id"],)).fetchone()
            if not curr_row or not verify_password(pw, curr_row[0]):
                self._show_toast("Incorrect admin password.", is_err=True)
                return

            # Check if username already exists
            dup = conn.execute(
                "SELECT id FROM users WHERE lower(username) = lower(?) AND id != ?",
                (new_uname, self.user["id"])
            ).fetchone()
            if dup:
                self._show_toast(f"Username '{new_uname}' is already in use by another account.", is_err=True)
                return

            conn.execute("UPDATE users SET username = ? WHERE id = ?", (new_uname, self.user["id"]))
            conn.commit()

            self.user["username"] = new_uname
            self.new_user_input.value = ""
            self.admin_user_pw.value = ""

            for c in self.app_page.controls:
                if hasattr(c, "update_user_badge"):
                    c.update_user_badge()

            self._show_toast(f"Login username changed to '@{new_uname}' successfully!")
            self._load_data()
        except Exception as e:
            self._show_toast(f"Update failed: {e}", is_err=True)
        finally:
            conn.close()

    def _info_box(self, label: str, val: str, colors: dict) -> ft.Control:
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(label.upper(), size=9, weight=ft.FontWeight.BOLD, color=colors["text_muted"]),
                    ft.Text(val, size=13, weight=ft.FontWeight.BOLD),
                ],
                spacing=2,
            ),
            expand=True,
            padding=12,
            border_radius=8,
            bgcolor=colors["surface_alt"],
        )

    def _save_contact_info(self, _):
        name = (self.name_input.value or "").strip()
        email = (self.email_input.value or "").strip()
        phone = (self.phone_input.value or "").strip()

        # 1. Name validation - cannot be empty
        if not name or len(name) < 2:
            self._show_toast("Name cannot be empty! Please enter your full name (minimum 2 characters).", is_err=True)
            return

        # 2. Email validation - cannot be empty and must be valid real Gmail
        try:
            email = validate_real_gmail(email)
        except ValueError as e:
            self._show_toast(str(e), is_err=True)
            return

        # 3. Phone validation - cannot be empty and must be valid 10-digit mobile number
        try:
            phone = validate_real_mobile_phone(phone)
        except ValueError as e:
            self._show_toast(str(e), is_err=True)
            return

        conn = get_connection()
        try:
            dup = conn.execute(
                "SELECT id FROM users WHERE lower(email) = lower(?) AND id != ?",
                (email, self.user["id"]),
            ).fetchone()
            if dup:
                self._show_toast("This email is already in use by another account.", is_err=True)
                return

            conn.execute(
                "UPDATE users SET full_name = ?, email = ?, phone = ? WHERE id = ?",
                (name, email, phone, self.user["id"]),
            )
            if self.user.get("role") == "student":
                gender = getattr(self, "gender_input", None) and self.gender_input.value
                dob = getattr(self, "dob_input", None) and (self.dob_input.value or "").strip()
                address = getattr(self, "address_input", None) and (self.address_input.value or "").strip()
                parent_name = getattr(self, "parent_input", None) and (self.parent_input.value or "").strip()

                conn.execute(
                    """UPDATE students 
                       SET name = ?, email = ?, phone = ?, gender = ?, date_of_birth = ?, address = ?, parent_name = COALESCE(?, parent_name)
                       WHERE lower(trim(email)) = lower(trim(?)) OR student_id = ?""",
                    (name, email, phone, gender or None, dob or None, address or None, parent_name or None, self.user.get("email", ""), self.user.get("username", "")),
                )
            conn.commit()

            self.user["full_name"] = name
            self.user["email"] = email
            self.user["phone"] = phone

            # Immediately update bottom-left user badge on DashboardView
            for c in self.app_page.controls:
                if hasattr(c, "update_user_badge"):
                    c.update_user_badge()

            self._show_toast("Profile & Name successfully updated!")
            self._load_data()
        except Exception as e:
            self._show_toast(f"Update failed: {e}", is_err=True)
        finally:
            conn.close()

    def _change_password(self, _):
        curr = (self.curr_pw.value or "").strip()
        new_p = (self.new_pw.value or "").strip()
        conf = (self.conf_pw.value or "").strip()

        if not curr or not new_p or not conf:
            self._show_toast("Please fill all password fields.", is_err=True)
            return

        if new_p != conf:
            self._show_toast("New password and confirmation do not match.", is_err=True)
            return

        try:
            validate_password(new_p)
        except ValueError as e:
            self._show_toast(str(e), is_err=True)
            return

        conn = get_connection()
        try:
            stored_hash = conn.execute(
                "SELECT password_hash FROM users WHERE id = ?", (self.user["id"],)
            ).fetchone()
            if not stored_hash or not verify_password(curr, stored_hash[0]):
                self._show_toast("Current password is incorrect.", is_err=True)
                return

            new_hashed = hash_password(new_p)
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (new_hashed, self.user["id"]),
            )
            conn.commit()

            self.curr_pw.value = ""
            self.new_pw.value = ""
            self.conf_pw.value = ""
            self._show_toast("Password successfully changed!")
        except Exception as e:
            self._show_toast(f"Password update failed: {e}", is_err=True)
        finally:
            conn.close()

    def _show_toast(self, message: str, is_err: bool = False):
        try:
            sb = ft.SnackBar(
                content=ft.Text(message, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.RED_600 if is_err else ft.Colors.GREEN_600,
                behavior=ft.SnackBarBehavior.FLOATING,
                shape=ft.RoundedRectangleBorder(radius=10),
                duration=ft.Duration(seconds=3),
                show_close_icon=True,
            )
            self.app_page.show_dialog(sb)
        except Exception:
            pass
