import customtkinter as ctk
from tkinter import messagebox
from utils.authorization import require_menu_access, guard_authorization_errors
from utils.authorization import load_actor
from utils.ui_theme import apply_professional_style

from services.notification_service import (
    create_notification,
    get_user_notifications,
    get_unread_count,
    get_all_users,
    mark_notification_as_read,
    mark_all_as_read,
    delete_notification,
    create_announcement,
)


class NotificationsWindow(ctk.CTkToplevel):
    ANNOUNCEMENT_TARGET = "All opted-in accounts — Announcement"

    def __init__(self, parent, user):
        require_menu_access(user, "Notifications")
        super().__init__(parent)

        self.parent = parent
        self.user = load_actor(user)

        self.title("Hostel Management System - Notifications")
        self.geometry("1000x700")
        self.minsize(850, 600)

        self.transient(parent)

        # Store users for dropdown
        self.users = []

        # Create UI
        self.create_ui()

        # Load notifications
        self.load_notifications()
        apply_professional_style(self)

        # Bring window to front
        self.lift()
        self.focus_force()

    # =========================================================
    # CREATE UI
    # =========================================================

    def create_ui(self):

        # =====================================================
        # HEADER
        # =====================================================

        header = ctk.CTkFrame(
            self
        )

        header.pack(
            fill="x",
            padx=20,
            pady=20
        )

        title = ctk.CTkLabel(
            header,
            text="Notifications",
            font=ctk.CTkFont(
                size=26,
                weight="bold"
            )
        )

        title.pack(
            side="left",
            padx=20,
            pady=15
        )

        self.unread_label = ctk.CTkLabel(
            header,
            text="Unread: 0",
            font=ctk.CTkFont(
                size=16,
                weight="bold"
            )
        )

        self.unread_label.pack(
            side="right",
            padx=20
        )

        # =====================================================
        # ADMIN CREATE NOTIFICATION
        # =====================================================

        if self.user.get("role", "").lower() == "admin":

            self.create_notification_section()

        # =====================================================
        # ACTION BUTTONS
        # =====================================================

        button_frame = ctk.CTkFrame(
            self
        )

        button_frame.pack(
            fill="x",
            padx=20,
            pady=(0, 10)
        )

        refresh_button = ctk.CTkButton(
            button_frame,
            text="Refresh",
            width=120,
            command=self.load_notifications
        )

        refresh_button.pack(
            side="left",
            padx=10,
            pady=10
        )

        mark_all_button = ctk.CTkButton(
            button_frame,
            text="Mark All as Read",
            width=150,
            command=self.mark_all_read
        )

        mark_all_button.pack(
            side="left",
            padx=10,
            pady=10
        )

        # =====================================================
        # NOTIFICATIONS LIST
        # =====================================================

        self.notification_frame = ctk.CTkScrollableFrame(
            self,
            label_text="Your Notifications"
        )

        self.notification_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

    # =========================================================
    # CREATE NOTIFICATION SECTION
    # =========================================================

    def create_notification_section(self):

        self.create_frame = ctk.CTkFrame(
            self
        )

        self.create_frame.pack(
            fill="x",
            padx=20,
            pady=(0, 10)
        )

        # =====================================================
        # Section Title
        # =====================================================

        create_title = ctk.CTkLabel(
            self.create_frame,
            text="Create Notification",
            font=ctk.CTkFont(
                size=18,
                weight="bold"
            )
        )

        create_title.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            padx=15,
            pady=(15, 10)
        )

        # =====================================================
        # User Dropdown
        # =====================================================

        user_label = ctk.CTkLabel(
            self.create_frame,
            text="Send To:"
        )

        user_label.grid(
            row=1,
            column=0,
            padx=15,
            pady=8,
            sticky="w"
        )

        self.user_dropdown = ctk.CTkComboBox(
            self.create_frame,
            width=250
        )

        self.user_dropdown.grid(
            row=1,
            column=1,
            padx=15,
            pady=8,
            sticky="w"
        )

        # =====================================================
        # Title Entry
        # =====================================================

        title_label = ctk.CTkLabel(
            self.create_frame,
            text="Title:"
        )

        title_label.grid(
            row=2,
            column=0,
            padx=15,
            pady=8,
            sticky="w"
        )

        self.title_entry = ctk.CTkEntry(
            self.create_frame,
            width=400,
            placeholder_text="Enter notification title"
        )

        self.title_entry.grid(
            row=2,
            column=1,
            padx=15,
            pady=8,
            sticky="w"
        )

        # =====================================================
        # Message
        # =====================================================

        message_label = ctk.CTkLabel(
            self.create_frame,
            text="Message:"
        )

        message_label.grid(
            row=3,
            column=0,
            padx=15,
            pady=8,
            sticky="nw"
        )

        self.message_entry = ctk.CTkTextbox(
            self.create_frame,
            width=400,
            height=80
        )

        self.message_entry.grid(
            row=3,
            column=1,
            padx=15,
            pady=8,
            sticky="w"
        )

        # =====================================================
        # Send Button
        # =====================================================

        send_button = ctk.CTkButton(
            self.create_frame,
            text="Send Notification",
            width=180,
            command=self.send_notification
        )

        send_button.grid(
            row=4,
            column=1,
            padx=15,
            pady=(5, 15),
            sticky="w"
        )

        # Load users into dropdown
        self.load_users()

    # =========================================================
    # LOAD USERS
    # =========================================================

    @guard_authorization_errors
    def load_users(self):

        if not hasattr(self, "user_dropdown"):
            return

        self.users = get_all_users(actor=self.user)

        user_values = []

        for user in self.users:

            user_id, username, role = user

            user_values.append(
                f"{username} ({role})"
            )

        user_values.append(self.ANNOUNCEMENT_TARGET)

        if not self.users:
            user_values.insert(0, "No users found")

        self.user_dropdown.configure(
            values=user_values
        )

        self.user_dropdown.set(
            user_values[0]
        )

    # =========================================================
    # SEND NOTIFICATION
    # =========================================================

    @guard_authorization_errors
    def send_notification(self):

        # Get selected user
        selected_user = self.user_dropdown.get().strip()

        if not selected_user:
            messagebox.showwarning(
                "Validation",
                "Please select a user."
            )
            return

        if selected_user == "No users found":
            messagebox.showwarning(
                "Validation",
                "No active users are available."
            )
            return

        # Find selected user's ID; announcements broadcast to opted-in active accounts.
        selected_user_id = None

        if selected_user != self.ANNOUNCEMENT_TARGET:
            for user in self.users:
                user_id, username, role = user
                if f"{username} ({role})" == selected_user:
                    selected_user_id = user_id
                    break

        if selected_user != self.ANNOUNCEMENT_TARGET and selected_user_id is None:

            messagebox.showerror(
                "Error",
                "Selected user could not be found."
            )

            return

        # Get title
        title = self.title_entry.get().strip()

        # Get message
        message = self.message_entry.get(
            "1.0",
            "end"
        ).strip()

        # Validation
        if not title:

            messagebox.showwarning(
                "Validation",
                "Please enter notification title."
            )

            return

        if not message:

            messagebox.showwarning(
                "Validation",
                "Please enter notification message."
            )

            return

        # Create notification
        if selected_user == self.ANNOUNCEMENT_TARGET:
            success, result_message = create_announcement(title, message, actor=self.user)
        else:
            success, result_message = create_notification(
                selected_user_id,
                title,
                message,
                actor=self.user
            )

        if success:

            messagebox.showinfo(
                "Success",
                result_message
            )

            # Clear fields
            self.title_entry.delete(
                0,
                "end"
            )

            self.message_entry.delete(
                "1.0",
                "end"
            )

            # Refresh current notifications
            self.load_notifications()
            if hasattr(self.parent, "update_notification_count"):
                self.parent.update_notification_count()

        else:

            messagebox.showerror(
                "Error",
                result_message
            )

    # =========================================================
    # LOAD NOTIFICATIONS
    # =========================================================

    @guard_authorization_errors
    def load_notifications(self):

        # Remove old notification cards
        for widget in self.notification_frame.winfo_children():

            widget.destroy()

        user_id = self.user.get("id")

        if not user_id:

            messagebox.showerror(
                "Error",
                "User information is missing."
            )

            return

        # Get notifications
        notifications = get_user_notifications(
            user_id,
            actor=self.user
        )

        # Get unread count
        unread_count = get_unread_count(
            user_id,
            actor=self.user
        )

        self.unread_label.configure(
            text=f"Unread: {unread_count}"
        )

        # No notifications
        if not notifications:

            empty_label = ctk.CTkLabel(
                self.notification_frame,
                text="No notifications found.",
                font=ctk.CTkFont(
                    size=16
                )
            )

            empty_label.pack(
                pady=40
            )
            apply_professional_style(self)

            return

        # Create cards
        for notification in notifications:

            self.create_notification_card(
                notification
            )
        apply_professional_style(self)

    # =========================================================
    # NOTIFICATION CARD
    # =========================================================

    def create_notification_card(
        self,
        notification
    ):

        (
            notification_id,
            title,
            message,
            is_read,
            created_at
        ) = notification

        # Different border for unread
        if is_read:

            card = ctk.CTkFrame(
                self.notification_frame
            )

        else:

            card = ctk.CTkFrame(
                self.notification_frame,
                border_width=2
            )

        card.pack(
            fill="x",
            padx=10,
            pady=8
        )

        # =====================================================
        # TITLE
        # =====================================================

        if is_read:

            title_text = title

        else:

            title_text = f"● {title}"

        title_label = ctk.CTkLabel(
            card,
            text=title_text,
            font=ctk.CTkFont(
                size=17,
                weight="bold"
            ),
            anchor="w"
        )

        title_label.pack(
            fill="x",
            padx=15,
            pady=(12, 5)
        )

        # =====================================================
        # MESSAGE
        # =====================================================

        message_label = ctk.CTkLabel(
            card,
            text=message,
            font=ctk.CTkFont(
                size=14
            ),
            anchor="w",
            justify="left",
            wraplength=700
        )

        message_label.pack(
            fill="x",
            padx=15,
            pady=5
        )

        # =====================================================
        # CREATED DATE
        # =====================================================

        date_label = ctk.CTkLabel(
            card,
            text=f"Created: {created_at}",
            font=ctk.CTkFont(
                size=12
            ),
            anchor="w"
        )

        date_label.pack(
            fill="x",
            padx=15,
            pady=5
        )

        # =====================================================
        # ACTION BUTTONS
        # =====================================================

        action_frame = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        action_frame.pack(
            fill="x",
            padx=15,
            pady=(5, 12)
        )

        # Mark as Read
        if not is_read:

            read_button = ctk.CTkButton(
                action_frame,
                text="Mark as Read",
                width=130,
                command=lambda notification_id=notification_id:
                self.mark_read(notification_id)
            )

            read_button.pack(
                side="left",
                padx=(0, 10)
            )

        # Delete
        delete_button = ctk.CTkButton(
            action_frame,
            text="Delete",
            width=100,
            fg_color="red",
            hover_color="darkred",
            command=lambda notification_id=notification_id:
            self.delete_notification_clicked(
                notification_id
            )
        )

        if self.user["role"] == "admin":
            delete_button.pack(side="left")

    # =========================================================
    # MARK ONE AS READ
    # =========================================================

    @guard_authorization_errors
    def mark_read(
        self,
        notification_id
    ):

        success, message = mark_notification_as_read(
            notification_id,
            actor=self.user
        )

        if success:

            self.load_notifications()

            # Update dashboard notification count
            if hasattr(
                self.parent,
                "update_notification_count"
            ):

                self.parent.update_notification_count()

        else:

            messagebox.showerror(
                "Error",
                message
            )

    # =========================================================
    # MARK ALL AS READ
    # =========================================================

    @guard_authorization_errors
    def mark_all_read(self):

        user_id = self.user.get("id")

        success, message = mark_all_as_read(
            user_id,
            actor=self.user
        )

        if success:

            self.load_notifications()

            # Update dashboard notification count
            if hasattr(
                self.parent,
                "update_notification_count"
            ):

                self.parent.update_notification_count()

        else:

            messagebox.showerror(
                "Error",
                message
            )

    # =========================================================
    # DELETE NOTIFICATION
    # =========================================================

    @guard_authorization_errors
    def delete_notification_clicked(
        self,
        notification_id
    ):

        confirm = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this notification?"
        )

        if not confirm:
            return

        success, message = delete_notification(
            notification_id,
            actor=self.user
        )

        if success:

            self.load_notifications()

            # Update dashboard notification count
            if hasattr(
                self.parent,
                "update_notification_count"
            ):

                self.parent.update_notification_count()

        else:

            messagebox.showerror(
                "Error",
                message
            )


# =============================================================
# DIRECT TEST
# =============================================================

if __name__ == "__main__":

    root = ctk.CTk()

    root.withdraw()

    test_user = {
        "id": 1,
        "username": "admin",
        "email": "admin@hostel.com",
        "role": "admin"
    }

    app = NotificationsWindow(
        root,
        test_user
    )

    app.mainloop()
