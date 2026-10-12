import customtkinter as ctk


class ShortcutManager:
    """
    Central keyboard shortcut manager.

    A window can provide callbacks for the shortcuts
    that it actually supports.
    """

    def __init__(
        self,
        window,
        home_callback=None,
        refresh_callback=None,
        students_callback=None,
        fees_callback=None,
        notifications_callback=None,
        logout_callback=None,
        theme_callback=None,
        exit_callback=None
    ):
        self.window = window

        self.home_callback = home_callback
        self.refresh_callback = refresh_callback
        self.students_callback = students_callback
        self.fees_callback = fees_callback
        self.notifications_callback = notifications_callback
        self.logout_callback = logout_callback
        self.theme_callback = theme_callback
        self.exit_callback = exit_callback

        self._bound_windows = set()
        self.bind_shortcuts(window)

    # =========================================================
    # BIND SHORTCUTS
    # =========================================================

    def attach_window(self, window):
        """Bind the application shortcuts to a dashboard or feature window."""
        self.bind_shortcuts(window)

    def bind_shortcuts(self, window):
        key = str(window)
        if key in self._bound_windows:
            return
        self._bound_windows.add(key)

        bindings = [
            ("<Control-h>", self.handle_home),
            ("<Control-r>", self.handle_refresh),
            ("<Control-l>", self.handle_logout),
            ("<Control-n>", self.handle_notifications),
            ("<Control-d>", self.handle_theme),
            ("<Control-q>", self.handle_exit),
            ("<F1>", self.show_shortcuts),
        ]
        if self.students_callback:
            bindings.append(("<Control-s>", self.handle_students))
        if self.fees_callback:
            bindings.append(("<Control-f>", self.handle_fees))

        for sequence, handler in bindings:
            window.bind(sequence, handler)

    # =========================================================
    # HOME
    # =========================================================

    def handle_home(self, event=None):

        if self.home_callback:
            self.home_callback()

        return "break"

    def handle_students(self, event=None):
        if self.students_callback:
            self.students_callback()
        return "break"

    def handle_fees(self, event=None):
        if self.fees_callback:
            self.fees_callback()
        return "break"

    def handle_notifications(self, event=None):
        if self.notifications_callback:
            self.notifications_callback()
        return "break"

    # =========================================================
    # REFRESH
    # =========================================================

    def handle_refresh(self, event=None):

        if self.refresh_callback:
            self.refresh_callback()

        return "break"

    # =========================================================
    # LOGOUT
    # =========================================================

    def handle_logout(self, event=None):

        if self.logout_callback:
            self.logout_callback()

        return "break"

    # =========================================================
    # THEME
    # =========================================================

    def handle_theme(self, event=None):

        if self.theme_callback:
            self.theme_callback()

        return "break"

    # =========================================================
    # EXIT
    # =========================================================

    def handle_exit(self, event=None):

        if self.exit_callback:
            self.exit_callback()

        return "break"

    # =========================================================
    # SHOW SHORTCUT HELP
    # =========================================================

    def show_shortcuts(self, event=None):

        help_window = ctk.CTkToplevel(
            self.window
        )

        help_window.title(
            "Keyboard Shortcuts"
        )

        help_window.geometry(
            "520x560"
        )

        help_window.resizable(
            False,
            False
        )

        help_window.transient(
            self.window
        )

        # =====================================================
        # Heading
        # =====================================================

        heading = ctk.CTkLabel(
            help_window,
            text="⌨ Keyboard Shortcuts",
            font=ctk.CTkFont(
                size=24,
                weight="bold"
            )
        )

        heading.pack(
            pady=(25, 10)
        )

        description = ctk.CTkLabel(
            help_window,
            text="Use these shortcuts to quickly control the application.",
            font=ctk.CTkFont(
                size=13
            )
        )

        description.pack(
            pady=(0, 20)
        )

        # =====================================================
        # Shortcut List
        # =====================================================

        shortcuts = [("Ctrl + H", "Go to Dashboard")]
        if self.students_callback:
            shortcuts.append(("Ctrl + S", "Open Students"))
        if self.fees_callback:
            shortcuts.append(("Ctrl + F", "Open Fees"))
        shortcuts.extend([
            ("Ctrl + R", "Refresh current page"),
            ("Ctrl + L", "Logout"),
        ])
        if self.notifications_callback:
            shortcuts.append(("Ctrl + N", "Open Notifications"))
        shortcuts.extend([
            ("Ctrl + D", "Toggle Theme"),
            ("Ctrl + Q", "Exit Application"),
            ("F1", "Show Keyboard Shortcuts"),
        ])

        for shortcut, description_text in shortcuts:

            row = ctk.CTkFrame(
                help_window
            )

            row.pack(
                fill="x",
                padx=35,
                pady=4
            )

            shortcut_label = ctk.CTkLabel(
                row,
                text=shortcut,
                width=120,
                anchor="w",
                font=ctk.CTkFont(
                    size=14,
                    weight="bold"
                )
            )

            shortcut_label.pack(
                side="left",
                padx=10,
                pady=8
            )

            description_label = ctk.CTkLabel(
                row,
                text=description_text,
                anchor="w",
                font=ctk.CTkFont(
                    size=13
                )
            )

            description_label.pack(
                side="left",
                padx=10,
                pady=8
            )

        # =====================================================
        # Close Button
        # =====================================================

        close_button = ctk.CTkButton(
            help_window,
            text="Close",
            width=130,
            command=help_window.destroy
        )

        close_button.pack(
            pady=25
        )

        # =====================================================
        # Window Focus
        # =====================================================

        help_window.lift()
        help_window.focus_force()
