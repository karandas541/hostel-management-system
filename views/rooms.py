"""Room directory and bed allocation screens."""

import customtkinter as ctk
from tkinter import messagebox

from services.room_service import (
    add_room, allocate_room, deallocate_room, delete_room,
    get_all_rooms, get_allocations, update_room,
)
from utils.authorization import (
    guard_authorization_errors, require_menu_access, resolve_student,
)
from utils.ui_theme import apply_professional_style, get_palette


class RoomsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        require_menu_access(parent.user, "Rooms")
        super().__init__(parent)
        self.actor = parent.user
        self.is_admin = self.actor["role"] == "admin"
        self.selected_room = None
        self.rooms = []
        self.title("Hostel Management System - Rooms")
        self.geometry("1180x780")
        self.minsize(900, 620)
        self.create_ui()
        if not self.is_admin:
            _, student_id = resolve_student(self.actor)
            self.student_id_entry.insert(0, student_id)
            self.student_id_entry.configure(state="disabled")
            self.allocation_frame.pack_forget()
        self.refresh_all()
        apply_professional_style(self)

    def create_ui(self):
        colors = get_palette()
        header = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        header.pack(fill="x", padx=22, pady=(18, 8))
        ctk.CTkLabel(header, text="Room Management", font=ctk.CTkFont(size=27, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="Refresh", width=110, command=self.refresh_all).pack(side="right")

        self.content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True, padx=14, pady=(4, 14))

        if self.is_admin:
            editor = ctk.CTkFrame(self.content)
            editor.pack(fill="x", padx=8, pady=8)
            ctk.CTkLabel(editor, text="Room Details", font=ctk.CTkFont(size=19, weight="bold")).grid(row=0, column=0, columnspan=6, sticky="w", padx=18, pady=(15, 8))
            self.room_number_entry = ctk.CTkEntry(editor, placeholder_text="Room number", width=170)
            self.floor_entry = ctk.CTkEntry(editor, placeholder_text="Floor", width=120)
            self.type_entry = ctk.CTkEntry(editor, placeholder_text="Room type (optional)", width=190)
            self.capacity_entry = ctk.CTkEntry(editor, placeholder_text="Bed capacity", width=140)
            for col, widget in enumerate((self.room_number_entry, self.floor_entry, self.type_entry, self.capacity_entry)):
                widget.grid(row=1, column=col, padx=8, pady=10, sticky="ew")
            self.save_button = ctk.CTkButton(editor, text="Add Room", width=130, command=self.save_room)
            self.save_button.grid(row=1, column=4, padx=8, pady=10)
            self.cancel_edit_button = ctk.CTkButton(editor, text="Clear", width=95, command=self.clear_editor)
            self.cancel_edit_button.grid(row=1, column=5, padx=8, pady=10)
            for col in range(6):
                editor.grid_columnconfigure(col, weight=1 if col < 4 else 0)

        filters = ctk.CTkFrame(self.content)
        filters.pack(fill="x", padx=8, pady=8)
        ctk.CTkLabel(filters, text="Room Directory", font=ctk.CTkFont(size=19, weight="bold")).grid(row=0, column=0, columnspan=4, sticky="w", padx=18, pady=(15, 8))
        self.room_search_entry = ctk.CTkEntry(filters, placeholder_text="Search room, floor or type", width=280)
        self.room_search_entry.grid(row=1, column=0, padx=10, pady=(4, 14), sticky="ew")
        self.room_search_entry.bind("<Return>", self.search_rooms)
        self.status_filter = ctk.CTkComboBox(filters, width=205, values=["All", "Available", "Partially Occupied", "Occupied"], command=lambda _value: self.search_rooms())
        self.status_filter.set("All")
        self.status_filter.grid(row=1, column=1, padx=10, pady=(4, 14))
        ctk.CTkButton(filters, text="Search", width=100, command=self.search_rooms).grid(row=1, column=2, padx=8, pady=(4, 14))
        ctk.CTkButton(filters, text="Clear", width=90, command=self.clear_room_filter).grid(row=1, column=3, padx=8, pady=(4, 14))
        filters.grid_columnconfigure(0, weight=1)

        self.room_list = ctk.CTkFrame(self.content, fg_color="transparent")
        self.room_list.pack(fill="x", padx=8, pady=3)

        self.allocation_frame = ctk.CTkFrame(self.content)
        self.allocation_frame.pack(fill="x", padx=8, pady=10)
        ctk.CTkLabel(self.allocation_frame, text="Bed Allocation", font=ctk.CTkFont(size=19, weight="bold")).grid(row=0, column=0, columnspan=4, sticky="w", padx=18, pady=(15, 8))
        self.student_id_entry = ctk.CTkEntry(self.allocation_frame, placeholder_text="Student ID", width=190)
        self.room_allocation_entry = ctk.CTkEntry(self.allocation_frame, placeholder_text="Room number", width=190)
        self.student_id_entry.grid(row=1, column=0, padx=10, pady=(4, 15), sticky="ew")
        self.room_allocation_entry.grid(row=1, column=1, padx=10, pady=(4, 15), sticky="ew")
        if self.is_admin:
            ctk.CTkButton(self.allocation_frame, text="Allocate Bed", command=self.allocate_clicked).grid(row=1, column=2, padx=8, pady=(4, 15))
            ctk.CTkButton(self.allocation_frame, text="Vacate Bed", command=self.vacate_clicked).grid(row=1, column=3, padx=8, pady=(4, 15))
        self.allocation_frame.grid_columnconfigure(0, weight=1)
        self.allocation_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.content, text="Active Allocations", font=ctk.CTkFont(size=19, weight="bold")).pack(anchor="w", padx=14, pady=(8, 4))
        self.allocation_list = ctk.CTkFrame(self.content, fg_color="transparent")
        self.allocation_list.pack(fill="x", padx=8, pady=(2, 12))

    @guard_authorization_errors
    def save_room(self):
        room_number = self.room_number_entry.get().strip()
        floor = self.floor_entry.get().strip()
        room_type = self.type_entry.get().strip()
        capacity = self.capacity_entry.get().strip()
        try:
            if self.selected_room:
                result = update_room(self.selected_room, room_number, floor, capacity, room_type, actor=self.actor)
            else:
                result = add_room(room_number, floor, capacity, actor=self.actor, room_type=room_type)
        except ValueError as error:
            messagebox.showwarning("Check room details", str(error), parent=self)
            return
        if result[0]:
            messagebox.showinfo("Room saved", result[1], parent=self)
            self.clear_editor()
            self.refresh_all()
        else:
            messagebox.showerror("Room could not be saved", result[1], parent=self)

    def select_room(self, room):
        self.selected_room = room[1]
        for entry, value in ((self.room_number_entry, room[1]), (self.floor_entry, room[2]), (self.type_entry, room[7] or ""), (self.capacity_entry, room[3])):
            entry.delete(0, "end")
            entry.insert(0, str(value))
        self.save_button.configure(text="Update Room")
        self.room_number_entry.focus_set()

    def clear_editor(self):
        self.selected_room = None
        if self.is_admin:
            for entry in (self.room_number_entry, self.floor_entry, self.type_entry, self.capacity_entry):
                entry.delete(0, "end")
            self.save_button.configure(text="Add Room")

    @guard_authorization_errors
    def delete_room_clicked(self, room_number):
        if not messagebox.askyesno("Delete room", f"Delete room {room_number}? Rooms with current or historical allocations are retained.", parent=self):
            return
        success, message = delete_room(room_number, actor=self.actor)
        (messagebox.showinfo if success else messagebox.showerror)("Room", message, parent=self)
        self.refresh_all()

    def render_rooms(self, rooms):
        for child in self.room_list.winfo_children():
            child.destroy()
        colors = get_palette()
        if not rooms:
            ctk.CTkLabel(self.room_list, text="No rooms match this search.", text_color=colors["muted"]).pack(anchor="w", padx=14, pady=20)
            return
        for room in rooms:
            _room_id, number, floor, capacity, occupied, available, status, room_type = room
            card = ctk.CTkFrame(self.room_list)
            card.pack(fill="x", padx=4, pady=5)
            detail = f"Floor {floor}  ·  {room_type or 'Standard'}  ·  {occupied}/{capacity} beds occupied  ·  {available} available"
            ctk.CTkLabel(card, text=number, font=ctk.CTkFont(size=17, weight="bold")).grid(row=0, column=0, sticky="w", padx=16, pady=(12, 2))
            ctk.CTkLabel(card, text=detail, text_color=colors["muted"]).grid(row=1, column=0, sticky="w", padx=16, pady=(2, 12))
            badge_color = {"Available": "#23855B", "Partially Occupied": "#B7791F", "Occupied": colors["danger"]}.get(status, colors["accent"])
            ctk.CTkLabel(card, text=status, text_color=badge_color, font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, rowspan=2, padx=12)
            if self.is_admin:
                ctk.CTkButton(card, text="Edit", width=70, command=lambda item=room: self.select_room(item)).grid(row=0, column=2, rowspan=2, padx=(4, 6))
                ctk.CTkButton(card, text="Delete", width=78, command=lambda name=number: self.delete_room_clicked(name)).grid(row=0, column=3, rowspan=2, padx=(4, 12))
            card.grid_columnconfigure(0, weight=1)

    @guard_authorization_errors
    def refresh_all(self):
        self.rooms = get_all_rooms(actor=self.actor)
        self.search_rooms()
        self.load_allocations()
        apply_professional_style(self)

    def search_rooms(self, _event=None):
        query = self.room_search_entry.get().strip().casefold()
        status = self.status_filter.get().strip()
        filtered = [room for room in self.rooms if (not query or query in str(room[1]).casefold() or query in str(room[2]).casefold() or query in str(room[7] or "").casefold()) and (status == "All" or room[6] == status)]
        self.render_rooms(filtered)
        apply_professional_style(self)

    def clear_room_filter(self):
        self.room_search_entry.delete(0, "end")
        self.status_filter.set("All")
        self.search_rooms()

    def load_allocations(self):
        for child in self.allocation_list.winfo_children():
            child.destroy()
        allocations = get_allocations(actor=self.actor)
        colors = get_palette()
        if not allocations:
            ctk.CTkLabel(self.allocation_list, text="No active bed allocations.", text_color=colors["muted"]).pack(anchor="w", padx=14, pady=16)
            return
        for _allocation_id, student_id, name, room, floor, bed, allocated_at in allocations:
            row = ctk.CTkFrame(self.allocation_list)
            row.pack(fill="x", padx=4, pady=3)
            ctk.CTkLabel(row, text=f"{name}  ·  {student_id}", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=14, pady=10)
            ctk.CTkLabel(row, text=f"Room {room}, floor {floor}  ·  Bed {bed}  ·  {allocated_at}", text_color=colors["muted"]).pack(side="right", padx=14, pady=10)

    @guard_authorization_errors
    def allocate_clicked(self):
        success, message = allocate_room(self.student_id_entry.get(), self.room_allocation_entry.get(), actor=self.actor)
        (messagebox.showinfo if success else messagebox.showerror)("Bed allocation", message, parent=self)
        if success:
            self.student_id_entry.delete(0, "end")
            self.room_allocation_entry.delete(0, "end")
        self.refresh_all()

    @guard_authorization_errors
    def vacate_clicked(self):
        success, message = deallocate_room(self.student_id_entry.get(), actor=self.actor)
        (messagebox.showinfo if success else messagebox.showerror)("Vacate bed", message, parent=self)
        if success:
            self.student_id_entry.delete(0, "end")
        self.refresh_all()


if __name__ == "__main__":
    print("RoomsWindow must be opened from the main application.")
