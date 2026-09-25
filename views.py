import pygame
from datetime import datetime
from config import *
from ui_components import Button

def draw_card(screen, font_regular, font_title, x, y, w, h, title, value, accent_color):
    rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(screen, CARD_BG, rect, border_radius=8)
    pygame.draw.rect(screen, accent_color, (x, y, 6, h), border_top_left_radius=8, border_bottom_left_radius=8)
    
    t_surf = font_regular.render(title, True, TEXT_LIGHT)
    v_surf = font_title.render(value, True, TEXT_DARK)
    screen.blit(t_surf, (x + 20, y + 18))
    screen.blit(v_surf, (x + 20, y + 50))

def render_dashboard(app):
    title = app.font_title.render(f"{ORG_NAME} - Dashboard", True, TEXT_DARK)
    app.screen.blit(title, (260, 30))

    students = app.db.get_students()
    teachers = app.db.get_teachers()
    total_dues = sum(s.get("fees_due", 0) for s in students)

    draw_card(app.screen, app.font_regular, app.font_title, 260, 90, 260, 110, "Total Students", str(len(students)), ACCENT_BLUE)
    draw_card(app.screen, app.font_regular, app.font_title, 540, 90, 260, 110, "Total Teachers", str(len(teachers)), ACCENT_BLUE)
    draw_card(app.screen, app.font_regular, app.font_title, 820, 90, 280, 110, "Outstanding Dues", f"{CURRENCY_SYMBOL} {total_dues:,.2f}", ACCENT_RED)

    info_rect = pygame.Rect(260, 230, 840, 400)
    pygame.draw.rect(app.screen, CARD_BG, info_rect, border_radius=8)
    
    h_text = app.font_header.render(f"Welcome to {ORG_NAME}", True, TEXT_DARK)
    app.screen.blit(h_text, (290, 260))
    
    guidelines = [
        "• Use sidebar buttons to navigate Student, Teacher, Financial, and Misc records.",
        "• Click 'History' in Students MIS to view combined monthly fee payments per year.",
        "• In Teachers MIS, click 'Salary & Ledger' to view monthly payment statuses and print slips.",
        f"• All monetary amounts are formatted in {CURRENCY_SYMBOL}.",
        "• All MongoDB data updates dynamically in real-time."
    ]
    y_pos = 310
    for g in guidelines:
        txt = app.font_regular.render(g, True, TEXT_DARK)
        app.screen.blit(txt, (290, y_pos))
        y_pos += 35

