import sys
import os
import subprocess
import pygame
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas

# ==========================================
# --- GLOBAL CONFIGURATION ---
# ==========================================
CURRENCY_SYMBOL = "NRS"
ORG_NAME = "X INSTITUTION MIS"
# ==========================================


# --- DATABASE SETUP ---
class SchoolDatabase:
    def __init__(self, uri="mongodb://localhost:27017/", db_name="school_mis_pro"):
        try:
            self.client = MongoClient(uri, serverSelectionTimeoutMS=2000)
            self.db = self.client[db_name]
            self.students = self.db["students"]
            self.teachers = self.db["teachers"]
            self.client.server_info()
            print("Connected to MongoDB successfully!")
            
            # Auto-repair existing documents
            self.repair_database()
        except Exception as e:
            print(f"Database Connection Error: {e}. Make sure MongoDB is running.")
            sys.exit(1)

    def repair_database(self):
        # Ensure teachers have 12-month salary structure
        default_months = [
            {"month": m, "status": "Unpaid"} for m in 
            ["January", "February", "March", "April", "May", "June", 
             "July", "August", "September", "October", "November", "December"]
        ]
        self.teachers.update_many(
            {"salary_records": {"$exists": False}},
            {"$set": {"salary_records": default_months}}
        )

        # Ensure students have a payment_history array
        self.students.update_many(
            {"payment_history": {"$exists": False}},
            {"$set": {"payment_history": []}}
        )

    def add_student(self, data):
        if "payment_history" not in data:
            data["payment_history"] = []
        return self.students.insert_one(data)

    def get_students(self, query={}):
        return list(self.students.find(query))

    def update_student(self, student_id, data):
        return self.students.update_one({"_id": ObjectId(student_id)}, {"$set": data})

    def delete_student(self, student_id):
        return self.students.delete_one({"_id": ObjectId(student_id)})

    def record_student_payment(self, student_id, payment_amount, new_due):
        now = datetime.now()
        payment_entry = {
            "timestamp": now,
            "year": now.year,
            "month": now.strftime("%B"), # e.g., "September"
            "amount": payment_amount
        }
        return self.students.update_one(
            {"_id": ObjectId(student_id)},
            {
                "$set": {"fees_due": new_due},
                "$push": {"payment_history": payment_entry}
            }
        )

    def add_teacher(self, data):
        if "salary_records" not in data:
            default_months = [
                {"month": m, "status": "Unpaid"} for m in 
                ["January", "February", "March", "April", "May", "June", 
                 "July", "August", "September", "October", "November", "December"]
            ]
            data["salary_records"] = default_months
        return self.teachers.insert_one(data)

    def get_teachers(self, query={}):
        return list(self.teachers.find(query))

    def update_teacher(self, teacher_id, data):
        return self.teachers.update_one({"_id": ObjectId(teacher_id)}, {"$set": data})

    def delete_teacher(self, teacher_id):
        return self.teachers.delete_one({"_id": ObjectId(teacher_id)})


