from decimal import ROUND_HALF_UP, Decimal
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from backend.app.models.invoice import Invoice

TWO = Decimal("0.01")


def _d(v) -> Decimal:
    return Decimal(str(v or 0)).quantize(TWO, rounding=ROUND_HALF_UP)


def calculate_invoice_totals(items: list[dict], discount: float = 0) -> tuple[Decimal, Decimal, Decimal]:
    """Return (subtotal, tax_amount, total) for a list of item dicts."""
    subtotal = Decimal(0)
    tax_total = Decimal(0)
    for item in items:
        qty = _d(item["quantity"])
        price = _d(item["unit_price"])
        line_amount = (qty * price).quantize(TWO, rounding=ROUND_HALF_UP)
        tax = (line_amount * _d(item.get("tax_rate", 0)) / Decimal(100)).quantize(TWO, rounding=ROUND_HALF_UP)
        subtotal += line_amount
        tax_total += tax
    total = subtotal + tax_total - _d(discount)
    return subtotal.quantize(TWO), tax_total.quantize(TWO), total.quantize(TWO)


def build_invoice_pdf(company_name: str, invoice: Invoice) -> BytesIO:
    buf = BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    pdf.setTitle(f"Invoice_{invoice.invoice_number}")

    # Header
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(40, h - 50, company_name)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawRightString(w - 40, h - 50, "INVOICE")

    # Invoice meta
    pdf.setFont("Helvetica", 10)
    y = h - 80
    pdf.drawString(40, y, f"Invoice #: {invoice.invoice_number}")
    pdf.drawString(40, y - 16, f"Date: {invoice.invoice_date}")
    if invoice.due_date:
        pdf.drawString(40, y - 32, f"Due: {invoice.due_date}")
    pdf.drawString(40, y - 48, f"Status: {invoice.status.upper()}")

    # Customer
    if invoice.customer:
        pdf.drawRightString(w - 40, y, f"Bill To: {invoice.customer.name}")
        if invoice.customer.email:
            pdf.drawRightString(w - 40, y - 16, invoice.customer.email)
        if invoice.customer.gstin:
            pdf.drawRightString(w - 40, y - 32, f"GSTIN: {invoice.customer.gstin}")

    # Table header
    y = h - 160
    pdf.setFont("Helvetica-Bold", 10)
    pdf.setFillColor(colors.HexColor("#302b63"))
    pdf.rect(36, y - 4, w - 72, 20, fill=True, stroke=False)
    pdf.setFillColor(colors.white)
    pdf.drawString(40, y, "#")
    pdf.drawString(60, y, "Description")
    pdf.drawString(320, y, "Qty")
    pdf.drawString(370, y, "Price")
    pdf.drawString(430, y, "Tax%")
    pdf.drawRightString(w - 40, y, "Amount")

    # Items
    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica", 10)
    y -= 24
    for idx, item in enumerate(invoice.items, 1):
        if y < 80:
            pdf.showPage()
            y = h - 50
        pdf.drawString(40, y, str(idx))
        pdf.drawString(60, y, str(item.description)[:45])
        pdf.drawString(320, y, str(item.quantity))
        pdf.drawString(370, y, f"{item.unit_price:,.2f}")
        pdf.drawString(430, y, f"{item.tax_rate}%")
        pdf.drawRightString(w - 40, y, f"{item.amount:,.2f}")
        y -= 18

    # Totals
    y -= 10
    pdf.line(320, y + 8, w - 40, y + 8)
    pdf.setFont("Helvetica", 11)
    pdf.drawString(370, y - 6, "Subtotal:")
    pdf.drawRightString(w - 40, y - 6, f"{invoice.subtotal:,.2f}")
    pdf.drawString(370, y - 24, "Tax:")
    pdf.drawRightString(w - 40, y - 24, f"{invoice.tax_amount:,.2f}")
    if invoice.discount:
        pdf.drawString(370, y - 42, "Discount:")
        pdf.drawRightString(w - 40, y - 42, f"-{invoice.discount:,.2f}")
        y -= 18
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(370, y - 42, "Total:")
    pdf.drawRightString(w - 40, y - 42, f"{invoice.total:,.2f}")

    # Notes
    if invoice.notes:
        pdf.setFont("Helvetica", 9)
        pdf.drawString(40, 60, f"Notes: {invoice.notes}")

    pdf.showPage()
    pdf.save()
    buf.seek(0)
    return buf


def build_invoice_excel(company_name: str, invoice: Invoice) -> BytesIO:
    """Build a simple CSV (Excel-compatible) export of the invoice."""
    buf = BytesIO()
    lines = [
        f"Invoice #{invoice.invoice_number}",
        f"Company,{company_name}",
        f"Customer,{invoice.customer.name if invoice.customer else ''}",
        f"Date,{invoice.invoice_date}",
        f"Due Date,{invoice.due_date or ''}",
        f"Status,{invoice.status}",
        "",
        "Description,Quantity,Unit Price,Tax Rate (%),Amount",
    ]
    for item in invoice.items:
        lines.append(f"{item.description},{item.quantity},{item.unit_price},{item.tax_rate},{item.amount}")
    lines += [
        "",
        f"Subtotal,,,,{invoice.subtotal}",
        f"Tax,,,,{invoice.tax_amount}",
        f"Discount,,,,{invoice.discount}",
        f"Total,,,,{invoice.total}",
    ]
    buf.write("\n".join(lines).encode("utf-8-sig"))
    buf.seek(0)
    return buf
