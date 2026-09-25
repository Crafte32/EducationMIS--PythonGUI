import os
import sys
import subprocess
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from config import ORG_NAME, CURRENCY_SYMBOL

def _open_pdf(filename):
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
    c.drawString(70, height - 330, "Tuition & Fee Payment Transaction")
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
    _open_pdf(filename)

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
    c.drawString(70, height - 330, f"Monthly Compensation for {month}")
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
    _open_pdf(filename)

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
    c.drawString(70, height - 310, description if description else "Miscellaneous Service")
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
    _open_pdf(filename)