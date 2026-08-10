import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def create_pdf_invoice(vendor: str, invoice_num: str, invoice_date: str, due_date: str, total_amount: float, headers: list, data_rows: list, target_month: str, output_path: str):
    """Generate a clean PDF invoice using ReportLab suitable for Melio OCR auto-import."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#1a365d')
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#718096')
    )

    vendor_style = ParagraphStyle(
        'VendorTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        alignment=2, # Right
        textColor=colors.HexColor('#2b6cb0')
    )

    meta_style = ParagraphStyle(
        'MetaText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        alignment=2 # Right
    )

    header_table_data = [
        [
            Paragraph(f"<b>INVOICE</b><br/><font color='#718096'>722 Milwaukee Dr - {target_month}</font>", title_style),
            Paragraph(f"<b>{vendor}</b><br/>Invoice #: {invoice_num}<br/>Invoice Date: {invoice_date}<br/>Due Date: {due_date}", meta_style)
        ]
    ]

    header_table = Table(header_table_data, colWidths=[270, 270])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))

    story = [header_table, Spacer(1, 20)]

    # Main Items Table
    table_data = [[Paragraph(f"<b>{h}</b>", styles['Normal']) for h in headers]]
    
    for r in data_rows:
        row_cells = []
        for cell in r:
            row_cells.append(Paragraph(str(cell), styles['Normal']))
        table_data.append(row_cells)

    # Calculate column widths
    num_cols = len(headers)
    col_w = 540 / num_cols
    col_widths = [col_w] * num_cols

    items_table = Table(table_data, colWidths=col_widths)
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#ebf8ff')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#2c5282')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
    ]))

    story.append(items_table)
    story.append(Spacer(1, 20))

    # Total Box
    total_table_data = [
        [
            Paragraph("<b>Total Payable:</b>", ParagraphStyle('TotLbl', fontName='Helvetica-Bold', fontSize=14, leading=18, textColor=colors.HexColor('#1a365d'), alignment=2)),
            Paragraph(f"<b>${total_amount:,.2f}</b>", ParagraphStyle('TotAmt', fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=colors.HexColor('#2b6cb0'), alignment=2))
        ]
    ]

    total_table = Table(total_table_data, colWidths=[380, 160])
    total_table.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,-1), 1.5, colors.HexColor('#2b6cb0')),
        ('TOPPADDING', (0,0), (-1,-1), 10),
    ]))

    story.append(total_table)

    doc.build(story)
    return output_path

def generate_pdf_invoices(result: dict, output_dir: str = "722 Milwaukee") -> list:
    """
    Generate PDF invoices for Melio auto-import according to gemini.md rules:
    - Step 5: Vendor = Gigi Property Management
    - Step 6: Vendor = Sondra Owens
    - Due Date = Today's date + 3 days
    """
    from datetime import timedelta
    
    t = result['totals']
    month_name = result['month_name']
    year = result['year']
    target_month_str = f"{month_name} {year}"
    
    now = datetime.now()
    inv_date = now.strftime('%Y-%m-%d')
    due_date = (now + timedelta(days=3)).strftime('%Y-%m-%d')

    month_abbr = month_name[:3].upper()
    yr_short = str(year)[-2:]

    generated_pdfs = []

    # 1. Cleaner PDF Invoice (Vendor: Sondra Owens) - Step 6 Rule
    cleaner_num = f"CLEAN-PAYOUT-{month_abbr}{yr_short}"
    cleaner_headers = ["Check-In", "Check-Out", "Guest Count", "Clean Fee (Guest)", "Notes Adj", "Total Fee"]
    cleaner_rows = []
    
    for r in result['rows']:
        arr = r['Check-In']
        dep = r['Check-Out']
        guests = f"{r['Total Guests']} guests"
        clean_base = f"${r['Cleaner Base Fee']:,.2f}"
        notes_adj = f"${r['Cleaner Notes Adjustment']:,.2f}"
        payout = f"${r['Cleaner Total Payout']:,.2f}"
        cleaner_rows.append([arr, dep, guests, clean_base, notes_adj, payout])

    cleaner_pdf_path = os.path.join(output_dir, f"Invoice_Sondra_Owens_{cleaner_num}.pdf")
    create_pdf_invoice(
        vendor="Sondra Owens",
        invoice_num=cleaner_num,
        invoice_date=inv_date,
        due_date=due_date,
        total_amount=t['cleaner_total'],
        headers=cleaner_headers,
        data_rows=cleaner_rows,
        target_month=target_month_str,
        output_path=cleaner_pdf_path
    )
    generated_pdfs.append((cleaner_num, "Sondra Owens", t['cleaner_total'], cleaner_pdf_path))

    # 2. Property Manager PDF Invoice (Vendor: Gigi Property Management) - Step 6 Rule
    pm_num = f"PM-PAYOUT-{month_abbr}{yr_short}"
    pm_headers = ["Check-In", "Check-Out", "Guest Count", "Guest Name", "Net Acc Rent", "PM Fee (15%)"]
    pm_rows = []
    for r in result['rows']:
        arr = r['Check-In']
        dep = r['Check-Out']
        guests = f"{r['Total Guests']} guests"
        guest_name = r['Guest Name']
        net_acc = f"${r['Net Accommodation Rent']:,.2f}"
        pm_fee = f"${r['PM Base Fee (15% Net Acc)']:,.2f}"
        pm_rows.append([arr, dep, guests, guest_name, net_acc, pm_fee])

    if t['pm_notes'] != 0:
        pm_rows.append(["-", "-", "-", "PM Notes Adjustment", "-", f"${t['pm_notes']:,.2f}"])

    pm_pdf_path = os.path.join(output_dir, f"Invoice_Gigi_PM_{pm_num}.pdf")
    create_pdf_invoice(
        vendor="Gigi Property Management",
        invoice_num=pm_num,
        invoice_date=inv_date,
        due_date=due_date,
        total_amount=t['pm_total'],
        headers=pm_headers,
        data_rows=pm_rows,
        target_month=target_month_str,
        output_path=pm_pdf_path
    )
    generated_pdfs.append((pm_num, "Gigi Property Management", t['pm_total'], pm_pdf_path))

    return generated_pdfs
