"""Shared visual styling for the hostel management desktop interface."""

import customtkinter as ctk


COLORS = {
    "page": "#F3F6FB",
    "surface": "#FFFFFF",
    "surface_alt": "#EAF0F7",
    "border": "#DCE4EE",
    "text": "#182538",
    "muted": "#64748B",
    "nav": "#14243A",
    "nav_hover": "#233A56",
    "accent": "#176B87",
    "accent_hover": "#12566D",
    "danger": "#B54747",
}


def get_palette():
    """Return colors for the active CustomTkinter appearance mode."""
    if ctk.get_appearance_mode().lower() == "dark":
        return {
            "page": "#0B1220",
            "surface": "#111C2E",
            "surface_alt": "#1B2A3E",
            "border": "#2A3B52",
            "text": "#E7EEF7",
            "muted": "#A4B3C5",
            "nav": "#101C2C",
            "nav_hover": "#253A52",
            "accent": "#55B7D2",
            "accent_hover": "#3698B5",
            "danger": "#C85B61",
        }
    return COLORS


def apply_professional_style(root):
    """Apply the active palette and consistent controls to a feature window."""
    colors = get_palette()
    try:
        root.configure(fg_color=colors["page"])
    except (AttributeError, TypeError):
        return

    def visit(parent):
        for widget in parent.winfo_children():
            try:
                kind = widget.__class__.__name__
                if kind in {"CTkFrame", "CTkScrollableFrame"}:
                    current = widget.cget("fg_color")
                    if current != "transparent":
                        widget.configure(
                            fg_color=colors["surface"],
                            border_color=colors["border"],
                            border_width=1,
                            corner_radius=12,
                        )
                elif kind == "CTkLabel":
                    widget.configure(text_color=colors["text"])
                elif kind == "CTkButton":
                    label = str(widget.cget("text")).lower()
                    if any(word in label for word in ("delete", "remove", "logout", "close")):
                        widget.configure(fg_color=colors["danger"], hover_color="#963B3B", corner_radius=9)
                    else:
                        widget.configure(fg_color=colors["accent"], hover_color=colors["accent_hover"], corner_radius=9)
                elif kind == "CTkEntry":
                    widget.configure(border_color=colors["border"], corner_radius=8)
                elif kind == "CTkTextbox":
                    widget.configure(border_color=colors["border"], corner_radius=8)
            except (AttributeError, TypeError, ValueError):
                pass

            # Recurse only through application containers. CustomTkinter
            # controls own internal canvas/label widgets; styling those too
            # adds many redundant redraws and can leave scroll repaint trails.
            if kind in {"CTkFrame", "CTkScrollableFrame"}:
                visit(widget)

    visit(root)
