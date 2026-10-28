"""Main Flet Desktop Application for Hostel Management System."""

import warnings
warnings.filterwarnings("ignore")

import flet as ft
from database import initialize_database
from flet_views.theme import build_theme, get_colors
from flet_views.login_view import LoginView
from flet_views.dashboard_view import DashboardView


# Backward compatibility handler for Flet 1.0+ dialog-based SnackBar
class _SnackBarHandler:
    def __set__(self, instance, value):
        if instance is None:
            return
        instance.__dict__["_snack_bar_val"] = value
        if value is not None and isinstance(value, ft.SnackBar):
            try:
                # Force floating pill style so it never spans full window width
                value.behavior = ft.SnackBarBehavior.FLOATING
                value.shape = ft.RoundedRectangleBorder(radius=10)
                value.duration = ft.Duration(seconds=3)
                for dlg in list(instance._dialogs.controls):
                    if isinstance(dlg, ft.SnackBar):
                        dlg.open = False
                instance.show_dialog(value)
            except Exception:
                pass

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance.__dict__.get("_snack_bar_val")


setattr(ft.Page, "snack_bar", _SnackBarHandler())


def main(page: ft.Page):
    initialize_database()

    # Suppress unwanted client error bars at the bottom
    page.on_error = lambda e: None

    # Window configuration
    page.title = "Hostel Management System"
    page.window.min_width = 880
    page.window.min_height = 580
    page.window.maximized = True  # Automatically open maximized on first launch
    page.window.resizable = True  # Allow subsequent adjustment / resizing
    page.padding = 0

    # Default light theme mode
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = build_theme(is_dark=False)
    page.bgcolor = get_colors(is_dark=False)["page"]

    def show_dashboard(user_data: dict):
        page.controls.clear()
        dashboard = DashboardView(page, user_data, on_logout=show_login)
        page.controls.append(dashboard)
        page.update()

    def show_login():
        page.controls.clear()
        login = LoginView(page, on_login_success=show_dashboard)
        page.controls.append(login)
        page.update()

    # Show initial view
    show_login()


if __name__ == "__main__":
    ft.run(main)