# --- PDF BILLING GENERATORS ---
def generate_fee_invoice(student_name, grade, phone, amount_paid, remaining_balance):
    os.makedirs("invoices", exist_ok=True)
    filename = f"invoices/Fee_Invoice_{student_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    c.setFillColor(colors.HexColor("#212f3d"))
    c.rect(0, height - 100, width, 100, fill=1, stroke=0)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(50, height - 55, ORG_NAME)
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 75, "Official Fee Statement & Payment Receipt")
    
    c.setFillColor(colors.HexColor("#bdc3c7"))
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(width - 50, height - 45, f"Date: {datetime.now().strftime('%b %d, %Y')}")
    c.drawRightString(width - 50, height - 60, f"Receipt ID: INV-{datetime.now().strftime('%H%M%S')}")
    
    c.setFillColor(colors.HexColor("#2c3e50"))
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 150, "Student Profile Overview:")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 180, f"Full Name:    {student_name}")
    c.drawString(50, height - 205, f"Grade Level:  {grade}")
    c.drawString(50, height - 230, f"Phone No:     {phone if phone else 'N/A'}")
    
    c.setFillColor(colors.HexColor("#2980b9"))
    c.rect(50, height - 290, width - 100, 30, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(70, height - 271, "Description")
    c.drawRightString(width - 70, height - 271, f"Amount ({CURRENCY_SYMBOL})")
    
    c.setFillColor(colors.HexColor("#444444"))
    c.setFont("Helvetica", 11)
    c.drawString(70, height - 330, "Tuition & Fee Partial/Full Payment Transaction")
    c.drawRightString(width - 70, height - 330, f"{CURRENCY_SYMBOL} {amount_paid:,.2f}")
    
    c.setStrokeColor(colors.HexColor("#bdc3c7"))
    c.setLineWidth(1)
    c.line(50, height - 355, width - 50, height - 355)
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(330, height - 385, "Payment Received Today:")
    c.drawRightString(width - 70, height - 385, f"{CURRENCY_SYMBOL} {amount_paid:,.2f}")
    
    c.drawString(330, height - 410, "Remaining Balance Due:")
    c.setFillColor(colors.HexColor("#c0392b"))
    c.drawRightString(width - 70, height - 410, f"{CURRENCY_SYMBOL} {remaining_balance:,.2f}")
    
    c.showPage()
    c.save()
    
    abs_filename = os.path.abspath(filename)
    try:
        if sys.platform == "win32":
            os.startfile(abs_filename)
        elif sys.platform == "darwin":
            subprocess.run(["open", abs_filename])
        else:
            subprocess.run(["xdg-open", abs_filename])
    except Exception as e:
        print(f"Could not open PDF viewer: {e}")


def generate_teacher_salary_slip(teacher_name, subject, month, amount):
    os.makedirs("invoices", exist_ok=True)
    filename = f"invoices/Salary_Slip_{teacher_name.replace(' ', '_')}_{month}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    c.setFillColor(colors.HexColor("#8e44ad"))
    c.rect(0, height - 100, width, 100, fill=1, stroke=0)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(50, height - 55, ORG_NAME)
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 75, f"Official Monthly Salary Disbursement Slip - {month}")
    
    c.setFillColor(colors.HexColor("#bdc3c7"))
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(width - 50, height - 45, f"Date: {datetime.now().strftime('%b %d, %Y')}")
    c.drawRightString(width - 50, height - 60, f"Slip ID: SAL-{datetime.now().strftime('%H%M%S')}")
    
    c.setFillColor(colors.HexColor("#2c3e50"))
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 150, "Faculty Member Details:")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 180, f"Teacher Name:  {teacher_name}")
    c.drawString(50, height - 205, f"Department:    {subject}")
    c.drawString(50, height - 230, f"Pay Period:    {month}")
    
    c.setFillColor(colors.HexColor("#8e44ad"))
    c.rect(50, height - 290, width - 100, 30, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(70, height - 271, "Salary Particulars")
    c.drawRightString(width - 70, height - 271, f"Amount ({CURRENCY_SYMBOL})")
    
    c.setFillColor(colors.HexColor("#444444"))
    c.setFont("Helvetica", 11)
    c.drawString(70, height - 330, f"Monthly Professional Compensation for {month}")
    c.drawRightString(width - 70, height - 330, f"{CURRENCY_SYMBOL} {amount:,.2f}")
    
    c.setStrokeColor(colors.HexColor("#bdc3c7"))
    c.setLineWidth(1)
    c.line(50, height - 355, width - 50, height - 355)
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(330, height - 385, "Total Disbursed Amount:")
    c.setFillColor(colors.HexColor("#27ae60"))
    c.drawRightString(width - 70, height - 385, f"{CURRENCY_SYMBOL} {amount:,.2f}")
    
    c.showPage()
    c.save()
    
    abs_filename = os.path.abspath(filename)
    try:
        if sys.platform == "win32":
            os.startfile(abs_filename)
        elif sys.platform == "darwin":
            subprocess.run(["open", abs_filename])
        else:
            subprocess.run(["xdg-open", abs_filename])
    except Exception as e:
        print(f"Could not open PDF viewer: {e}")


def generate_misc_invoice(client_name, phone, description, amount):
    os.makedirs("invoices", exist_ok=True)
    filename = f"invoices/Misc_Invoice_{client_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    c.setFillColor(colors.HexColor("#16a085"))
    c.rect(0, height - 100, width, 100, fill=1, stroke=0)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(50, height - 55, ORG_NAME)
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 75, "Miscellaneous Billing & Service Invoice")
    
    c.setFillColor(colors.HexColor("#bdc3c7"))
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(width - 50, height - 45, f"Date: {datetime.now().strftime('%b %d, %Y')}")
    c.drawRightString(width - 50, height - 60, f"Invoice ID: MISC-{datetime.now().strftime('%H%M%S')}")
    
    c.setFillColor(colors.HexColor("#2c3e50"))
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 150, "Client / Recipient Details:")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 180, f"Recipient Name: {client_name if client_name else 'Walk-in Client'}")
    c.drawString(50, height - 205, f"Phone Number:   {phone if phone else 'N/A'}")
    
    c.setFillColor(colors.HexColor("#16a085"))
    c.rect(50, height - 275, width - 100, 30, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(70, height - 256, "Item / Task Description")
    c.drawRightString(width - 70, height - 256, f"Amount ({CURRENCY_SYMBOL})")
    
    c.setFillColor(colors.HexColor("#444444"))
    c.setFont("Helvetica", 11)
    c.drawString(70, height - 310, description if description else "Miscellaneous Institutional Service")
    c.drawRightString(width - 70, height - 310, f"{CURRENCY_SYMBOL} {amount:,.2f}")
    
    c.setStrokeColor(colors.HexColor("#bdc3c7"))
    c.setLineWidth(1)
    c.line(50, height - 335, width - 50, height - 335)
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(350, height - 365, "Total Amount Due:")
    c.setFillColor(colors.HexColor("#16a085"))
    c.drawRightString(width - 70, height - 365, f"{CURRENCY_SYMBOL} {amount:,.2f}")
    
    c.showPage()
    c.save()
    
    abs_filename = os.path.abspath(filename)
    try:
        if sys.platform == "win32":
            os.startfile(abs_filename)
        elif sys.platform == "darwin":
            subprocess.run(["open", abs_filename])
        else:
            subprocess.run(["xdg-open", abs_filename])
    except Exception as e:
        print(f"Could not open PDF viewer: {e}")


# --- UI COMPONENTS ---
class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, text_color=(255, 255, 255), font_size=18):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.font = pygame.font.SysFont("Arial", font_size)

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        current_color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.color
        pygame.draw.rect(surface, current_color, self.rect, border_radius=6)
        
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False


