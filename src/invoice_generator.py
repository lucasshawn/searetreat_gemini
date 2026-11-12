import os
from datetime import datetime

def generate_invoice_html(vendor: str, invoice_num: str, invoice_date: str, due_date: str, amount: float, details: list, target_month: str) -> str:
    """Generate professional HTML invoice suitable for Melio auto-import OCR."""
    details_html = ""
    for item, qty, rate, line_total in details:
        qty_str = str(qty) if qty != "" else "-"
        rate_str = f"${rate:,.2f}" if rate != "" and isinstance(rate, (int, float)) else str(rate)
        details_html += f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #eee;">{item}</td>
            <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: center;">{qty_str}</td>
            <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: right;">{rate_str}</td>
            <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: right; font-weight: bold;">${line_total:,.2f}</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>INVOICE - {invoice_num}</title>
</head>
<body style="font-family: Arial, sans-serif; margin: 40px; color: #333; line-height: 1.6;">
    <table width="100%" style="margin-bottom: 30px;">
        <tr>
            <td>
                <h1 style="color: #1a365d; margin: 0;">INVOICE</h1>
                <p style="color: #718096; margin: 5px 0 0 0;">722 Milwaukee Dr - {target_month}</p>
            </td>
            <td style="text-align: right;">
                <h2 style="color: #2b6cb0; margin: 0;">{vendor}</h2>
                <p style="margin: 5px 0 0 0;"><strong>Invoice #:</strong> {invoice_num}</p>
                <p style="margin: 2px 0 0 0;"><strong>Invoice Date:</strong> {invoice_date}</p>
                <p style="margin: 2px 0 0 0;"><strong>Due Date:</strong> {due_date}</p>
            </td>
        </tr>
    </table>

    <table width="100%" style="border-collapse: collapse; margin-bottom: 30px;">
        <thead>
            <tr style="background-color: #ebf8ff; color: #2c5282;">
                <th style="padding: 12px; text-align: left;">Description (Check-In / Check-Out / Guest Count)</th>
                <th style="padding: 12px; text-align: center;">Nights / Qty</th>
                <th style="padding: 12px; text-align: right;">Rate / Info</th>
                <th style="padding: 12px; text-align: right;">Total Amount</th>
            </tr>
        </thead>
        <tbody>
            {details_html}
        </tbody>
    </table>

    <table width="100%">
        <tr>
            <td width="60%"></td>
            <td width="40%">
                <table width="100%" style="border-top: 2px solid #2b6cb0; padding-top: 10px;">
                    <tr>
                        <td style="font-size: 18px; font-weight: bold; color: #1a365d;">Total Payable:</td>
                        <td style="font-size: 22px; font-weight: bold; color: #2b6cb0; text-align: right;">${amount:,.2f}</td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>

    <footer style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #a0aec0; text-align: center;">
        Generated for Melio Payment Processing - 722 Milwaukee Dr
    </footer>
</body>
</html>
"""
    return html

def create_monthly_invoices(result: dict, output_dir: str = "722 Milwaukee") -> list:
    """
    Create HTML invoice files according to gemini.md rules:
    - Cleaner Vendor: Sondra Owens (redacted line items showing check in, check out, total guest count)
    - PM Vendor: Gigi Property Management
    """
    t = result['totals']
    month_name = result['month_name']
    year = result['year']
    target_month_str = f"{month_name} {year}"
    
    if result['year'] and result['rows']:
        month_num = int(datetime.strptime(month_name, '%B').month)
        if month_num == 12:
            inv_date = f"{year+1}-01-01"
            due_date = f"{year+1}-01-05"
        else:
            inv_date = f"{year}-{month_num+1:02d}-01"
            due_date = f"{year}-{month_num+1:02d}-05"
    else:
        inv_date = datetime.now().strftime('%Y-%m-01')
        due_date = datetime.now().strftime('%Y-%m-05')

    month_abbr = month_name[:3].upper()
    yr_short = str(year)[-2:]

    generated_files = []

    # 1. Cleaner Invoice (Vendor: Sondra Owens)
    # Rule 7: Keep line items for the invoice redacted to: check in / check out / total guest count
    cleaner_num = f"CLEAN-PAYOUT-{month_abbr}{yr_short}"
    cleaner_details = []
    for r in result['rows']:
        arr = r['Check-In']
        dep = r['Check-Out']
        guests = r['Total Guests']
        nights = r['Nights']
        stay_payout = r['Cleaner Total Payout']
        desc = f"Stay: {arr} to {dep} | Total Guests: {guests}"
        cleaner_details.append((desc, f"{nights} nights", f"{guests} guests", stay_payout))

    cleaner_html = generate_invoice_html(
        vendor="Sondra Owens",
        invoice_num=cleaner_num,
        invoice_date=inv_date,
        due_date=due_date,
        amount=t['cleaner_total'],
        details=cleaner_details,
        target_month=target_month_str
    )

    cleaner_path = os.path.join(output_dir, f"Invoice_Sondra_Owens_{cleaner_num}.html")
    with open(cleaner_path, 'w', encoding='utf-8') as f:
        f.write(cleaner_html)
    generated_files.append((cleaner_num, "Sondra Owens", t['cleaner_total'], cleaner_path))

    # 2. Property Manager Invoice (Vendor: Gigi Property Management)
    pm_num = f"PM-PAYOUT-{month_abbr}{yr_short}"
    pm_details = [
        (f"15% Management Fee on Net Accommodation Rent (${t['net_acc']:,.2f})", 1, t['pm_base'], t['pm_base'])
    ]
    if t['pm_notes'] != 0:
        pm_details.append(("Property Manager Notes Adjustments", 1, t['pm_notes'], t['pm_notes']))

    pm_html = generate_invoice_html(
        vendor="Gigi Property Management",
        invoice_num=pm_num,
        invoice_date=inv_date,
        due_date=due_date,
        amount=t['pm_total'],
        details=pm_details,
        target_month=target_month_str
    )

    pm_path = os.path.join(output_dir, f"Invoice_Gigi_PM_{pm_num}.html")
    with open(pm_path, 'w', encoding='utf-8') as f:
        f.write(pm_html)
    generated_files.append((pm_num, "Gigi Property Management", t['pm_total'], pm_path))

    return generated_files
