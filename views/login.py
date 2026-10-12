import customtkinter as ctk
from tkinter import messagebox

from services.auth_service import login_user
from views.dashboard import DashboardWindow


class LoginWindow(ctk.CTk):
    """Clean, welcoming sign-in screen for the local hostel application."""

    def __init__(self):
        super().__init__()

        ctk.set_default_color_theme("blue")

        self.title("Hostel Management System | Log in")
        self.geometry("980x650")
        self.minsize(900, 600)
        self.configure(fg_color="#edf2f8")
        self.resizable(True, True)

        self.create_widgets()
        self.bind("<Return>", lambda event: self.handle_login())
        self.after(40, self.center_window)

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = max(0, (self.winfo_screenwidth() - width) // 2)
        y = max(0, (self.winfo_screenheight() - height) // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        self.container = ctk.CTkFrame(
            self,
            fg_color="#ffffff",
            corner_radius=24,
            border_width=1,
            border_color="#dce5ef",
        )
        self.container.pack(fill="both", expand=True, padx=26, pady=26)
        self.container.grid_columnconfigure(0, weight=4, minsize=330)
        self.container.grid_columnconfigure(1, weight=5, minsize=440)
        self.container.grid_rowconfigure(0, weight=1)

        self.create_brand_panel()
        self.create_login_panel()

    def create_brand_panel(self):
        panel = ctk.CTkFrame(
            self.container,
            fg_color="#12324f",
            corner_radius=20,
        )
        panel.grid(row=0, column=0, sticky="nsew", padx=(6, 10), pady=6)

        content = ctk.CTkFrame(panel, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=34, pady=34)

        mark = ctk.CTkLabel(
            content,
            text="H",
            width=58,
            height=58,
            corner_radius=18,
            fg_color="#1f83a8",
            text_color="#ffffff",
            font=ctk.CTkFont(size=30, weight="bold"),
        )
        mark.pack(anchor="w", pady=(4, 34))

        ctk.CTkLabel(
            content,
            text="HOSTEL LIFE,\nMADE EASIER.",
            justify="left",
            anchor="w",
            text_color="#ffffff",
            font=ctk.CTkFont(size=27, weight="bold"),
        ).pack(fill="x", anchor="w")

        ctk.CTkLabel(
            content,
            text="Hostel Management System",
            justify="left",
            anchor="w",
            text_color="#c6d8e7",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(fill="x", anchor="w", pady=(12, 0))

        ctk.CTkLabel(
            content,
            text=(
                "A simpler way for students and administrators "
                "to stay informed, connected, and on top of hostel life."
            ),
            justify="left",
            anchor="w",
            wraplength=270,
            text_color="#b5c9d9",
            font=ctk.CTkFont(size=13),
        ).pack(fill="x", anchor="w", pady=(12, 0))

    def create_login_panel(self):
        panel = ctk.CTkFrame(self.container, fg_color="transparent", corner_radius=0)
        panel.grid(row=0, column=1, sticky="nsew", padx=(12, 24), pady=24)
        panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            panel,
            text="Welcome back",
            anchor="w",
            text_color="#17324d",
            font=ctk.CTkFont(size=29, weight="bold"),
        ).grid(row=0, column=0, sticky="ew", pady=(44, 6))

        ctk.CTkLabel(
            panel,
            text="Log in to continue to your hostel account.",
            anchor="w",
            text_color="#718096",
            font=ctk.CTkFont(size=14),
        ).grid(row=1, column=0, sticky="ew", pady=(0, 30))

        ctk.CTkLabel(
            panel,
            text="USERNAME",
            anchor="w",
            text_color="#42566b",
            font=ctk.CTkFont(size=11, weight="bold"),
        ).grid(row=2, column=0, sticky="ew", pady=(0, 8))

        self.username_entry = ctk.CTkEntry(
            panel,
            height=48,
            corner_radius=11,
            border_width=1,
            border_color="#d3deea",
            fg_color="#f8fafc",
            text_color="#1d2d3e",
            placeholder_text="Enter your username",
            placeholder_text_color="#98a6b5",
            font=ctk.CTkFont(size=14),
        )
        self.username_entry.grid(row=3, column=0, sticky="ew", pady=(0, 20))

        ctk.CTkLabel(
            panel,
            text="PASSWORD",
            anchor="w",
            text_color="#42566b",
            font=ctk.CTkFont(size=11, weight="bold"),
        ).grid(row=4, column=0, sticky="ew", pady=(0, 8))

        self.password_entry = ctk.CTkEntry(
            panel,
            height=48,
            corner_radius=11,
            border_width=1,
            border_color="#d3deea",
            fg_color="#f8fafc",
            text_color="#1d2d3e",
            placeholder_text="Enter your password",
            placeholder_text_color="#98a6b5",
            show="*",
            font=ctk.CTkFont(size=14),
        )
        self.password_entry.grid(row=5, column=0, sticky="ew", pady=(0, 10))

        self.show_password_var = ctk.BooleanVar(value=False)
        self.show_password_checkbox = ctk.CTkCheckBox(
            panel,
            text="Show password",
            variable=self.show_password_var,
            command=self.toggle_password,
            checkbox_width=18,
            checkbox_height=18,
            corner_radius=5,
            text_color="#526579",
            font=ctk.CTkFont(size=12),
        )
        self.show_password_checkbox.grid(row=6, column=0, sticky="w", pady=(0, 14))

        self.forgot_password_button = ctk.CTkButton(
            panel,
            text="Forgot password?",
            height=24,
            fg_color="transparent",
            hover_color="#edf5f9",
            text_color="#176c91",
            anchor="e",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.show_password_help,
        )
        self.forgot_password_button.grid(row=7, column=0, sticky="e", pady=(0, 4))

        self.status_label = ctk.CTkLabel(
            panel,
            text="",
            anchor="w",
            justify="left",
            height=24,
            wraplength=430,
            text_color="#b42332",
            font=ctk.CTkFont(size=12),
        )
        self.status_label.grid(row=8, column=0, sticky="ew", pady=(0, 4))

        self.login_button = ctk.CTkButton(
            panel,
            text="Log in",
            height=49,
            corner_radius=11,
            fg_color="#176c91",
            hover_color="#125777",
            text_color="#ffffff",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.handle_login,
        )
        self.login_button.grid(row=9, column=0, sticky="ew", pady=(4, 16))

        ctk.CTkLabel(
            panel,
            text="Your account is for authorized hostel users only.",
            anchor="w",
            text_color="#8a98a8",
            font=ctk.CTkFont(size=11),
        ).grid(row=10, column=0, sticky="ew", pady=(0, 10))

        panel.grid_rowconfigure(11, weight=1)
        self.username_entry.focus_set()

    def show_password_help(self):
        messagebox.showinfo(
            "Password help",
            "Self-service password reset is not available. Please contact your hostel administrator to reset your password.",
            parent=self,
        )

    def set_status(self, text, success=False):
        self.status_label.configure(
            text=text,
            text_color="#16805a" if success else "#b42332",
        )

    def toggle_password(self):
        self.password_entry.configure(
            show="" if self.show_password_var.get() else "*"
        )

    def handle_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            self.set_status("Enter both your username and password.")
            (self.username_entry if not username else self.password_entry).focus_set()
            return

        self.login_button.configure(state="disabled", text="Logging in…")
        self.set_status("Checking your account…", success=True)
        self.update_idletasks()

        try:
            success, result = login_user(username, password)
        except Exception:
            self.login_button.configure(state="normal", text="Log in")
            self.set_status("Sign-in is temporarily unavailable. Please try again.")
            return

        if not success:
            self.login_button.configure(state="normal", text="Log in")
            self.set_status(result)
            self.password_entry.focus_set()
            return

        self.set_status("Logged in successfully.", success=True)
        self.destroy()
        dashboard = DashboardWindow(result)
        dashboard.mainloop()


if __name__ == "__main__":
    app = LoginWindow()
    app.mainloop()
