import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

def send_invoice_email(recipient_email: str, subject: str, body_html: str, attachments: list = None, env_path: str = '.env') -> bool:
    """
    Send invoice email via SMTP.
    Reads SMTP credentials from .env:
    - SMTP_SERVER (default: smtp.gmail.com)
    - SMTP_PORT (default: 587)
    - SMTP_USER
    - SMTP_PASS
    """
    smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))
    smtp_user = os.environ.get('SMTP_USER', '')
    smtp_pass = os.environ.get('SMTP_PASS', '')

    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith('SMTP_SERVER='):
                    smtp_server = line.strip().split('=', 1)[1].strip('"\'')
                elif line.startswith('SMTP_PORT='):
                    smtp_port = int(line.strip().split('=', 1)[1].strip('"\''))
                elif line.startswith('SMTP_USER='):
                    smtp_user = line.strip().split('=', 1)[1].strip('"\'')
                elif line.startswith('SMTP_PASS='):
                    smtp_pass = line.strip().split('=', 1)[1].strip('"\'')

    if not smtp_user or not smtp_pass:
        print(f"[Email Notice] SMTP credentials not configured in .env. To enable auto-sending to {recipient_email}, set SMTP_USER and SMTP_PASS in .env.")
        return False

    msg = MIMEMultipart('mixed')
    msg['Subject'] = subject
    msg['From'] = f"Sea Retreat PA <{smtp_user}>"
    msg['To'] = recipient_email

    msg.attach(MIMEText(body_html, 'html'))

    if attachments:
        for file_path in attachments:
            if os.path.exists(file_path):
                filename = os.path.basename(file_path)
                with open(file_path, 'rb') as f:
                    part = MIMEApplication(f.read(), Name=filename)
                    part['Content-Disposition'] = f'attachment; filename="{filename}"'
                    msg.attach(part)

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        print(f"[Email Success] Sent email to {recipient_email}")
        return True
    except Exception as e:
        print(f"[Email Error] Failed to send email to {recipient_email}: {e}")
        return False

