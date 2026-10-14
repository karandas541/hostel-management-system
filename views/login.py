import math
import random
import time
import tkinter as tk
import tkinter.font as tkfont
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

from services.auth_service import login_user
from views.dashboard import DashboardWindow


# ---------------------------------------------------------------------------
# Design tokens
# ---------------------------------------------------------------------------
COLORS = {
    "window": "#F2F5FA",
    "surface": "#FFFFFF",
    "surface_soft": "#F7F9FC",
    "surface_hover": "#EEF4FA",
    "navy": "#102A43",
    "navy_light": "#183B56",
    "blue": "#246BFD",
    "blue_hover": "#1558E8",
    "blue_pale": "#EAF1FF",
    "teal": "#50D6C5",
    "text": "#172B4D",
    "muted": "#65758B",
    "subtle": "#91A0B4",
    "border": "#DFE7F1",
    "danger": "#B42332",
    "danger_bg": "#FFF0F0",
    "success": "#137A55",
    "success_bg": "#EAF8F1",
    "white": "#FFFFFF",
}


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def ease_out(t):
    return 1 - (1 - t) ** 3


def _rgb(color):
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    """Blend hex colour a -> b by t (0..1). Used for every fade in this file."""
    t = clamp(t)
    ra, rb = _rgb(a), _rgb(b)
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(ra, rb))


def round_rect(canvas, x1, y1, x2, y2, r, **kwargs):
    pts = [
        x1 + r, y1, x1 + r, y1, x2 - r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y1 + r, x2, y2 - r, x2, y2 - r, x2, y2, x2 - r, y2, x2 - r, y2,
        x1 + r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y2 - r, x1, y1 + r,
        x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kwargs)


