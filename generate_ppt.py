"""Generate an executive, professional 16:9 PowerPoint presentation for Review 1 & 2."""

from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE


# ── Color Palette ───────────────────────────────────────────────────────────
C_BG_DARK = RGBColor(15, 23, 42)       # Slate 950 (Cover & Dark accents)
C_PRIMARY = RGBColor(79, 70, 229)      # Indigo 600
C_PRIMARY_LIGHT = RGBColor(238, 242, 255) # Indigo 50
C_ACCENT_TEAL = RGBColor(13, 148, 136) # Teal 600
C_SUCCESS = RGBColor(16, 185, 129)     # Emerald 500
C_WARNING = RGBColor(245, 158, 11)     # Amber 500
C_DANGER = RGBColor(239, 68, 68)       # Red 500
C_TEXT_DARK = RGBColor(15, 23, 42)     # Slate 950
C_TEXT_MUTED = RGBColor(100, 116, 139) # Slate 500
C_CARD_BG = RGBColor(255, 255, 255)    # White
C_CARD_ALT = RGBColor(248, 250, 252)   # Slate 50
C_BORDER = RGBColor(226, 232, 240)     # Slate 200
C_WHITE = RGBColor(255, 255, 255)


def create_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Helper: Set background of a slide
    def set_slide_background(slide, color):
        bg = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5)
        )
        bg.fill.solid()
        bg.fill.fore_color.rgb = color
        bg.line.fill.background()
        return bg

    # Helper: Slide header
    def add_header(slide, title_text, category_text="REVIEW 1 & 2 • PROJECT DOCUMENTATION"):
        # Category Tag
        tag_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.45), Inches(8), Inches(0.35))
        tf_tag = tag_box.text_frame
        tf_tag.word_wrap = True
        p_tag = tf_tag.paragraphs[0]
        p_tag.text = category_text.upper()
        p_tag.font.name = "Arial"
        p_tag.font.size = Pt(10)
        p_tag.font.bold = True
        p_tag.font.color.rgb = C_PRIMARY

        # Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11), Inches(0.65))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.name = "Arial"
        p_title.font.size = Pt(22)
        p_title.font.bold = True
        p_title.font.color.rgb = C_TEXT_DARK

    # Helper: Add card container
    def add_card(slide, x, y, w, h, bg_color=C_CARD_BG, border_color=C_BORDER):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        card.line.color.rgb = border_color
        card.line.width = Pt(1.2)
        return card

    # Helper: Add table
    def add_table(slide, x, y, w, h, headers, rows, col_widths=None):
        num_rows = len(rows) + 1
        num_cols = len(headers)
        table_shape = slide.shapes.add_table(num_rows, num_cols, Inches(x), Inches(y), Inches(w), Inches(h))
        table = table_shape.table

        if col_widths and len(col_widths) == num_cols:
            for idx, width in enumerate(col_widths):
                table.columns[idx].width = Inches(width)

        # Style headers
        for col_idx, header in enumerate(headers):
            cell = table.cell(0, col_idx)
            cell.text = header
            cell.fill.solid()
            cell.fill.fore_color.rgb = C_BG_DARK
            p = cell.text_frame.paragraphs[0]
            p.font.name = "Arial"
            p.font.size = Pt(11)
            p.font.bold = True
            p.font.color.rgb = C_WHITE
            p.alignment = PP_ALIGN.LEFT

        # Style data rows
        for row_idx, row in enumerate(rows):
            is_even = row_idx % 2 == 0
            for col_idx, val in enumerate(row):
                cell = table.cell(row_idx + 1, col_idx)
                cell.text = str(val)
                cell.fill.solid()
                cell.fill.fore_color.rgb = C_WHITE if is_even else C_CARD_ALT
                p = cell.text_frame.paragraphs[0]
                p.font.name = "Arial"
                p.font.size = Pt(10)
                p.font.color.rgb = C_TEXT_DARK
                p.alignment = PP_ALIGN.LEFT

        return table_shape

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 1: TITLE SLIDE (Dark Executive Cover)
    # ══════════════════════════════════════════════════════════════════════════
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1, C_BG_DARK)

    # Accent decorative glow bar
    glow = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.5), Inches(0.12), Inches(3.8))
    glow.fill.solid()
    glow.fill.fore_color.rgb = C_PRIMARY
    glow.line.fill.background()

    # Title box
    tb = s1.shapes.add_textbox(Inches(1.2), Inches(1.4), Inches(11), Inches(4.5))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = "ACADEMIC CAPSTONE PROJECT • REVIEW 1 & REVIEW 2"
    p0.font.name = "Arial"
    p0.font.size = Pt(12)
    p0.font.bold = True
    p0.font.color.rgb = RGBColor(129, 140, 248)
    p0.space_after = Pt(14)

    p1 = tf.add_paragraph()
    p1.text = "Hostel Management System"
    p1.font.name = "Arial"
    p1.font.size = Pt(38)
    p1.font.bold = True
    p1.font.color.rgb = C_WHITE
    p1.space_after = Pt(12)

    p2 = tf.add_paragraph()
    p2.text = "An Enterprise-Grade, Modular Desktop Application Built with Python, Flet & SQLite"
    p2.font.name = "Arial"
    p2.font.size = Pt(16)
    p2.font.color.rgb = RGBColor(203, 213, 225)
    p2.space_after = Pt(28)

    p3 = tf.add_paragraph()
    p3.text = "Key Focus: SRS • System Design • CRUD & Core Features • Interactive Dashboard • Visual Reports • TQM"
    p3.font.name = "Arial"
    p3.font.size = Pt(13)
    p3.font.bold = True
    p3.font.color.rgb = C_SUCCESS

    # Meta cards at bottom
    add_card(s1, 1.2, 5.7, 3.4, 1.1, RGBColor(30, 41, 59), RGBColor(51, 65, 85))
    tb_m1 = s1.shapes.add_textbox(Inches(1.4), Inches(5.8), Inches(3.0), Inches(0.9))
    tf_m1 = tb_m1.text_frame
    p_m1a = tf_m1.paragraphs[0]
    p_m1a.text = "PROJECT STACK"
    p_m1a.font.size = Pt(10)
    p_m1a.font.bold = True
    p_m1a.font.color.rgb = RGBColor(148, 163, 184)
    p_m1b = tf_m1.add_paragraph()
    p_m1b.text = "Python 3.13 • Flet SaaS UI • SQLite"
    p_m1b.font.size = Pt(12)
    p_m1b.font.bold = True
    p_m1b.font.color.rgb = C_WHITE

    add_card(s1, 4.9, 5.7, 3.4, 1.1, RGBColor(30, 41, 59), RGBColor(51, 65, 85))
    tb_m2 = s1.shapes.add_textbox(Inches(5.1), Inches(5.8), Inches(3.0), Inches(0.9))
    tf_m2 = tb_m2.text_frame
    p_m2a = tf_m2.paragraphs[0]
    p_m2a.text = "TESTING & QUALITY STATUS"
    p_m2a.font.size = Pt(10)
    p_m2a.font.bold = True
    p_m2a.font.color.rgb = RGBColor(148, 163, 184)
    p_m2b = tf_m2.add_paragraph()
    p_m2b.text = "28/28 Pytest Verification Passed"
    p_m2b.font.size = Pt(12)
    p_m2b.font.bold = True
    p_m2b.font.color.rgb = C_SUCCESS

    add_card(s1, 8.6, 5.7, 3.8, 1.1, RGBColor(30, 41, 59), RGBColor(51, 65, 85))
    tb_m3 = s1.shapes.add_textbox(Inches(8.8), Inches(5.8), Inches(3.4), Inches(0.9))
    tf_m3 = tb_m3.text_frame
    p_m3a = tf_m3.paragraphs[0]
    p_m3a.text = "USER ACCESS ARCHITECTURE"
    p_m3a.font.size = Pt(10)
    p_m3a.font.bold = True
    p_m3a.font.color.rgb = RGBColor(148, 163, 184)
    p_m3b = tf_m3.add_paragraph()
    p_m3b.text = "Role-Based Auth (Admin & Student)"
    p_m3b.font.size = Pt(12)
    p_m3b.font.bold = True
    p_m3b.font.color.rgb = C_WHITE

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 2: PROBLEM STATEMENT & MOTIVATION
    # ══════════════════════════════════════════════════════════════════════════
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2, C_CARD_ALT)
    add_header(s2, "Problem Statement & Need for Digital Automation", "REVIEW 1 • SETUP & SRS")

    # Left: Challenges Card
    add_card(s2, 0.8, 1.5, 5.6, 5.4, C_WHITE)
    tb2_left = s2.shapes.add_textbox(Inches(1.1), Inches(1.7), Inches(5.0), Inches(5.0))
    tf2_l = tb2_left.text_frame
    tf2_l.word_wrap = True

    p = tf2_l.paragraphs[0]
    p.text = "❌ Current Manual & Legacy Challenges"
    p.font.name = "Arial"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_DANGER
    p.space_after = Pt(14)

    challenges = [
        ("Disorganized Paper Records", "Student admission forms, room allocations, and documents stored in physical registers lead to data loss and slow retrieval."),
        ("Double Allocation Risks", "Manual room assignments often cause conflicting bed allotments and room overcapacity without real-time inventory."),
        ("Opaque Fee Tracking", "Lack of clear ledgers results in delayed fee collections, untracked partial dues, and disputed cash receipts."),
        ("Unresolved Student Grievances", "Maintenance complaints written in logbooks are frequently missed, poorly prioritized, and lack resolution tracking."),
        ("Manual Attendance Overhead", "Paper-based daily in/out entries require tedious tallying for warden night curfews and leaves."),
    ]
    for title, desc in challenges:
        p_t = tf2_l.add_paragraph()
        p_t.text = f"• {title}: "
        p_t.font.bold = True
        p_t.font.size = Pt(11)
        p_t.font.color.rgb = C_TEXT_DARK
        p_d = tf2_l.add_paragraph()
        p_d.text = f"   {desc}"
        p_d.font.size = Pt(10)
        p_d.font.color.rgb = C_TEXT_MUTED
        p_d.space_after = Pt(8)

    # Right: Solution Card
    add_card(s2, 6.7, 1.5, 5.8, 5.4, C_WHITE)
    tb2_right = s2.shapes.add_textbox(Inches(7.0), Inches(1.7), Inches(5.2), Inches(5.0))
    tf2_r = tb2_right.text_frame
    tf2_r.word_wrap = True

    p = tf2_r.paragraphs[0]
    p.text = "✅ The Modern Digital Solution (HostelHub)"
    p.font.name = "Arial"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_SUCCESS
    p.space_after = Pt(14)

    solutions = [
        ("Centralized SQLite Relational DB", "Persistent, single-source-of-truth storage with ACID transactions and foreign key integrity constraints."),
        ("Live Room & Bed Matrix", "Automatic occupancy counters preventing double-booking; instant reallocation and room transfer workflows."),
        ("Automated Ledger & Receipt Engine", "Records partial and full payments, calculates remaining dues, and exports formal PDF receipts."),
        ("Digital Grievance Cell", "Role-scoped ticketing system with status tags ('Pending', 'In Progress', 'Resolved') and admin remark logs."),
        ("Interactive Multi-Role Dashboards", "Separate secure views for Administrators (full control) and Students (self-service tracking)."),
    ]
    for title, desc in solutions:
        p_t = tf2_r.add_paragraph()
        p_t.text = f"• {title}: "
        p_t.font.bold = True
        p_t.font.size = Pt(11)
        p_t.font.color.rgb = C_TEXT_DARK
        p_d = tf2_r.add_paragraph()
        p_d.text = f"   {desc}"
        p_d.font.size = Pt(10)
        p_d.font.color.rgb = C_TEXT_MUTED
        p_d.space_after = Pt(8)

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 3: QUALITY OBJECTIVES & TQM ALIGNMENT
    # ══════════════════════════════════════════════════════════════════════════
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3, C_CARD_ALT)
    add_header(s3, "Quality Objectives & Total Quality Management (TQM)", "REVIEW 1 • SETUP & SRS")

    q_cards = [
        ("Zero Double Allocations", "100% Guaranteed", "Database-level constraints and pre-allocation checks guarantee that no bed is ever assigned to two active students simultaneously.", C_PRIMARY),
        ("Instant Fee Visibility", "< 100 ms Query", "Real-time fee ledger updates showing total dues, collected payments, and pending balances instantly across all dashboard views.", C_SUCCESS),
        ("Role Data Isolation", "100% Scoped", "Strict authorization barrier: Students can only view their own fees, complaints, room, and feedback records; Admin maintains broad governance.", C_PRIMARY),
        ("Quality Feedback Engine", "10-Factor TQM", "Comprehensive student satisfaction ratings across Cleanliness, Food, Wifi, Security, and Warden Support generating actionable AI guidance.", C_WARNING),
        ("Data Export Compliance", "Instant CSV/PDF", "Instant generation of auditable CSV sheets and official PDF receipts formatted for university and institutional record audits.", C_ACCENT_TEAL),
        ("Reliability & Test Coverage", "28/28 Tests Passed", "Full automated end-to-end test suite testing security, CRUD workflows, session lifecycle, and analytics data integrity.", C_SUCCESS),
    ]

    for idx, (title, metric, desc, color) in enumerate(q_cards):
        col = idx % 3
        row = idx // 3
        x = 0.8 + col * 3.9
        y = 1.5 + row * 2.7
        card = add_card(s3, x, y, 3.65, 2.45, C_WHITE)

        # Top indicator stripe
        stripe = s3.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(3.65), Inches(0.08))
        stripe.fill.solid()
        stripe.fill.fore_color.rgb = color
        stripe.line.fill.background()

        tb_q = s3.shapes.add_textbox(Inches(x + 0.2), Inches(y + 0.2), Inches(3.25), Inches(2.0))
        tf_q = tb_q.text_frame
        tf_q.word_wrap = True

        p1 = tf_q.paragraphs[0]
        p1.text = title
        p1.font.bold = True
        p1.font.size = Pt(13)
        p1.font.color.rgb = C_TEXT_DARK

        p2 = tf_q.add_paragraph()
        p2.text = metric
        p2.font.bold = True
        p2.font.size = Pt(16)
        p2.font.color.rgb = color
        p2.space_after = Pt(6)

        p3 = tf_q.add_paragraph()
        p3.text = desc
        p3.font.size = Pt(10)
        p3.font.color.rgb = C_TEXT_MUTED

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 4: SOFTWARE REQUIREMENTS SPECIFICATION (SRS)
    # ══════════════════════════════════════════════════════════════════════════
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4, C_CARD_ALT)
    add_header(s4, "Software Requirements Specification (SRS)", "REVIEW 1 • SETUP & SRS")

    # Table for Functional Requirements
    fr_headers = ["Req ID", "Module", "Functional Requirement Description", "Priority"]
    fr_rows = [
        ["FR-01", "Auth & RBAC", "Authenticate users via bcrypt password hash; enforce role-scoped dashboard views.", "High"],
        ["FR-02", "Room Allotment", "Allocate/deallocate beds, track capacity thresholds, prevent overbooking.", "Critical"],
        ["FR-03", "Student Records", "CRUD student records with unique Student IDs, contact details, and parent info.", "High"],
        ["FR-04", "Fee Management", "Issue fee invoices, support partial/full settlement, generate audit trails.", "High"],
        ["FR-05", "Grievance Cell", "Students register categorized tickets; admin updates progress and resolution notes.", "Medium"],
        ["FR-06", "Attendance", "Log timestamped daily check-ins/check-outs and night curfew leave status.", "Medium"],
        ["FR-07", "Reports & Export", "Export official CSV reports and ReportLab PDF receipts for compliance.", "High"],
        ["FR-08", "Theme & Prefs", "Persist UI theme (Light/Dark) and profile preferences across active sessions.", "Low"],
    ]
    add_table(s4, 0.8, 1.5, 6.8, 5.4, fr_headers, fr_rows, [0.8, 1.4, 3.8, 0.8])

    # Right Card: Non-Functional Requirements (NFRs)
    add_card(s4, 7.9, 1.5, 4.6, 5.4, C_WHITE)
    tb_nfr = s4.shapes.add_textbox(Inches(8.2), Inches(1.7), Inches(4.0), Inches(5.0))
    tf_nfr = tb_nfr.text_frame
    tf_nfr.word_wrap = True

    pn = tf_nfr.paragraphs[0]
    pn.text = "🛡️ Non-Functional Requirements (NFRs)"
    pn.font.bold = True
    pn.font.size = Pt(15)
    pn.font.color.rgb = C_PRIMARY
    pn.space_after = Pt(12)

    nfrs = [
        ("NFR-01: Security & Protection", "Bcrypt password hashing with salt, SQL parameterized queries preventing injection, and session token verification."),
        ("NFR-02: Low Latency Performance", "Sub-second database queries using SQLite PRAGMA indexes; responsive UI powered by Flutter rendering engine."),
        ("NFR-03: Data Integrity & ACID", "Foreign key cascades, atomic transactions for allocations and payments, rollback on unexpected failure."),
        ("NFR-04: Cross-Platform Portability", "Built on Python 3 and Flet UI framework; fully compatible with Windows, macOS, and Linux without native changes."),
        ("NFR-05: Usability & Ergonomics", "Modern SaaS visual layout, keyboard navigation shortcuts, one-click autofills, and responsive theme toggling."),
    ]
    for t, d in nfrs:
        p_t = tf_nfr.add_paragraph()
        p_t.text = f"• {t}"
        p_t.font.bold = True
        p_t.font.size = Pt(11)
        p_t.font.color.rgb = C_TEXT_DARK
        p_d = tf_nfr.add_paragraph()
        p_d.text = f"  {d}"
        p_d.font.size = Pt(10)
        p_d.font.color.rgb = C_TEXT_MUTED
        p_d.space_after = Pt(6)

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 5: SCOPE AND USER ROLES
    # ══════════════════════════════════════════════════════════════════════════
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5, C_CARD_ALT)
    add_header(s5, "Scope & Role-Based Access Control (RBAC)", "REVIEW 1 • SETUP & SRS")

    # Admin Role Card
    add_card(s5, 0.8, 1.5, 5.6, 5.4, C_WHITE)
    tb_admin = s5.shapes.add_textbox(Inches(1.1), Inches(1.7), Inches(5.0), Inches(5.0))
    tf_adm = tb_admin.text_frame
    tf_adm.word_wrap = True

    p = tf_adm.paragraphs[0]
    p.text = "👑 Administrator Role (Warden / Management)"
    p.font.bold = True
    p.font.size = Pt(16)
    p.font.color.rgb = C_PRIMARY
    p.space_after = Pt(10)

    admin_perms = [
        ("Full Student Management", "Enrolls students, edits records, deletes inactive files, and provisions initial student credentials."),
        ("Room & Capacity Control", "Creates room inventories, sets capacity thresholds, allocates beds, and processes transfers."),
        ("Fee Invoicing & Audits", "Issues fee schedules, marks cash/UPI settlements, verifies balances, and prints reports."),
        ("Grievance Resolution", "Views all hostel maintenance tickets, updates status, and enters formal admin resolution notes."),
        ("Quality & TQM Analytics", "Accesses quality dashboards, AI facility recommendations, and institutional compliance exports."),
        ("Broadcast Announcements", "Publishes hostel-wide notifications and urgent curfew or maintenance alerts."),
    ]
    for t, d in admin_perms:
        pt = tf_adm.add_paragraph()
        pt.text = f"✔ {t}: "
        pt.font.bold = True
        pt.font.size = Pt(11)
        pt.font.color.rgb = C_TEXT_DARK
        pd = tf_adm.add_paragraph()
        pd.text = f"   {d}"
        pd.font.size = Pt(10)
        pd.font.color.rgb = C_TEXT_MUTED
        pd.space_after = Pt(6)

    # Student Role Card
    add_card(s5, 6.7, 1.5, 5.8, 5.4, C_WHITE)
    tb_stu = s5.shapes.add_textbox(Inches(7.0), Inches(1.7), Inches(5.2), Inches(5.0))
    tf_stu = tb_stu.text_frame
    tf_stu.word_wrap = True

    p = tf_stu.paragraphs[0]
    p.text = "🎓 Student Resident Role (Resident Self-Service)"
    p.font.bold = True
    p.font.size = Pt(16)
    p.font.color.rgb = C_SUCCESS
    p.space_after = Pt(10)

    student_perms = [
        ("Personal Profile Portal", "Views personal admission details, assigned room number, bed number, and contact info."),
        ("Isolated Fee History", "Checks personal dues, verifies payment receipt history, and downloads official fee vouchers."),
        ("Complaint Registration", "Files maintenance tickets (Electrical, Plumbing, Wifi, Cleanliness) and tracks live status."),
        ("Attendance & Curfew Logs", "Self-checks daily timestamped check-in/out records and leaves."),
        ("Quality Feedback Submission", "Submits rating evaluations across 8 living parameters for continuous hostel quality improvements."),
        ("Account Self-Care", "Changes login password securely and adjusts notification preferences."),
    ]
    for t, d in student_perms:
        pt = tf_stu.add_paragraph()
        pt.text = f"✔ {t}: "
        pt.font.bold = True
        pt.font.size = Pt(11)
        pt.font.color.rgb = C_TEXT_DARK
        pd = tf_stu.add_paragraph()
        pd.text = f"   {d}"
        pd.font.size = Pt(10)
        pd.font.color.rgb = C_TEXT_MUTED
        pd.space_after = Pt(6)

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 6: MODULAR FOLDER ARCHITECTURE & FILE STRUCTURE
    # ══════════════════════════════════════════════════════════════════════════
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6, C_CARD_ALT)
    add_header(s6, "Modular Folder Architecture & Codebase Structure", "REVIEW 1 • SYSTEM DESIGN")

    # Left: ASCII Tree Box
    add_card(s6, 0.8, 1.5, 5.2, 5.4, C_BG_DARK, C_BG_DARK)
    tb_tree = s6.shapes.add_textbox(Inches(1.0), Inches(1.6), Inches(4.8), Inches(5.2))
    tf_tree = tb_tree.text_frame
    tf_tree.word_wrap = False

    tree_text = """HostelManagementSystem/
├── app_flet.py         # Main Flet App Launcher
├── main.py             # Entrypoint & venv resolver
├── database.py         # SQLite Schema & Migration
├── database/hostel.db  # Relational Database File
├── flet_views/         # Modern SaaS Presentation Layer
│   ├── login_view.py       # Dual-Pane Auth Screen
│   ├── dashboard_view.py   # Admin Unified Portal
│   ├── student_dashboard_view.py # Student Portal
│   ├── students_view.py    # CRUD Student Records
│   ├── rooms_view.py       # Live Room Allocation
│   ├── fees_view.py        # Ledger & Invoicing
│   ├── complaints_view.py  # Ticket Management
│   ├── attendance_view.py  # In/Out Curfew Logs
│   ├── feedback_view.py    # TQM Feedback System
│   ├── quality_dashboard_view.py # Analytics Hub
│   ├── reports_view.py     # CSV/PDF Compliance
│   ├── settings_view.py    # Shortcuts & Themes
│   └── theme.py            # Light/Dark Design Tokens
├── services/           # Decoupled Business Logic
│   ├── auth_service.py     # Login, Register & Session
│   ├── student_service.py  # Validation & Persistence
│   ├── room_service.py     # Capacity & Bed Control
│   ├── fee_service.py      # Receipts & Dues Calc
│   └── complaint_service.py# Lifecycle & Resolution
├── utils/              # Security & Authorization
│   ├── authorization.py    # Role Guard & Scoping
│   ├── security.py         # Bcrypt Password Hashing
│   └── shortcuts.py        # Global Keyboard Binds
└── tests/              # 28 Unit & E2E Pytest Suite"""

    p = tf_tree.paragraphs[0]
    p.text = tree_text
    p.font.name = "Courier New"
    p.font.size = Pt(8.5)
    p.font.color.rgb = RGBColor(226, 232, 240)

    # Right: Architectural Layer Explanations
    layers = [
        ("Presentation Layer (`flet_views/`)", "Built with modern reactive Flet controls. Implements responsive layouts, interactive modal dialogs, and tokenized Light/Dark theme switching."),
        ("Service & Business Logic Layer (`services/`)", "Decoupled domain services enforce business rules, capacity validation, data isolation, and fee balance calculations independently of the UI."),
        ("Security & Utilities Layer (`utils/`)", "Enforces bcrypt cryptographic hashing, role-based session guards (`require_role`), keyboard shortcut managers, and data validators."),
        ("Data Persistence Layer (`database/`)", "Direct SQLite3 engine with automated schema migrations, foreign key constraints (`PRAGMA foreign_keys = ON`), and connection pooling."),
    ]
    for idx, (title, desc) in enumerate(layers):
        y = 1.5 + idx * 1.35
        add_card(s6, 6.3, y, 6.2, 1.25, C_WHITE)
        tb_l = s6.shapes.add_textbox(Inches(6.5), Inches(y + 0.1), Inches(5.8), Inches(1.05))
        tf_l = tb_l.text_frame
        tf_l.word_wrap = True
        pt = tf_l.paragraphs[0]
        pt.text = title
        pt.font.bold = True
        pt.font.size = Pt(12)
        pt.font.color.rgb = C_PRIMARY
        pd = tf_l.add_paragraph()
        pd.text = desc
        pd.font.size = Pt(10)
        pd.font.color.rgb = C_TEXT_MUTED

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 7: DATABASE SCHEMA & SYSTEM DESIGN
    # ══════════════════════════════════════════════════════════════════════════
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7, C_CARD_ALT)
    add_header(s7, "Database Design & Relational Entity Schema", "REVIEW 1 • SYSTEM DESIGN")

    db_tables = [
        ("users", "Authentication & Access", ["id (PK)", "username (UNIQUE)", "email", "password_hash", "role ('admin'|'student')", "student_id", "is_active"]),
        ("students", "Student Demographic Registry", ["id (PK)", "student_id (UNIQUE)", "name", "gender", "phone", "email", "course", "room_number", "bed_number", "status"]),
        ("rooms", "Room Capacity & Allocation", ["id (PK)", "room_number (UNIQUE)", "floor", "room_type", "capacity", "occupied_beds", "status ('Available'|'Occupied')"]),
        ("fees", "Invoicing & Financial Ledger", ["id (PK)", "student_id (FK)", "amount", "due_date", "status ('Paid'|'Unpaid'|'Partial')", "payment_date", "payment_method"]),
        ("complaints", "Digital Grievance Cell", ["id (PK)", "student_id (FK)", "category", "title", "description", "priority", "status ('Pending'|'Resolved')", "admin_remarks"]),
        ("attendance", "In/Out Curfew Tracking", ["id (PK)", "student_id (FK)", "date", "status ('Present'|'Leave'|'Late')", "check_in", "check_out", "remarks"]),
    ]

    for idx, (tname, tdesc, cols) in enumerate(db_tables):
        col = idx % 3
        row = idx // 3
        x = 0.8 + col * 3.9
        y = 1.5 + row * 2.7
        add_card(s7, x, y, 3.65, 2.5, C_WHITE)

        # Header bar for table card
        hbar = s7.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(3.65), Inches(0.45))
        hbar.fill.solid()
        hbar.fill.fore_color.rgb = C_BG_DARK
        hbar.line.fill.background()

        tb_th = s7.shapes.add_textbox(Inches(x + 0.15), Inches(y + 0.05), Inches(3.35), Inches(0.35))
        tf_th = tb_th.text_frame
        p_th = tf_th.paragraphs[0]
        p_th.text = f"TABLE: {tname.upper()}"
        p_th.font.bold = True
        p_th.font.size = Pt(11)
        p_th.font.color.rgb = C_WHITE

        tb_tb = s7.shapes.add_textbox(Inches(x + 0.2), Inches(y + 0.5), Inches(3.25), Inches(1.9))
        tf_tb = tb_tb.text_frame
        tf_tb.word_wrap = True

        p_desc = tf_tb.paragraphs[0]
        p_desc.text = tdesc
        p_desc.font.size = Pt(9.5)
        p_desc.font.bold = True
        p_desc.font.color.rgb = C_PRIMARY
        p_desc.space_after = Pt(4)

        for c in cols:
            pc = tf_tb.add_paragraph()
            pc.text = f"• {c}"
            pc.font.name = "Courier New"
            pc.font.size = Pt(8.5)
            pc.font.color.rgb = C_TEXT_DARK

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 8: CORE MODULES & CRUD OPERATIONS
    # ══════════════════════════════════════════════════════════════════════════
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8, C_CARD_ALT)
    add_header(s8, "Review 2: Core Modules & CRUD Operations", "REVIEW 2 • CRUD & CORE FEATURES")

    crud_data = [
        ("Student Management", "Enrolls students with real-time field validation (Email, Phone, Year).", "Search by ID/Name, view details, filter by Course/Branch/Status.", "Update contact info, course, change status, assign/swap room allotment.", "Soft/Hard delete records; cascading room bed release automatically."),
        ("Room Allotment", "Registers new rooms with floor, room type (Single, Double, Triple) & capacity.", "Matrix viewer showing live occupancy progress ring and bed vacancies.", "Swap room allocations, re-allocate beds, adjust room maintenance status.", "Deallocate students; decrement occupancy counter safely in atomic transaction."),
        ("Fee & Invoicing", "Generate single or recurring student fee dues with due date & descriptions.", "Filter by Paid, Unpaid, or Partial dues; inspect individual payment histories.", "Record full or partial settlement; captures payment date & mode (UPI/Cash).", "Rollback incorrect invoice records; archive settled financial transaction logs."),
        ("Grievance Cell", "Students file categorized tickets (Maintenance, Wifi, Food, Cleanliness).", "Categorized ticket lists with priority tags (High, Medium, Low) & status.", "Admin updates ticket lifecycle ('In Progress', 'Resolved') with remarks.", "Close tickets and archive complaints upon resident sign-off."),
    ]

    for idx, (mname, c_op, r_op, u_op, d_op) in enumerate(crud_data):
        y = 1.5 + idx * 1.35
        add_card(s8, 0.8, y, 11.7, 1.25, C_WHITE)

        tb_m = s8.shapes.add_textbox(Inches(1.0), Inches(y + 0.1), Inches(11.3), Inches(1.05))
        tf_m = tb_m.text_frame
        tf_m.word_wrap = True

        pm = tf_m.paragraphs[0]
        pm.text = f"MODULE: {mname.upper()}"
        pm.font.bold = True
        pm.font.size = Pt(12)
        pm.font.color.rgb = C_PRIMARY

        p_crud = tf_m.add_paragraph()
        p_crud.text = f"[C] Create: {c_op}   |   [R] Read: {r_op}"
        p_crud.font.size = Pt(9.5)
        p_crud.font.color.rgb = C_TEXT_DARK

        p_crud2 = tf_m.add_paragraph()
        p_crud2.text = f"[U] Update: {u_op}   |   [D] Delete: {d_op}"
        p_crud2.font.size = Pt(9.5)
        p_crud2.font.color.rgb = C_TEXT_MUTED

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 9: INTERACTIVE DASHBOARD
    # ══════════════════════════════════════════════════════════════════════════
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9, C_CARD_ALT)
    add_header(s9, "Feature Showcase: Interactive Role Dashboards", "REVIEW 2 • CORE FEATURES")

    # Stat Badges (Top Row)
    kpis = [
        ("Total Residents", "128 Active", "Enrolled students across floors", C_PRIMARY),
        ("Room Occupancy", "84.2%", "Occupied beds vs total capacity", C_SUCCESS),
        ("Pending Fee Dues", "₹42,500", "Outstanding student balances", C_DANGER),
        ("Active Complaints", "3 Open", "2 High Priority, 1 Medium", C_WARNING),
    ]
    for idx, (label, val, sub, col) in enumerate(kpis):
        x = 0.8 + idx * 2.95
        add_card(s9, x, 1.5, 2.8, 1.3, C_WHITE)
        tb_k = s9.shapes.add_textbox(Inches(x + 0.15), Inches(1.55), Inches(2.5), Inches(1.1))
        tf_k = tb_k.text_frame
        tf_k.word_wrap = True
        pk1 = tf_k.paragraphs[0]
        pk1.text = label.upper()
        pk1.font.size = Pt(9)
        pk1.font.bold = True
        pk1.font.color.rgb = C_TEXT_MUTED
        pk2 = tf_k.add_paragraph()
        pk2.text = val
        pk2.font.size = Pt(17)
        pk2.font.bold = True
        pk2.font.color.rgb = col
        pk3 = tf_k.add_paragraph()
        pk3.text = sub
        pk3.font.size = Pt(8.5)
        pk3.font.color.rgb = C_TEXT_MUTED

    # Left: Admin Dashboard Capabilities
    add_card(s9, 0.8, 3.0, 5.7, 3.9, C_WHITE)
    tb_ad = s9.shapes.add_textbox(Inches(1.0), Inches(3.15), Inches(5.3), Inches(3.6))
    tf_ad = tb_ad.text_frame
    tf_ad.word_wrap = True
    p = tf_ad.paragraphs[0]
    p.text = "👑 Administrator Interactive Analytics"
    p.font.bold = True
    p.font.size = Pt(14)
    p.font.color.rgb = C_PRIMARY
    p.space_after = Pt(8)

    admin_features = [
        ("Live Occupancy Donut Metrics", "Visual progress breakdown of vacant vs occupied rooms by floor."),
        ("Recent Financial Activities", "Chronological feed of latest fee payments with transaction timestamps."),
        ("Complaint Resolution Speed", "Calculates average resolution duration and highlights SLA breaches."),
        ("TQM Satisfaction Index", "Aggregated star score across 8 living quality dimensions with recommendations."),
        ("Quick-Action Launchers", "Direct shortcuts to enroll student, allot room, or record fee settlement."),
    ]
    for t, d in admin_features:
        pt = tf_ad.add_paragraph()
        pt.text = f"• {t}: "
        pt.font.bold = True
        pt.font.size = Pt(10.5)
        pt.font.color.rgb = C_TEXT_DARK
        pd = tf_ad.add_paragraph()
        pd.text = f"   {d}"
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = C_TEXT_MUTED
        pd.space_after = Pt(4)

    # Right: Student Dashboard Capabilities
    add_card(s9, 6.8, 3.0, 5.7, 3.9, C_WHITE)
    tb_sd = s9.shapes.add_textbox(Inches(7.0), Inches(3.15), Inches(5.3), Inches(3.6))
    tf_sd = tb_sd.text_frame
    tf_sd.word_wrap = True
    p = tf_sd.paragraphs[0]
    p.text = "🎓 Student Resident Personalized Hub"
    p.font.bold = True
    p.font.size = Pt(14)
    p.font.color.rgb = C_SUCCESS
    p.space_after = Pt(8)

    student_features = [
        ("Room & Roommate Card", "Displays assigned room number, bed number, room type, and fellow roommates."),
        ("My Fee Clearance Status", "Shows exact paid amount, balance due date, and download button for receipts."),
        ("My Grievance Progress Bar", "Visual step tracker ('Submitted' → 'Under Review' → 'Resolved')."),
        ("Attendance & Leave Balance", "Curfew compliance meter and past leave approval status."),
        ("Hostel Announcements Carousel", "Live notifications broadcast by hostel management."),
    ]
    for t, d in student_features:
        pt = tf_sd.add_paragraph()
        pt.text = f"• {t}: "
        pt.font.bold = True
        pt.font.size = Pt(10.5)
        pt.font.color.rgb = C_TEXT_DARK
        pd = tf_sd.add_paragraph()
        pd.text = f"   {d}"
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = C_TEXT_MUTED
        pd.space_after = Pt(4)

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 10: VISUAL REPORTS & INSTITUTIONAL COMPLIANCE
    # ══════════════════════════════════════════════════════════════════════════
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10, C_CARD_ALT)
    add_header(s10, "Feature Showcase: Visual Reports & Data Exports", "REVIEW 2 • CORE FEATURES")

    rep_cards = [
        ("📊 CSV Compliance Exports", "Official Data Auditing", [
            "Generates full CSV data sheets for enrolled students, fees collection, and room occupancy.",
            "Complies with institutional audit formats and accreditation reporting standards.",
            "Native save-file dialog (`prompt_save_file`) allowing custom export locations.",
            "Structured headers with complete demographic, financial, and contact fields.",
        ], C_PRIMARY),
        ("📑 ReportLab Automated PDF Receipts", "Instant Fee Documentation", [
            "Generates formal, printable PDF receipts whenever a fee payment is recorded.",
            "Includes Institution Header, Student ID, Transaction ID, Mode (UPI/Cash), and Date.",
            "Embeds outstanding balance calculations and official authorized signature stamp area.",
            "Stored securely with auto-naming conventions for easy retrieval.",
        ], C_ACCENT_TEAL),
        ("📈 Total Quality Management (TQM) Analytics", "AI Facility Guidance", [
            "Consolidates student feedback into a 5-star metric dashboard across 8 categories.",
            "Visual comparison bars identify lowest-scoring facilities (e.g., Wifi, Food Quality).",
            "Auto-generates priority recommendations for management facility upgrades.",
            "Continuous improvement cycle aligned with ISO 9001 quality management principles.",
        ], C_SUCCESS),
    ]

    for idx, (title, sub, bullets, color) in enumerate(rep_cards):
        x = 0.8 + idx * 3.9
        add_card(s10, x, 1.5, 3.65, 5.4, C_WHITE)

        hbar = s10.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(1.5), Inches(3.65), Inches(0.1))
        hbar.fill.solid()
        hbar.fill.fore_color.rgb = color
        hbar.line.fill.background()

        tb_rc = s10.shapes.add_textbox(Inches(x + 0.2), Inches(1.75), Inches(3.25), Inches(5.0))
        tf_rc = tb_rc.text_frame
        tf_rc.word_wrap = True

        p1 = tf_rc.paragraphs[0]
        p1.text = title
        p1.font.bold = True
        p1.font.size = Pt(13)
        p1.font.color.rgb = C_TEXT_DARK

        p2 = tf_rc.add_paragraph()
        p2.text = sub
        p2.font.bold = True
        p2.font.size = Pt(10)
        p2.font.color.rgb = color
        p2.space_after = Pt(12)

        for b in bullets:
            pb = tf_rc.add_paragraph()
            pb.text = f"✔ {b}"
            pb.font.size = Pt(10)
            pb.font.color.rgb = C_TEXT_MUTED
            pb.space_after = Pt(8)

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 11: THEME TOGGLE & UI MODERNIZATION
    # ══════════════════════════════════════════════════════════════════════════
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_background(s11, C_CARD_ALT)
    add_header(s11, "Feature Showcase: Theme Toggle & Modern SaaS Styling", "REVIEW 2 • CORE FEATURES")

    # Light Theme Card
    add_card(s11, 0.8, 1.5, 5.6, 5.4, C_WHITE)
    tb_th_l = s11.shapes.add_textbox(Inches(1.1), Inches(1.7), Inches(5.0), Inches(5.0))
    tf_tl = tb_th_l.text_frame
    tf_tl.word_wrap = True
    p = tf_tl.paragraphs[0]
    p.text = "☀️ Clean Slate Light Theme Mode"
    p.font.bold = True
    p.font.size = Pt(15)
    p.font.color.rgb = C_PRIMARY
    p.space_after = Pt(12)

    l_specs = [
        ("Background Token (`page`)", "#F8FAFC (Slate 50) - Soft, low-contrast backdrop."),
        ("Surface Card Token (`surface`)", "#FFFFFF (Pure White) - Crisp card elevation."),
        ("Text & Typography (`text`)", "#0F172A (Slate 950) - Optimal readability."),
        ("Subtle Border Token (`border`)", "#E2E8F0 (Slate 200) - Clean modular separation."),
        ("Primary Brand Accent", "#6366F1 (Indigo 500) - Modern SaaS visual identity."),
        ("Ergonomics & Readability", "Ideal for daytime administrative office operations and report reviews."),
    ]
    for t, d in l_specs:
        pt = tf_tl.add_paragraph()
        pt.text = f"• {t}: "
        pt.font.bold = True
        pt.font.size = Pt(10.5)
        pt.font.color.rgb = C_TEXT_DARK
        pd = tf_tl.add_paragraph()
        pd.text = f"   {d}"
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = C_TEXT_MUTED
        pd.space_after = Pt(5)

    # Dark Theme Card
    add_card(s11, 6.7, 1.5, 5.8, 5.4, C_BG_DARK, C_BG_DARK)
    tb_th_d = s11.shapes.add_textbox(Inches(7.0), Inches(1.7), Inches(5.2), Inches(5.0))
    tf_td = tb_th_d.text_frame
    tf_td.word_wrap = True
    p = tf_td.paragraphs[0]
    p.text = "🌙 True Dark Zinc Theme Mode"
    p.font.bold = True
    p.font.size = Pt(15)
    p.font.color.rgb = RGBColor(129, 140, 248)
    p.space_after = Pt(12)

    d_specs = [
        ("Background Token (`page`)", "#09090B (Zinc 950) - True dark ocular comfort."),
        ("Surface Card Token (`surface`)", "#18181B (Zinc 900) - Elevated dark card."),
        ("Text & Typography (`text`)", "#FAFAFA (Zinc 50) - High contrast crisp white."),
        ("Subtle Border Token (`border`)", "#3F3F46 (Zinc 700) - Muted visual borders."),
        ("Vibrant Indigo Accent", "#818CF8 (Indigo 400) - Glowing neon brand contrast."),
        ("Instant Real-Time Toggle", "Switchable in one click from Login, Top Bar, or `Ctrl+T` shortcut."),
    ]
    for t, d in d_specs:
        pt = tf_td.add_paragraph()
        pt.text = f"• {t}: "
        pt.font.bold = True
        pt.font.size = Pt(10.5)
        pt.font.color.rgb = C_WHITE
        pd = tf_td.add_paragraph()
        pd.text = f"   {d}"
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = RGBColor(148, 163, 184)
        pd.space_after = Pt(5)

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 12: KEYBOARD SHORTCUTS & PRODUCTIVITY
    # ══════════════════════════════════════════════════════════════════════════
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_background(s12, C_CARD_ALT)
    add_header(s12, "Feature Showcase: Global Keyboard Shortcuts & Ergonomics", "REVIEW 2 • CORE FEATURES")

    sh_headers = ["Key Combination", "Target Action / Screen", "Role Accessibility", "Description"]
    sh_rows = [
        ["Ctrl + H", "Home / Dashboard", "Admin & Student", "Instantly returns to the main dashboard overview from any screen."],
        ["Ctrl + R", "Refresh Active View", "Admin & Student", "Reloads table datasets and metric counters directly from SQLite database."],
        ["Ctrl + S", "Open Students View", "Administrator", "Navigates directly to the Student Records management and CRUD console."],
        ["Ctrl + F", "Open Fees Ledger", "Administrator", "Opens fee collections, pending invoice tracking, and receipt generation."],
        ["Ctrl + N", "Notifications Panel", "Admin & Student", "Pulls up the broadcast announcement feed and personal notification alerts."],
        ["Ctrl + T", "Toggle Theme Mode", "Admin & Student", "Switches between Light and Dark mode without reloading the page state."],
        ["Ctrl + L", "Secure Logout", "Admin & Student", "Destroys active session token and safely returns to the Login Gateway."],
        ["Ctrl + Q", "Quit Application", "All Users", "Safely closes all database connections and shuts down application window."],
    ]
    add_table(s12, 0.8, 1.5, 11.7, 5.4, sh_headers, sh_rows, [1.8, 2.5, 2.2, 5.2])

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 13: USER PROFILE & SECURITY SETTINGS
    # ══════════════════════════════════════════════════════════════════════════
    s13 = prs.slides.add_slide(blank_layout)
    set_slide_background(s13, C_CARD_ALT)
    add_header(s13, "Feature Showcase: User Profile & Security Settings", "REVIEW 2 • CORE FEATURES")

    p_cards = [
        ("👤 Identity & Contact Info", "Profile Management", [
            "View registered full name, student ID, course, and hostel room information.",
            "Edit and persist phone number, primary email address, and emergency contact details.",
            "Auto-updates across both `users` and `students` tables in single atomic transaction.",
            "Input format validation for phone (+91/10-digit) and standard RFC email format.",
        ], C_PRIMARY),
        ("🔒 Credential & Password Guard", "Cryptographic Security", [
            "Self-service password update requiring existing password verification.",
            "Enforces password strength: minimum 8 characters with numbers and symbols.",
            "Hashes new passwords with high-cost salt using bcrypt library.",
            "Admin can provision initial student passwords during new admissions.",
        ], C_SUCCESS),
        ("⚙️ Session & Preferences", "Customization Control", [
            "Manage persistent preferences including default startup screen and notification toasts.",
            "Session revocation: Invalidate credentials immediately upon suspicious activity.",
            "Audit trail logging: Timestamps track last password change and account updates.",
            "Data isolation prevents students from modifying administrative account flags.",
        ], C_ACCENT_TEAL),
    ]

    for idx, (title, sub, bullets, color) in enumerate(p_cards):
        x = 0.8 + idx * 3.9
        add_card(s13, x, 1.5, 3.65, 5.4, C_WHITE)

        hbar = s13.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(1.5), Inches(3.65), Inches(0.1))
        hbar.fill.solid()
        hbar.fill.fore_color.rgb = color
        hbar.line.fill.background()

        tb_pc = s13.shapes.add_textbox(Inches(x + 0.2), Inches(1.75), Inches(3.25), Inches(5.0))
        tf_pc = tb_pc.text_frame
        tf_pc.word_wrap = True

        p1 = tf_pc.paragraphs[0]
        p1.text = title
        p1.font.bold = True
        p1.font.size = Pt(13)
        p1.font.color.rgb = C_TEXT_DARK

        p2 = tf_pc.add_paragraph()
        p2.text = sub
        p2.font.bold = True
        p2.font.size = Pt(10)
        p2.font.color.rgb = color
        p2.space_after = Pt(12)

        for b in bullets:
            pb = tf_pc.add_paragraph()
            pb.text = f"✔ {b}"
            pb.font.size = Pt(10)
            pb.font.color.rgb = C_TEXT_MUTED
            pb.space_after = Pt(8)

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 14: SYSTEM WORKFLOW & FLOWCHART
    # ══════════════════════════════════════════════════════════════════════════
    s14 = prs.slides.add_slide(blank_layout)
    set_slide_background(s14, C_CARD_ALT)
    add_header(s14, "System Architecture & Execution Flowchart", "REVIEW 1 & 2 • WORKFLOW DESIGN")

    # Workflow Steps across horizontal chain
    steps = [
        ("Step 1: Gateway", "User enters credentials on dual-pane LoginView; role selected.", C_BG_DARK),
        ("Step 2: Auth Check", "Bcrypt verifies hash; session token issued with role scoping.", C_PRIMARY),
        ("Step 3: Route Hub", "Role router opens Admin DashboardView or StudentDashboardView.", C_ACCENT_TEAL),
        ("Step 4: Services", "Modules invoke `room_service`, `fee_service`, `student_service`.", C_SUCCESS),
        ("Step 5: Database", "SQLite executes atomic transactions with foreign key checks.", C_BG_DARK),
    ]

    for idx, (title, desc, col) in enumerate(steps):
        x = 0.8 + idx * 2.45
        add_card(s14, x, 1.6, 2.25, 2.2, C_WHITE)

        hbar = s14.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(1.6), Inches(2.25), Inches(0.4))
        hbar.fill.solid()
        hbar.fill.fore_color.rgb = col
        hbar.line.fill.background()

        tb_s = s14.shapes.add_textbox(Inches(x + 0.1), Inches(1.65), Inches(2.05), Inches(0.3))
        tf_s = tb_s.text_frame
        p_s = tf_s.paragraphs[0]
        p_s.text = title
        p_s.font.bold = True
        p_s.font.size = Pt(10)
        p_s.font.color.rgb = C_WHITE

        tb_sb = s14.shapes.add_textbox(Inches(x + 0.15), Inches(2.1), Inches(1.95), Inches(1.6))
        tf_sb = tb_sb.text_frame
        tf_sb.word_wrap = True
        psb = tf_sb.paragraphs[0]
        psb.text = desc
        psb.font.size = Pt(9.5)
        psb.font.color.rgb = C_TEXT_MUTED

    # Bottom Core Flowchart Box
    add_card(s14, 0.8, 4.1, 11.7, 2.8, C_WHITE)
    tb_fc = s14.shapes.add_textbox(Inches(1.0), Inches(4.25), Inches(11.3), Inches(2.5))
    tf_fc = tb_fc.text_frame
    tf_fc.word_wrap = True

    p = tf_fc.paragraphs[0]
    p.text = "🔄 Key System Operational Lifecycles"
    p.font.bold = True
    p.font.size = Pt(13)
    p.font.color.rgb = C_PRIMARY
    p.space_after = Pt(8)

    flows = [
        ("Room Allocation Lifecycle", "Admin selects student & room → Capacity check (`occupied_beds < capacity`) → Atomic INSERT into allocations → Increment `rooms.occupied_beds` → Update `students.room_number` & `bed_number`."),
        ("Fee Payment & Receipt Lifecycle", "Fee invoiced (`status='Unpaid'`) → Student/Admin records settlement → Verify amount → `fees.status` updated to 'Paid' or 'Partial' → Auto-generate PDF receipt via ReportLab → Audit log stored."),
        ("Grievance Resolution Lifecycle", "Student logs complaint with category & priority → Real-time alert to Warden → Admin updates status to 'In Progress' → Maintenance completed → Admin enters resolution remarks → Status updated to 'Resolved'."),
    ]
    for t, d in flows:
        pt = tf_fc.add_paragraph()
        pt.text = f"• {t}: "
        pt.font.bold = True
        pt.font.size = Pt(10.5)
        pt.font.color.rgb = C_TEXT_DARK
        pd = tf_fc.add_paragraph()
        pd.text = f"   {d}"
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = C_TEXT_MUTED
        pd.space_after = Pt(4)

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 15: REVIEW 2 IMPLEMENTATION & VERIFICATION
    # ══════════════════════════════════════════════════════════════════════════
    s15 = prs.slides.add_slide(blank_layout)
    set_slide_background(s15, C_CARD_ALT)
    add_header(s15, "Review 2: Verification, Automated Testing & Working Proof", "REVIEW 2 • CRUD & VERIFICATION")

    # Left: Test Summary Stats
    add_card(s15, 0.8, 1.5, 4.2, 5.4, C_WHITE)
    tb_ts = s15.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(3.8), Inches(5.0))
    tf_ts = tb_ts.text_frame
    tf_ts.word_wrap = True

    p = tf_ts.paragraphs[0]
    p.text = "🧪 Automated Test Suite"
    p.font.bold = True
    p.font.size = Pt(15)
    p.font.color.rgb = C_SUCCESS
    p.space_after = Pt(12)

    p_stat = tf_ts.add_paragraph()
    p_stat.text = "28 / 28 PASSED"
    p_stat.font.bold = True
    p_stat.font.size = Pt(28)
    p_stat.font.color.rgb = C_SUCCESS
    p_stat.space_after = Pt(12)

    test_highlights = [
        ("Authentication & RBAC", "Tested invalid passwords, role escalation prevention, and session token timeouts."),
        ("Student CRUD & Scoping", "Tested student additions, duplicate email blocks, updates, and cascading room frees."),
        ("Room Capacity Integrity", "Tested zero over-allocation guarantees and atomic capacity adjustments."),
        ("Fee Calculation & Ledger", "Tested partial vs full payment math, isolation between students, and zero-fee conditions."),
        ("Data Isolation Guarantees", "Ensured student users cannot query other students' complaints, fees, or profiles."),
    ]
    for t, d in test_highlights:
        pt = tf_ts.add_paragraph()
        pt.text = f"✔ {t}"
        pt.font.bold = True
        pt.font.size = Pt(10)
        pt.font.color.rgb = C_TEXT_DARK
        pd = tf_ts.add_paragraph()
        pd.text = f"   {d}"
        pd.font.size = Pt(9)
        pd.font.color.rgb = C_TEXT_MUTED
        pd.space_after = Pt(4)

    # Right: Working Demo Deliverables
    add_card(s15, 5.3, 1.5, 7.2, 5.4, C_WHITE)
    tb_wd = s15.shapes.add_textbox(Inches(5.6), Inches(1.7), Inches(6.6), Inches(5.0))
    tf_wd = tb_wd.text_frame
    tf_wd.word_wrap = True

    p = tf_wd.paragraphs[0]
    p.text = "🚀 Working Application Deliverables Completed"
    p.font.bold = True
    p.font.size = Pt(15)
    p.font.color.rgb = C_PRIMARY
    p.space_after = Pt(12)

    deliverables = [
        ("1. Fully Functional Flet Desktop App", "Launched with `python main.py` or `.venv/Scripts/python app_flet.py`; native window with maximized default state."),
        ("2. Complete End-to-End CRUD", "Active user management, student admission & records, live room & bed matrix, and dues settlement."),
        ("3. Modern SaaS Presentation Tier", "Tokenized styling, responsive split-screen cards, dark/light theme switching, and interactive modal dialogs."),
        ("4. Role-Scoped Portals", "Separate, tailored experiences for Warden/Administrator (governance) and Student Residents (self-service)."),
        ("5. Institutional Compliance Reporting", "Direct one-click CSV export and ReportLab PDF fee receipt generation."),
        ("6. Production-Ready Code Architecture", "Clean separation of presentation (`flet_views/`), domain services (`services/`), and data storage (`database/`)."),
    ]
    for t, d in deliverables:
        pt = tf_wd.add_paragraph()
        pt.text = f"• {t}: "
        pt.font.bold = True
        pt.font.size = Pt(10.5)
        pt.font.color.rgb = C_TEXT_DARK
        pd = tf_wd.add_paragraph()
        pd.text = f"   {d}"
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = C_TEXT_MUTED
        pd.space_after = Pt(6)

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 16: CONCLUSION & ROADMAP
    # ══════════════════════════════════════════════════════════════════════════
    s16 = prs.slides.add_slide(blank_layout)
    set_slide_background(s16, C_BG_DARK)

    tb_end = s16.shapes.add_textbox(Inches(1.2), Inches(1.0), Inches(11), Inches(1.5))
    tf_end = tb_end.text_frame
    tf_end.word_wrap = True

    p = tf_end.paragraphs[0]
    p.text = "PROJECT SUMMARY & FUTURE ROADMAP"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = RGBColor(129, 140, 248)

    p2 = tf_end.add_paragraph()
    p2.text = "Hostel Management System — Review 1 & 2 Completed"
    p2.font.bold = True
    p2.font.size = Pt(30)
    p2.font.color.rgb = C_WHITE

    # Left Card: Completed Highlights
    add_card(s16, 1.2, 2.7, 5.2, 4.0, RGBColor(30, 41, 59), RGBColor(51, 65, 85))
    tb_c1 = s16.shapes.add_textbox(Inches(1.4), Inches(2.9), Inches(4.8), Inches(3.6))
    tf_c1 = tb_c1.text_frame
    tf_c1.word_wrap = True
    p = tf_c1.paragraphs[0]
    p.text = "🌟 Completed Milestones"
    p.font.bold = True
    p.font.size = Pt(15)
    p.font.color.rgb = C_SUCCESS
    p.space_after = Pt(10)

    milestones = [
        "Comprehensive SRS with Functional & Non-Functional specifications.",
        "Modular folder architecture cleanly separating UI, business logic & DB.",
        "Full CRUD operations implemented and verified across 7 core modules.",
        "Interactive role-scoped dashboards for Administrators and Students.",
        "Modern SaaS UI with Light/Dark Theme toggle & keyboard shortcuts.",
        "Export engine generating CSV audits & ReportLab PDF fee vouchers.",
        "100% test pass rate across 28 automated Pytest test suites.",
    ]
    for m in milestones:
        pm = tf_c1.add_paragraph()
        pm.text = f"✔ {m}"
        pm.font.size = Pt(9.5)
        pm.font.color.rgb = RGBColor(226, 232, 240)
        pm.space_after = Pt(4)

    # Right Card: Future Scope
    add_card(s16, 6.8, 2.7, 5.3, 4.0, RGBColor(30, 41, 59), RGBColor(51, 65, 85))
    tb_c2 = s16.shapes.add_textbox(Inches(7.0), Inches(2.9), Inches(4.9), Inches(3.6))
    tf_c2 = tb_c2.text_frame
    tf_c2.word_wrap = True
    p = tf_c2.paragraphs[0]
    p.text = "🚀 Future Scope & Enhancements"
    p.font.bold = True
    p.font.size = Pt(15)
    p.font.color.rgb = RGBColor(129, 140, 248)
    p.space_after = Pt(10)

    future = [
        ("Biometric & RFID Attendance", "Hardware sensor integration for automated student turnstile check-ins and curfew tracking."),
        ("Online Payment Gateway", "Integration of Razorpay / UPI QR code generation for instant in-app fee settlement."),
        ("Automated SMS & WhatsApp Alerts", "Instant notification dispatch to parents regarding night curfew leaves or fee dues."),
        ("AI Predictive Maintenance", "Predictive machine learning models to forecast hostel facility repairs before major breakdowns."),
        ("Cross-Platform Mobile App", "Extending Flet presentation layer to iOS and Android resident mobile apps."),
    ]
    for t, d in future:
        pt = tf_c2.add_paragraph()
        pt.text = f"• {t}: "
        pt.font.bold = True
        pt.font.size = Pt(10)
        pt.font.color.rgb = C_WHITE
        pd = tf_c2.add_paragraph()
        pd.text = f"   {d}"
        pd.font.size = Pt(9)
        pd.font.color.rgb = RGBColor(148, 163, 184)
        pd.space_after = Pt(3)

    # Save presentation
    output_path = Path("Hostel_Management_System_Review_Presentation.pptx").resolve()
    prs.save(str(output_path))
    print(f"Presentation successfully saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    create_presentation()
