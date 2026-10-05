import os
import sys
import json
import logging
import smtplib
import shutil
import csv
import re
from datetime import datetime, date, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.hospitable_api import fetch_reservations, load_env, load_pat

def calculate_pl_for_date_range(start_str: str, end_str: str, label: str):
    """Calculate P&L data and CSV for arbitrary start and end date range."""
    load_env()
    pat = load_pat()
    
    start_dt = datetime.strptime(start_str, "%Y-%m-%d")
    end_dt = datetime.strptime(end_str, "%Y-%m-%d")
    
    fetch_start = (start_dt - timedelta(days=7)).strftime("%Y-%m-%d")
    fetch_end = (end_dt + timedelta(days=7)).strftime("%Y-%m-%d")
    
    all_res = fetch_reservations(fetch_start, fetch_end, pat=pat)
    
    filtered = []
    for r in all_res:
        arr = (r.get('arrival_date') or r.get('check_in') or "")[:10]
        dep = (r.get('departure_date') or r.get('check_out') or "")[:10]
        # Check if reservation is active and accepted (strictly exclude cancelled, expired, or unaccepted bookings)
        status = str(r.get('status') or '').lower()
        res_status = r.get('reservation_status') or {}
        curr_category = str((res_status.get('current') or {}).get('category') or '').lower()
        if status != 'accepted' or (curr_category and curr_category != 'accepted'):
            continue

        if start_str <= arr <= end_str or start_str < dep <= (end_dt + timedelta(days=1)).strftime("%Y-%m-%d"):
            filtered.append(r)

    filtered.sort(key=lambda x: (x.get('arrival_date') or x.get('check_in') or ""))

    rows = []
    for r in filtered:
        code = r.get('code')
        platform = r.get('platform')
        guest_name = f"{r.get('guest', {}).get('first_name', '')} {r.get('guest', {}).get('last_name', '')}".strip()
        arr = (r.get('arrival_date') or r.get('check_in'))[:10]
        dep = (r.get('departure_date') or r.get('check_out'))[:10]
        nights = r.get('nights', 0)
        total_guests = r.get('guests', {}).get('total', 0)
        
        fin = r.get('financials', {})
        host_fin = fin.get('host', {})

        acc = host_fin.get('accommodation', {}).get('amount', 0) / 100.0
        discounts = sum([d.get('amount', 0) for d in host_fin.get('discounts', [])]) / 100.0
        adjustments = sum([a.get('amount', 0) for a in host_fin.get('adjustments', [])]) / 100.0
        net_accommodation = round(acc + discounts + adjustments, 2)

        cleaning_fee = 0.0
        extra_guest_fee = 0.0
        for gf in host_fin.get('guest_fees', []):
            lbl = gf.get('label', '').lower()
            amt = gf.get('amount', 0) / 100.0
            if 'clean' in lbl:
                cleaning_fee += amt
            elif 'extra' in lbl or 'additional guest' in lbl:
                extra_guest_fee += amt
                
        host_fees = sum([hf.get('amount', 0) for hf in host_fin.get('host_fees', [])]) / 100.0
        platform_fee = abs(host_fees)
        host_taxes = sum([t.get('amount', 0) for t in host_fin.get('taxes', [])]) / 100.0
        
        net_rental_revenue = round(net_accommodation + extra_guest_fee, 2)
        gross_revenue = round(net_rental_revenue + cleaning_fee, 2)

        note_str = r.get('notes') or ""
        pm_base_fee = round(net_accommodation * 0.15, 2)
        pm_notes_adj = 0.0
        match_pm = re.search(r'(?:pm|manager)\s*(?:adjustment|fee)?:\s*([+-]?\$?\d+(?:\.\d{2})?)', note_str, re.IGNORECASE)
        if match_pm:
            pm_notes_adj = float(match_pm.group(1).replace('$', ''))
        pm_subtotal = round(pm_base_fee + pm_notes_adj, 2)
        pm_handling_fee = round(pm_subtotal * 0.03, 2)
        pm_payout = round(pm_subtotal + pm_handling_fee, 2)

        cleaner_base = round(cleaning_fee, 2)
        cleaner_notes_adj = 0.0
        match_cleaner = re.search(r'(?:cleaner|cleaning)\s*(?:adjustment|fee)?:\s*([+-]?\$?\d+(?:\.\d{2})?)', note_str, re.IGNORECASE)
        if match_cleaner:
            cleaner_notes_adj = float(match_cleaner.group(1).replace('$', ''))
        cleaner_subtotal = round(cleaner_base + cleaner_notes_adj, 2)
        cleaner_handling_fee = round(cleaner_subtotal * 0.03, 2)
        cleaner_payout = round(cleaner_subtotal + cleaner_handling_fee, 2)

        net_owner_income = round(gross_revenue - platform_fee - host_taxes - pm_payout - cleaner_payout, 2)

        rows.append({
            'Reservation Code': code,
            'Platform': platform,
            'Guest Name': guest_name,
            'Check-In': arr,
            'Check-Out': dep,
            'Nights': nights,
            'Total Guests': total_guests,
            'Gross Accommodation': acc,
            'Discounts': discounts,
            'Adjustments': adjustments,
            'Net Accommodation Rent': net_accommodation,
            'Extra Guest Fee (Collected)': extra_guest_fee,
            'Cleaning Fee (Collected)': cleaning_fee,
            'Gross Revenue': gross_revenue,
            'Platform Fee': platform_fee,
            'Taxes': host_taxes,
            'PM Base Fee (15% Net Acc)': pm_base_fee,
            'PM Notes Adjustment': pm_notes_adj,
            'PM Handling Fee (3%)': pm_handling_fee,
            'PM Total Payout': pm_payout,
            'Cleaner Base Fee': cleaner_base,
            'Cleaner Notes Adjustment': cleaner_notes_adj,
            'Cleaner Handling Fee (3%)': cleaner_handling_fee,
            'Cleaner Total Payout': cleaner_payout,
            'Net Owner Income': net_owner_income,
            'Notes': note_str
        })

    tot_nights = sum(r['Nights'] for r in rows)
    tot_guests = sum(r['Total Guests'] for r in rows)
    tot_gross_acc = round(sum(r['Gross Accommodation'] for r in rows), 2)
    tot_disc = round(sum(r['Discounts'] for r in rows), 2)
    tot_adj = round(sum(r['Adjustments'] for r in rows), 2)
    tot_net_acc = round(sum(r['Net Accommodation Rent'] for r in rows), 2)
    tot_extra = round(sum(r['Extra Guest Fee (Collected)'] for r in rows), 2)
    tot_clean = round(sum(r['Cleaning Fee (Collected)'] for r in rows), 2)
    tot_gross = round(sum(r['Gross Revenue'] for r in rows), 2)
    tot_plat = round(sum(r['Platform Fee'] for r in rows), 2)
    tot_taxes = round(sum(r['Taxes'] for r in rows), 2)
    tot_pm_base = round(sum(r['PM Base Fee (15% Net Acc)'] for r in rows), 2)
    tot_pm_notes = round(sum(r['PM Notes Adjustment'] for r in rows), 2)
    tot_pm_handling = round(sum(r['PM Handling Fee (3%)'] for r in rows), 2)
    tot_pm = round(sum(r['PM Total Payout'] for r in rows), 2)
    tot_cleaner_base = round(sum(r['Cleaner Base Fee'] for r in rows), 2)
    tot_cleaner_notes = round(sum(r['Cleaner Notes Adjustment'] for r in rows), 2)
    tot_cleaner_handling = round(sum(r['Cleaner Handling Fee (3%)'] for r in rows), 2)
    tot_cleaner = round(sum(r['Cleaner Total Payout'] for r in rows), 2)
    tot_net_owner = round(sum(r['Net Owner Income'] for r in rows), 2)

    output_dir = os.path.join(ROOT_DIR, "722 Milwaukee")
    os.makedirs(output_dir, exist_ok=True)
    clean_label = label.replace(" ", "_").replace("-", "_")
    csv_path = os.path.join(output_dir, f"PL_{clean_label}.csv")

    headers = [
        'Reservation Code', 'Platform', 'Guest Name', 'Check-In', 'Check-Out', 'Nights', 'Total Guests',
        'Gross Accommodation', 'Discounts', 'Adjustments', 'Net Accommodation Rent',
        'Extra Guest Fee (Collected)', 'Cleaning Fee (Collected)', 'Gross Revenue',
        'Platform Fee', 'Taxes',
        'PM Base Fee (15% Net Acc)', 'PM Notes Adjustment', 'PM Handling Fee (3%)', 'PM Total Payout',
        'Cleaner Base Fee', 'Cleaner Notes Adjustment', 'Cleaner Handling Fee (3%)', 'Cleaner Total Payout',
        'Net Owner Income', 'Notes'
    ]

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for r in rows:
            writer.writerow([r[h] for h in headers])

    return {
        'label': label,
        'start_date': start_str,
        'end_date': end_str,
        'rows': rows,
        'csv_path': csv_path,
        'totals': {
            'nights': tot_nights,
            'guests': tot_guests,
            'gross_acc': tot_gross_acc,
            'disc': tot_disc,
            'adj': tot_adj,
            'net_acc': tot_net_acc,
            'extra_fees': tot_extra,
            'cleaning_fees': tot_clean,
            'gross_revenue': tot_gross,
            'platform_fees': tot_plat,
            'taxes': tot_taxes,
            'pm_base': tot_pm_base,
            'pm_notes': tot_pm_notes,
            'pm_handling': tot_pm_handling,
            'pm_total': tot_pm,
            'cleaner_base': tot_cleaner_base,
            'cleaner_notes': tot_cleaner_notes,
            'cleaner_handling': tot_cleaner_handling,
            'cleaner_total': tot_cleaner,
            'net_owner_income': tot_net_owner
        }
    }

