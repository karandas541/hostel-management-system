"""Shared visual styling for the hostel management desktop interface.

Design system: SaaS-grade dark / light combo.
  Light — clean, airy (Vercel / Linear inspired)
  Dark  — true dark Zinc palette (not navy-blue)
Accent colour: Indigo (#6366F1 light / #818CF8 dark).
"""

import customtkinter as ctk


# ─────────────────────────────────────────────────────────────────────────────
# Light palette  (default / fallback)
# ─────────────────────────────────────────────────────────────────────────────
COLORS = {
    # backgrounds
    "page":        "#F8FAFC",   # slate-50  — main canvas
    "surface":     "#FFFFFF",   # pure white cards
    "surface_alt": "#F1F5F9",   # slate-100 — alternate rows / inner panels
    "surface_2":   "#E9EEF5",   # slightly darker for nested areas

    # chrome
    "border":      "#E2E8F0",   # slate-200
    "divider":     "#CBD5E1",   # slate-300

    # navigation sidebar
    "nav":          "#0F172A",   # slate-950 — deep & premium
    "nav_surface":  "#1E293B",   # slate-800 — sidebar card area
    "nav_hover":    "#1E293B",   # slate-800 hover
    "nav_active":   "#312E81",   # indigo-900 active item bg
    "nav_active_border": "#6366F1",  # indigo-500 left indicator

    # typography
    "text":        "#0F172A",   # slate-950
    "text_2":      "#334155",   # slate-700
    "muted":       "#64748B",   # slate-500
    "subtle":      "#94A3B8",   # slate-400

    # accent (Indigo)
    "accent":      "#6366F1",   # indigo-500
    "accent_hover":"#4F46E5",   # indigo-600
    "accent_soft": "#EEF2FF",   # indigo-50

    # status
    "success":     "#10B981",   # emerald-500
    "success_soft":"#ECFDF5",
    "warning":     "#F59E0B",   # amber-500
    "warning_soft":"#FFFBEB",
    "danger":      "#EF4444",   # red-500
    "danger_soft": "#FEF2F2",
    "info":        "#3B82F6",   # blue-500
    "info_soft":   "#EFF6FF",
}


# ─────────────────────────────────────────────────────────────────────────────
# Dark palette
# ─────────────────────────────────────────────────────────────────────────────
_DARK = {
    # backgrounds
    "page":        "#09090B",   # zinc-950
    "surface":     "#18181B",   # zinc-900
    "surface_alt": "#27272A",   # zinc-800
    "surface_2":   "#3F3F46",   # zinc-700

    # chrome
    "border":      "#3F3F46",   # zinc-700
    "divider":     "#52525B",   # zinc-600

    # navigation sidebar
    "nav":          "#09090B",   # zinc-950 — unified with page
    "nav_surface":  "#18181B",
    "nav_hover":    "#27272A",   # zinc-800
    "nav_active":   "#312E81",   # indigo-900 (same as light — brand consistent)
    "nav_active_border": "#818CF8",  # indigo-400

    # typography
    "text":        "#FAFAFA",   # zinc-50
    "text_2":      "#D4D4D8",   # zinc-300
    "muted":       "#A1A1AA",   # zinc-400
    "subtle":      "#71717A",   # zinc-500

    # accent
    "accent":      "#818CF8",   # indigo-400 — readable on dark bg
    "accent_hover":"#6366F1",   # indigo-500
    "accent_soft": "#1E1B4B",   # indigo-950

    # status
    "success":     "#34D399",   # emerald-400
    "success_soft":"#064E3B",
    "warning":     "#FBBF24",   # amber-400
    "warning_soft":"#451A03",
    "danger":      "#F87171",   # red-400
    "danger_soft": "#450A0A",
    "info":        "#60A5FA",   # blue-400
    "info_soft":   "#1E3A5F",
}


def get_palette() -> dict:
    """Return the colour dict for the current CustomTkinter appearance mode."""
    if ctk.get_appearance_mode().lower() == "dark":
        return _DARK
    return COLORS


# ─────────────────────────────────────────────────────────────────────────────
# Theme applicator
# ─────────────────────────────────────────────────────────────────────────────
def apply_professional_style(root) -> None:
    """Apply the active palette to a feature window recursively.

    Key scroll-artifact fix: CTkScrollableFrame must NOT receive border_width;
    doing so causes the internal canvas to repaint incorrectly, leaving colour
    streaks during scrolling.  We set only fg_color on scroll frames.
    """
    colors = get_palette()
    try:
        root.configure(fg_color=colors["page"])
    except (AttributeError, TypeError):
        return

    def visit(parent):
        for widget in parent.winfo_children():
            try:
                kind = widget.__class__.__name__

                if kind == "CTkScrollableFrame":
                    # ── scroll-artifact fix: no border on scroll frames ──
                    current = widget.cget("fg_color")
                    if current != "transparent":
                        widget.configure(fg_color=colors["page"])

                elif kind == "CTkFrame":
                    current = widget.cget("fg_color")
                    if current not in ("transparent", ""):
                        widget.configure(
                            fg_color=colors["surface"],
                            border_color=colors["border"],
                        )

                elif kind == "CTkLabel":
                    widget.configure(text_color=colors["text"])

                elif kind == "CTkButton":
                    label = str(widget.cget("text")).lower()
                    if any(w in label for w in ("delete", "remove", "logout", "close")):
                        widget.configure(
                            fg_color=colors["danger"],
                            hover_color=colors["danger_soft"],
                            text_color="#FFFFFF",
                            corner_radius=9,
                        )
                    elif widget.cget("fg_color") == "transparent":
                        # sidebar / ghost buttons — leave them alone
                        pass
                    else:
                        widget.configure(
                            fg_color=colors["accent"],
                            hover_color=colors["accent_hover"],
                            text_color="#FFFFFF",
                            corner_radius=9,
                        )

                elif kind == "CTkEntry":
                    widget.configure(
                        fg_color=colors["surface_alt"],
                        border_color=colors["border"],
                        text_color=colors["text"],
                        corner_radius=8,
                    )

                elif kind == "CTkTextbox":
                    widget.configure(
                        fg_color=colors["surface_alt"],
                        border_color=colors["border"],
                        text_color=colors["text"],
                        corner_radius=8,
                    )

                elif kind == "CTkOptionMenu":
                    widget.configure(
                        fg_color=colors["surface_alt"],
                        button_color=colors["border"],
                        text_color=colors["text"],
                    )

                elif kind == "CTkComboBox":
                    widget.configure(
                        fg_color=colors["surface_alt"],
                        border_color=colors["border"],
                        text_color=colors["text"],
                    )

            except (AttributeError, TypeError, ValueError):
                pass

            # Only recurse into CTk containers — not into CTk internal widgets.
            if kind in {"CTkFrame", "CTkScrollableFrame"}:
                visit(widget)

    visit(root)