def render_students(app):
    title_text = "Process Fee Payment" if app.billing_student_id else ("Edit Student Record" if app.editing_student_id else "Student Management & Records")
    title = app.font_title.render(title_text, True, TEXT_DARK)
    app.screen.blit(title, (260, 30))

    panel_rect = pygame.Rect(260, 85, 840, 175)
    pygame.draw.rect(app.screen, CARD_BG, panel_rect, border_radius=8)

    if app.billing_student_id:
        doc = app.db.students.find_one({"_id": app.billing_student_id})
        s_name = doc.get("name", "") if doc else ""
        lbl = app.font_regular.render(f"Payment for: {s_name} (Current Due: {CURRENCY_SYMBOL} {doc.get('fees_due', 0):,.2f})", True, ACCENT_PURPLE)
        app.screen.blit(lbl, (285, 105))
        
        app.s_fees_input.rect.x, app.s_fees_input.rect.y = 420, 160
        app.s_fees_input.draw(app.screen)
        app.btn_add_student.rect.x, app.btn_add_student.rect.y = 550, 160
        app.btn_add_student.draw(app.screen)
        app.btn_cancel_student.rect.x, app.btn_cancel_student.rect.y = 680, 160
        app.btn_cancel_student.draw(app.screen)
    else:
        lbl_text = "Modify Student Details" if app.editing_student_id else "Register New Student"
        lbl = app.font_regular.render(lbl_text, True, ACCENT_ORANGE if app.editing_student_id else TEXT_DARK)
        app.screen.blit(lbl, (285, 105))

        app.s_name_input.rect.x, app.s_name_input.rect.y = 270, 160
        app.s_grade_input.rect.x, app.s_grade_input.rect.y = 450, 160
        app.s_phone_input.rect.x, app.s_phone_input.rect.y = 535, 160
        app.s_fees_input.rect.x, app.s_fees_input.rect.y = 675, 160
        app.btn_add_student.rect.x, app.btn_add_student.rect.y = 780, 160
        app.btn_cancel_student.rect.x, app.btn_cancel_student.rect.y = 905, 160

        app.s_name_input.draw(app.screen)
        app.s_grade_input.draw(app.screen)
        app.s_phone_input.draw(app.screen)
        app.s_fees_input.draw(app.screen)
        app.btn_add_student.draw(app.screen)
        if app.editing_student_id:
            app.btn_cancel_student.draw(app.screen)

    app.s_search_input.draw(app.screen)

    table_rect = pygame.Rect(260, 275, 840, 390)
    pygame.draw.rect(app.screen, CARD_BG, table_rect, border_radius=8)

    pygame.draw.rect(app.screen, (230, 235, 240), (260, 275, 840, 40), border_top_left_radius=8, border_top_right_radius=8)
    app.screen.blit(app.font_regular.render("Full Name", True, TEXT_DARK), (275, 285))
    app.screen.blit(app.font_regular.render("Grade", True, TEXT_DARK), (440, 285))
    app.screen.blit(app.font_regular.render("Phone No", True, TEXT_DARK), (520, 285))
    app.screen.blit(app.font_regular.render(f"Fees Due ({CURRENCY_SYMBOL})", True, TEXT_DARK), (630, 285))
    app.screen.blit(app.font_regular.render("Actions", True, TEXT_DARK), (780, 285))

    students = app.get_filtered_students()
    app.student_row_buttons = []
    y_offset = 325
    for s in students[:8]:
        app.screen.blit(app.font_regular.render(s.get("name", ""), True, TEXT_DARK), (275, y_offset + 5))
        app.screen.blit(app.font_regular.render(str(s.get("grade", "")), True, TEXT_DARK), (440, y_offset + 5))
        app.screen.blit(app.font_regular.render(str(s.get("phone", "")), True, TEXT_DARK), (520, y_offset + 5))
        app.screen.blit(app.font_regular.render(f"{CURRENCY_SYMBOL} {s.get('fees_due', 0):,.2f}", True, TEXT_DARK), (630, y_offset + 5))

        edit_btn = Button(760, y_offset, 45, 30, "Edit", ACCENT_ORANGE, (211, 84, 0), font_size=12)
        del_btn = Button(810, y_offset, 50, 30, "Delete", ACCENT_RED, (192, 57, 43), font_size=12)
        bill_btn = Button(865, y_offset, 75, 30, "Print Bill", ACCENT_PURPLE, (125, 60, 152), font_size=12)
        hist_btn = Button(945, y_offset, 65, 30, "History", ACCENT_TEAL, (26, 188, 156), font_size=12)
        
        edit_btn.draw(app.screen)
        del_btn.draw(app.screen)
        bill_btn.draw(app.screen)
        hist_btn.draw(app.screen)

        app.student_row_buttons.append({
            "id": s["_id"], "edit": edit_btn, "delete": del_btn, "bill": bill_btn, "history": hist_btn
        })
        y_offset += 45