def dispatch_weekly_and_mtd_email(weekly_res: dict, mtd_res: dict) -> bool:
    """Send HTML email report containing Weekly and MTD P&L tables directly to the owner."""
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")
    owner_email = os.getenv("OWNER_EMAIL", "searetreatpa@gmail.com")

    if not smtp_user or not smtp_pass:
        logging.error("SMTP credentials missing.")
        return False

    w_t = weekly_res['totals']
    m_t = mtd_res['totals']

    subject = f"📊 Weekly & Month-to-Date P&L Report - 722 Milwaukee Dr [{mtd_res['start_date']} to {mtd_res['end_date']}]"

    def render_table_rows(rows):
        if not rows:
            return '<tr><td colspan="8" style="padding:10px; text-align:center; color:#718096;">No bookings for this period.</td></tr>'
        html = ""
        for r in rows:
            platform_name = (r.get('Platform') or 'none').lower()
            html += f"""
            <tr>
                <td style="padding: 6px 8px; border-bottom: 1px solid #e2e8f0; white-space: nowrap;">{r['Check-In']} to {r['Check-Out']}</td>
                <td style="padding: 6px 8px; border-bottom: 1px solid #e2e8f0;">{platform_name}</td>
                <td style="padding: 6px 8px; border-bottom: 1px solid #e2e8f0;">{r['Guest Name']}</td>
                <td style="padding: 6px 8px; border-bottom: 1px solid #e2e8f0; text-align: right;">${r['Gross Accommodation']:,.2f}</td>
                <td style="padding: 6px 8px; border-bottom: 1px solid #e2e8f0; text-align: right;">${r['Net Accommodation Rent']:,.2f}</td>
                <td style="padding: 6px 8px; border-bottom: 1px solid #e2e8f0; text-align: right;">${r['PM Total Payout']:,.2f}</td>
                <td style="padding: 6px 8px; border-bottom: 1px solid #e2e8f0; text-align: right;">${r['Cleaner Total Payout']:,.2f}</td>
                <td style="padding: 6px 8px; border-bottom: 1px solid #e2e8f0; text-align: right; font-weight: bold; color: #2b6cb0;">${r['Net Owner Income']:,.2f}</td>
            </tr>
            """
        return html

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; color: #2d3748; line-height: 1.5; margin: 0; padding: 20px; background-color: #f7fafc; }}
            .container {{ max-width: 750px; margin: 0 auto; background: #ffffff; padding: 25px; border-radius: 8px; border: 1px solid #e2e8f0; }}
            .header {{ border-bottom: 3px solid #2b6cb0; padding-bottom: 12px; margin-bottom: 20px; }}
            .title {{ font-size: 22px; font-weight: bold; color: #1a365d; margin: 0; }}
            .subtitle {{ color: #718096; font-size: 13px; margin-top: 4px; }}
            .section {{ margin-bottom: 25px; }}
            .section-title {{ font-size: 16px; font-weight: bold; color: #2b6cb0; border-bottom: 2px solid #e2e8f0; padding-bottom: 6px; margin-bottom: 12px; }}
            .summary-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; font-size: 13px; }}
            .summary-table td {{ padding: 8px 10px; border-bottom: 1px solid #e2e8f0; }}
            .summary-table td.label {{ font-weight: bold; color: #4a5568; }}
            .summary-table td.val {{ text-align: right; font-weight: bold; color: #2d3748; }}
            .highlight {{ background-color: #ebf8ff; font-size: 15px; }}
            .highlight td {{ color: #2b6cb0 !important; font-weight: bold; }}
            table.details {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
            table.details th {{ background: #edf2f7; padding: 7px; text-align: left; color: #4a5568; border-bottom: 2px solid #cbd5e0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="title">Weekly & Month-to-Date P&L Performance</div>
                <div class="subtitle">722 Milwaukee Dr &bull; Executed Sunday {date.today().isoformat()} &bull; No Invoices Submitted to Melio</div>
            </div>

            <!-- WEEKLY SECTION -->
            <div class="section">
                <div class="section-title">📅 WEEKLY PERFORMANCE ({weekly_res['start_date']} to {weekly_res['end_date']})</div>
                <table class="summary-table">
                    <tr><td class="label">Bookings & Nights</td><td class="val">{len(weekly_res['rows'])} Bookings ({w_t['nights']} Nights)</td></tr>
                    <tr><td class="label">Gross Revenue</td><td class="val">${w_t['gross_revenue']:,.2f}</td></tr>
                    <tr><td class="label">Platform Fees</td><td class="val">-${w_t['platform_fees']:,.2f}</td></tr>
                    <tr><td class="label">Cleaner Payout (Sondra Owens)</td><td class="val">-${w_t['cleaner_total']:,.2f}</td></tr>
                    <tr><td class="label">Property Manager Payout (15% Net Acc)</td><td class="val">-${w_t['pm_total']:,.2f}</td></tr>
                    <tr class="highlight"><td class="label">Weekly Net Owner Income</td><td class="val">${w_t['net_owner_income']:,.2f}</td></tr>
                </table>
            </div>

            <!-- MTD SECTION -->
            <div class="section">
                <div class="section-title">📈 MONTH-TO-DATE AGGREGATION ({mtd_res['start_date']} to {mtd_res['end_date']})</div>
                <table class="summary-table">
                    <tr><td class="label">Bookings & Nights MTD</td><td class="val">{len(mtd_res['rows'])} Bookings ({m_t['nights']} Nights)</td></tr>
                    <tr><td class="label">Gross Accommodation Rent MTD</td><td class="val">${m_t['gross_acc']:,.2f}</td></tr>
                    <tr><td class="label">Net Accommodation Rent MTD</td><td class="val">${m_t['net_acc']:,.2f}</td></tr>
                    <tr><td class="label">Total Gross Revenue MTD</td><td class="val">${m_t['gross_revenue']:,.2f}</td></tr>
                    <tr><td class="label">Platform Fees MTD</td><td class="val">-${m_t['platform_fees']:,.2f}</td></tr>
                    <tr><td class="label">Cleaner Payouts MTD</td><td class="val">-${m_t['cleaner_total']:,.2f}</td></tr>
                    <tr><td class="label">Property Manager Payouts MTD</td><td class="val">-${m_t['pm_total']:,.2f}</td></tr>
                    <tr class="highlight"><td class="label">Month-to-Date Net Owner Income</td><td class="val">${m_t['net_owner_income']:,.2f}</td></tr>
                </table>
            </div>

            <!-- RESERVATIONS BREAKDOWN -->
            <div class="section">
                <div class="section-title">📋 Month-to-Date Reservation Details</div>
                <table class="details">
                    <thead>
                        <tr>
                            <th>Dates</th>
                            <th>Platform</th>
                            <th>Guest</th>
                            <th style="text-align: right;">Gross Rent</th>
                            <th style="text-align: right;">Net Rent</th>
                            <th style="text-align: right;">Property Mgmt</th>
                            <th style="text-align: right;">Cleaner</th>
                            <th style="text-align: right;">Owner Profit</th>
                        </tr>
                    </thead>
                    <tbody>
                        {render_table_rows(mtd_res['rows'])}
                    </tbody>
                </table>
            </div>
            
            <p style="font-size: 11px; color: #a0aec0; margin-top: 25px;">
                Attached CSV files: Weekly_PL.csv and Month_to_Date_PL.csv. No invoices were submitted to Melio.
            </p>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = owner_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    for csv_file in [weekly_res['csv_path'], mtd_res['csv_path']]:
        if csv_file and os.path.exists(csv_file):
            part = MIMEBase("application", "octet-stream")
            with open(csv_file, "rb") as attachment:
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(csv_file)}")
            msg.attach(part)

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [owner_email], msg.as_string())
        logging.info(f"Weekly & MTD P&L Report email sent to {owner_email}.")
        return True
    except Exception as e:
        logging.error(f"Failed to dispatch weekly P&L report email: {e}")
        return False

def run_weekly_pl_automation():
    today = date.today()
    # Calculate Weekly range (last 7 days: Sunday to Saturday)
    weekly_start = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    weekly_end = (today - timedelta(days=1)).strftime("%Y-%m-%d")

    # Calculate MTD range (1st of month to today)
    mtd_start = today.replace(day=1).strftime("%Y-%m-%d")
    mtd_end = today.strftime("%Y-%m-%d")

    print(f"Calculating Weekly P&L ({weekly_start} to {weekly_end})...")
    weekly_res = calculate_pl_for_date_range(weekly_start, weekly_end, f"Weekly_{weekly_start}_to_{weekly_end}")

    print(f"Calculating MTD P&L ({mtd_start} to {mtd_end})...")
    mtd_res = calculate_pl_for_date_range(mtd_start, mtd_end, f"MTD_{mtd_start}_to_{mtd_end}")

    print("Dispatching Weekly + MTD Summary Email to Owner...")
    email_success = dispatch_weekly_and_mtd_email(weekly_res, mtd_res)

    print("\n" + "="*80)
    print(" WEEKLY & MONTH-TO-DATE P&L REPORT - 722 MILWAUKEE DR")
    print("================================================================================")
    print(f"Weekly Range: {weekly_start} to {weekly_end} ({len(weekly_res['rows'])} Bookings)")
    print(f"  - Weekly Gross Revenue: ${weekly_res['totals']['gross_revenue']:,.2f}")
    print(f"  - Weekly Net Owner Income: ${weekly_res['totals']['net_owner_income']:,.2f}")
    print("-" * 80)
    print(f"MTD Range: {mtd_start} to {mtd_end} ({len(mtd_res['rows'])} Bookings)")
    print(f"  - MTD Gross Revenue: ${mtd_res['totals']['gross_revenue']:,.2f}")
    print(f"  - MTD Net Owner Income: ${mtd_res['totals']['net_owner_income']:,.2f}")
    print("="*80)
    print(f"Owner Email Status: {'Sent Successfully' if email_success else 'Dispatch Failed'}")
    print("Melio Invoices: SKIPPED (No invoices submitted to Melio)")
    print("="*80 + "\n")

if __name__ == '__main__':
    run_weekly_pl_automation()
