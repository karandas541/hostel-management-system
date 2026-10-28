"""Modern SaaS Complaints & Grievance View built with Flet."""

import flet as ft
from services.complaint_service import get_all_complaints, add_complaint, update_complaint_status
from flet_views.theme import get_colors


class ComplaintsSubView(ft.Column):
    def __init__(self, page: ft.Page, user: dict):
        super().__init__()
        self.app_page = page
        self.user = user
        self.expand = True
        self.spacing = 16

        self.list_container = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=10)

        self.controls = [
            self._build_header(),
            ft.Container(
                content=self.list_container,
                expand=True,
                padding=16,
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
                        ft.Text("Complaints & Support Tickets", size=22, weight=ft.FontWeight.BOLD),
                        ft.Text("Submit maintenance tickets, track resolutions, and manage feedback", size=12, color=get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)["text_muted"]),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.FilledButton(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.ADD_COMMENT_ROUNDED, size=16, color=ft.Colors.WHITE),
                            ft.Text("New Complaint", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ],
                        spacing=6,
                    ),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.INDIGO_600,
                        shape=ft.RoundedRectangleBorder(radius=10),
                        padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                    ),
                    on_click=self._open_new_complaint_dialog,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def load_data(self):
        colors = get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)
        try:
            complaints = get_all_complaints(actor=self.user)
            if not complaints:
                self.list_container.controls = [
                    ft.Container(
                        content=ft.Text("No complaints or tickets logged.", color=colors["text_muted"]),
                        alignment=ft.Alignment.CENTER,
                        padding=40,
                    )
                ]
                self.app_page.update()
                return

            cards = []
            is_admin = self.user.get("role") == "admin"

            for c in complaints:
                cid = c[0]
                stu_code = c[1]
                stu_name = c[2]
                cat = c[3]
                desc = c[4]
                prio = c[5]
                status = c[6]
                assigned_to = c[7] if len(c) > 7 else None
                created = c[8] if len(c) > 8 else None
                resolved = c[9] if len(c) > 9 else None
                remarks = c[10] if len(c) > 10 else None

                status_color = ft.Colors.GREEN_500 if status in ("Resolved", "Closed") else (ft.Colors.AMBER_500 if status == "In Progress" else ft.Colors.RED_500)
                prio_color = ft.Colors.RED_500 if prio == "High" else (ft.Colors.AMBER_500 if prio == "Medium" else ft.Colors.BLUE_500)

                status_chip = ft.Container(
                    content=ft.Text(status, size=10, weight=ft.FontWeight.BOLD, color=status_color),
                    padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                    border_radius=10,
                    bgcolor=ft.Colors.with_opacity(0.12, status_color),
                )
                prio_chip = ft.Container(
                    content=ft.Text(f"{prio} Priority", size=10, weight=ft.FontWeight.BOLD, color=prio_color),
                    padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                    border_radius=10,
                    bgcolor=ft.Colors.with_opacity(0.12, prio_color),
                )

                actions = []
                if is_admin and status not in ("Resolved", "Closed"):
                    actions.append(
                        ft.FilledButton(
                            "Mark Resolved",
                            bgcolor=ft.Colors.GREEN_600,
                            color=ft.Colors.WHITE,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                            on_click=lambda e, comp_id=cid: self._resolve_ticket(comp_id),
                        )
                    )

                card = ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Text(f"#{cid:03d} · {cat}", size=14, weight=ft.FontWeight.BOLD),
                                            prio_chip,
                                            status_chip,
                                        ],
                                        spacing=8,
                                    ),
                                    ft.Text(desc, size=13),
                                    ft.Text(f"Logged by {stu_name} ({stu_code}) · {created}", size=11, color=colors["text_muted"]),
                                ],
                                spacing=4,
                                expand=True,
                            ),
                            ft.Row(actions) if actions else ft.Container(),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=14,
                    border_radius=10,
                    bgcolor=colors["surface_alt"],
                )
                cards.append(card)

            self.list_container.controls = cards
            self.app_page.update()
        except Exception as err:
            self.list_container.controls = [ft.Text(f"Error loading complaints: {err}", color=ft.Colors.RED_400)]
            self.app_page.update()

    def _resolve_ticket(self, comp_id: int):
        success, msg = update_complaint_status(comp_id, "Resolved", actor=self.user)
        if success:
            self.load_data()
            self.app_page.snack_bar = ft.SnackBar(ft.Text("Ticket resolved!"), bgcolor=ft.Colors.GREEN_600)
            self.app_page.snack_bar.open = True
        else:
            self.app_page.snack_bar = ft.SnackBar(ft.Text(f"Failed: {msg}"), bgcolor=ft.Colors.RED_600)
            self.app_page.snack_bar.open = True
        self.app_page.update()

    def _open_new_complaint_dialog(self, _):
        stu_id_field = ft.TextField(
            label="Student ID (e.g. STU001)",
            value=self.user.get("student_id") or "" if self.user.get("role") == "student" else "",
            read_only=self.user.get("role") == "student",
            border_radius=8,
        )
        cat_dropdown = ft.Dropdown(
            label="Category",
            value="Plumbing",
            options=[ft.dropdown.Option("Plumbing"), ft.dropdown.Option("Electrical"), ft.dropdown.Option("Cleaning"), ft.dropdown.Option("Furniture"), ft.dropdown.Option("Internet / WiFi"), ft.dropdown.Option("Other")],
            border_radius=8,
        )
        prio_dropdown = ft.Dropdown(
            label="Priority",
            value="Medium",
            options=[ft.dropdown.Option("Low"), ft.dropdown.Option("Medium"), ft.dropdown.Option("High")],
            border_radius=8,
        )
        desc_field = ft.TextField(label="Description of issue", multiline=True, min_lines=3, border_radius=8)

        dlg = ft.AlertDialog(
            title=ft.Text("Submit New Complaint", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([stu_id_field, cat_dropdown, prio_dropdown, desc_field], spacing=10),
                width=380,
                height=280,
            ),
            actions=[
                ft.TextButton(content="Cancel", on_click=lambda _: self._close_dialog(dlg)),
                ft.FilledButton(
                    "Submit Ticket",
                    bgcolor=ft.Colors.INDIGO_600,
                    color=ft.Colors.WHITE,
                    on_click=lambda _: self._save_new_complaint(dlg, stu_id_field.value, cat_dropdown.value, prio_dropdown.value, desc_field.value),
                ),
            ],
        )
        self.app_page.overlay.append(dlg)
        dlg.open = True
        self.app_page.update()

    def _close_dialog(self, dlg):
        dlg.open = False
        self.app_page.update()

    def _save_new_complaint(self, dlg, sid, cat, prio, desc):
        success, msg = add_complaint(
            student_id=sid,
            category=cat,
            description=desc,
            priority=prio,
            actor=self.user,
        )
        if success:
            dlg.open = False
            self.load_data()
            self.app_page.snack_bar = ft.SnackBar(ft.Text("Complaint submitted!"), bgcolor=ft.Colors.GREEN_600)
            self.app_page.snack_bar.open = True
        else:
            self.app_page.snack_bar = ft.SnackBar(ft.Text(f"Failed: {msg}"), bgcolor=ft.Colors.RED_600)
            self.app_page.snack_bar.open = True
        self.app_page.update()
