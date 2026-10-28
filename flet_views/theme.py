"""Modern SaaS visual styling & theme tokens for Flet application."""

import flet as ft

# ── Color Palettes ──────────────────────────────────────────────────────────
LIGHT_COLORS = {
    "page": "#F8FAFC",          # Slate 50
    "surface": "#FFFFFF",       # Pure white
    "surface_alt": "#F1F5F9",   # Slate 100
    "border": "#E2E8F0",        # Slate 200
    "sidebar": "#0F172A",       # Slate 950 deep sidebar
    "sidebar_active": "#1E293B",# Slate 800
    "sidebar_text": "#F8FAFC",  # White
    "sidebar_sub": "#94A3B8",   # Slate 400
    "text": "#0F172A",          # Slate 950
    "text_muted": "#64748B",    # Slate 500
    "accent": "#6366F1",        # Indigo 500
    "accent_hover": "#4F46E5",  # Indigo 600
    "accent_soft": "#EEF2FF",   # Indigo 50
    "success": "#10B981",       # Emerald 500
    "success_soft": "#ECFDF5",  # Emerald 50
    "warning": "#F59E0B",       # Amber 500
    "warning_soft": "#FFFBEB",  # Amber 50
    "danger": "#EF4444",        # Red 500
    "danger_soft": "#FEF2F2",   # Red 50
    "info": "#3B82F6",          # Blue 500
    "info_soft": "#EFF6FF",     # Blue 50
}

DARK_COLORS = {
    "page": "#09090B",          # Zinc 950 true dark
    "surface": "#18181B",       # Zinc 900
    "surface_alt": "#27272A",   # Zinc 800
    "border": "#3F3F46",        # Zinc 700
    "sidebar": "#09090B",       # Zinc 950
    "sidebar_active": "#27272A",# Zinc 800
    "sidebar_text": "#FAFAFA",  # Zinc 50
    "sidebar_sub": "#A1A1AA",   # Zinc 400
    "text": "#FAFAFA",          # Zinc 50
    "text_muted": "#A1A1AA",    # Zinc 400
    "accent": "#818CF8",        # Indigo 400
    "accent_hover": "#6366F1",  # Indigo 500
    "accent_soft": "#1E1B4B",   # Indigo 950
    "success": "#34D399",       # Emerald 400
    "success_soft": "#064E3B",
    "warning": "#FBBF24",       # Amber 400
    "warning_soft": "#451A03",
    "danger": "#F87171",        # Red 400
    "danger_soft": "#450A0A",
    "info": "#60A5FA",          # Blue 400
    "info_soft": "#1E3A5F",
}


def get_colors(is_dark: bool = False) -> dict:
    return DARK_COLORS if is_dark else LIGHT_COLORS


def build_theme(is_dark: bool = False) -> ft.Theme:
    colors = get_colors(is_dark)
    return ft.Theme(
        color_scheme_seed=colors["accent"],
        font_family="Segoe UI, Inter, Roboto, sans-serif",
    )


def attach_date_picker(textfield: ft.TextField, page: ft.Page, first_date=None, last_date=None):
    from datetime import datetime

    def handle_change(e):
        selected = dp.value or getattr(e, "data", None)
        if selected:
            if isinstance(selected, str):
                try:
                    selected = datetime.fromisoformat(selected.replace("Z", "+00:00"))
                except Exception:
                    pass
            if hasattr(selected, "astimezone") and getattr(selected, "tzinfo", None) is not None:
                try:
                    selected = selected.astimezone()
                except Exception:
                    pass
            if hasattr(selected, "strftime"):
                textfield.value = selected.strftime("%Y-%m-%d")
            else:
                textfield.value = str(selected)[:10]
            dp.open = False
            page.update()

    def open_picker(_):
        initial = None
        if textfield.value:
            try:
                initial = datetime.strptime(textfield.value.strip(), "%Y-%m-%d")
            except Exception:
                initial = None
        dp.value = initial or datetime.now()
        dp.open = True
        page.update()

    dp = ft.DatePicker(
        first_date=first_date or datetime(1960, 1, 1),
        last_date=last_date or datetime(2040, 12, 31),
        on_change=handle_change,
    )
    page.overlay.append(dp)
    textfield.suffix = ft.IconButton(
        icon=ft.Icons.CALENDAR_MONTH_ROUNDED,
        icon_size=18,
        tooltip="Select date from calendar",
        on_click=open_picker,
    )
