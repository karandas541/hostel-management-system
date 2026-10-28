"""Modern SaaS Quality & TQM Dashboard View built with Flet."""

import flet as ft
from analytics.satisfaction_analysis import get_satisfaction_analysis
from services.quality_service import get_quality_recommendations
from flet_views.theme import get_colors


class QualityDashboardSubView(ft.Column):
    def __init__(self, page: ft.Page, user: dict):
        super().__init__()
        self.app_page = page
        self.user = user
        self.expand = True
        self.spacing = 16

        self.content_container = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=16)

        self.controls = [
            self._build_header(),
            ft.Container(
                content=self.content_container,
                expand=True,
                padding=20,
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
                        ft.Text("Quality & TQM Performance Dashboard", size=22, weight=ft.FontWeight.BOLD),
                        ft.Text("Total Quality Management analytics, satisfaction metrics, and AI recommendations", size=12, color=get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)["text_muted"]),
                    ],
                    spacing=2,
                    expand=True,
                ),
            ],
        )

    def load_data(self):
        colors = get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)
        try:
            satisfaction = get_satisfaction_analysis(actor=self.user)
            recommendations = get_quality_recommendations(actor=self.user)

            # 1. Satisfaction category metric cards
            metric_cards = []
            for cat_name, score in satisfaction.items():
                val = score if score is not None else 0.0
                ratio = min(1.0, max(0.0, val / 5.0))
                card_color = ft.Colors.GREEN_500 if val >= 4.0 else (ft.Colors.AMBER_500 if val >= 3.0 else ft.Colors.RED_500)

                metric_cards.append(
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Text(cat_name, size=13, weight=ft.FontWeight.BOLD),
                                        ft.Text(f"{val:.1f}/5" if score is not None else "N/A", size=13, weight=ft.FontWeight.BOLD, color=card_color),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                ft.ProgressBar(value=ratio, color=card_color, bgcolor=colors["border"], height=6, border_radius=3),
                                ft.Text(f"{int(ratio * 100)}% satisfaction rating", size=10, color=colors["text_muted"]),
                            ],
                            spacing=4,
                        ),
                        width=270,
                        padding=14,
                        border_radius=10,
                        bgcolor=colors["surface_alt"],
                    )
                )

            metrics_section = ft.Column(
                controls=[
                    ft.Text("Category Satisfaction Breakdown", size=15, weight=ft.FontWeight.BOLD),
                    ft.Row(controls=metric_cards, wrap=True, spacing=12),
                ],
                spacing=8,
            )

            # 2. Recommendations Section
            rec_cards = []
            for rec in recommendations:
                st = rec.get("status", "")
                st_color = ft.Colors.GREEN_500 if "Good" in st else (ft.Colors.AMBER_500 if "Needs" in st else ft.Colors.RED_500)

                rec_cards.append(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, size=20, color=st_color),
                                ft.Column(
                                    controls=[
                                        ft.Row(
                                            controls=[
                                                ft.Text(rec["category"], size=13, weight=ft.FontWeight.BOLD),
                                                ft.Container(
                                                    content=ft.Text(st, size=9, weight=ft.FontWeight.BOLD, color=st_color),
                                                    padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                                                    border_radius=8,
                                                    bgcolor=ft.Colors.with_opacity(0.12, st_color),
                                                ),
                                            ],
                                            spacing=8,
                                        ),
                                        ft.Text(rec["recommendation"], size=12),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                            ],
                            spacing=12,
                        ),
                        padding=12,
                        border_radius=10,
                        bgcolor=colors["surface_alt"],
                    )
                )

            recs_section = ft.Column(
                controls=[
                    ft.Text("Actionable Quality Recommendations", size=15, weight=ft.FontWeight.BOLD),
                    ft.Column(controls=rec_cards, spacing=8),
                ],
                spacing=8,
            )

            self.content_container.controls = [metrics_section, ft.Divider(height=1, color=colors["border"]), recs_section]
            self.app_page.update()
        except Exception as err:
            self.content_container.controls = [ft.Text(f"Error loading Quality Dashboard: {err}", color=ft.Colors.RED_400)]
            self.app_page.update()