# ---------------------------------------------------------------------------
# Animated brand panel (everything is drawn on one canvas so the moving
# background really stays *behind* the text)
# ---------------------------------------------------------------------------
class BrandCanvas(tk.Canvas):
    RADIUS = 22
    GROUP_STEP = 0.13   # delay between staggered entrance groups (seconds)
    GROUP_DUR = 0.70    # duration of each group's fade/slide (seconds)

    def __init__(self, master):
        super().__init__(
            master, width=10, height=10, bg=COLORS["surface"],
            highlightthickness=0, bd=0,
        )
        self._family = tkfont.nametofont("TkDefaultFont").actual("family")
        self._running = False
        self._tick_job = None
        self._rebuild_job = None
        self._t0 = None
        self._size = (0, 0)
        self._k = 1.0
        self._fonts = {}
        self._fades = {}
        self._dy = {}
        self._done = set()
        self._blob_items = []
        self._ring_items = []
        self._particle_items = []
        self._halo = None
        self._pulse = None
        self._logo_c = (0, 0)

        rnd = random.Random(11)
        tints = (COLORS["teal"], "#5BA4F5", "#9CC3E8")
        self._particles = [
            {
                "x": rnd.random(),
                "y": rnd.random(),
                "speed": rnd.uniform(0.010, 0.036),
                "size": rnd.uniform(2.0, 5.0),
                "phase": rnd.uniform(0, math.tau),
                "sway": rnd.uniform(0.004, 0.012),
                "tint": rnd.choice(tints),
            }
            for _ in range(28)
        ]
        # (x, y, radius as fraction of width, phase, colour, strength)
        self._blobs = [
            (0.15, 0.22, 0.34, 0.0, COLORS["blue"], 0.16),
            (0.90, 0.85, 0.42, 2.0, COLORS["teal"], 0.08),
            (0.55, 0.50, 0.26, 4.0, COLORS["blue"], 0.08),
        ]
        self.bind("<Configure>", self._on_configure)

    # -- scale / fonts ------------------------------------------------------
    def _scale(self):
        try:
            return float(self.winfo_toplevel()._get_window_scaling())
        except Exception:
            return max(1.0, self.winfo_fpixels("1i") / 96.0)

    def px(self, value):
        return int(round(value * self._k))

    def _font(self, size, bold=False):
        key = (size, bold, self._k)
        if key not in self._fonts:
            self._fonts[key] = tkfont.Font(
                family=self._family,
                size=-self.px(size),
                weight="bold" if bold else "normal",
            )
        return self._fonts[key]

    # -- lifecycle ----------------------------------------------------------
    def start(self):
        if self._running:
            return
        self._running = True
        self._tick_job = self.after(33, self._tick)

    def stop(self):
        self._running = False
        for job in (self._tick_job, self._rebuild_job):
            if job:
                try:
                    self.after_cancel(job)
                except Exception:
                    pass
        self._tick_job = self._rebuild_job = None

    def _on_configure(self, event):
        if (event.width, event.height) == self._size and self._fades:
            return
        if self._rebuild_job:
            try:
                self.after_cancel(self._rebuild_job)
            except Exception:
                pass
        self._rebuild_job = self.after(30, self._build)

    # -- scene construction -------------------------------------------------
    def _build(self):
        self._rebuild_job = None
        w, h = self.winfo_width(), self.winfo_height()
        if w < 80 or h < 80:
            return
        self._size = (w, h)
        self._k = self._scale()
        navy = COLORS["navy"]

        self.delete("all")
        self._fades, self._dy, self._done = {}, {}, set()
        if self._t0 is None:
            self._t0 = time.perf_counter()

        self.create_rectangle(0, 0, w, h, fill=navy, outline="")
        self._blob_items = [
            self.create_oval(0, 0, 1, 1, fill=mix(navy, c, a), outline="")
            for (_x, _y, _r, _p, c, a) in self._blobs
        ]
        self._ring_items = [
            self.create_oval(0, 0, 1, 1, outline=navy, fill="", width=2)
            for _ in range(4)
        ]
        self._particle_items = [
            self.create_oval(0, 0, 1, 1, fill=navy, outline="")
            for _ in self._particles
        ]
        self._corner_masks(w, h)
        self._build_scene(w, h)

    def _corner_masks(self, w, h):
        """Paint the four corners white so the panel looks rounded."""
        r = self.px(self.RADIUS)
        steps = 12
        specs = (
            ((0, 0), (r, r), 180),
            ((w, 0), (w - r, r), 90),
            ((w, h), (w - r, h - r), 0),
            ((0, h), (r, h - r), -90),
        )
        for corner, (cx, cy), start in specs:
            pts = list(corner)
            for i in range(steps + 1):
                a = math.radians(start - 90 * i / steps)
                pts += [cx + r * math.cos(a), cy - r * math.sin(a)]
            self.create_polygon(
                pts, fill=COLORS["surface"], outline=COLORS["surface"]
            )

    def _build_scene(self, w, h):
        P = self.px
        navy = COLORS["navy"]
        box = "#173751"
        mx = P(36)
        top = P(34)

        def reg(group, item, option, final, base=navy):
            self._fades.setdefault(group, []).append((item, option, final, base))
            self.addtag_withtag(f"g{group}", item)
            return item

        # --- logo + brand name (group 0) ---------------------------------
        ls = P(54)
        self._logo_c = (mx + ls / 2, top + ls / 2)
        self._halo = self.create_oval(
            0, 0, 1, 1, outline=navy, fill="", width=2, state="hidden"
        )
        reg(0, round_rect(self, mx, top, mx + ls, top + ls, P(17),
                          fill=navy, outline=""), "fill", COLORS["blue"])
        reg(0, self.create_text(mx + ls / 2, top + ls / 2 - P(1), text="H",
                                font=self._font(26, True), fill=navy),
            "fill", COLORS["white"])
        tx = mx + ls + P(13)
        reg(0, self.create_text(tx, top + P(17), text="HOSTEL", anchor="w",
                                font=self._font(15, True), fill=navy),
            "fill", COLORS["white"])
        reg(0, self.create_text(tx, top + P(37), text="MANAGEMENT", anchor="w",
                                font=self._font(10, True), fill=navy),
            "fill", "#B6C7D9")

        # --- hero text ----------------------------------------------------
        block_h = P(336)
        free = h - (top + ls) - P(52) - block_h
        hero_y = max(P(118), top + ls + free // 2)

        reg(1, self.create_text(mx, hero_y, text="A BETTER WAY TO LIVE TOGETHER",
                                anchor="nw", font=self._font(10, True), fill=navy),
            "fill", COLORS["teal"])
        reg(2, self.create_text(mx, hero_y + P(26),
                                text="Hostel life,\nmade simpler.", anchor="nw",
                                font=self._font(34, True), fill=navy),
            "fill", COLORS["white"])
        desc_y = hero_y + P(128)
        reg(3, self.create_text(
            mx, desc_y, anchor="nw", width=w - 2 * mx,
            text=("One organized place for rooms, fees, attendance and student "
                  "support. Less paperwork. More peace of mind."),
            font=self._font(13), fill=navy), "fill", "#B9C9D9")

        # --- feature card (groups 4..7) -----------------------------------
        box_y = desc_y + P(80)
        box_item = round_rect(self, mx, box_y, w - mx, box_y + P(132), P(15),
                              fill=navy, outline=navy)
        reg(4, box_item, "fill", box)
        reg(4, box_item, "outline", "#244761")

        rows = ("Room & student records",
                "Fees and attendance tracking",
                "Complaints and feedback")
        for i, label in enumerate(rows):
            g = 5 + i
            cy = box_y + P(32) + i * P(36)
            reg(g, self.create_oval(mx + P(16), cy - P(10), mx + P(36), cy + P(10),
                                    fill=box, outline=""),
                "fill", mix(box, COLORS["teal"], 0.22), box)
            reg(g, self.create_text(mx + P(26), cy - P(1), text="✓",
                                    font=self._font(11, True), fill=box),
                "fill", COLORS["teal"], box)
            reg(g, self.create_text(mx + P(48), cy, text=label, anchor="w",
                                    font=self._font(12), fill=box),
                "fill", "#DDE7F0", box)

        # --- footer (group 8) ---------------------------------------------
        fy = h - P(34)
        reg(8, self.create_text(mx + P(14), fy, text="SYSTEM ACCESS", anchor="w",
                                font=self._font(10, True), fill=navy),
            "fill", COLORS["teal"])
        reg(8, self.create_text(w - mx, fy, text="Built for your hostel community",
                                anchor="e", font=self._font(10), fill=navy),
            "fill", "#91A8BC")
        self._pulse = self.create_oval(mx, fy - P(4), mx + P(8), fy + P(4),
                                       fill=navy, outline="", state="hidden")

    # -- per-frame animation ------------------------------------------------
    def _tick(self):
        self._tick_job = None
        if not self._running:
            return
        if self._t0 is not None and self._size[0]:
            t = time.perf_counter() - self._t0
            try:
                self._update_fx(t)
                self._apply_groups(t)
            except tk.TclError:
                return
        self._tick_job = self.after(33, self._tick)

    def _update_fx(self, t):
        w, h = self._size
        k = self._k
        navy = COLORS["navy"]
        appear = ease_out(clamp(t / 1.2))

        # drifting glow blobs
        for item, (bx, by, br, phase, _c, _a) in zip(self._blob_items, self._blobs):
            cx = w * (bx + 0.03 * math.sin(t * 0.20 + phase))
            cy = h * (by + 0.03 * math.cos(t * 0.17 + phase))
            r = w * br
            self.coords(item, cx - r, cy - r, cx + r, cy + r)

        # expanding rings
        rcx, rcy = w * 0.84, h * 0.64
        count = len(self._ring_items)
        for i, ring in enumerate(self._ring_items):
            p = (t * 0.10 + i / count) % 1.0
            r = k * (28 + 250 * p)
            self.coords(ring, rcx - r, rcy - r, rcx + r, rcy + r)
            self.itemconfigure(
                ring, outline=mix(navy, "#2E78AE", (1 - p) ** 1.5 * 0.7 * appear)
            )

        # floating particles
        for item, pt in zip(self._particle_items, self._particles):
            yy = (pt["y"] - pt["speed"] * t) % 1.0
            xx = pt["x"] + math.sin(t * 0.7 + pt["phase"]) * pt["sway"] * 6
            x = w * (0.04 + 0.92 * (xx % 1.0))
            y = h * yy
            twinkle = 0.65 + 0.35 * math.sin(t * 2.0 + pt["phase"])
            a = math.sin(math.pi * yy) * twinkle * appear
            r = pt["size"] * k / 2
            self.coords(item, x - r, y - r, x + r, y + r)
            self.itemconfigure(item, fill=mix(navy, pt["tint"], 0.08 + 0.80 * a))

        # pulsing halo around the logo
        if self._halo is not None:
            if t > 0.8:
                p = (t * 0.55) % 1.0
                r = k * (27 + 16 * p)
                cx, cy = self._logo_c
                self.coords(self._halo, cx - r, cy - r, cx + r, cy + r)
                self.itemconfigure(
                    self._halo, state="normal",
                    outline=mix(navy, COLORS["blue"], (1 - p) ** 1.5 * 0.8),
                )

        # blinking "system access" dot
        if self._pulse is not None and t > 1.9:
            glow = 0.5 + 0.5 * math.sin(t * 3.0)
            self.itemconfigure(
                self._pulse, state="normal",
                fill=mix(navy, COLORS["teal"], 0.35 + 0.65 * glow),
            )

    def _apply_groups(self, t):
        """Staggered fade-in + small upward slide for each text group."""
        P = self.px
        for g, items in self._fades.items():
            if g in self._done:
                continue
            p = clamp((t - (0.10 + g * self.GROUP_STEP)) / self.GROUP_DUR)
            e = ease_out(p)
            dy = (1 - e) * P(18)
            prev = self._dy.get(g, 0.0)
            if abs(dy - prev) > 0.05:
                self.move(f"g{g}", 0, dy - prev)
                self._dy[g] = dy
            for item, option, final, base in items:
                self.itemconfigure(item, **{option: mix(base, final, e)})
            if p >= 1:
                self._done.add(g)


# ---------------------------------------------------------------------------
# Login window
# ---------------------------------------------------------------------------
class LoginWindow(ctk.CTk):
    """Animated sign-in page for the Hostel Management System."""

    DESIGN_W, DESIGN_H = 1100, 720
    IGNORED_KEYS = {
        "Return", "KP_Enter", "Tab", "ISO_Left_Tab", "Escape",
        "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R",
    }

    def __init__(self):
        super().__init__()

        ctk.set_default_color_theme("blue")
        ctk.set_appearance_mode("light")

        self.title("Hostel Management System | Sign in")
        self.minsize(920, 620)
        self.configure(fg_color=COLORS["window"])
        self._center_window()

        self._closing = False
        self._busy = False
        self._btn_anim = False
        self._btn_frame = 0
        self._shaking = False
        self._password_visible = False
        self._jobs = set()
        self._fade_items = []
        self._tweens = {}
        self._error_widgets = []

        self._build_shell()
        self._build_brand_panel()
        self._build_form_panel()
        self._bind_events()

        self.brand.start()
        self._later(120, self._run_entrance)
        self.protocol("WM_DELETE_WINDOW", self.close_window)

    # ------------------------------------------------------------------
    # Scheduling helpers (every callback is tracked so we can cancel on exit)
    # ------------------------------------------------------------------
    def _later(self, ms, func):
        if self._closing:
            return None
        job_id = None

        def run():
            self._jobs.discard(job_id)
            func()

        job_id = self.after(ms, run)
        self._jobs.add(job_id)
        return job_id

    def _shutdown(self):
        self._closing = True
        for job in list(self._jobs):
            try:
                self.after_cancel(job)
            except Exception:
                pass
        self._jobs.clear()
        self.brand.stop()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _center_window(self):
        try:
            scale = float(self._get_window_scaling())
        except Exception:
            scale = 1.0
        x = max(0, int((self.winfo_screenwidth() - self.DESIGN_W * scale) // 2))
        y = max(0, int((self.winfo_screenheight() - self.DESIGN_H * scale) // 2) - 20)
        self.geometry(f"{self.DESIGN_W}x{self.DESIGN_H}+{x}+{y}")

    def _build_shell(self):
        self.shell = ctk.CTkFrame(
            self,
            fg_color=COLORS["surface"],
            corner_radius=26,
            border_width=1,
            border_color=COLORS["border"],
        )
        self.shell.pack(fill="both", expand=True, padx=24, pady=24)
        self.shell.grid_columnconfigure(0, weight=5, minsize=370)
        self.shell.grid_columnconfigure(1, weight=6, minsize=430)
        self.shell.grid_rowconfigure(0, weight=1)

    def _build_brand_panel(self):
        self.brand = BrandCanvas(self.shell)
        self.brand.grid(row=0, column=0, sticky="nsew", padx=(8, 12), pady=8)

    def _fade(self, widget, option, end, delay, start=None, dur=0.55):
        """Register a colour fade-in for a widget option and hide it now."""
        start = start or COLORS["surface"]
        widget.configure(**{option: start})
        self._fade_items.append({
            "widget": widget, "option": option, "start": start, "end": end,
            "delay": delay, "dur": dur, "p": -1.0,
        })

    def _make_field_label(self, text, row, delay):
        label = ctk.CTkLabel(
            self.form_panel,
            text=text.upper(),
            anchor="w",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=10, weight="bold"),
        )
        label.grid(row=row, column=0, sticky="ew")
        self._fade(label, "text_color", COLORS["text"], delay)
        return label

    def _build_form_panel(self):
        self.form_panel = ctk.CTkFrame(
            self.shell, fg_color="transparent", corner_radius=0
        )
        self.form_panel.grid(
            row=0, column=1, sticky="nsew", padx=(22, 38), pady=(28, 24)
        )
        self.form_panel.grid_columnconfigure(0, weight=1)

        # header row
        top = ctk.CTkFrame(self.form_panel, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew")
        top.grid_columnconfigure(0, weight=1)
        secure = ctk.CTkLabel(
            top, text="SECURE SIGN IN", text_color=COLORS["blue"],
            font=ctk.CTkFont(size=10, weight="bold"),
        )
        secure.grid(row=0, column=0, sticky="w")
        roles = ctk.CTkLabel(
            top, text="ADMIN • STAFF • STUDENT", text_color=COLORS["subtle"],
            font=ctk.CTkFont(size=9, weight="bold"),
        )
        roles.grid(row=0, column=1, sticky="e")
        self._fade(secure, "text_color", COLORS["blue"], 0.00)
        self._fade(roles, "text_color", COLORS["subtle"], 0.05)

        # welcome (typed out) + greeting
        self.welcome_label = ctk.CTkLabel(
            self.form_panel, text="", anchor="w", height=46,
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=32, weight="bold"),
        )
        self.welcome_label.grid(row=1, column=0, sticky="ew", pady=(35, 7))

        hour = datetime.now().hour
        greeting = ("Good morning" if hour < 12
                    else "Good afternoon" if hour < 17 else "Good evening")
        self.subtitle = ctk.CTkLabel(
            self.form_panel,
            text=f"{greeting}! Enter your details to access your account.",
            anchor="w", text_color=COLORS["muted"],
            font=ctk.CTkFont(size=13),
        )
        self.subtitle.grid(row=2, column=0, sticky="ew", pady=(0, 28))
        self._fade(self.subtitle, "text_color", COLORS["muted"], 0.25)

        # username
        self._make_field_label("Username", row=3, delay=0.32)
        self.username_entry = ctk.CTkEntry(
            self.form_panel, height=50, corner_radius=12, border_width=1,
            border_color=COLORS["border"], fg_color=COLORS["surface_soft"],
            text_color=COLORS["text"], placeholder_text="Enter your username",
            placeholder_text_color=COLORS["subtle"],
            font=ctk.CTkFont(size=14),
        )
        self.username_entry.grid(row=4, column=0, sticky="ew", pady=(8, 20))
        self._fade(self.username_entry, "fg_color", COLORS["surface_soft"], 0.38)
        self._fade(self.username_entry, "border_color", COLORS["border"], 0.38)

        # password
        self._make_field_label("Password", row=5, delay=0.46)
        self.password_wrap = ctk.CTkFrame(
            self.form_panel, fg_color=COLORS["surface_soft"], corner_radius=12,
            border_width=1, border_color=COLORS["border"],
        )
        self.password_wrap.grid(row=6, column=0, sticky="ew", pady=(8, 0))
        self.password_wrap.grid_columnconfigure(0, weight=1)

        self.password_entry = ctk.CTkEntry(
            self.password_wrap, height=48, corner_radius=12, border_width=0,
            fg_color="transparent", text_color=COLORS["text"],
            placeholder_text="Enter your password",
            placeholder_text_color=COLORS["subtle"], show="•",
            font=ctk.CTkFont(size=14),
        )
        self.password_entry.grid(row=0, column=0, sticky="ew", padx=(10, 0), pady=1)

        self.reveal_button = ctk.CTkButton(
            self.password_wrap, text="Show", width=58, height=34,
            corner_radius=9, fg_color="transparent",
            hover_color=COLORS["surface_hover"], text_color=COLORS["muted"],
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.toggle_password,
        )
        self.reveal_button.grid(row=0, column=1, padx=(3, 7), pady=7)
        self._fade(self.password_wrap, "fg_color", COLORS["surface_soft"], 0.52)
        self._fade(self.password_wrap, "border_color", COLORS["border"], 0.52)

        # hint + help
        options = ctk.CTkFrame(self.form_panel, fg_color="transparent")
        options.grid(row=7, column=0, sticky="ew", pady=(13, 8))
        options.grid_columnconfigure(0, weight=1)
        hint = ctk.CTkLabel(
            options, text="↵  Press Enter to sign in", anchor="w",
            text_color=COLORS["subtle"], font=ctk.CTkFont(size=11),
        )
        hint.grid(row=0, column=0, sticky="w")
    
        self._fade(hint, "text_color", COLORS["subtle"], 0.62)

        # status line
        self.status_box = ctk.CTkFrame(
            self.form_panel, fg_color="transparent", corner_radius=10, height=38
        )
        self.status_box.grid(row=8, column=0, sticky="ew", pady=(7, 8))
        self.status_box.grid_columnconfigure(1, weight=1)
        self.status_icon = ctk.CTkLabel(
            self.status_box, text="", width=24, text_color=COLORS["danger"],
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.status_icon.grid(row=0, column=0, padx=(8, 2), pady=5)
        self.status_label = ctk.CTkLabel(
            self.status_box, text="", anchor="w", justify="left",
            wraplength=380, text_color=COLORS["danger"],
            font=ctk.CTkFont(size=11),
        )
        self.status_label.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=5)

        # sign-in button
        self.login_button = ctk.CTkButton(
            self.form_panel, text="Sign in  →", height=52, corner_radius=12,
            fg_color=COLORS["blue"], hover_color=COLORS["blue_hover"],
            text_color=COLORS["white"], text_color_disabled=COLORS["white"],
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.handle_login,
        )
        self.login_button.grid(row=9, column=0, sticky="ew", pady=(6, 14))
        self._fade(self.login_button, "fg_color", COLORS["blue"], 0.72)

        # divider + footer texts
        divider = ctk.CTkFrame(self.form_panel, fg_color="transparent")
        divider.grid(row=10, column=0, sticky="ew", pady=(4, 14))
        divider.grid_columnconfigure(0, weight=1)
        divider.grid_columnconfigure(2, weight=1)
        line_a = ctk.CTkFrame(divider, height=1, fg_color=COLORS["border"])
        line_a.grid(row=0, column=0, sticky="ew")
        div_label = ctk.CTkLabel(
            divider, text="  ACCOUNT ACCESS  ", text_color=COLORS["subtle"],
            font=ctk.CTkFont(size=9, weight="bold"),
        )
        div_label.grid(row=0, column=1)
        line_b = ctk.CTkFrame(divider, height=1, fg_color=COLORS["border"])
        line_b.grid(row=0, column=2, sticky="ew")
        self._fade(line_a, "fg_color", COLORS["border"], 0.85)
        self._fade(line_b, "fg_color", COLORS["border"], 0.85)
        self._fade(div_label, "text_color", COLORS["subtle"], 0.85)

        foot_a = ctk.CTkLabel(
            self.form_panel, text="Protected access for authorized hostel users.",
            text_color=COLORS["muted"], font=ctk.CTkFont(size=11),
        )
        foot_a.grid(row=11, column=0, sticky="ew")
        foot_b = ctk.CTkLabel(
            self.form_panel,
            text="If you cannot sign in, contact your hostel administrator.",
            text_color=COLORS["subtle"], font=ctk.CTkFont(size=10),
            wraplength=410,
        )
        foot_b.grid(row=12, column=0, sticky="ew", pady=(6, 0))
        self._fade(foot_a, "text_color", COLORS["muted"], 0.95)
        self._fade(foot_b, "text_color", COLORS["subtle"], 1.00)

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def _bind_events(self):
        self.bind("<Return>", self._on_enter)
        self.bind("<Escape>", lambda _e: self.close_window())
        for entry, frame in (
            (self.username_entry, self.username_entry),
            (self.password_entry, self.password_wrap),
        ):
            # NOTE: CTkEntry.bind() delivers the *inner* tk.Entry as
            # event.widget, so we pass the CTk widget explicitly.
            entry.bind("<FocusIn>",
                       lambda _e, f=frame: self._on_focus(f, True))
            entry.bind("<FocusOut>",
                       lambda _e, f=frame: self._on_focus(f, False))
            entry.bind("<KeyRelease>",
                       lambda e, f=frame: self._on_key(e, f))

    def _on_enter(self, _event=None):
        if not self._busy:
            self.handle_login()
        return "break"

    def _on_focus(self, frame, focused):
        if frame in self._error_widgets and not focused:
            return
        self._tween_border(frame, COLORS["blue"] if focused else COLORS["border"])

    def _on_key(self, event, frame):
        if event.keysym in self.IGNORED_KEYS or self._busy:
            return
        if self._error_widgets or self.status_label.cget("text"):
            for widget in list(self._error_widgets):
                self._tween_border(
                    widget, COLORS["blue"] if widget is frame else COLORS["border"]
                )
            self._error_widgets.clear()
            self._set_status("", kind="")

    def _tween_border(self, widget, target, steps=6):
        key = id(widget)
        token = self._tweens.get(key, 0) + 1
        self._tweens[key] = token
        try:
            start = widget.cget("border_color")
            if not (isinstance(start, str) and start.startswith("#")):
                start = target
        except Exception:
            start = target

        def step(i):
            if self._closing or self._tweens.get(key) != token:
                return
            widget.configure(border_color=mix(start, target, i / steps))
            if i < steps:
                self._later(16, lambda: step(i + 1))

        step(1)

    def toggle_password(self):
        self._password_visible = not self._password_visible
        self.password_entry.configure(show="" if self._password_visible else "•")
        self.reveal_button.configure(
            text="Hide" if self._password_visible else "Show"
        )

    def _set_status(self, text, kind="error"):
        if kind == "error":
            bg, fg, icon = COLORS["danger_bg"], COLORS["danger"], "!"
        elif kind == "success":
            bg, fg, icon = COLORS["success_bg"], COLORS["success"], "✓"
        elif kind == "info":
            bg, fg, icon = COLORS["blue_pale"], COLORS["blue"], "i"
        else:
            bg, fg, icon = "transparent", COLORS["muted"], ""
        self.status_box.configure(fg_color=bg)
        self.status_icon.configure(text=icon, text_color=fg)
        self.status_label.configure(text=text, text_color=fg)

    def _flag_error(self, *widgets):
        for widget in widgets:
            widget.configure(border_color=COLORS["danger"])
            if widget not in self._error_widgets:
                self._error_widgets.append(widget)

    def _reject(self, message, flagged, focus_widget):
        self._set_status(message)
        self._flag_error(*flagged)
        focus_widget.focus_set()
        self._shake_form()

    # ------------------------------------------------------------------
    # Login flow
    # ------------------------------------------------------------------
    def handle_login(self):
        if self._busy or self._closing:
            return

        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username and not password:
            self._reject("Enter your username and password.",
                         (self.username_entry, self.password_wrap),
                         self.username_entry)
            return
        if not username:
            self._reject("Username is required.",
                         (self.username_entry,), self.username_entry)
            return
        if not password:
            self._reject("Password is required.",
                         (self.password_wrap,), self.password_entry)
            return

        self._set_busy(True)
        self._set_status("Verifying your account…", kind="info")
        self._btn_anim = True
        self._btn_frame = 0
        self._animate_login_button()
        # Small delay so the "verifying" animation is visible before the
        # (blocking) database call runs.
        self._later(450, lambda: self._authenticate(username, password))

    def _authenticate(self, username, password):
        if self._closing:
            return
        try:
            success, result = login_user(username, password)
        except Exception:
            # Never expose internal error details on a login screen.
            self._finish_busy()
            self._set_status("Sign-in is temporarily unavailable. Please try again.")
            return

        if not success:
            self._finish_busy()
            self._set_status(str(result) if result else "Sign-in failed.")
            self.password_entry.delete(0, "end")
            self._flag_error(self.username_entry, self.password_wrap)
            self.password_entry.focus_set()
            self._shake_form()
            return

        self._btn_anim = False
        self.login_button.configure(
            text="Welcome  ✓", fg_color=COLORS["success"],
            hover_color=COLORS["success"],
        )
        self._set_status("Signed in successfully. Opening your dashboard…",
                         kind="success")
        self._later(650, lambda: self._open_dashboard(result))

    def _finish_busy(self):
        self._btn_anim = False
        self._set_busy(False)
        self.login_button.configure(text="Sign in  →")

    def _set_busy(self, busy):
        self._busy = busy
        state = "disabled" if busy else "normal"
        for widget in (self.login_button, self.username_entry,
                       self.password_entry, self.reveal_button,
                       self.forgot_button):
            widget.configure(state=state)

    def _animate_login_button(self):
        if self._closing or not self._btn_anim:
            return
        frames = ("Verifying account  ·", "Verifying account  · ·",
                  "Verifying account  · · ·")
        self.login_button.configure(text=frames[self._btn_frame % len(frames)])
        self._btn_frame += 1
        self._later(220, self._animate_login_button)

    def _open_dashboard(self, user_result):
        if self._closing:
            return
        self._shutdown()
        self.destroy()
        dashboard = DashboardWindow(user_result)
        dashboard.mainloop()

    def show_password_help(self):
        messagebox.showinfo(
            "Account help",
            "Password reset is not configured in this application yet. "
            "Please contact your hostel administrator to reset your password.",
            parent=self,
        )

    # ------------------------------------------------------------------
    # Animation
    # ------------------------------------------------------------------
    def _run_entrance(self):
        if self._closing:
            return
        self._welcome_text = "Welcome back."
        self._welcome_index = 0
        self._type_welcome()
        self._run_fades()

    def _type_welcome(self):
        if self._closing:
            return
        if self._welcome_index <= len(self._welcome_text):
            self.welcome_label.configure(
                text=self._welcome_text[:self._welcome_index] + "|"
            )
            self._welcome_index += 1
            self._later(55, self._type_welcome)
        else:
            self._blink_cursor(7)

    def _blink_cursor(self, count):
        if self._closing:
            return
        cursor = "|" if count % 2 == 1 else ""
        self.welcome_label.configure(text=self._welcome_text + cursor)
        if count > 0:
            self._later(380, lambda: self._blink_cursor(count - 1))

    def _run_fades(self, t0=None):
        if self._closing:
            return
        if t0 is None:
            t0 = time.perf_counter()
        elapsed = time.perf_counter() - t0
        pending = False
        for item in self._fade_items:
            p = clamp((elapsed - item["delay"]) / item["dur"])
            if p != item["p"]:
                item["p"] = p
                item["widget"].configure(
                    **{item["option"]: mix(item["start"], item["end"], ease_out(p))}
                )
            if p < 1:
                pending = True
        if pending:
            self._later(33, lambda: self._run_fades(t0))
        else:
            self.username_entry.focus_set()

    def _shake_form(self):
        """Small, restrained horizontal nudge so validation errors are noticed."""
        if self._closing or self._shaking:
            return
        self._shaking = True
        base = (22, 38)
        offsets = (0, -8, 8, -6, 6, -3, 3, 0)

        def step(i=0):
            if self._closing:
                return
            if i >= len(offsets):
                self.form_panel.grid_configure(padx=base)
                self._shaking = False
                return
            o = offsets[i]
            self.form_panel.grid_configure(padx=(base[0] + o, base[1] - o))
            self._later(24, lambda: step(i + 1))

        step()

    # ------------------------------------------------------------------
    # Window behaviour
    # ------------------------------------------------------------------
    def close_window(self):
        if self._closing:
            return
        self._shutdown()
        self.destroy()


if __name__ == "__main__":
    app = LoginWindow()
    app.mainloop()
