"""Modern SaaS Feedback & Ratings View built with Flet."""

import flet as ft
from services.feedback_service import get_all_feedback, add_feedback, get_overall_satisfaction
from flet_views.theme import get_colors


class FeedbackSubView(ft.Column):
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
        avg = get_overall_satisfaction(actor=self.user)
        avg_str = f"Avg. Score: {avg:.1f}/5 ⭐" if avg else "No ratings yet"

        return ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("Student Feedback & Experience", size=22, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Quality feedback across cleanliness, food, wifi, and warden support · {avg_str}", size=12, color=get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)["text_muted"]),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.FilledButton(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.RATE_REVIEW_ROUNDED, size=16, color=ft.Colors.WHITE),
                            ft.Text("Submit Feedback", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ],
                        spacing=6,
                    ),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.INDIGO_600,
                        shape=ft.RoundedRectangleBorder(radius=10),
                        padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                    ),
                    on_click=self._open_feedback_dialog,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def load_data(self):
        colors = get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)
        try:
            feedbacks = get_all_feedback(actor=self.user)
            if not feedbacks:
                self.list_container.controls = [
                    ft.Container(
                        content=ft.Text("No feedback entries submitted yet.", color=colors["text_muted"]),
                        alignment=ft.Alignment.CENTER,
                        padding=40,
                    )
                ]
                self.app_page.update()
                return

            cards = []
            for fb in feedbacks:
                fbid = fb[0]
                sid = fb[1]
                sname = fb[2]
                c_clean = fb[4] if len(fb) > 4 else 5
                c_food = fb[5] if len(fb) > 5 else 5
                c_wifi = fb[7] if len(fb) > 7 else 5
                c_over = fb[11] if len(fb) > 11 else 5
                comments = fb[12] if len(fb) > 12 else ''
                fdate = str(fb[14] or 'Recent')[:16] if len(fb) > 14 else 'Recent'

                stars = "★" * int(c_over or 5) + "☆" * (5 - int(c_over or 5))

                card = ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(f"{sname} ({sid})", size=13, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"{stars} ({c_over}/5)", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_500),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Text(f'"{comments}"' if comments else "No written comments.", size=12, italic=True),
                            ft.Text(f"Cleanliness: {c_clean}/5  ·  Food: {c_food}/5  ·  WiFi: {c_wifi}/5   ·  Submitted: {fdate}", size=11, color=colors["text_muted"]),
                        ],
                        spacing=4,
                    ),
                    padding=14,
                    border_radius=10,
                    bgcolor=colors["surface_alt"],
                )
                cards.append(card)

            self.list_container.controls = cards
            self.app_page.update()
        except Exception as err:
            self.list_container.controls = [ft.Text(f"Error loading feedback: {err}", color=ft.Colors.RED_400)]
            self.app_page.update()

    def _open_feedback_dialog(self, _):
        sid_field = ft.TextField(
            label="Student ID (e.g. STU001)",
            value=self.user.get("student_id") or "" if self.user.get("role") == "student" else "",
            read_only=self.user.get("role") == "student",
            border_radius=8,
        )
        clean_slider = ft.Slider(min=1, max=5, divisions=4, value=5, label="{value} Stars")
        food_slider = ft.Slider(min=1, max=5, divisions=4, value=4, label="{value} Stars")
        wifi_slider = ft.Slider(min=1, max=5, divisions=4, value=4, label="{value} Stars")
        overall_slider = ft.Slider(min=1, max=5, divisions=4, value=5, label="{value} Stars")
        comments_field = ft.TextField(label="Comments / Suggestions", multiline=True, min_lines=2, border_radius=8)

        dlg = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.RATE_REVIEW_ROUNDED, color=ft.Colors.INDIGO_600, size=24),
                    ft.Text("Submit Hostel Feedback", weight=ft.FontWeight.BOLD, size=18),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        sid_field,
                        ft.Text("Cleanliness Rating (1-5):", size=12),
                        clean_slider,
                        ft.Text("Mess / Food Quality (1-5):", size=12),
                        food_slider,
                        ft.Text("Internet / Amenities (1-5):", size=12),
                        wifi_slider,
                        ft.Text("Overall Experience (1-5):", size=12),
                        overall_slider,
                        comments_field,
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    spacing=6,
                ),
                width=380,
                height=360,
            ),
            actions=[
                ft.TextButton(content="Cancel", on_click=lambda _: self._close_dialog(dlg)),
                ft.FilledButton(
                    "Submit Review",
                    bgcolor=ft.Colors.INDIGO_600,
                    color=ft.Colors.WHITE,
                    on_click=lambda _: self._save_feedback(
                        dlg, sid_field.value, int(clean_slider.value), int(food_slider.value),
                        int(wifi_slider.value), int(overall_slider.value), comments_field.value
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

    def _save_feedback(self, dlg, sid, clean, food, wifi, overall, comments):
        sid_clean = (sid or "").strip()
        if not sid_clean:
            self._show_toast("Please enter a valid Student ID.", is_err=True)
            return

        try:
            success, msg = add_feedback(
                student_id=sid_clean,
                room_quality=clean,
                cleanliness=clean,
                food_quality=food,
                maintenance=clean,
                wifi=wifi,
                security=5,
                hostel_staff=5,
                common_facilities=wifi,
                overall_experience=overall,
                comments=(comments or "").strip(),
                evaluation_period="Monthly",
                actor=self.user,
            )
        except Exception as e:
            success, msg = False, str(e)

        if success:
            dlg.open = False
            self.load_data()
            self._show_toast("Thank you for your feedback!")
        else:
            self._show_toast(f"Failed: {msg}", is_err=True)

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
