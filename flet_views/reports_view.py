"""Modern SaaS Reports & Analytics Export View built with Flet."""

import flet as ft
import csv
import os
from pathlib import Path
from services.student_service import get_all_students
from services.fee_service import get_all_fees
from services.complaint_service import get_all_complaints
from services.attendance_service import get_all_attendance
from flet_views.theme import get_colors


def prompt_save_file(default_filename: str) -> str | None:
    """Prompt user to choose exact file destination using native Windows Save As dialog."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        file_path = filedialog.asksaveasfilename(
            parent=root,
            title="Save Export File As",
            initialfile=default_filename,
            defaultextension=".csv",
            filetypes=[("CSV Spreadsheet (*.csv)", "*.csv"), ("All Files (*.*)", "*.*")],
        )
        root.destroy()
        return file_path if file_path else None
    except Exception as e:
        print(f"Error opening save dialog: {e}")
        # Fallback to Desktop or Downloads if Tkinter fails
        desktop = Path.home() / "Desktop"
        if desktop.exists():
            return str(desktop / default_filename)
        return str(Path.cwd() / default_filename)


class ReportsSubView(ft.Column):
    def __init__(self, page: ft.Page, user: dict):
        super().__init__()
        self.app_page = page
        self.user = user
        self.expand = True
        self.spacing = 16

        self.controls = [
            self._build_header(),
            ft.Container(
                content=self._build_content(),
                expand=True,
                padding=24,
                border_radius=14,
                bgcolor=get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)["surface"],
                border=ft.Border.all(1, get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)["border"]),
            ),
        ]

    def _build_header(self) -> ft.Control:
        return ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("Executive Reports & Data Export", size=22, weight=ft.FontWeight.BOLD),
                        ft.Text("Download official CSV data sheets and audit records for institutional compliance", size=12, color=get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)["text_muted"]),
                    ],
                    spacing=2,
                    expand=True,
                ),
            ],
        )

    def _build_content(self) -> ft.Control:
        colors = get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)

        cards = [
            ("Students Roster", "Full list of active and inactive students, course, branch, and bed allocations.", "students_export.csv", self._export_students, ft.Icons.PEOPLE_ALT_ROUNDED, ft.Colors.INDIGO_500),
            ("Fee Invoices & Dues", "Financial statements, collected fees, outstanding balances, and payment modes.", "fees_export.csv", self._export_fees, ft.Icons.PAYMENTS_ROUNDED, ft.Colors.GREEN_500),
            ("Complaints & Tickets", "Service records, resolution rates, open issues, and priority status.", "complaints_export.csv", self._export_complaints, ft.Icons.REPORT_ROUNDED, ft.Colors.AMBER_500),
            ("Attendance Log", "Student daily movement timestamps, entry/exit logs, and leaves.", "attendance_export.csv", self._export_attendance, ft.Icons.CHECKLIST_ROUNDED, ft.Colors.BLUE_500),
        ]

        card_widgets = []
        for title, desc, filename, export_fn, icon, accent in cards:
            card_widgets.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Icon(icon, size=24, color=accent),
                                width=48,
                                height=48,
                                border_radius=12,
                                bgcolor=ft.Colors.with_opacity(0.12, accent),
                                alignment=ft.Alignment.CENTER,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(title, size=14, weight=ft.FontWeight.BOLD),
                                    ft.Text(desc, size=11, color=colors["text_muted"]),
                                    ft.Text(f"File: {filename}", size=10, weight=ft.FontWeight.BOLD, color=accent),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.FilledButton(
                                content=ft.Row([ft.Icon(ft.Icons.DOWNLOAD_ROUNDED, size=16), ft.Text("Export CSV", size=12)], spacing=6),
                                style=ft.ButtonStyle(
                                    bgcolor=accent,
                                    color=ft.Colors.WHITE,
                                    shape=ft.RoundedRectangleBorder(radius=8),
                                ),
                                on_click=lambda e, fn=export_fn: fn(),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=16,
                    ),
                    padding=18,
                    border_radius=12,
                    bgcolor=colors["surface_alt"],
                )
            )

        return ft.Column(
            controls=card_widgets,
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
        )

    def _show_export_dialog(self, filename: str, path: Path, record_count: int):
        colors = get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)

        def close_dialog(e):
            self.app_page.pop_dialog()

        def open_file(e):
            try:
                if os.name == "nt":
                    os.startfile(str(path))
            except Exception as ex:
                self._show_toast(f"Could not open file: {ex}", is_err=True)

        def open_folder(e):
            try:
                if os.name == "nt":
                    os.startfile(str(path.parent))
            except Exception as ex:
                self._show_toast(f"Could not open folder: {ex}", is_err=True)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=ft.Colors.GREEN_600, size=28),
                    ft.Text("Export Completed", weight=ft.FontWeight.BOLD, size=18),
                ],
                spacing=10,
            ),
            content=ft.Column(
                controls=[
                    ft.Text(f"Successfully exported {record_count} record(s) to CSV."),
                    ft.Container(height=6),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("File:", size=11, weight=ft.FontWeight.BOLD, color=colors["text_muted"]),
                                ft.Text(path.name, size=13, weight=ft.FontWeight.BOLD),
                                ft.Divider(height=10),
                                ft.Text("Saved Path:", size=11, weight=ft.FontWeight.BOLD, color=colors["text_muted"]),
                                ft.Text(str(path), size=11, selectable=True, color=ft.Colors.BLUE_600),
                            ],
                            spacing=3,
                        ),
                        padding=12,
                        border_radius=8,
                        bgcolor=colors["surface_alt"],
                        border=ft.Border.all(1, colors["border"]),
                    ),
                ],
                tight=True,
                spacing=4,
            ),
            actions=[
                ft.OutlinedButton(
                    content=ft.Row([ft.Icon(ft.Icons.FOLDER_OPEN_ROUNDED, size=16), ft.Text("Open Folder", size=12)], spacing=6),
                    on_click=open_folder,
                ),
                ft.FilledButton(
                    content=ft.Row([ft.Icon(ft.Icons.DESCRIPTION_ROUNDED, size=16), ft.Text("Open File", size=12)], spacing=6),
                    on_click=open_file,
                ),
                ft.TextButton("Close", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.app_page.show_dialog(dlg)
        self._show_toast(f"Exported to {path.name} successfully!")

    def _export_students(self):
        try:
            path_str = prompt_save_file("students_export.csv")
            if not path_str:
                return  # User clicked Cancel

            path = Path(path_str)
            records = get_all_students(actor=self.user)
            with open(path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "ID", "Student ID", "Name", "Parent Name", "Gender",
                    "Date of Birth", "Phone", "Email", "Address", "Course",
                    "Branch", "Year", "Admission Date", "Room Number", "Bed Number", "Status"
                ])
                for s in records:
                    writer.writerow([
                        s.get("id"),
                        s.get("student_id"),
                        s.get("name"),
                        s.get("parent_name"),
                        s.get("gender"),
                        s.get("date_of_birth"),
                        s.get("phone"),
                        s.get("email"),
                        s.get("address"),
                        s.get("course"),
                        s.get("branch"),
                        s.get("year"),
                        s.get("admission_date"),
                        s.get("room_number"),
                        s.get("bed_number"),
                        s.get("status"),
                    ])
            self._show_export_dialog(path.name, path, len(records))
        except Exception as e:
            self._show_toast(f"Export failed: {e}", is_err=True)

    def _export_fees(self):
        try:
            path_str = prompt_save_file("fees_export.csv")
            if not path_str:
                return  # User clicked Cancel

            path = Path(path_str)
            records = get_all_fees(actor=self.user)
            with open(path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Fee ID", "Student ID", "Student Name", "Total Amount",
                    "Due Date", "Status", "Paid Amount", "Pending Amount"
                ])
                for row in records:
                    writer.writerow(list(row))
            self._show_export_dialog(path.name, path, len(records))
        except Exception as e:
            self._show_toast(f"Export failed: {e}", is_err=True)

    def _export_complaints(self):
        try:
            path_str = prompt_save_file("complaints_export.csv")
            if not path_str:
                return  # User clicked Cancel

            path = Path(path_str)
            records = get_all_complaints(actor=self.user)
            with open(path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Ticket ID", "Student ID", "Student Name", "Category",
                    "Description", "Priority", "Status", "Assigned Staff",
                    "Created At", "Resolved At", "Resolution Remarks"
                ])
                for row in records:
                    writer.writerow(list(row))
            self._show_export_dialog(path.name, path, len(records))
        except Exception as e:
            self._show_toast(f"Export failed: {e}", is_err=True)

    def _export_attendance(self):
        try:
            path_str = prompt_save_file("attendance_export.csv")
            if not path_str:
                return  # User clicked Cancel

            path = Path(path_str)
            records = get_all_attendance(actor=self.user)
            with open(path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Log ID", "Student ID", "Student Name",
                    "Entry Time", "Exit Time", "Attendance Date"
                ])
                for row in records:
                    writer.writerow(list(row))
            self._show_export_dialog(path.name, path, len(records))
        except Exception as e:
            self._show_toast(f"Export failed: {e}", is_err=True)

    def _show_toast(self, message: str, is_err: bool = False):
        try:
            sb = ft.SnackBar(
                content=ft.Text(message, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.RED_600 if is_err else ft.Colors.GREEN_600,
                behavior=ft.SnackBarBehavior.FLOATING,
                shape=ft.RoundedRectangleBorder(radius=10),
                duration=ft.Duration(seconds=3),
                show_close_icon=True,
            )
            self.app_page.show_dialog(sb)
        except Exception:
            pass