def render_student_history_view(app):
    doc = app.db.students.find_one({"_id": app.history_student_id})
    if not doc:
        app.state = "STUDENTS"
        return

    title = app.font_title.render(f"Payment History: {doc.get('name')} (Grade {doc.get('grade')})", True, TEXT_DARK)
    app.screen.blit(title, (260, 25))

    app.btn_back_to_students.draw(app.screen)

    card_rect = pygame.Rect(260, 75, 840, 590)
    pygame.draw.rect(app.screen, CARD_BG, card_rect, border_radius=8)

    pygame.draw.rect(app.screen, (230, 235, 240), (260, 75, 840, 40), border_top_left_radius=8, border_top_right_radius=8)
    app.screen.blit(app.font_regular.render("Year", True, TEXT_DARK), (290, 85))
    app.screen.blit(app.font_regular.render("Month", True, TEXT_DARK), (420, 85))
    app.screen.blit(app.font_regular.render("Transactions", True, TEXT_DARK), (580, 85))
    app.screen.blit(app.font_regular.render(f"Total Paid ({CURRENCY_SYMBOL})", True, TEXT_DARK), (760, 85))

    history = doc.get("payment_history", [])
    monthly_summary = {}
    for entry in history:
        yr = entry.get("year", datetime.now().year)
        m = entry.get("month", "Unknown")
        amt = entry.get("amount", 0.0)
        
        key = (yr, m)
        if key not in monthly_summary:
            monthly_summary[key] = {"count": 0, "total": 0.0}
        
        monthly_summary[key]["count"] += 1
        monthly_summary[key]["total"] += amt

    y_offset = 130
    if not monthly_summary:
        empty_msg = app.font_regular.render("No fee payments recorded yet for this student.", True, TEXT_LIGHT)
        app.screen.blit(empty_msg, (290, y_offset))
    else:
        for (year, month), summary in sorted(monthly_summary.items(), key=lambda x: (x[0][0], x[0][1]), reverse=True):
            app.screen.blit(app.font_regular.render(str(year), True, TEXT_DARK), (290, y_offset))
            app.screen.blit(app.font_regular.render(str(month), True, TEXT_DARK), (420, y_offset))
            app.screen.blit(app.font_regular.render(f"{summary['count']} Payment(s)", True, ACCENT_BLUE), (580, y_offset))
            
            tot_surf = pygame.font.SysFont("Arial", 15, bold=True).render(f"{CURRENCY_SYMBOL} {summary['total']:,.2f}", True, ACCENT_GREEN)
            app.screen.blit(tot_surf, (760, y_offset))
            
            pygame.draw.line(app.screen, (240, 240, 240), (280, y_offset + 30), (1070, y_offset + 30))
            y_offset += 40

