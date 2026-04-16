from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from backend.app.models.payroll import PayrollRecord


def build_payslip_pdf(company_name: str, employee_name: str, employee_code: str, payroll_record: PayrollRecord) -> BytesIO:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    pdf.setTitle(f"Payslip_{employee_code}_{payroll_record.month}_{payroll_record.year}")
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(40, height - 50, company_name)
    pdf.setFont("Helvetica", 12)
    pdf.drawString(40, height - 80, f"Payslip for {payroll_record.month:02d}/{payroll_record.year}")

    details = [
        f"Employee: {employee_name}",
        f"Employee Code: {employee_code}",
        f"Status: {payroll_record.status.title()}",
        f"Processed At: {payroll_record.processed_at}",
        f"Basic: {payroll_record.basic}",
        f"HRA: {payroll_record.hra}",
        f"Allowances: {payroll_record.allowances}",
        f"Gross Salary: {payroll_record.gross_salary}",
        f"Deductions: {payroll_record.deductions}",
        f"Tax Amount: {payroll_record.tax_amount}",
        f"Net Salary: {payroll_record.net_salary}",
    ]

    y_position = height - 120
    for line in details:
        pdf.drawString(40, y_position, line)
        y_position -= 22

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer
