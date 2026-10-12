import customtkinter as ctk
from tkinter import messagebox
from utils.authorization import require_menu_access, guard_authorization_errors
from utils.authorization import load_actor

from utils.theme_manager import ThemeManager
from database import get_connection
from utils.ui_theme import apply_professional_style


class SettingsWindow(ctk.CTkToplevel):

    def __init__(self, parent, user_data):
        require_menu_access(user_data, "Settings")
        super().__init__(parent)

        self.parent = parent
        self.user_data = load_actor(user_data)

        # ==========================================
        # WINDOW SETTINGS
        # ==========================================
        self.title("Settings")
        self.geometry("750x700")
        self.minsize(600, 550)

        # Allow maximize + resize
        self.resizable(True, True)

        # Bring window to front
        self.transient(parent)

        self.create_ui()
        self.load_settings()
        apply_professional_style(self)
        if hasattr(self.parent, "apply_visual_theme"):
            self.parent.apply_visual_theme()

    # ==========================================
    # CREATE UI
    # ==========================================
    def create_ui(self):

        # ==========================================
        # OUTER FRAME
        # ==========================================
        outer_frame = ctk.CTkFrame(
            self,
            corner_radius=0
        )
        outer_frame.pack(
            fill="both",
            expand=True
        )

        # ==========================================
        # SCROLLABLE FRAME
        # ==========================================
        self.scroll_frame = ctk.CTkScrollableFrame(
            outer_frame,
            corner_radius=15
        )

        self.scroll_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )

        # ==========================================
        # TITLE
        # ==========================================
        title = ctk.CTkLabel(
            self.scroll_frame,
            text="⚙ Settings",
            font=ctk.CTkFont(
                size=30,
                weight="bold"
            )
        )

        title.pack(
            pady=(20, 5)
        )

        subtitle = ctk.CTkLabel(
            self.scroll_frame,
            text="Manage your application preferences",
            font=ctk.CTkFont(size=14)
        )

        subtitle.pack(
            pady=(0, 25)
        )

        # ==========================================
        # APPEARANCE
        # ==========================================
        appearance_label = ctk.CTkLabel(
            self.scroll_frame,
            text="Appearance",
            font=ctk.CTkFont(
                size=19,
                weight="bold"
            )
        )

        appearance_label.pack(
            anchor="w",
            padx=25,
            pady=(5, 10)
        )

        appearance_frame = ctk.CTkFrame(
            self.scroll_frame,
            corner_radius=10
        )

        appearance_frame.pack(
            fill="x",
            padx=25,
            pady=5
        )

        theme_label = ctk.CTkLabel(
            appearance_frame,
            text="Theme",
            font=ctk.CTkFont(
                size=15,
                weight="bold"
            )
        )

        theme_label.pack(
            side="left",
            padx=20,
            pady=20
        )

        self.theme_menu = ctk.CTkOptionMenu(
            appearance_frame,
            values=["Light", "Dark"],
            width=160
        )

        self.theme_menu.pack(
            side="right",
            padx=20,
            pady=20
        )

        # ==========================================
        # NOTIFICATIONS
        # ==========================================
        notification_label = ctk.CTkLabel(
            self.scroll_frame,
            text="Notifications",
            font=ctk.CTkFont(
                size=19,
                weight="bold"
            )
        )

        notification_label.pack(
            anchor="w",
            padx=25,
            pady=(25, 10)
        )

        notification_frame = ctk.CTkFrame(
            self.scroll_frame,
            corner_radius=10
        )

        notification_frame.pack(
            fill="x",
            padx=25,
            pady=5
        )

        self.notification_switch = ctk.CTkSwitch(
            notification_frame,
            text="Enable Notifications",
            font=ctk.CTkFont(size=15)
        )

        self.notification_switch.pack(
            side="left",
            padx=20,
            pady=20
        )

        # ==========================================
        # KEYBOARD SHORTCUTS
        # ==========================================
        shortcut_label = ctk.CTkLabel(
            self.scroll_frame,
            text="Keyboard Shortcuts",
            font=ctk.CTkFont(
                size=19,
                weight="bold"
            )
        )

        shortcut_label.pack(
            anchor="w",
            padx=25,
            pady=(25, 10)
        )

        shortcut_frame = ctk.CTkFrame(
            self.scroll_frame,
            corner_radius=10
        )

        shortcut_frame.pack(
            fill="x",
            padx=25,
            pady=5
        )

        shortcuts = [("Ctrl + H", "Home / Dashboard")]
        if self.user_data.get("role") == "admin":
            shortcuts.append(("Ctrl + S", "Open Students"))
        shortcuts.extend([
            ("Ctrl + F", "Open Fees"),
            ("Ctrl + R", "Refresh current page"),
            ("Ctrl + L", "Logout"),
            ("Ctrl + N", "Open Notifications"),
            ("Ctrl + D", "Toggle Theme"),
            ("Ctrl + Q", "Quit Application"),
        ])

        for key, description in shortcuts:

            row = ctk.CTkFrame(
                shortcut_frame,
                fg_color="transparent"
            )

            row.pack(
                fill="x",
                padx=15,
                pady=5
            )

            key_label = ctk.CTkLabel(
                row,
                text=key,
                width=110,
                anchor="w",
                font=ctk.CTkFont(
                    size=14,
                    weight="bold"
                )
            )

            key_label.pack(
                side="left"
            )

            description_label = ctk.CTkLabel(
                row,
                text=description,
                anchor="w",
                font=ctk.CTkFont(size=14)
            )

            description_label.pack(
                side="left",
                padx=15
            )

        # ==========================================
        # SETTINGS INFORMATION
        # ==========================================
        info_label = ctk.CTkLabel(
            self.scroll_frame,
            text="Settings Information",
            font=ctk.CTkFont(
                size=19,
                weight="bold"
            )
        )

        info_label.pack(
            anchor="w",
            padx=25,
            pady=(25, 10)
        )

        info_frame = ctk.CTkFrame(
            self.scroll_frame,
            corner_radius=10
        )

        info_frame.pack(
            fill="x",
            padx=25,
            pady=5
        )

        info_text = (
            "Your preferences are saved to the database.\n"
            "Theme and notification settings will remain active "
            "after restarting the application."
        )

        info = ctk.CTkLabel(
            info_frame,
            text=info_text,
            justify="left",
            anchor="w",
            font=ctk.CTkFont(size=13)
        )

        info.pack(
            fill="x",
            padx=20,
            pady=15
        )

        # ==========================================
        # BUTTONS
        # ==========================================
        button_frame = ctk.CTkFrame(
            self.scroll_frame,
            fg_color="transparent"
        )

        button_frame.pack(
            fill="x",
            padx=25,
            pady=30
        )

        save_button = ctk.CTkButton(
            button_frame,
            text="💾 Save Settings",
            width=180,
            height=42,
            command=self.save_settings
        )

        save_button.pack(
            side="left",
            padx=5
        )

        reset_button = ctk.CTkButton(
            button_frame,
            text="↻ Reset",
            width=130,
            height=42,
            fg_color="gray",
            hover_color="darkgray",
            command=self.reset_settings
        )

        reset_button.pack(
            side="right",
            padx=5
        )

    # ==========================================
    # LOAD SETTINGS
    # ==========================================
    @guard_authorization_errors
    def load_settings(self):

        self.user_data = load_actor(self.user_data)

        connection = get_connection()
        try:
            settings = connection.execute(
                "SELECT theme, notifications_enabled FROM user_settings WHERE user_id = ?",
                (self.user_data["id"],),
            ).fetchone()
        finally:
            connection.close()

        theme = str(settings[0] if settings and settings[0] else "light").lower()
        if theme not in {"light", "dark"}:
            theme = "light"
        notifications_enabled = (
            1 if settings is None or settings[1] is None else int(bool(settings[1]))
        )
        self.theme_menu.set(theme.capitalize())
        if notifications_enabled:
            self.notification_switch.select()
        else:
            self.notification_switch.deselect()
        ThemeManager.set_theme(theme)

    # ==========================================
    # SAVE SETTINGS
    # ==========================================
    @guard_authorization_errors
    def save_settings(self):

        self.user_data = load_actor(self.user_data)

        selected_theme = self.theme_menu.get().lower()
        if selected_theme not in {"light", "dark"}:
            messagebox.showwarning("Settings", "Choose Light or Dark theme.", parent=self)
            return

        notifications_enabled = (
            1
            if self.notification_switch.get() == 1
            else 0
        )

        connection = None
        try:
            connection = get_connection()
            existing = connection.execute(
                "SELECT id FROM user_settings WHERE user_id = ?",
                (self.user_data["id"],),
            ).fetchone()
            if existing:
                connection.execute(
                    "UPDATE user_settings SET theme = ?, notifications_enabled = ? WHERE user_id = ?",
                    (selected_theme, notifications_enabled, self.user_data["id"]),
                )
            else:
                connection.execute(
                    "INSERT INTO user_settings (user_id, theme, notifications_enabled) VALUES (?, ?, ?)",
                    (self.user_data["id"], selected_theme, notifications_enabled),
                )
            connection.commit()
        except Exception:
            if connection:
                connection.rollback()
            messagebox.showerror(
                "Error",
                "Failed to save settings. Please check your selection and try again.",
                parent=self,
            )
            self.load_settings()
            if hasattr(self.parent, "apply_visual_theme"):
                self.parent.apply_visual_theme()
            return
        finally:
            if connection:
                connection.close()

        ThemeManager.set_theme(selected_theme)
        if hasattr(self.parent, "apply_visual_theme"):
            self.parent.apply_visual_theme()
        messagebox.showinfo(
            "Settings",
            "Settings saved successfully.",
            parent=self,
        )

    # ==========================================
    # RESET SETTINGS
    # ==========================================
    @guard_authorization_errors
    def reset_settings(self):

        self.user_data = load_actor(self.user_data)

        confirm = messagebox.askyesno(
            "Reset Settings",
            "Are you sure you want to reset all settings?",
            parent=self
        )

        if not confirm:
            return

        connection = None
        try:
            connection = get_connection()
            existing = connection.execute(
                "SELECT id FROM user_settings WHERE user_id = ?",
                (self.user_data["id"],),
            ).fetchone()
            if existing:
                connection.execute(
                    "UPDATE user_settings SET theme = 'light', notifications_enabled = 1 WHERE user_id = ?",
                    (self.user_data["id"],),
                )
            else:
                connection.execute(
                    "INSERT INTO user_settings (user_id, theme, notifications_enabled) VALUES (?, 'light', 1)",
                    (self.user_data["id"],),
                )
            connection.commit()
        except Exception:
            if connection:
                connection.rollback()
            messagebox.showerror(
                "Error",
                "Failed to reset settings. Please try again.",
                parent=self,
            )
            self.load_settings()
            if hasattr(self.parent, "apply_visual_theme"):
                self.parent.apply_visual_theme()
            return
        finally:
            if connection:
                connection.close()

        self.theme_menu.set("Light")
        self.notification_switch.select()
        ThemeManager.set_theme("light")
        if hasattr(self.parent, "apply_visual_theme"):
            self.parent.apply_visual_theme()
        messagebox.showinfo(
            "Settings Reset",
            "Settings have been reset to default.",
            parent=self,
        )


# ==========================================
# STANDALONE TEST
# ==========================================
if __name__ == "__main__":

    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    test_user = {
        "id": 1,
        "username": "admin",
        "email": "admin@hostel.com",
        "role": "admin"
    }

    root = ctk.CTk()

    root.withdraw()

    window = SettingsWindow(
        root,
        test_user
    )

    window.mainloop()