class TextInput:
    def __init__(self, x, y, width, height, placeholder=""):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = ""
        self.placeholder = placeholder
        self.active = False
        self.font = pygame.font.SysFont("Arial", 16)
        self.color_inactive = (200, 205, 210)
        self.color_active = (41, 128, 185)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                pass
            else:
                self.text += event.unicode

    def draw(self, surface):
        color = self.color_active if self.active else self.color_inactive
        pygame.draw.rect(surface, (255, 255, 255), self.rect, border_radius=4)
        pygame.draw.rect(surface, color, self.rect, 2, border_radius=4)
        
        if not self.text and not self.active:
            txt_surface = self.font.render(self.placeholder, True, (150, 150, 150))
        else:
            txt_surface = self.font.render(self.text, True, (44, 62, 80))
            
        surface.blit(txt_surface, (self.rect.x + 8, self.rect.y + 8))

    def clear(self):
        self.text = ""


# --- MAIN APPLICATION ---
class SchoolMISApp:
    def __init__(self):
        pygame.init()
        self.width, self.height = 1150, 700
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(f"{ORG_NAME} - Management Information System")
        self.clock = pygame.time.Clock()
        
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
        
        # Color Palette
        self.BG_COLOR = (240, 243, 246)
        self.SIDEBAR_COLOR = (33, 47, 60)
        self.CARD_BG = (255, 255, 255)
        self.TEXT_DARK = (44, 62, 80)
        self.TEXT_LIGHT = (127, 140, 141)
        self.ACCENT_BLUE = (41, 128, 185)
        self.ACCENT_GREEN = (39, 174, 96)
        self.ACCENT_RED = (231, 76, 60)
        self.ACCENT_ORANGE = (243, 156, 18)
        self.ACCENT_PURPLE = (142, 68, 173)
        self.ACCENT_TEAL = (22, 160, 133)
        
        self.font_title = pygame.font.SysFont("Arial", 26, bold=True)
        self.font_header = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_regular = pygame.font.SysFont("Arial", 15)
        
        # Navigation Buttons (Sidebar)
        self.btn_dashboard = Button(20, 30, 200, 42, "Dashboard", self.ACCENT_BLUE, (52, 152, 219), font_size=17)
        self.btn_students = Button(20, 82, 200, 42, "Students MIS", self.ACCENT_BLUE, (52, 152, 219), font_size=17)
        self.btn_teachers = Button(20, 134, 200, 42, "Teachers MIS", self.ACCENT_BLUE, (52, 152, 219), font_size=17)
        self.btn_finances = Button(20, 186, 200, 42, "Fees & Salaries", self.ACCENT_BLUE, (52, 152, 219), font_size=17)
        self.btn_misc_billing = Button(20, 238, 200, 42, "Misc Billing", self.ACCENT_TEAL, (26, 188, 156), font_size=17)

        # Back Buttons
        self.btn_back_to_teachers = Button(930, 25, 170, 35, "← Back to Teachers", self.ACCENT_BLUE, (52, 152, 219), font_size=14)
        self.btn_back_to_students = Button(930, 25, 170, 35, "← Back to Students", self.ACCENT_BLUE, (52, 152, 219), font_size=14)

        # Student Form Inputs
        self.s_name_input = TextInput(270, 160, 170, 35, "Full Name")
        self.s_grade_input = TextInput(450, 160, 75, 35, "Grade")
        self.s_phone_input = TextInput(535, 160, 130, 35, "Phone No")
        self.s_fees_input = TextInput(675, 160, 140, 35, f"Fees Due ({CURRENCY_SYMBOL})")
        self.btn_add_student = Button(1000, 160, 115, 35, "Add Student", self.ACCENT_GREEN, (46, 204, 113), font_size=14)
        self.btn_cancel_student = Button(905, 160, 75, 35, "Cancel", self.ACCENT_RED, (192, 57, 43), font_size=14)
        self.s_search_input = TextInput(270, 210, 320, 35, "Search student by name...")

        # Teacher Form Inputs
        self.t_name_input = TextInput(270, 160, 200, 35, "Teacher Name")
        self.t_subject_input = TextInput(485, 160, 150, 35, "Subject")
        self.t_sal_input = TextInput(650, 160, 120, 35, f"Salary ({CURRENCY_SYMBOL})")
        self.btn_add_teacher = Button(790, 160, 120, 35, "Add Teacher", self.ACCENT_GREEN, (46, 204, 113), font_size=14)
        self.btn_cancel_teacher = Button(920, 160, 75, 35, "Cancel", self.ACCENT_RED, (192, 57, 43), font_size=14)
        self.t_search_input = TextInput(270, 210, 320, 35, "Search teacher by name...")

        # Misc Billing Form Inputs
        self.m_name_input = TextInput(290, 160, 260, 40, "Client / Recipient Name")
        self.m_phone_input = TextInput(570, 160, 220, 40, "Phone Number")
        self.m_desc_input = TextInput(290, 240, 500, 40, "Item / Task Description")
        self.m_amount_input = TextInput(290, 320, 220, 40, f"Amount ({CURRENCY_SYMBOL})")
        self.btn_gen_misc = Button(530, 320, 260, 40, "Generate & Print PDF", self.ACCENT_TEAL, (26, 188, 156), font_size=16)

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

            # Event handling based on state
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
                            
                            # Update due fees and record transaction entry
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
        self.screen.fill(self.BG_COLOR)
        
        # Sidebar Container
        sidebar_rect = pygame.Rect(0, 0, 240, self.height)
        pygame.draw.rect(self.screen, self.SIDEBAR_COLOR, sidebar_rect)
        
        self.btn_dashboard.draw(self.screen)
        self.btn_students.draw(self.screen)
        self.btn_teachers.draw(self.screen)
        self.btn_finances.draw(self.screen)
        self.btn_misc_billing.draw(self.screen)

        if self.state == "DASHBOARD":
            self.render_dashboard()
        elif self.state == "STUDENTS":
            self.render_students()
        elif self.state == "STUDENT_HISTORY_VIEW":
            self.render_student_history_view()
        elif self.state == "TEACHERS":
            self.render_teachers()
        elif self.state == "TEACHER_SALARY_VIEW":
            self.render_teacher_salary_view()
        elif self.state == "FINANCES":
            self.render_finances()
        elif self.state == "MISC_BILLING":
            self.render_misc_billing()

        pygame.display.flip()

    def render_dashboard(self):
        title = self.font_title.render(f"{ORG_NAME} - Dashboard", True, self.TEXT_DARK)
        self.screen.blit(title, (260, 30))

        students = self.db.get_students()
        teachers = self.db.get_teachers()
        total_dues = sum(s.get("fees_due", 0) for s in students)

        self.draw_card(260, 90, 260, 110, "Total Students", str(len(students)), self.ACCENT_BLUE)
        self.draw_card(540, 90, 260, 110, "Total Teachers", str(len(teachers)), self.ACCENT_BLUE)
        self.draw_card(820, 90, 280, 110, "Outstanding Dues", f"{CURRENCY_SYMBOL} {total_dues:,.2f}", self.ACCENT_RED)

        info_rect = pygame.Rect(260, 230, 840, 400)
        pygame.draw.rect(self.screen, self.CARD_BG, info_rect, border_radius=8)
        
        h_text = self.font_header.render(f"Welcome to {ORG_NAME}", True, self.TEXT_DARK)
        self.screen.blit(h_text, (290, 260))
        
        guidelines = [
            "• Use sidebar buttons to navigate Student, Teacher, Financial, and Misc records.",
            "• Click 'History' in Students MIS to view combined monthly fee payments per year.",
            "• In Teachers MIS, click 'Salary & Ledger' to view monthly payment statuses and print slips.",
            f"• All monetary amounts are formatted in {CURRENCY_SYMBOL}.",
        ]
        y_pos = 310
        for g in guidelines:
            txt = self.font_regular.render(g, True, self.TEXT_DARK)
            self.screen.blit(txt, (290, y_pos))
            y_pos += 35

    def draw_card(self, x, y, w, h, title, value, accent_color):
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, self.CARD_BG, rect, border_radius=8)
        pygame.draw.rect(self.screen, accent_color, (x, y, 6, h), border_top_left_radius=8, border_bottom_left_radius=8)
        
        t_surf = self.font_regular.render(title, True, self.TEXT_LIGHT)
        v_surf = self.font_title.render(value, True, self.TEXT_DARK)
        
        self.screen.blit(t_surf, (x + 20, y + 18))
        self.screen.blit(v_surf, (x + 20, y + 50))

    def render_students(self):
        title_text = "Process Fee Payment" if self.billing_student_id else ("Edit Student Record" if self.editing_student_id else "Student Management & Records")
        title = self.font_title.render(title_text, True, self.TEXT_DARK)
        self.screen.blit(title, (260, 30))

        panel_rect = pygame.Rect(260, 85, 840, 175)
        pygame.draw.rect(self.screen, self.CARD_BG, panel_rect, border_radius=8)

        if self.billing_student_id:
            doc = self.db.students.find_one({"_id": self.billing_student_id})
            s_name = doc.get("name", "") if doc else ""
            lbl = self.font_regular.render(f"Payment for: {s_name} (Current Due: {CURRENCY_SYMBOL} {doc.get('fees_due', 0):,.2f})", True, self.ACCENT_PURPLE)
            self.screen.blit(lbl, (285, 105))
            
            self.s_fees_input.rect.x, self.s_fees_input.rect.y = 420, 160
            self.s_fees_input.draw(self.screen)
            self.btn_add_student.rect.x, self.btn_add_student.rect.y = 550, 160
            self.btn_add_student.draw(self.screen)
            self.btn_cancel_student.rect.x, self.btn_cancel_student.rect.y = 680, 160
            self.btn_cancel_student.draw(self.screen)
        else:
            lbl_text = "Modify Student Details" if self.editing_student_id else "Register New Student"
            lbl = self.font_regular.render(lbl_text, True, self.ACCENT_ORANGE if self.editing_student_id else self.TEXT_DARK)
            self.screen.blit(lbl, (285, 105))

            self.s_name_input.rect.x, self.s_name_input.rect.y = 270, 160
            self.s_grade_input.rect.x, self.s_grade_input.rect.y = 450, 160
            self.s_phone_input.rect.x, self.s_phone_input.rect.y = 535, 160
            self.s_fees_input.rect.x, self.s_fees_input.rect.y = 675, 160
            self.btn_add_student.rect.x, self.btn_add_student.rect.y = 850, 160
            self.btn_cancel_student.rect.x, self.btn_cancel_student.rect.y = 905, 160

            self.s_name_input.draw(self.screen)
            self.s_grade_input.draw(self.screen)
            self.s_phone_input.draw(self.screen)
            self.s_fees_input.draw(self.screen)
            self.btn_add_student.draw(self.screen)
            if self.editing_student_id:
                self.btn_cancel_student.draw(self.screen)

        self.s_search_input.draw(self.screen)

        table_rect = pygame.Rect(260, 275, 840, 390)
        pygame.draw.rect(self.screen, self.CARD_BG, table_rect, border_radius=8)

        pygame.draw.rect(self.screen, (230, 235, 240), (260, 275, 840, 40), border_top_left_radius=8, border_top_right_radius=8)
        self.screen.blit(self.font_regular.render("Full Name", True, self.TEXT_DARK), (275, 285))
        self.screen.blit(self.font_regular.render("Grade", True, self.TEXT_DARK), (440, 285))
        self.screen.blit(self.font_regular.render("Phone No", True, self.TEXT_DARK), (520, 285))
        self.screen.blit(self.font_regular.render(f"Fees Due ({CURRENCY_SYMBOL})", True, self.TEXT_DARK), (630, 285))
        self.screen.blit(self.font_regular.render("Actions", True, self.TEXT_DARK), (780, 285))

        students = self.get_filtered_students()
        self.student_row_buttons = []
        y_offset = 325
        for s in students[:8]:
            self.screen.blit(self.font_regular.render(s.get("name", ""), True, self.TEXT_DARK), (275, y_offset + 5))
            self.screen.blit(self.font_regular.render(str(s.get("grade", "")), True, self.TEXT_DARK), (440, y_offset + 5))
            self.screen.blit(self.font_regular.render(str(s.get("phone", "")), True, self.TEXT_DARK), (520, y_offset + 5))
            self.screen.blit(self.font_regular.render(f"{CURRENCY_SYMBOL} {s.get('fees_due', 0):,.2f}", True, self.TEXT_DARK), (630, y_offset + 5))

            edit_btn = Button(760, y_offset, 45, 30, "Edit", self.ACCENT_ORANGE, (211, 84, 0), font_size=12)
            del_btn = Button(810, y_offset, 50, 30, "Delete", self.ACCENT_RED, (192, 57, 43), font_size=12)
            bill_btn = Button(865, y_offset, 75, 30, "Print Bill", self.ACCENT_PURPLE, (125, 60, 152), font_size=12)
            hist_btn = Button(945, y_offset, 65, 30, "History", self.ACCENT_TEAL, (26, 188, 156), font_size=12)
            
            edit_btn.draw(self.screen)
            del_btn.draw(self.screen)
            bill_btn.draw(self.screen)
            hist_btn.draw(self.screen)

            self.student_row_buttons.append({
                "id": s["_id"], "edit": edit_btn, "delete": del_btn, "bill": bill_btn, "history": hist_btn
            })
            y_offset += 45

    def render_student_history_view(self):
        doc = self.db.students.find_one({"_id": self.history_student_id})
        if not doc:
            self.state = "STUDENTS"
            return

        title = self.font_title.render(f"Payment History: {doc.get('name')} (Grade {doc.get('grade')})", True, self.TEXT_DARK)
        self.screen.blit(title, (260, 25))

        self.btn_back_to_students.draw(self.screen)

        card_rect = pygame.Rect(260, 75, 840, 590)
        pygame.draw.rect(self.screen, self.CARD_BG, card_rect, border_radius=8)

        pygame.draw.rect(self.screen, (230, 235, 240), (260, 75, 840, 40), border_top_left_radius=8, border_top_right_radius=8)
        self.screen.blit(self.font_regular.render("Year", True, self.TEXT_DARK), (290, 85))
        self.screen.blit(self.font_regular.render("Month", True, self.TEXT_DARK), (420, 85))
        self.screen.blit(self.font_regular.render("Transactions", True, self.TEXT_DARK), (580, 85))
        self.screen.blit(self.font_regular.render(f"Total Paid ({CURRENCY_SYMBOL})", True, self.TEXT_DARK), (760, 85))

        history = doc.get("payment_history", [])

        # Group and sum payments by (Year, Month)
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
            empty_msg = self.font_regular.render("No fee payments recorded yet for this student.", True, self.TEXT_LIGHT)
            self.screen.blit(empty_msg, (290, y_offset))
        else:
            for (year, month), summary in sorted(monthly_summary.items(), key=lambda x: (x[0][0], x[0][1]), reverse=True):
                self.screen.blit(self.font_regular.render(str(year), True, self.TEXT_DARK), (290, y_offset))
                self.screen.blit(self.font_regular.render(str(month), True, self.TEXT_DARK), (420, y_offset))
                self.screen.blit(self.font_regular.render(f"{summary['count']} Payment(s)", True, self.ACCENT_BLUE), (580, y_offset))
                
                tot_surf = pygame.font.SysFont("Arial", 15, bold=True).render(f"{CURRENCY_SYMBOL} {summary['total']:,.2f}", True, self.ACCENT_GREEN)
                self.screen.blit(tot_surf, (760, y_offset))
                
                pygame.draw.line(self.screen, (240, 240, 240), (280, y_offset + 30), (1070, y_offset + 30))
                y_offset += 40

    def render_teachers(self):
        title_text = "Edit Teacher Record" if self.editing_teacher_id else "Teacher Management & Salaries"
        title = self.font_title.render(title_text, True, self.TEXT_DARK)
        self.screen.blit(title, (260, 30))

        # Input Card Panel
        panel_rect = pygame.Rect(260, 85, 840, 175)
        pygame.draw.rect(self.screen, self.CARD_BG, panel_rect, border_radius=8)

        lbl_text = "Modify Teacher Details" if self.editing_teacher_id else "Register New Teacher"
        lbl = self.font_regular.render(lbl_text, True, self.ACCENT_ORANGE if self.editing_teacher_id else self.TEXT_DARK)
        self.screen.blit(lbl, (285, 105))

        self.t_name_input.rect.x, self.t_name_input.rect.y = 270, 160
        self.t_subject_input.rect.x, self.t_subject_input.rect.y = 485, 160
        self.t_sal_input.rect.x, self.t_sal_input.rect.y = 650, 160
        self.btn_add_teacher.rect.x, self.btn_add_teacher.rect.y = 790, 160
        self.btn_cancel_teacher.rect.x, self.btn_cancel_teacher.rect.y = 920, 160

        self.t_name_input.draw(self.screen)
        self.t_subject_input.draw(self.screen)
        self.t_sal_input.draw(self.screen)
        self.btn_add_teacher.draw(self.screen)
        if self.editing_teacher_id:
            self.btn_cancel_teacher.draw(self.screen)

        self.t_search_input.rect.x, self.t_search_input.rect.y = 270, 210
        self.t_search_input.draw(self.screen)

        # Teachers Table Container
        table_rect = pygame.Rect(260, 275, 840, 390)
        pygame.draw.rect(self.screen, self.CARD_BG, table_rect, border_radius=8)

        pygame.draw.rect(self.screen, (230, 235, 240), (260, 275, 840, 40), border_top_left_radius=8, border_top_right_radius=8)
        self.screen.blit(self.font_regular.render("Teacher Name", True, self.TEXT_DARK), (285, 285))
        self.screen.blit(self.font_regular.render("Subject", True, self.TEXT_DARK), (450, 285))
        self.screen.blit(self.font_regular.render(f"Salary ({CURRENCY_SYMBOL})", True, self.TEXT_DARK), (570, 285))
        self.screen.blit(self.font_regular.render("Actions", True, self.TEXT_DARK), (760, 285))

        teachers = self.get_filtered_teachers()
        self.teacher_row_buttons = []
        y_offset = 325
        for t in teachers[:8]:
            self.screen.blit(self.font_regular.render(t.get("name", ""), True, self.TEXT_DARK), (285, y_offset + 5))
            self.screen.blit(self.font_regular.render(str(t.get("subject", "")), True, self.TEXT_DARK), (450, y_offset + 5))
            self.screen.blit(self.font_regular.render(f"{CURRENCY_SYMBOL} {t.get('salary', 0):,.2f}", True, self.TEXT_DARK), (570, y_offset + 5))

            edit_btn = Button(735, y_offset, 50, 30, "Edit", self.ACCENT_ORANGE, (211, 84, 0), font_size=13)
            del_btn = Button(790, y_offset, 60, 30, "Delete", self.ACCENT_RED, (192, 57, 43), font_size=13)
            salary_btn = Button(855, y_offset, 110, 30, "Salary & Ledger", self.ACCENT_PURPLE, (125, 60, 152), font_size=12)
            
            edit_btn.draw(self.screen)
            del_btn.draw(self.screen)
            salary_btn.draw(self.screen)

            self.teacher_row_buttons.append({"id": t["_id"], "edit": edit_btn, "delete": del_btn, "salary_view": salary_btn})
            y_offset += 45

    def render_teacher_salary_view(self):
        t_doc = self.db.teachers.find_one({"_id": self.selected_teacher_id})
        if not t_doc:
            self.state = "TEACHERS"
            return

        title = self.font_title.render(f"Salary Ledger: {t_doc.get('name')} ({t_doc.get('subject')})", True, self.TEXT_DARK)
        self.screen.blit(title, (260, 25))

        self.btn_back_to_teachers.draw(self.screen)

        card_rect = pygame.Rect(260, 75, 840, 590)
        pygame.draw.rect(self.screen, self.CARD_BG, card_rect, border_radius=8)

        pygame.draw.rect(self.screen, (230, 235, 240), (260, 75, 840, 40), border_top_left_radius=8, border_top_right_radius=8)
        self.screen.blit(self.font_regular.render("Month", True, self.TEXT_DARK), (285, 85))
        self.screen.blit(self.font_regular.render(f"Monthly Amount ({CURRENCY_SYMBOL})", True, self.TEXT_DARK), (430, 85))
        self.screen.blit(self.font_regular.render("Payment Status", True, self.TEXT_DARK), (630, 85))
        self.screen.blit(self.font_regular.render("Actions / Controls", True, self.TEXT_DARK), (790, 85))

        records = t_doc.get("salary_records", [])
        
        # Guarantee 12 months fallback if records missing
        if not records:
            records = [
                {"month": m, "status": "Unpaid"} for m in 
                ["January", "February", "March", "April", "May", "June", 
                 "July", "August", "September", "October", "November", "December"]
            ]

        monthly_sal = t_doc.get("salary", 0.0)
        self.salary_row_buttons = []
        y_offset = 125

        for rec in records:
            m_name = rec["month"]
            status = rec["status"]

            month_surf = self.font_regular.render(m_name, True, self.TEXT_DARK)
            amt_surf = self.font_regular.render(f"{CURRENCY_SYMBOL} {monthly_sal:,.2f}", True, self.TEXT_DARK)
            
            status_color = self.ACCENT_GREEN if status == "Paid" else self.ACCENT_RED
            status_surf = pygame.font.SysFont("Arial", 15, bold=True).render(status, True, status_color)

            self.screen.blit(month_surf, (285, y_offset + 5))
            self.screen.blit(amt_surf, (430, y_offset + 5))
            self.screen.blit(status_surf, (630, y_offset + 5))

            # Toggle status button
            toggle_btn = Button(760, y_offset, 100, 28, "Toggle Paid", self.ACCENT_BLUE, (52, 152, 219), font_size=12)
            toggle_btn.draw(self.screen)

            # Pay & Print button
            pay_btn = Button(870, y_offset, 110, 28, "Pay & Print", self.ACCENT_GREEN, (46, 204, 113), font_size=12)
            pay_btn.draw(self.screen)

            self.salary_row_buttons.append({
                "month": m_name, 
                "pay_btn": pay_btn,
                "toggle_btn": toggle_btn
            })

            y_offset += 43

    def render_finances(self):
        title = self.font_title.render("Financial Overview: Fees & Salaries", True, self.TEXT_DARK)
        self.screen.blit(title, (260, 30))

        students = self.db.get_students()
        teachers = self.db.get_teachers()

        total_dues = sum(s.get("fees_due", 0) for s in students)
        total_salaries = sum(t.get("salary", 0) for t in teachers)

        self.draw_card(260, 90, 390, 120, "Total Outstanding Student Fees", f"{CURRENCY_SYMBOL} {total_dues:,.2f}", self.ACCENT_RED)
        self.draw_card(670, 90, 390, 120, "Total Monthly Teacher Salaries", f"{CURRENCY_SYMBOL} {total_salaries:,.2f}", self.ACCENT_BLUE)

        box_rect = pygame.Rect(260, 235, 800, 400)
        pygame.draw.rect(self.screen, self.CARD_BG, box_rect, border_radius=8)

        head = self.font_header.render("Balance Sheet Summary", True, self.TEXT_DARK)
        self.screen.blit(head, (290, 265))

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
            txt = self.font_regular.render(l, True, self.TEXT_DARK)
            self.screen.blit(txt, (290, y))
            y += 40

    def render_misc_billing(self):
        title = self.font_title.render("Miscellaneous Billing & Invoicing", True, self.TEXT_DARK)
        self.screen.blit(title, (260, 30))

        card_rect = pygame.Rect(260, 85, 840, 560)
        pygame.draw.rect(self.screen, self.CARD_BG, card_rect, border_radius=8)

        head = self.font_header.render("Create Ad-hoc / Misc Item Invoice", True, self.ACCENT_TEAL)
        self.screen.blit(head, (290, 115))

        self.m_name_input.draw(self.screen)
        self.m_phone_input.draw(self.screen)
        self.m_desc_input.draw(self.screen)
        self.m_amount_input.draw(self.screen)
        self.btn_gen_misc.draw(self.screen)

        instructions = [
            "• Use this section for non-tuition items, fines, ID cards, certificate fees, or special events.",
            "• Fill in the recipient's details, task description, and amount.",
            "• Clicking 'Generate & Print PDF' will immediately format and open a custom misc invoice."
        ]
        y = 400
        for ins in instructions:
            txt = self.font_regular.render(ins, True, self.TEXT_DARK)
            self.screen.blit(txt, (290, y))
            y += 35


if __name__ == "__main__":
    app = SchoolMISApp()
    app.run()