def render_teachers(app):
    title_text = "Edit Teacher Record" if app.editing_teacher_id else "Teacher Management & Salaries"
    title = app.font_title.render(title_text, True, TEXT_DARK)
    app.screen.blit(title, (260, 30))

    panel_rect = pygame.Rect(260, 85, 840, 175)
    pygame.draw.rect(app.screen, CARD_BG, panel_rect, border_radius=8)

    lbl_text = "Modify Teacher Details" if app.editing_teacher_id else "Register New Teacher"
    lbl = app.font_regular.render(lbl_text, True, ACCENT_ORANGE if app.editing_teacher_id else TEXT_DARK)
    app.screen.blit(lbl, (285, 105))

    app.t_name_input.rect.x, app.t_name_input.rect.y = 270, 160
    app.t_subject_input.rect.x, app.t_subject_input.rect.y = 485, 160
    app.t_sal_input.rect.x, app.t_sal_input.rect.y = 650, 160
    app.btn_add_teacher.rect.x, app.btn_add_teacher.rect.y = 790, 160
    app.btn_cancel_teacher.rect.x, app.btn_cancel_teacher.rect.y = 920, 160

    app.t_name_input.draw(app.screen)
    app.t_subject_input.draw(app.screen)
    app.t_sal_input.draw(app.screen)
    app.btn_add_teacher.draw(app.screen)
    if app.editing_teacher_id:
        app.btn_cancel_teacher.draw(app.screen)

    app.t_search_input.rect.x, app.t_search_input.rect.y = 270, 210
    app.t_search_input.draw(app.screen)

    table_rect = pygame.Rect(260, 275, 840, 390)
    pygame.draw.rect(app.screen, CARD_BG, table_rect, border_radius=8)

    pygame.draw.rect(app.screen, (230, 235, 240), (260, 275, 840, 40), border_top_left_radius=8, border_top_right_radius=8)
    app.screen.blit(app.font_regular.render("Teacher Name", True, TEXT_DARK), (285, 285))
    app.screen.blit(app.font_regular.render("Subject", True, TEXT_DARK), (450, 285))
    app.screen.blit(app.font_regular.render(f"Salary ({CURRENCY_SYMBOL})", True, TEXT_DARK), (570, 285))
    app.screen.blit(app.font_regular.render("Actions", True, TEXT_DARK), (760, 285))

    teachers = app.get_filtered_teachers()
    app.teacher_row_buttons = []
    y_offset = 325
    for t in teachers[:8]:
        app.screen.blit(app.font_regular.render(t.get("name", ""), True, TEXT_DARK), (285, y_offset + 5))
        app.screen.blit(app.font_regular.render(str(t.get("subject", "")), True, TEXT_DARK), (450, y_offset + 5))
        app.screen.blit(app.font_regular.render(f"{CURRENCY_SYMBOL} {t.get('salary', 0):,.2f}", True, TEXT_DARK), (570, y_offset + 5))

        edit_btn = Button(735, y_offset, 50, 30, "Edit", ACCENT_ORANGE, (211, 84, 0), font_size=13)
        del_btn = Button(790, y_offset, 60, 30, "Delete", ACCENT_RED, (192, 57, 43), font_size=13)
        salary_btn = Button(855, y_offset, 110, 30, "Salary & Ledger", ACCENT_PURPLE, (125, 60, 152), font_size=12)
        
        edit_btn.draw(app.screen)
        del_btn.draw(app.screen)
        salary_btn.draw(app.screen)

        app.teacher_row_buttons.append({"id": t["_id"], "edit": edit_btn, "delete": del_btn, "salary_view": salary_btn})
        y_offset += 45

def render_teacher_salary_view(app):
    t_doc = app.db.teachers.find_one({"_id": app.selected_teacher_id})
    if not t_doc:
        app.state = "TEACHERS"
        return

    title = app.font_title.render(f"Salary Ledger: {t_doc.get('name')} ({t_doc.get('subject')})", True, TEXT_DARK)
    app.screen.blit(title, (260, 25))

    app.btn_back_to_teachers.draw(app.screen)

    card_rect = pygame.Rect(260, 75, 840, 590)
    pygame.draw.rect(app.screen, CARD_BG, card_rect, border_radius=8)

    pygame.draw.rect(app.screen, (230, 235, 240), (260, 75, 840, 40), border_top_left_radius=8, border_top_right_radius=8)
    app.screen.blit(app.font_regular.render("Month", True, TEXT_DARK), (285, 85))
    app.screen.blit(app.font_regular.render(f"Monthly Amount ({CURRENCY_SYMBOL})", True, TEXT_DARK), (430, 85))
    app.screen.blit(app.font_regular.render("Payment Status", True, TEXT_DARK), (630, 85))
    app.screen.blit(app.font_regular.render("Actions / Controls", True, TEXT_DARK), (790, 85))

    records = t_doc.get("salary_records", [])
    if not records:
        records = [{"month": m, "status": "Unpaid"} for m in 
                   ["January", "February", "March", "April", "May", "June", 
                    "July", "August", "September", "October", "November", "December"]]

    monthly_sal = t_doc.get("salary", 0.0)
    app.salary_row_buttons = []
    y_offset = 125

    for rec in records:
        m_name = rec["month"]
        status = rec["status"]

        month_surf = app.font_regular.render(m_name, True, TEXT_DARK)
        amt_surf = app.font_regular.render(f"{CURRENCY_SYMBOL} {monthly_sal:,.2f}", True, TEXT_DARK)
        
        status_color = ACCENT_GREEN if status == "Paid" else ACCENT_RED
        status_surf = pygame.font.SysFont("Arial", 15, bold=True).render(status, True, status_color)

        app.screen.blit(month_surf, (285, y_offset + 5))
        app.screen.blit(amt_surf, (430, y_offset + 5))
        app.screen.blit(status_surf, (630, y_offset + 5))

        toggle_btn = Button(760, y_offset, 100, 28, "Toggle Paid", ACCENT_BLUE, (52, 152, 219), font_size=12)
        toggle_btn.draw(app.screen)

        pay_btn = Button(870, y_offset, 110, 28, "Pay & Print", ACCENT_GREEN, (46, 204, 113), font_size=12)
        pay_btn.draw(app.screen)

        app.salary_row_buttons.append({"month": m_name, "pay_btn": pay_btn, "toggle_btn": toggle_btn})
        y_offset += 43

