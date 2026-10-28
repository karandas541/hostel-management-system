"""Modern SaaS Rooms & Allocations View built with Flet."""

import flet as ft
from services.room_service import (
    get_all_rooms,
    add_room,
    allocate_room,
    get_allocations,
    deallocate_room,
)
from services.student_service import get_all_students
from flet_views.theme import get_colors


class RoomsSubView(ft.Column):
    def __init__(self, page: ft.Page, user: dict):
        super().__init__()
        self.app_page = page
        self.user = user
        self.expand = True
        self.spacing = 16

        self.rooms_grid = ft.Row(wrap=True, spacing=16)
        self.allocations_container = ft.Column(spacing=10)

        self.controls = [
            self._build_header(),
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Room Directory & Capacity", size=16, weight=ft.FontWeight.BOLD),
                        self.rooms_grid,
                        ft.Container(height=16),
                        ft.Divider(height=1),
                        ft.Container(height=8),
                        ft.Row(
                            controls=[
                                ft.Text("Active Bed Allocations", size=16, weight=ft.FontWeight.BOLD),
                                ft.Text("Real-time list of students and their assigned bed numbers", size=12, color=get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)["text_muted"]),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        self.allocations_container,
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                    spacing=12,
                ),
                expand=True,
                padding=16,
            ),
        ]
        self.load_data()

    def _build_header(self) -> ft.Control:
        is_admin = self.user.get("role") == "admin"
        colors = get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)

        buttons = []
        if is_admin:
            buttons.extend([
                ft.FilledButton(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.BED_ROUNDED, size=16, color=ft.Colors.WHITE),
                            ft.Text("Assign Room & Bed", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ],
                        spacing=6,
                    ),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.INDIGO_600,
                        shape=ft.RoundedRectangleBorder(radius=10),
                        padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                    ),
                    on_click=lambda _: self._open_allocate_dialog(),
                ),
                ft.OutlinedButton(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.ADD_HOME_ROUNDED, size=16),
                            ft.Text("Add Room", size=13, weight=ft.FontWeight.BOLD),
                        ],
                        spacing=6,
                    ),
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=10),
                        padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                    ),
                    on_click=self._open_add_room_dialog,
                ),
            ])

        return ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("Rooms & Bed Allocations", size=22, weight=ft.FontWeight.BOLD),
                        ft.Text("Monitor room capacities, current occupancies, and manage student beds", size=12, color=colors["text_muted"]),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.Row(controls=buttons, spacing=10),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def load_data(self):
        colors = get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)
        is_admin = self.user.get("role") == "admin"

        # ── 1. Render Room Cards ──────────────────────────────────────────
        try:
            rooms = get_all_rooms(actor=self.user)
            if not rooms:
                self.rooms_grid.controls = [ft.Text("No rooms configured yet.", color=colors["text_muted"])]
            else:
                cards = []
                for r in rooms:
                    # r: (id, room_number, floor, capacity, occupied, available, status, rent)
                    room_id, r_num, floor, cap, occ, avail, status, rent = r
                    ratio = occ / cap if cap else 0

                    status_color = ft.Colors.GREEN_500 if status == "Available" else (ft.Colors.AMBER_500 if status == "Partially Occupied" else ft.Colors.RED_500)

                    card_controls = [
                        ft.Row(
                            controls=[
                                ft.Text(f"Room {r_num}", size=16, weight=ft.FontWeight.BOLD),
                                ft.Container(
                                    content=ft.Text(status, size=10, weight=ft.FontWeight.BOLD, color=status_color),
                                    padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                                    border_radius=10,
                                    bgcolor=ft.Colors.with_opacity(0.12, status_color),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Text(f"Floor {floor or 1}", size=11, color=colors["text_muted"]),
                        ft.Container(height=6),
                        ft.ProgressBar(value=ratio, color=status_color, bgcolor=colors["border"], height=8, border_radius=4),
                        ft.Container(height=4),
                        ft.Row(
                            controls=[
                                ft.Text(f"Occupied: {occ}/{cap} Beds", size=12, weight=ft.FontWeight.W_500),
                                ft.Text(f"Available: {avail}", size=12, color=colors["text_muted"]),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                    ]

                    # Quick Assign button on card if space is available
                    if is_admin and avail > 0:
                        card_controls.extend([
                            ft.Container(height=8),
                            ft.OutlinedButton(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.PERSON_ADD_ALT_1_ROUNDED, size=14, color=ft.Colors.INDIGO_400),
                                        ft.Text("Assign Student", size=12, color=ft.Colors.INDIGO_400),
                                    ],
                                    spacing=6,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                                on_click=lambda e, rn=r_num: self._open_allocate_dialog(default_room_number=rn),
                            ),
                        ])

                    card = ft.Container(
                        content=ft.Column(controls=card_controls, spacing=3),
                        width=280,
                        padding=18,
                        border_radius=14,
                        bgcolor=colors["surface"],
                        border=ft.Border.all(1, colors["border"]),
                    )
                    cards.append(card)

                self.rooms_grid.controls = cards
        except Exception as err:
            self.rooms_grid.controls = [ft.Text(f"Error loading rooms: {err}", color=ft.Colors.RED_400)]

        # ── 2. Render Active Allocations Table ─────────────────────────────
        try:
            allocations = get_allocations(actor=self.user)
            if not allocations:
                self.allocations_container.controls = [
                    ft.Container(
                        content=ft.Text("No active room allocations currently.", color=colors["text_muted"]),
                        padding=16,
                    )
                ]
            else:
                rows = []
                for alloc in allocations:
                    # alloc: (id, student_id, student_name, room_number, floor, bed_number, allocated_at)
                    alloc_id, sid, sname, rnum, flr, bed_num, alloc_date = alloc

                    actions = []
                    if is_admin:
                        actions.append(
                            ft.IconButton(
                                icon=ft.Icons.DOOR_BACK_DOOR_OUTLINED,
                                icon_size=18,
                                icon_color=ft.Colors.AMBER_500,
                                tooltip=f"Vacate Room {rnum}",
                                on_click=lambda e, st_id=sid, st_name=sname: self._confirm_vacate(st_id, st_name),
                            )
                        )

                    bed_badge = ft.Container(
                        content=ft.Text(f"Bed #{bed_num}", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_400),
                        padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                        border_radius=8,
                        bgcolor=ft.Colors.INDIGO_50 if not (self.app_page.theme_mode == ft.ThemeMode.DARK) else ft.Colors.with_opacity(0.15, ft.Colors.INDIGO_400),
                    )

                    rows.append(
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text(sid, weight=ft.FontWeight.BOLD)),
                                ft.DataCell(ft.Text(sname, weight=ft.FontWeight.W_500)),
                                ft.DataCell(ft.Text(f"Room {rnum} (Floor {flr})")),
                                ft.DataCell(bed_badge),
                                ft.DataCell(ft.Text(str(alloc_date or "—")[:16])),
                                ft.DataCell(ft.Row(actions) if actions else ft.Text("—")),
                            ]
                        )
                    )

                table = ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("STUDENT ID", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
                        ft.DataColumn(ft.Text("STUDENT NAME", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
                        ft.DataColumn(ft.Text("ROOM", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
                        ft.DataColumn(ft.Text("BED NUMBER", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
                        ft.DataColumn(ft.Text("ALLOCATED ON", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
                        ft.DataColumn(ft.Text("ACTIONS", weight=ft.FontWeight.BOLD, size=11, color=colors["text_muted"])),
                    ],
                    rows=rows,
                    border_radius=10,
                    heading_row_color=colors["surface_alt"],
                    column_spacing=24,
                )
                self.allocations_container.controls = [
                    ft.Container(
                        content=table,
                        padding=12,
                        border_radius=12,
                        bgcolor=colors["surface"],
                        border=ft.Border.all(1, colors["border"]),
                    )
                ]
        except Exception as err:
            self.allocations_container.controls = [ft.Text(f"Error loading allocations: {err}", color=ft.Colors.RED_400)]

        self.app_page.update()

    def _open_allocate_dialog(self, default_student_id=None, default_room_number=None):
        colors = get_colors(self.app_page.theme_mode == ft.ThemeMode.DARK)

        # Fetch room choices
        rooms = get_all_rooms(actor=self.user)
        avail_rooms = [r for r in rooms if r[5] > 0]
        room_opts = [
            ft.dropdown.Option(
                key=str(r[1]),
                text=f"Room {r[1]} (Floor {r[2]} · {r[5]} beds free)",
            )
            for r in avail_rooms
        ]
        # Also include currently selected room if it was specified
        if default_room_number and not any(opt.key == str(default_room_number) for opt in room_opts):
            room_opts.insert(0, ft.dropdown.Option(key=str(default_room_number), text=f"Room {default_room_number}"))

        # Fetch student choices
        students = get_all_students(actor=self.user)
        student_opts = []
        for s in students:
            curr_room = f" [Rm {s['room_number']}]" if s.get("room_number") else " [No Room]"
            student_opts.append(
                ft.dropdown.Option(
                    key=s["student_id"],
                    text=f"{s['name']} ({s['student_id']}){curr_room}",
                )
            )

        student_dropdown = ft.Dropdown(
            label="Select Student",
            options=student_opts,
            value=default_student_id,
            border_radius=8,
            expand=True,
        )
        student_id_input = ft.TextField(
            label="Or Enter Student ID (e.g. STU001)",
            value=default_student_id or "",
            border_radius=8,
            expand=True,
        )

        def on_student_select(e):
            if student_dropdown.value:
                student_id_input.value = student_dropdown.value
                self.app_page.update()

        student_dropdown.on_change = on_student_select

        selected_room_val = str(default_room_number) if default_room_number else (room_opts[0].key if room_opts else None)
        room_dropdown = ft.Dropdown(
            label="Select Room (with available beds)",
            options=room_opts,
            value=selected_room_val,
            border_radius=8,
            expand=True,
        )

        info_box = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, size=16, color=ft.Colors.INDIGO_400),
                    ft.Text(
                        "Bed number is automatically allocated to the lowest free bed in the room.",
                        size=12,
                        color=colors["text_muted"],
                        expand=True,
                    ),
                ],
                spacing=8,
            ),
            padding=10,
            border_radius=8,
            bgcolor=colors["surface_alt"],
        )

        dlg = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.BED_ROUNDED, color=ft.Colors.INDIGO_600, size=24),
                    ft.Text("Assign Room & Bed", weight=ft.FontWeight.BOLD, size=18),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        student_dropdown,
                        student_id_input,
                        room_dropdown,
                        info_box,
                    ],
                    spacing=14,
                ),
                width=420,
                height=260,
            ),
            actions=[
                ft.TextButton(content="Cancel", on_click=lambda _: self._close_dialog(dlg)),
                ft.FilledButton(
                    content="Assign Bed",
                    bgcolor=ft.Colors.INDIGO_600,
                    color=ft.Colors.WHITE,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=lambda _: self._submit_allocation(
                        dlg,
                        student_id_input.value or student_dropdown.value,
                        room_dropdown.value,
                    ),
                ),
            ],
        )
        self.app_page.overlay.append(dlg)
        dlg.open = True
        self.app_page.update()

    def _submit_allocation(self, dlg, sid, rnum):
        sid_clean = (sid or "").strip()
        rnum_clean = (rnum or "").strip()

        if not sid_clean:
            self._show_toast("Please select or enter a valid Student ID.", is_err=True)
            return

        if not rnum_clean:
            self._show_toast("Please select a valid Room Number.", is_err=True)
            return

        try:
            success, msg = allocate_room(student_id=sid_clean, room_number=rnum_clean, actor=self.user)
            if success:
                dlg.open = False
                self.load_data()
                self._show_toast(msg)
            else:
                self._show_toast(f"Allocation Failed: {msg}", is_err=True)
        except Exception as e:
            self._show_toast(f"Error: {e}", is_err=True)

    def _confirm_vacate(self, student_id, student_name):
        def do_vacate(_):
            dlg.open = False
            try:
                success, msg = deallocate_room(student_id=student_id, actor=self.user)
                if success:
                    self.load_data()
                    self._show_toast(f"Room vacated successfully for {student_name}.")
                else:
                    self._show_toast(f"Vacate Failed: {msg}", is_err=True)
            except Exception as e:
                self._show_toast(f"Error: {e}", is_err=True)

        dlg = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.DOOR_BACK_DOOR_OUTLINED, color=ft.Colors.AMBER_500, size=24),
                    ft.Text("Confirm Room Vacate", weight=ft.FontWeight.BOLD, size=18),
                ],
                spacing=8,
            ),
            content=ft.Text(f"Are you sure you want to vacate the room for {student_name} ({student_id})?"),
            actions=[
                ft.OutlinedButton("Cancel", on_click=lambda _: self._close_dialog(dlg)),
                ft.FilledButton("Yes, Vacate", bgcolor=ft.Colors.AMBER_600, color=ft.Colors.WHITE, on_click=do_vacate),
            ],
        )
        self.app_page.overlay.append(dlg)
        dlg.open = True
        self.app_page.update()

    def _open_add_room_dialog(self, _):
        r_num_field = ft.TextField(label="Room Number (e.g. 105)", border_radius=8)
        cap_field = ft.TextField(label="Capacity (Beds)", value="3", border_radius=8)
        floor_field = ft.TextField(label="Floor Number", value="1", border_radius=8)

        dlg = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.ADD_HOME_ROUNDED, color=ft.Colors.INDIGO_600, size=24),
                    ft.Text("Add Room", weight=ft.FontWeight.BOLD, size=18),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=ft.Column([r_num_field, cap_field, floor_field], spacing=10),
                width=340,
                height=220,
            ),
            actions=[
                ft.TextButton(content="Cancel", on_click=lambda _: self._close_dialog(dlg)),
                ft.FilledButton(
                    "Save Room",
                    bgcolor=ft.Colors.INDIGO_600,
                    color=ft.Colors.WHITE,
                    on_click=lambda _: self._save_room(dlg, r_num_field.value, cap_field.value, floor_field.value),
                ),
            ],
        )
        self.app_page.overlay.append(dlg)
        dlg.open = True
        self.app_page.update()

    def _close_dialog(self, dlg):
        dlg.open = False
        self.app_page.update()

    def _save_room(self, dlg, r_num, cap, floor):
        try:
            success, msg = add_room(
                room_number=r_num,
                capacity=int(cap),
                floor=int(floor),
                actor=self.user,
            )
            if success:
                dlg.open = False
                self.load_data()
                self._show_toast("Room added successfully!")
            else:
                self._show_toast(f"Failed: {msg}", is_err=True)
        except Exception as e:
            self._show_toast(f"Error: {e}", is_err=True)

    def _show_toast(self, message: str, is_err: bool = False):
        try:
            sb = ft.SnackBar(
                content=ft.Text(message, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.RED_600 if is_err else ft.Colors.GREEN_600,
                behavior=ft.SnackBarBehavior.FLOATING,
                shape=ft.RoundedRectangleBorder(radius=10),
                duration=ft.Duration(seconds=4),
                show_close_icon=True,
            )
            self.app_page.show_dialog(sb)
        except Exception:
            pass