def send_pl_summary_email(result: dict, recipient_email: str = None, env_path: str = '.env') -> bool:
    """
    Send formatted P&L Summary report email with attached CSV report to the owner inbox.
    """
    smtp_user = os.environ.get('SMTP_USER', '')
    owner_email = os.environ.get('OWNER_EMAIL', '')

    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith('OWNER_EMAIL='):
                    owner_email = line.strip().split('=', 1)[1].strip('"\'')
                elif line.startswith('SMTP_USER='):
                    smtp_user = line.strip().split('=', 1)[1].strip('"\'')

    if not recipient_email:
        recipient_email = owner_email or smtp_user or "searetreatpa@gmail.com"

    month_name = result['month_name']
    year = result['year']
    t = result['totals']
    rows = result['rows']
    csv_path = result.get('csv_path')

    subject = f"P&L Summary Report - {month_name} {year} - 722 Milwaukee Dr."

    reservation_table_rows = ""
    for r in rows:
        reservation_table_rows += f"""
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">{r['Check-In']} to {r['Check-Out']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">{r['Guest Name']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; text-align: right;">${r['Net Accommodation Rent']:,.2f}</td>
            <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; text-align: right;">${r['Cleaning Fee (Collected)']:,.2f}</td>
            <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; text-align: right;">${r['Gross Revenue']:,.2f}</td>
        </tr>
        """

    body_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; color: #2d3748; line-height: 1.6; margin: 0; padding: 20px; background-color: #f7fafc; }}
            .container {{ max-width: 700px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 8px; border: 1px solid #e2e8f0; }}
            .header {{ border-bottom: 2px solid #2b6cb0; padding-bottom: 15px; margin-bottom: 20px; }}
            .title {{ font-size: 22px; font-weight: bold; color: #1a365d; margin: 0; }}
            .subtitle {{ color: #718096; font-size: 14px; margin-top: 5px; }}
            .section {{ margin-bottom: 25px; }}
            .section-title {{ font-size: 16px; font-weight: bold; color: #2b6cb0; border-bottom: 1px solid #e2e8f0; padding-bottom: 5px; margin-bottom: 10px; }}
            .stat-grid {{ display: table; width: 100%; margin-bottom: 20px; }}
            .stat-card {{ display: table-cell; background: #f0f4f8; padding: 15px; border-radius: 6px; width: 31%; text-align: center; }}
            .stat-label {{ font-size: 11px; color: #4a5568; text-transform: uppercase; font-weight: bold; }}
            .stat-value {{ font-size: 18px; font-weight: bold; color: #1a365d; margin-top: 5px; }}
            .summary-table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            .summary-table td {{ padding: 10px; border-bottom: 1px solid #e2e8f0; }}
            .summary-table td.label {{ font-weight: bold; color: #4a5568; }}
            .summary-table td.val {{ text-align: right; font-weight: bold; color: #2d3748; }}
            .highlight {{ background-color: #ebf8ff; font-size: 16px; }}
            .highlight td {{ color: #2b6cb0 !important; font-weight: bold; }}
            table.details {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
            table.details th {{ background: #edf2f7; padding: 8px; text-align: left; color: #4a5568; border-bottom: 2px solid #cbd5e0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="title">Sea Retreat P&L Summary Report</div>
                <div class="subtitle">722 Milwaukee Dr &bull; {month_name} {year} &bull; {len(rows)} Bookings ({t['nights']} Nights)</div>
            </div>

            <div class="stat-grid">
                <div class="stat-card">
                    <div class="stat-label">Gross Revenue</div>
                    <div class="stat-value">${t['gross_revenue']:,.2f}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Total Deductions</div>
                    <div class="stat-value">${t['platform_fees'] + t['taxes'] + t['pm_total'] + t['cleaner_total']:,.2f}</div>
                </div>
                <div class="stat-card" style="background: #e6fffa;">
                    <div class="stat-label" style="color: #234e52;">Net Owner Income</div>
                    <div class="stat-value" style="color: #234e52;">${t['net_owner_income']:,.2f}</div>
                </div>
            </div>

            <div class="section">
                <div class="section-title">Financial Breakdown</div>
                <table class="summary-table">
                    <tr><td class="label">Gross Accommodation Rent</td><td class="val">${t['gross_acc']:,.2f}</td></tr>
                    <tr><td class="label">Discounts & Adjustments</td><td class="val">${t['disc'] + t['adj']:,.2f}</td></tr>
                    <tr><td class="label">Net Accommodation Rent</td><td class="val">${t['net_acc']:,.2f}</td></tr>
                    <tr><td class="label">Cleaning Fees Collected</td><td class="val">${t['cleaning_fees']:,.2f}</td></tr>
                    <tr><td class="label">Extra Guest Fees Collected</td><td class="val">${t['extra_fees']:,.2f}</td></tr>
                    <tr style="border-top: 2px solid #2b6cb0;"><td class="label">Total Gross Revenue</td><td class="val">${t['gross_revenue']:,.2f}</td></tr>
                </table>
            </div>

            <div class="section">
                <div class="section-title">Payouts & Deductions</div>
                <table class="summary-table">
                    <tr><td class="label">Platform Host Fees</td><td class="val">-${t['platform_fees']:,.2f}</td></tr>
                    <tr><td class="label">Pass-through Taxes</td><td class="val">-${t['taxes']:,.2f}</td></tr>
                    <tr><td class="label">Cleaner Payout (Sondra Owens)</td><td class="val">-${t['cleaner_total']:,.2f}</td></tr>
                    <tr><td class="label">Property Manager Payout (Gigi PM - 15% Net Acc)</td><td class="val">-${t['pm_total']:,.2f}</td></tr>
                    <tr class="highlight"><td class="label">Net Owner Income Distributed</td><td class="val">${t['net_owner_income']:,.2f}</td></tr>
                </table>
            </div>

            <div class="section">
                <div class="section-title">Reservation Breakdown</div>
                <table class="details">
                    <thead>
                        <tr>
                            <th>Dates</th>
                            <th>Guest</th>
                            <th style="text-align: right;">Net Rent</th>
                            <th style="text-align: right;">Cleaning</th>
                            <th style="text-align: right;">Gross</th>
                        </tr>
                    </thead>
                    <tbody>
                        {reservation_table_rows}
                    </tbody>
                </table>
            </div>
            
            <p style="font-size: 12px; color: #a0aec0; margin-top: 30px;">
                Detailed P&L CSV file is attached to this email. Invoices for Sondra Owens and Gigi Property Management have been automatically delivered to Melio.
            </p>
        </div>
    </body>
    </html>
    """

    attachments = [csv_path] if csv_path and os.path.exists(csv_path) else None

    return send_invoice_email(
        recipient_email=recipient_email,
        subject=subject,
        body_html=body_html,
        attachments=attachments,
        env_path=env_path
    )
