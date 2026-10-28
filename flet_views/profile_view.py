import re
"""Modern SaaS Profile & Account Management View built with Flet."""

import flet as ft
from database import get_connection
from services.auth_service import hash_password, verify_password
from utils.validators import validate_email, validate_password, validate_phone
from flet_views.theme import get_colors


class ProfileSubView(ft.Column):
    def __init__(self, page: ft.Page, user: dict):
        super().__init__()
        self.app_page = page
        self.user = user
        self.expand = True
        self.spacing = 16

        self.content_container = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=18)

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
        self.load_data()

    def _build_header(self) -> ft.Control:
        return ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("User Profile & Security", size=22, weight=ft.FontWeight.BOLD),
                        ft.Text("Manage your personal details, student information, and account security", size=12, color=get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)["text_muted"]),
                    ],
                    spacing=2,
                    expand=True,
                ),
            ],
        )

    def load_data(self):
        colors = get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)

        initials = (self.user.get("username") or "?")[:2].upper()
        role = self.user.get("role", "student")

        # Fetch latest details from DB
        student_info = None
        conn = get_connection()
        try:
            curr_user = conn.execute(
                "SELECT username, email FROM users WHERE id = ?", (self.user["id"],)
            ).fetchone()
            if curr_user:
                self.user["email"] = curr_user[1] or self.user.get("email", "")

            if role == "student":
                student_info = conn.execute(
                    """
                    SELECT s.student_id, s.name, s.course, s.branch, s.year, s.phone,
                           s.admission_date, s.status, r.room_number, a.bed_number
                    FROM students s
                    LEFT JOIN room_allocations a ON a.student_id = s.id AND a.vacated_at IS NULL
                    LEFT JOIN rooms r ON r.id = a.room_id
                    WHERE s.user_id = ?
                    """,
                    (self.user["id"],),
                ).fetchone()
        finally:
            conn.close()

        # ── 1. Hero Identity Card ──────────────────────────────────────────
        name_display = self.user.get("username", "User")
        if student_info and student_info[1]:
            name_display = student_info[1]

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
                            ft.Text(f"Username: @{self.user['username']} · Email: {self.user.get('email', 'N/A')}", size=12, color=colors["text_muted"]),
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
        student_section = ft.Container()
        if student_info:
            sid, sname, course, branch, yr, phone, adm_date, status, rnum, bnum = student_info
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
            )

        # ── 3. Edit Personal Information ──────────────────────────────────
        self.email_input = ft.TextField(
            label="Email Address",
            value=self.user.get("email") or "",
            border_radius=8,
            expand=True,
        )
        self.phone_input = ft.TextField(
            label="Phone Number",
            value=student_info[5] if student_info and student_info[5] else "",
            border_radius=8,
            expand=True,
        )

        personal_edit_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Contact Information", size=15, weight=ft.FontWeight.BOLD),
                    ft.Row(controls=[self.email_input, self.phone_input], spacing=14),
                    ft.FilledButton(
                        content="Save Contact Info",
                        bgcolor=ft.Colors.INDIGO_600,
                        color=ft.Colors.WHITE,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                        on_click=self._save_contact_info,
                    ),
                ],
                spacing=12,
            ),
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
                        content="Update Password",
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

        self.content_container.controls = [hero_card]
        if student_info:
            self.content_container.controls.append(student_section)
        self.content_container.controls.extend([personal_edit_card, password_card])
        self.app_page.update()

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

    def _show_invalid_email_dialog(self):
        err_dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, color=ft.Colors.RED_500, size=24),
                    ft.Text("Invalid Email ID", weight=ft.FontWeight.BOLD, size=16),
                ],
                spacing=10,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "Invalid email address entered!",
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.RED_600,
                        ),
                        ft.Text(
                            "Please enter a valid email address with '@gmail.com' format.\n(Example: user@gmail.com)\n\n'@gmail.com' format is required.",
                            size=12,
                        ),
                    ],
                    spacing=8,
                    tight=True,
                ),
                width=360,
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

    def _close_dialog(self, dlg):
        dlg.open = False
        self.app_page.update()

    def _save_contact_info(self, _):
        email = (self.email_input.value or "").strip()
        phone = (self.phone_input.value or "").strip()

        if not email or not re.match(r"^[a-zA-Z0-9._%+-]+@gmail\.com$", email, re.IGNORECASE):
            self._show_invalid_email_dialog()
            return

        conn = get_connection()
        try:
            # Check duplicate email
            dup = conn.execute(
                "SELECT id FROM users WHERE lower(email) = lower(?) AND id != ?",
                (email, self.user["id"]),
            ).fetchone()
            if dup:
                self._show_toast("This email is already in use by another account.", is_err=True)
                return

            conn.execute("UPDATE users SET email = ? WHERE id = ?", (email, self.user["id"]))
            if self.user.get("role") == "student":
                conn.execute(
                    "UPDATE students SET email = ?, phone = ? WHERE user_id = ?",
                    (email, phone, self.user["id"]),
                )
            conn.commit()
            self.user["email"] = email
            self._show_toast("Profile contact information updated!")
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
