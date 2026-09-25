import sys
import pygame
from config import *
from db import SchoolDatabase
from ui_components import Button, TextInput
from pdf_generator import generate_fee_invoice, generate_teacher_salary_slip, generate_misc_invoice
import views

class SchoolMISApp:
    def __init__(self):
        pygame.init()
        pygame.event.pump()
        self.width, self.height = 1150, 700
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(f"{ORG_NAME} - Management Information System")
        self.clock = pygame.time.Clock()

        # Render immediate initial frame
        self.screen.fill(BG_COLOR)
        pygame.display.flip()

        self.db = SchoolDatabase()
        self.state = "DASHBOARD"
        
        self.editing_student_id = None
        self.billing_student_id = None
        self.history_student_id = None
        self.editing_teacher_id = None
        self.selected_teacher_id = None
        
        self.student_row_buttons = []
        self.teacher_row_buttons = []
        self.salary_row_buttons = []
        
        self.font_title = pygame.font.SysFont("Arial", 26, bold=True)
        self.font_header = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_regular = pygame.font.SysFont("Arial", 15)
        
        # Navigation Buttons (Sidebar)
        self.btn_dashboard = Button(20, 30, 200, 42, "Dashboard", ACCENT_BLUE, (52, 152, 219), font_size=17)
        self.btn_students = Button(20, 82, 200, 42, "Students MIS", ACCENT_BLUE, (52, 152, 219), font_size=17)
        self.btn_teachers = Button(20, 134, 200, 42, "Teachers MIS", ACCENT_BLUE, (52, 152, 219), font_size=17)
        self.btn_finances = Button(20, 186, 200, 42, "Fees & Salaries", ACCENT_BLUE, (52, 152, 219), font_size=17)
        self.btn_misc_billing = Button(20, 238, 200, 42, "Misc Billing", ACCENT_TEAL, (26, 188, 156), font_size=17)

        # Back Buttons
        self.btn_back_to_teachers = Button(930, 25, 170, 35, "← Back to Teachers", ACCENT_BLUE, (52, 152, 219), font_size=14)
        self.btn_back_to_students = Button(930, 25, 170, 35, "← Back to Students", ACCENT_BLUE, (52, 152, 219), font_size=14)

        # Student Form Inputs
        self.s_name_input = TextInput(270, 160, 170, 35, "Full Name")
        self.s_grade_input = TextInput(450, 160, 75, 35, "Grade")
        self.s_phone_input = TextInput(535, 160, 130, 35, "Phone No")
        self.s_fees_input = TextInput(675, 160, 95, 35, f"Fees Due ({CURRENCY_SYMBOL})")
        self.btn_add_student = Button(780, 160, 115, 35, "Add Student", ACCENT_GREEN, (46, 204, 113), font_size=14)
        self.btn_cancel_student = Button(905, 160, 75, 35, "Cancel", ACCENT_RED, (192, 57, 43), font_size=14)
        self.s_search_input = TextInput(270, 210, 320, 35, "Search student by name...")

        # Teacher Form Inputs
        self.t_name_input = TextInput(270, 160, 200, 35, "Teacher Name")
        self.t_subject_input = TextInput(485, 160, 150, 35, "Subject")
        self.t_sal_input = TextInput(650, 160, 120, 35, f"Salary ({CURRENCY_SYMBOL})")
        self.btn_add_teacher = Button(790, 160, 120, 35, "Add Teacher", ACCENT_GREEN, (46, 204, 113), font_size=14)
        self.btn_cancel_teacher = Button(920, 160, 75, 35, "Cancel", ACCENT_RED, (192, 57, 43), font_size=14)
        self.t_search_input = TextInput(270, 210, 320, 35, "Search teacher by name...")

        # Misc Billing Form Inputs
        self.m_name_input = TextInput(290, 160, 260, 40, "Client / Recipient Name")
        self.m_phone_input = TextInput(570, 160, 220, 40, "Phone Number")
        self.m_desc_input = TextInput(290, 240, 500, 40, "Item / Task Description")
        self.m_amount_input = TextInput(290, 320, 220, 40, f"Amount ({CURRENCY_SYMBOL})")
        self.btn_gen_misc = Button(530, 320, 260, 40, "Generate & Print PDF", ACCENT_TEAL, (26, 188, 156), font_size=16)

    def run(self):
        while True:
            self.handle_events()
            self.render()
            self.clock.tick(60)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Sidebar Navigation
            if self.btn_dashboard.is_clicked(event):
                self.state = "DASHBOARD"
            elif self.btn_students.is_clicked(event):
                self.state = "STUDENTS"
                self.reset_student_form()
            elif self.btn_teachers.is_clicked(event):
                self.state = "TEACHERS"
                self.selected_teacher_id = None
                self.reset_teacher_form()
            elif self.btn_finances.is_clicked(event):
                self.state = "FINANCES"
            elif self.btn_misc_billing.is_clicked(event):
                self.state = "MISC_BILLING"

            if self.state == "STUDENTS":
                if self.billing_student_id:
                    self.s_fees_input.handle_event(event)
                    self.s_search_input.handle_event(event)
                else:
                    self.s_name_input.handle_event(event)
                    self.s_grade_input.handle_event(event)
                    self.s_phone_input.handle_event(event)
                    self.s_fees_input.handle_event(event)
                    self.s_search_input.handle_event(event)

                if self.btn_add_student.is_clicked(event):
                    if self.billing_student_id:
                        try:
                            payment_amount = float(self.s_fees_input.text) if self.s_fees_input.text.strip() else 0.0
                        except ValueError:
                            payment_amount = 0.0

                        doc = self.db.students.find_one({"_id": self.billing_student_id})
                        if doc and payment_amount > 0:
                            current_due = doc.get("fees_due", 0.0)
                            new_remaining = max(0.0, current_due - payment_amount)
                            self.db.record_student_payment(self.billing_student_id, payment_amount, new_remaining)
                            generate_fee_invoice(
                                doc.get("name"), doc.get("grade"), doc.get("phone"), payment_amount, new_remaining
                            )
                        self.reset_student_form()
                    else:
                        if self.s_name_input.text.strip():
                            try:
                                fees = float(self.s_fees_input.text) if self.s_fees_input.text.strip() else 0.0
                            except ValueError:
                                fees = 0.0
                            
                            data = {
                                "name": self.s_name_input.text.strip(),
                                "grade": self.s_grade_input.text.strip() or "N/A",
                                "phone": self.s_phone_input.text.strip() or "N/A",
                                "fees_due": fees
                            }

                            if self.editing_student_id:
                                self.db.update_student(self.editing_student_id, data)
                            else:
                                self.db.add_student(data)
                            self.reset_student_form()

                if self.btn_cancel_student.is_clicked(event):
                    self.reset_student_form()

                for row in self.student_row_buttons:
                    if row["edit"].is_clicked(event):
                        self.editing_student_id = row["id"]
                        self.billing_student_id = None
                        doc = self.db.students.find_one({"_id": row["id"]})
                        if doc:
                            self.s_name_input.text = doc.get("name", "")
                            self.s_grade_input.text = str(doc.get("grade", ""))
                            self.s_phone_input.text = str(doc.get("phone", ""))
                            self.s_fees_input.text = str(doc.get("fees_due", ""))
                            self.btn_add_student.text = "Update"
                        break
                    elif row["delete"].is_clicked(event):
                        self.db.delete_student(row["id"])
                        if self.editing_student_id == row["id"] or self.billing_student_id == row["id"]:
                            self.reset_student_form()
                        break
                    elif row["bill"].is_clicked(event):
                        self.billing_student_id = row["id"]
                        self.editing_student_id = None
                        doc = self.db.students.find_one({"_id": row["id"]})
                        if doc:
                            self.s_fees_input.text = str(doc.get("fees_due", ""))
                            self.btn_add_student.text = "Process & Print"
                        break
                    elif row["history"].is_clicked(event):
                        self.history_student_id = row["id"]
                        self.state = "STUDENT_HISTORY_VIEW"
                        break

            elif self.state == "STUDENT_HISTORY_VIEW":
                if self.btn_back_to_students.is_clicked(event):
                    self.state = "STUDENTS"
                    self.history_student_id = None

            elif self.state == "TEACHERS":
                self.t_name_input.handle_event(event)
                self.t_subject_input.handle_event(event)
                self.t_sal_input.handle_event(event)
                self.t_search_input.handle_event(event)

                if self.btn_add_teacher.is_clicked(event):
                    if self.t_name_input.text.strip():
                        try:
                            sal = float(self.t_sal_input.text) if self.t_sal_input.text.strip() else 0.0
                        except ValueError:
                            sal = 0.0

                        data = {
                            "name": self.t_name_input.text.strip(),
                            "subject": self.t_subject_input.text.strip() or "General",
                            "salary": sal
                        }

                        if self.editing_teacher_id:
                            self.db.update_teacher(self.editing_teacher_id, data)
                        else:
                            self.db.add_teacher(data)
                        self.reset_teacher_form()

                if self.btn_cancel_teacher.is_clicked(event):
                    self.reset_teacher_form()

                for row in self.teacher_row_buttons:
                    if row["edit"].is_clicked(event):
                        self.editing_teacher_id = row["id"]
                        doc = self.db.teachers.find_one({"_id": row["id"]})
                        if doc:
                            self.t_name_input.text = doc.get("name", "")
                            self.t_subject_input.text = str(doc.get("subject", ""))
                            self.t_sal_input.text = str(doc.get("salary", ""))
                            self.btn_add_teacher.text = "Update"
                        break
                    elif row["delete"].is_clicked(event):
                        self.db.delete_teacher(row["id"])
                        if self.editing_teacher_id == row["id"]:
                            self.reset_teacher_form()
                        break
                    elif row["salary_view"].is_clicked(event):
                        self.selected_teacher_id = row["id"]
                        self.state = "TEACHER_SALARY_VIEW"
                        break

            elif self.state == "TEACHER_SALARY_VIEW":
                if self.btn_back_to_teachers.is_clicked(event):
                    self.state = "TEACHERS"

                for row in self.salary_row_buttons:
                    if row["pay_btn"].is_clicked(event):
                        t_doc = self.db.teachers.find_one({"_id": self.selected_teacher_id})
                        if t_doc:
                            records = t_doc.get("salary_records", [])
                            for rec in records:
                                if rec["month"] == row["month"]:
                                    rec["status"] = "Paid"
                                    break
                            
                            self.db.update_teacher(self.selected_teacher_id, {"salary_records": records})
                            generate_teacher_salary_slip(
                                t_doc.get("name"), t_doc.get("subject"), row["month"], t_doc.get("salary", 0.0)
                            )
                        break
                    elif row["toggle_btn"].is_clicked(event):
                        t_doc = self.db.teachers.find_one({"_id": self.selected_teacher_id})
                        if t_doc:
                            records = t_doc.get("salary_records", [])
                            for rec in records:
                                if rec["month"] == row["month"]:
                                    rec["status"] = "Unpaid" if rec["status"] == "Paid" else "Paid"
                                    break
                            
                            self.db.update_teacher(self.selected_teacher_id, {"salary_records": records})
                        break

            elif self.state == "MISC_BILLING":
                self.m_name_input.handle_event(event)
                self.m_phone_input.handle_event(event)
                self.m_desc_input.handle_event(event)
                self.m_amount_input.handle_event(event)

                if self.btn_gen_misc.is_clicked(event):
                    try:
                        amt = float(self.m_amount_input.text) if self.m_amount_input.text.strip() else 0.0
                    except ValueError:
                        amt = 0.0

                    if amt > 0:
                        generate_misc_invoice(
                            self.m_name_input.text.strip(),
                            self.m_phone_input.text.strip(),
                            self.m_desc_input.text.strip(),
                            amt
                        )
                        self.m_name_input.clear()
                        self.m_phone_input.clear()
                        self.m_desc_input.clear()
                        self.m_amount_input.clear()

    def reset_student_form(self):
        self.s_name_input.clear()
        self.s_grade_input.clear()
        self.s_phone_input.clear()
        self.s_fees_input.clear()
        self.editing_student_id = None
        self.billing_student_id = None
        self.btn_add_student.text = "Add Student"

    def reset_teacher_form(self):
        self.t_name_input.clear()
        self.t_subject_input.clear()
        self.t_sal_input.clear()
        self.editing_teacher_id = None
        self.btn_add_teacher.text = "Add Teacher"

    def get_filtered_students(self):
        students = self.db.get_students()
        query = self.s_search_input.text.lower().strip()
        if query:
            students = [s for s in students if query in s.get("name", "").lower()]
        return students

    def get_filtered_teachers(self):
        teachers = self.db.get_teachers()
        query = self.t_search_input.text.lower().strip()
        if query:
            teachers = [t for t in teachers if query in t.get("name", "").lower()]
        return teachers

    def render(self):
        self.screen.fill(BG_COLOR)
        
        sidebar_rect = pygame.Rect(0, 0, 240, self.height)
        pygame.draw.rect(self.screen, SIDEBAR_COLOR, sidebar_rect)
        
        self.btn_dashboard.draw(self.screen)
        self.btn_students.draw(self.screen)
        self.btn_teachers.draw(self.screen)
        self.btn_finances.draw(self.screen)
        self.btn_misc_billing.draw(self.screen)

        if self.state == "DASHBOARD":
            views.render_dashboard(self)
        elif self.state == "STUDENTS":
            views.render_students(self)
        elif self.state == "STUDENT_HISTORY_VIEW":
            views.render_student_history_view(self)
        elif self.state == "TEACHERS":
            views.render_teachers(self)
        elif self.state == "TEACHER_SALARY_VIEW":
            views.render_teacher_salary_view(self)
        elif self.state == "FINANCES":
            views.render_finances(self)
        elif self.state == "MISC_BILLING":
            views.render_misc_billing(self)

        pygame.display.flip()


if __name__ == "__main__":
    app = SchoolMISApp()
    app.run()