def render_finances(app):
    title = app.font_title.render("Financial Overview: Fees & Salaries", True, TEXT_DARK)
    app.screen.blit(title, (260, 30))

    students = app.db.get_students()
    teachers = app.db.get_teachers()

    total_dues = sum(s.get("fees_due", 0) for s in students)
    total_salaries = sum(t.get("salary", 0) for t in teachers)

    draw_card(app.screen, app.font_regular, app.font_title, 260, 90, 390, 120, "Total Outstanding Student Fees", f"{CURRENCY_SYMBOL} {total_dues:,.2f}", ACCENT_RED)
    draw_card(app.screen, app.font_regular, app.font_title, 670, 90, 390, 120, "Total Monthly Teacher Salaries", f"{CURRENCY_SYMBOL} {total_salaries:,.2f}", ACCENT_BLUE)

    box_rect = pygame.Rect(260, 235, 800, 400)
    pygame.draw.rect(app.screen, CARD_BG, box_rect, border_radius=8)

    head = app.font_header.render("Balance Sheet Summary", True, TEXT_DARK)
    app.screen.blit(head, (290, 265))

    net_balance = total_dues - total_salaries
    lines = [
        f"Active Enrolled Students: {len(students)}",
        f"Active Teaching Staff: {len(teachers)}",
        f"Gross Student Fee Receivables: {CURRENCY_SYMBOL} {total_dues:,.2f}",
        f"Gross Payroll Liabilities: {CURRENCY_SYMBOL} {total_salaries:,.2f}",
        f"Net Projected Flow: {CURRENCY_SYMBOL} {net_balance:,.2f}"
    ]

    y = 320
    for l in lines:
        txt = app.font_regular.render(l, True, TEXT_DARK)
        app.screen.blit(txt, (290, y))
        y += 40

def render_misc_billing(app):
    title = app.font_title.render("Miscellaneous Billing & Invoicing", True, TEXT_DARK)
    app.screen.blit(title, (260, 30))

    card_rect = pygame.Rect(260, 85, 840, 560)
    pygame.draw.rect(app.screen, CARD_BG, card_rect, border_radius=8)

    head = app.font_header.render("Create Ad-hoc / Misc Item Invoice", True, ACCENT_TEAL)
    app.screen.blit(head, (290, 115))

    app.m_name_input.draw(app.screen)
    app.m_phone_input.draw(app.screen)
    app.m_desc_input.draw(app.screen)
    app.m_amount_input.draw(app.screen)
    app.btn_gen_misc.draw(app.screen)

    instructions = [
        "• Use this section for non-tuition items, fines, ID cards, certificate fees, or special events.",
        "• Fill in the recipient's details, task description, and amount.",
        "• Clicking 'Generate & Print PDF' will immediately format and open a custom misc invoice."
    ]
    y = 400
    for ins in instructions:
        txt = app.font_regular.render(ins, True, TEXT_DARK)
        app.screen.blit(txt, (290, y))
        y += 35