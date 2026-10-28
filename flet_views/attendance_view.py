"""Modern SaaS Attendance View built with Flet."""

import flet as ft
from services.attendance_service import (
    get_all_attendance,
    mark_entry,
    mark_exit,
    delete_attendance,
    update_attendance_remarks,
)
from flet_views.theme import get_colors


class AttendanceSubView(ft.Column):
    def __init__(self, page: ft.Page, user: dict):
        super().__init__()
        self.app_page = page
        self.user = user
        self.expand = True
        self.spacing = 16

        self.table_container = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

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
        action_controls = []
        if is_admin:
            action_controls = [
                ft.FilledButton(
                    content=ft.Row([ft.Icon(ft.Icons.LOGIN_ROUNDED, size=15), ft.Text("Mark Entry", size=12)], spacing=6),
                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=lambda _: self._open_log_dialog("Entry"),
                ),
                ft.FilledButton(
                    content=ft.Row([ft.Icon(ft.Icons.LOGOUT_ROUNDED, size=15), ft.Text("Mark Exit", size=12)], spacing=6),
                    style=ft.ButtonStyle(bgcolor=ft.Colors.AMBER_600, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=lambda _: self._open_log_dialog("Exit"),
                ),
            ]

        return ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("Student Attendance & Movement Log", size=22, weight=ft.FontWeight.BOLD),
                        ft.Text("Track daily hostel entries, exits, timestamps, and leave records", size=12, color=get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)["text_muted"]),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.Row(controls=action_controls, spacing=10) if action_controls else ft.Container(),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def load_data(self):
        colors = get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)
        is_admin = self.user.get("role") == "admin"
        try:
            records = get_all_attendance(actor=self.user)
            if not records:
                self.table_container.controls = [
                    ft.Container(
                        content=ft.Text("No attendance logs found.", color=colors["text_muted"]),
                        alignment=ft.Alignment.CENTER,
                        padding=40,
                    )
                ]
                self.app_page.update()
                return

            rows = []
            for r in records:
                aid = r[0]
                stu_code = r[1]
                stu_name = r[2]
                entry = r[3] if len(r) > 3 else None
                exit_val = r[4] if len(r) > 4 else None
                date_val = r[5] if len(r) > 5 else None
                if exit_val and not entry:
                    status = 'Exited'
                elif entry and not exit_val:
                    status = 'Present'
                elif exit_val and entry:
                    status = 'Present' if str(entry) >= str(exit_val) else 'Exited'
                else:
                    status = 'Present'
                remarks = r[6] if len(r) > 6 else '—' 

                status_color = ft.Colors.GREEN_500 if status == "Present" else ft.Colors.AMBER_500

                cells = [
                    ft.DataCell(ft.Text(f"{stu_name} ({stu_code})", weight=ft.FontWeight.W_500)),
                    ft.DataCell(ft.Text(date_val or "—")),
                    ft.DataCell(ft.Text(entry or "—", color=ft.Colors.GREEN_600)),
                    ft.DataCell(ft.Text(exit_val or "—", color=ft.Colors.AMBER_600)),
                    ft.DataCell(
                        ft.Container(
                            content=ft.Text(status, size=10, weight=ft.FontWeight.BOLD, color=status_color),
                            padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                            border_radius=10,
                            bgcolor=ft.Colors.with_opacity(0.12, status_color),
                        )
                    ),
                    ft.DataCell(
                        ft.Container(
                            content=ft.Text(remarks or "—", size=12, color=colors["text"] if remarks and remarks != "—" else colors["text_muted"]),
                            padding=ft.Padding.symmetric(horizontal=8, vertical=4) if remarks and remarks != "—" else None,
                            border_radius=6,
                            bgcolor=colors["surface_alt"] if remarks and remarks != "—" else None,
                        )
                    ),
                ]

                if is_admin:
                    cells.append(
                        ft.DataCell(
                            ft.Row(
                                controls=[
                                    ft.IconButton(
                                        icon=ft.Icons.EDIT_NOTE_ROUNDED,
                                        icon_size=18,
                                        icon_color=ft.Colors.INDIGO_400,
                                        tooltip="Edit Remarks",
                                        on_click=lambda e, rid=aid, rmk=remarks, sn=stu_name: self._open_edit_remarks_dialog(rid, rmk, sn),
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                                        icon_size=18,
                                        icon_color=ft.Colors.RED_400,
                                        tooltip="Delete Attendance Record",
                                        on_click=lambda e, rid=aid, sn=stu_name, dt=date_val: self._confirm_delete_attendance(rid, sn, dt),
                                    ),
                                ],
                                spacing=2,
                            )
                        )
                    )

                rows.append(ft.DataRow(cells=cells))

            columns = [
                ft.DataColumn(ft.Text("STUDENT", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
                ft.DataColumn(ft.Text("DATE", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
                ft.DataColumn(ft.Text("ENTRY TIME", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
                ft.DataColumn(ft.Text("EXIT TIME", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
                ft.DataColumn(ft.Text("STATUS", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
                ft.DataColumn(ft.Text("REMARKS", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
            ]
            if is_admin:
                columns.append(ft.DataColumn(ft.Text("ACTIONS", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])))

            col_spacing = 38 if is_admin else 68
            table = ft.DataTable(
                columns=columns,
                rows=rows,
                border_radius=10,
                heading_row_color=colors["surface_alt"],
                column_spacing=col_spacing,
                data_row_min_height=48,
                heading_row_height=44,
            )

            self.table_container.controls = [
                ft.Row(
                    controls=[table],
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                )
            ]
            self.app_page.update()
        except Exception as err:
            self.table_container.controls = [ft.Text(f"Error loading attendance: {err}", color=ft.Colors.RED_400)]
            self.app_page.update()

    def _open_log_dialog(self, movement_type: str):
        sid_field = ft.TextField(
            label="Student ID (e.g. STU001)",
            value=self.user.get("student_id") or "" if self.user.get("role") == "student" else "",
            read_only=self.user.get("role") == "student",
            border_radius=8,
        )
        remarks_field = ft.TextField(label="Remarks (Optional)", border_radius=8)

        dlg = ft.AlertDialog(
            title=ft.Text(f"Mark {movement_type}", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([sid_field, remarks_field], spacing=10),
                width=340,
                height=160,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self._close_dialog(dlg)),
                ft.FilledButton(
                    f"Record {movement_type}",
                    bgcolor=ft.Colors.INDIGO_600,
                    color=ft.Colors.WHITE,
                    on_click=lambda _: self._submit_log(dlg, movement_type, sid_field.value, remarks_field.value),
                ),
            ],
        )
        self.app_page.overlay.append(dlg)
        dlg.open = True
        self.app_page.update()

    def _close_dialog(self, dlg):
        dlg.open = False
        self.app_page.update()

    def _submit_log(self, dlg, mtype, sid, remarks=""):
        sid_clean = (sid or "").strip()
        if not sid_clean:
            self._show_toast("Please enter a valid Student ID.", is_err=True)
            return

        fn = mark_entry if mtype == "Entry" else mark_exit
        try:
            success, msg = fn(student_id=sid_clean, actor=self.user, remarks=remarks)
        except Exception as e:
            success, msg = False, str(e)
        if success:
            dlg.open = False
            self.load_data()
            self._show_toast(f"{mtype} marked successfully!")
        else:
            self._show_toast(f"Failed: {msg}", is_err=True)

    def _open_edit_remarks_dialog(self, aid: int, current_remarks: str, student_name: str):
        rem_input = ft.TextField(
            label="Remarks",
            value=current_remarks if current_remarks and current_remarks != "—" else "",
            hint_text="e.g. Late entry permitted, Doctor visit, Night out",
            border_radius=8,
            multiline=True,
            min_lines=2,
            max_lines=3,
        )

        def do_save(_):
            dlg.open = False
            self.app_page.update()
            ok, msg = update_attendance_remarks(aid, rem_input.value, actor=self.user)
            if ok:
                self.load_data()
                self._show_toast("Remarks updated successfully.")
            else:
                self._show_toast(f"Failed to update remarks: {msg}", is_err=True)

        dlg = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.EDIT_NOTE_ROUNDED, color=ft.Colors.INDIGO_400, size=24),
                    ft.Text(f"Edit Remarks ({student_name})", weight=ft.FontWeight.BOLD, size=16),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=ft.Column([rem_input], spacing=10),
                width=380,
                height=110,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self._close_dialog(dlg)),
                ft.FilledButton("Save Remarks", bgcolor=ft.Colors.INDIGO_600, color=ft.Colors.WHITE, on_click=do_save),
            ],
        )
        self.app_page.overlay.append(dlg)
        dlg.open = True
        self.app_page.update()

    def _confirm_delete_attendance(self, aid, student_name, date_val):
        def do_delete(_):
            dlg.open = False
            self.app_page.update()
            try:
                success, msg = delete_attendance(aid, actor=self.user)
                if success:
                    self.load_data()
                    self._show_toast("Attendance record deleted successfully.")
                else:
                    self._show_toast(f"Failed to delete: {msg}", is_err=True)
            except Exception as e:
                self._show_toast(f"Error: {e}", is_err=True)

        dlg = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.DELETE_OUTLINE_ROUNDED, color=ft.Colors.RED_500, size=24),
                    ft.Text("Confirm Delete Record", weight=ft.FontWeight.BOLD, size=18),
                ],
                spacing=8,
            ),
            content=ft.Text(f"Are you sure you want to delete the attendance log for {student_name} on {date_val}?"),
            actions=[
                ft.OutlinedButton("Cancel", on_click=lambda _: self._close_dialog(dlg)),
                ft.FilledButton("Yes, Delete", bgcolor=ft.Colors.RED_600, color=ft.Colors.WHITE, on_click=do_delete),
            ],
        )
        self.app_page.overlay.append(dlg)
        dlg.open = True
        self.app_page.update()

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
