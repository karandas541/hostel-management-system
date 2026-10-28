"""Modern SaaS Notifications View built with Flet."""

import flet as ft
from services.notification_service import (
    get_user_notifications,
    mark_all_as_read,
    mark_notification_as_read,
    create_announcement,
)
from flet_views.theme import get_colors


class NotificationsSubView(ft.Column):
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
        is_admin = self.user.get("role") == "admin"
        return ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("Notifications & Announcements", size=22, weight=ft.FontWeight.BOLD),
                        ft.Text("Stay updated with hostel dues, maintenance notices, and broadcast alerts", size=12, color=get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)["text_muted"]),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.Row(
                    controls=[
                        ft.OutlinedButton(
                            content=ft.Row([ft.Icon(ft.Icons.DONE_ALL_ROUNDED, size=15), ft.Text("Mark all read", size=12)], spacing=6),
                            on_click=self._mark_all_read,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                        ),
                        ft.FilledButton(
                            content=ft.Row([ft.Icon(ft.Icons.CAMPAIGN_ROUNDED, size=16), ft.Text("Broadcast", size=12)], spacing=6),
                            style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_600, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8)),
                            visible=is_admin,
                            on_click=self._open_announcement_dialog,
                        ),
                    ],
                    spacing=10,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def load_data(self):
        colors = get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)
        try:
            notifs = get_user_notifications(self.user["id"], actor=self.user)
            if not notifs:
                self.list_container.controls = [
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.NOTIFICATIONS_NONE_ROUNDED, size=40, color=colors["text_muted"]),
                                ft.Text("You have no notifications.", color=colors["text_muted"]),
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

            cards = []
            for n in notifs:
                nid = n[0]
                title = n[1]
                msg = n[2]
                is_read = bool(n[3]) if len(n) > 3 else False
                created = n[4] if len(n) > 4 else 'Recently' 

                icon_color = ft.Colors.INDIGO_500 if not is_read else colors["text_muted"]

                card = ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.NOTIFICATIONS_ACTIVE_ROUNDED if not is_read else ft.Icons.NOTIFICATIONS_NONE_ROUNDED, size=20, color=icon_color),
                            ft.Column(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Text(title, size=13, weight=ft.FontWeight.BOLD if not is_read else ft.FontWeight.W_500),
                                            ft.Container(
                                                content=ft.Text("NEW", size=9, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                                padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                                                border_radius=8,
                                                bgcolor=ft.Colors.INDIGO_500,
                                                visible=not is_read,
                                            ),
                                        ],
                                        spacing=8,
                                    ),
                                    ft.Text(msg, size=12),
                                    ft.Text(str(created or "Just now"), size=10, color=colors["text_muted"]),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CHECK_ROUNDED,
                                icon_size=16,
                                tooltip="Mark as read",
                                visible=not is_read,
                                on_click=lambda e, notif_id=nid: self._mark_read(notif_id),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=14,
                    border_radius=10,
                    bgcolor=colors["surface_alt"] if is_read else colors["accent_soft"],
                )
                cards.append(card)

            self.list_container.controls = cards
            self.app_page.update()
        except Exception as err:
            self.list_container.controls = [ft.Text(f"Error loading notifications: {err}", color=ft.Colors.RED_400)]
            self.app_page.update()

    def _mark_read(self, nid: int):
        mark_notification_as_read(nid, actor=self.user)
        self.load_data()
        for c in self.app_page.controls:
            if hasattr(c, "update_sidebar_badges"):
                c.update_sidebar_badges()

    def _mark_all_read(self, _):
        mark_all_as_read(self.user["id"], actor=self.user)
        self.load_data()
        for c in self.app_page.controls:
            if hasattr(c, "update_sidebar_badges"):
                c.update_sidebar_badges()
        self.app_page.snack_bar = ft.SnackBar(ft.Text("All notifications marked as read."), bgcolor=ft.Colors.GREEN_600)
        self.app_page.snack_bar.open = True
        self.app_page.update()

    def _open_announcement_dialog(self, _):
        title_field = ft.TextField(label="Announcement Title", border_radius=8)
        msg_field = ft.TextField(label="Message to all students", multiline=True, min_lines=3, border_radius=8)

        dlg = ft.AlertDialog(
            title=ft.Text("Broadcast Announcement", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([title_field, msg_field], spacing=10),
                width=380,
                height=220,
            ),
            actions=[
                ft.TextButton(content="Cancel", on_click=lambda _: self._close_dialog(dlg)),
                ft.FilledButton(
                    "Send to All",
                    bgcolor=ft.Colors.INDIGO_600,
                    color=ft.Colors.WHITE,
                    on_click=lambda _: self._send_broadcast(dlg, title_field.value, msg_field.value),
                ),
            ],
        )
        self.app_page.overlay.append(dlg)
        dlg.open = True
        self.app_page.update()

    def _close_dialog(self, dlg):
        dlg.open = False
        self.app_page.update()

    def _send_broadcast(self, dlg, title, msg):
        success, res = create_announcement(title=title, message=msg, actor=self.user)
        if success:
            dlg.open = False
            self.load_data()
            self.app_page.snack_bar = ft.SnackBar(ft.Text("Announcement sent to all users!"), bgcolor=ft.Colors.GREEN_600)
            self.app_page.snack_bar.open = True
        else:
            self.app_page.snack_bar = ft.SnackBar(ft.Text(f"Failed: {res}"), bgcolor=ft.Colors.RED_600)
            self.app_page.snack_bar.open = True
        self.app_page.update()
