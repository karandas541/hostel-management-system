"""Modern SaaS Fee & Payment Tracker View built with Flet."""

import flet as ft
from services.fee_service import get_all_fees, make_payment, add_fee
from flet_views.theme import get_colors, attach_date_picker
from datetime import datetime, timedelta


class FeesSubView(ft.Column):
    def __init__(self, page: ft.Page, user: dict):
        super().__init__()
        self.app_page = page
        self.user = user
        self.expand = True
        self.spacing = 16

        self.table_container = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

        self.controls = [
            self._build_header(),
            ft.Container(
                content=self.table_container,
                expand=True,
                padding=16,
                border_radius=14,
                bgcolor=get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)["surface"],
                border=ft.Border.all(1, get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)["border"]),
            ),
        ]
        self.load_data()

    def _build_header(self) -> ft.Control:
        is_admin = self.user.get("role") == "admin"
        return ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("Fee Management & Invoices", size=22, weight=ft.FontWeight.BOLD),
                        ft.Text("Track dues, issue fees, and process UPI / Cash payments", size=12, color=get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)["text_muted"]),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.FilledButton(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.ADD_CARD_ROUNDED, size=16, color=ft.Colors.WHITE),
                            ft.Text("Assign Fee", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ],
                        spacing=6,
                    ),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.INDIGO_600,
                        shape=ft.RoundedRectangleBorder(radius=10),
                        padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                    ),
                    visible=is_admin,
                    on_click=self._open_add_fee_dialog,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _build_kpi_card(self, title: str, value: str, icon, icon_color, colors: dict) -> ft.Control:
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(icon, size=20, color=icon_color),
                        width=38,
                        height=38,
                        border_radius=10,
                        bgcolor=ft.Colors.with_opacity(0.12, icon_color),
                        alignment=ft.Alignment.CENTER,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(title, size=11, weight=ft.FontWeight.W_500, color=colors["text_muted"]),
                            ft.Text(value, size=15, weight=ft.FontWeight.BOLD),
                        ],
                        spacing=1,
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=16, vertical=12),
            border_radius=10,
            bgcolor=colors["surface_alt"],
            border=ft.Border.all(1, colors["border"]),
            expand=True,
        )

    def load_data(self):
        colors = get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)
        try:
            fees = get_all_fees(actor=self.user)
            if not fees:
                self.table_container.controls = [
                    ft.Container(
                        content=ft.Text("No fees or invoices found.", color=colors["text_muted"]),
                        alignment=ft.Alignment.CENTER,
                        padding=40,
                    )
                ]
                self.app_page.update()
                return

            is_admin = self.user.get("role") == "admin"
            total_invoiced = sum(f[3] for f in fees)
            total_paid = sum(f[6] for f in fees)
            total_pending = sum(f[7] for f in fees)

            kpi_cards = ft.Row(
                controls=[
                    self._build_kpi_card("Total Invoiced", f"₹{total_invoiced:,.2f}", ft.Icons.RECEIPT_LONG_ROUNDED, ft.Colors.INDIGO_400, colors),
                    self._build_kpi_card("Total Collected / Paid", f"₹{total_paid:,.2f}", ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED, ft.Colors.GREEN_500, colors),
                    self._build_kpi_card("Pending Balance", f"₹{total_pending:,.2f}", ft.Icons.PENDING_ACTIONS_ROUNDED, ft.Colors.RED_500 if total_pending > 0 else ft.Colors.GREEN_500, colors),
                ],
                spacing=14,
            )

            rows = []
            for f in fees:
                # f: (id, student_id, name, amount, due_date, status, paid_amount, pending_amount)
                fee_id, stu_code, stu_name, total_amt, due_date, status, paid_amt, pending_amt = f

                status_color = ft.Colors.GREEN_500 if status == "Paid" else (ft.Colors.AMBER_500 if status == "Partial" else ft.Colors.RED_500)
                status_chip = ft.Container(
                    content=ft.Text(status, size=10, weight=ft.FontWeight.BOLD, color=status_color),
                    padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                    border_radius=12,
                    bgcolor=ft.Colors.with_opacity(0.12, status_color),
                )

                cells = [
                    ft.DataCell(ft.Text(f"INV-{fee_id:04d}", weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(f"{stu_name} ({stu_code})", weight=ft.FontWeight.W_500)),
                    ft.DataCell(ft.Text(f"₹{total_amt:,.2f}")),
                    ft.DataCell(ft.Text(f"₹{paid_amt:,.2f}", color=ft.Colors.GREEN_600)),
                    ft.DataCell(ft.Text(f"₹{pending_amt:,.2f}", color=ft.Colors.RED_500 if pending_amt > 0 else colors["text_muted"], weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(due_date or "—")),
                    ft.DataCell(status_chip),
                ]

                if is_admin:
                    pay_btn = ft.Container()
                    if pending_amt > 0:
                        pay_btn = ft.TextButton(
                            "Collect / Pay",
                            icon=ft.Icons.PAYMENTS_ROUNDED,
                            icon_color=ft.Colors.INDIGO_500,
                            on_click=lambda e, fid=fee_id, pamt=pending_amt: self._open_payment_dialog(fid, pamt),
                        )
                    cells.append(ft.DataCell(pay_btn))

                rows.append(ft.DataRow(cells=cells))

            columns = [
                ft.DataColumn(ft.Text("INVOICE #", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
                ft.DataColumn(ft.Text("STUDENT", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
                ft.DataColumn(ft.Text("TOTAL AMOUNT", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
                ft.DataColumn(ft.Text("PAID", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
                ft.DataColumn(ft.Text("PENDING", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
                ft.DataColumn(ft.Text("DUE DATE", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
                ft.DataColumn(ft.Text("STATUS", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
            ]
            if is_admin:
                columns.append(ft.DataColumn(ft.Text("ACTION", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])))

            col_spacing = 32 if is_admin else 55
            table = ft.DataTable(
                columns=columns,
                rows=rows,
                border_radius=10,
                heading_row_color=colors["surface_alt"],
                column_spacing=col_spacing,
                data_row_min_height=48,
                heading_row_height=44,
            )

            self.table_container.controls = [
                kpi_cards,
                ft.Divider(height=16, color=ft.Colors.TRANSPARENT),
                ft.Container(
                    content=table,
                    alignment=ft.Alignment.TOP_LEFT,
                ),
            ]
            self.app_page.update()
        except Exception as err:
            self.table_container.controls = [ft.Text(f"Error loading fees: {err}", color=ft.Colors.RED_400)]
            self.app_page.update()

    def _open_payment_dialog(self, fee_id: int, pending_amount: float):
        amt_field = ft.TextField(label="Payment Amount (₹)", value=f"{pending_amount:.2f}", border_radius=8)
        mode_dropdown = ft.Dropdown(
            label="Payment Mode",
            value="UPI",
            options=[
                ft.dropdown.Option("UPI"),
                ft.dropdown.Option("Cash"),
                ft.dropdown.Option("Card"),
                ft.dropdown.Option("Net Banking"),
                ft.dropdown.Option("Bank Transfer"),
            ],
            border_radius=8,
        )
        receipt_field = ft.TextField(label="Receipt / Ref ID (Optional)", hint_text="Auto-generated if empty", border_radius=8)

        dlg = ft.AlertDialog(
            title=ft.Text(f"Record Payment (INV-{fee_id:04d})", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([amt_field, mode_dropdown, receipt_field], spacing=10),
                width=340,
                height=220,
            ),
            actions=[
                ft.TextButton(content="Cancel", on_click=lambda _: self._close_dialog(dlg)),
                ft.FilledButton(
                    "Confirm Payment",
                    bgcolor=ft.Colors.GREEN_600,
                    color=ft.Colors.WHITE,
                    on_click=lambda _: self._submit_payment(dlg, fee_id, amt_field.value, mode_dropdown.value, receipt_field.value),
                ),
            ],
        )
        self.app_page.overlay.append(dlg)
        dlg.open = True
        self.app_page.update()

    def _submit_payment(self, dlg, fee_id, amount, mode, receipt):
        try:
            amt = float(amount)
            success, msg = make_payment(
                fee_id=fee_id,
                amount=amt,
                payment_mode=mode,
                receipt_number=receipt.strip() or None,
                actor=self.user,
            )
            if success:
                dlg.open = False
                self.load_data()
                self.app_page.snack_bar = ft.SnackBar(ft.Text("Payment recorded successfully!"), bgcolor=ft.Colors.GREEN_600)
                self.app_page.snack_bar.open = True
            else:
                self.app_page.snack_bar = ft.SnackBar(ft.Text(f"Failed: {msg}"), bgcolor=ft.Colors.RED_600)
                self.app_page.snack_bar.open = True
        except Exception as e:
            self.app_page.snack_bar = ft.SnackBar(ft.Text(f"Error: {e}"), bgcolor=ft.Colors.RED_600)
            self.app_page.snack_bar.open = True
        self.app_page.update()

    def _open_add_fee_dialog(self, _):
        stu_id_field = ft.TextField(label="Student ID (e.g. STU001)", border_radius=8)
        amt_field = ft.TextField(label="Fee Amount (₹)", border_radius=8)
        default_due = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        due_date_field = ft.TextField(
            label="Due Date (YYYY-MM-DD)",
            value=default_due,
            hint_text="YYYY-MM-DD",
            border_radius=8,
            prefix_icon=ft.Icons.CALENDAR_MONTH_ROUNDED,
        )
        attach_date_picker(due_date_field, self.app_page, first_date=datetime(2020, 1, 1), last_date=datetime(2035, 12, 31))

        dlg = ft.AlertDialog(
            title=ft.Text("Assign New Fee", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([stu_id_field, amt_field, due_date_field], spacing=10),
                width=340,
                height=220,
            ),
            actions=[
                ft.TextButton(content="Cancel", on_click=lambda _: self._close_dialog(dlg)),
                ft.FilledButton(
                    "Assign Fee",
                    bgcolor=ft.Colors.INDIGO_600,
                    color=ft.Colors.WHITE,
                    on_click=lambda _: self._save_new_fee(dlg, stu_id_field.value, amt_field.value, due_date_field.value),
                ),
            ],
        )
        self.app_page.overlay.append(dlg)
        dlg.open = True
        self.app_page.update()

    def _close_dialog(self, dlg):
        dlg.open = False
        self.app_page.update()

    def _save_new_fee(self, dlg, sid, amount, due_date):
        success, msg = add_fee(
            student_id=sid,
            amount=amount,
            due_date=due_date,
            actor=self.user,
        )
        if success:
            dlg.open = False
            self.load_data()
            self.app_page.snack_bar = ft.SnackBar(ft.Text("Fee assigned successfully!"), bgcolor=ft.Colors.GREEN_600)
            self.app_page.snack_bar.open = True
        else:
            self.app_page.snack_bar = ft.SnackBar(ft.Text(f"Failed: {msg}"), bgcolor=ft.Colors.RED_600)
            self.app_page.snack_bar.open = True
        self.app_page.update()
