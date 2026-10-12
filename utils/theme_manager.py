import customtkinter as ctk


class ThemeManager:
    """
    Handles application-wide theme settings.
    """

    LIGHT_MODE = "light"
    DARK_MODE = "dark"

    @staticmethod
    def load_user_theme(user_id):
        """Load a user's saved theme, defaulting to light when none is saved."""
        from database import get_connection

        connection = get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT theme FROM user_settings WHERE user_id = ?",
                (user_id,),
            )
            row = cursor.fetchone()
            theme = str(row[0]).lower() if row and row[0] else ThemeManager.LIGHT_MODE
            return theme if theme in (ThemeManager.LIGHT_MODE, ThemeManager.DARK_MODE) else ThemeManager.LIGHT_MODE
        finally:
            connection.close()

    @staticmethod
    def save_user_theme(user_id, theme):
        """Persist only the theme preference while preserving other settings."""
        from database import get_connection

        theme = str(theme).lower()
        if theme not in (ThemeManager.LIGHT_MODE, ThemeManager.DARK_MODE):
            raise ValueError("Theme must be 'light' or 'dark'.")

        connection = get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE user_settings SET theme = ? WHERE user_id = ?",
                (theme, user_id),
            )
            if cursor.rowcount == 0:
                cursor.execute(
                    "INSERT INTO user_settings (user_id, theme) VALUES (?, ?)",
                    (user_id, theme),
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def set_theme(theme):
        """
        Set application appearance mode.
        """
        if theme == ThemeManager.DARK_MODE:
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")

    @staticmethod
    def get_current_theme():
        """
        Return current application theme.
        """
        current_mode = ctk.get_appearance_mode()

        if current_mode.lower() == "dark":
            return ThemeManager.DARK_MODE

        return ThemeManager.LIGHT_MODE

    @staticmethod
    def toggle_theme():
        """
        Toggle between light and dark mode.
        """
        current_theme = ThemeManager.get_current_theme()

        if current_theme == ThemeManager.LIGHT_MODE:
            ThemeManager.set_theme(ThemeManager.DARK_MODE)
            return ThemeManager.DARK_MODE

        ThemeManager.set_theme(ThemeManager.LIGHT_MODE)
        return ThemeManager.LIGHT_MODE


if __name__ == "__main__":
    print("Current Theme:", ThemeManager.get_current_theme())

    new_theme = ThemeManager.toggle_theme()

    print("Theme after toggle:", new_theme)
