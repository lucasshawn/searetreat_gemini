import os
import csv
import re
from datetime import datetime
from src.hospitable_api import fetch_reservations

def calculate_pl_for_month(year: int, month: int, output_dir: str = "722 Milwaukee"):
    """
    Calculate P&L report for a specific target month according to rules in gemini.md:
    - Month assignment: Checkout date > 1st of month and <= 1st of next month.
    - PM Payout: 15% of Net Accommodation Rent (Gross Acc + Discounts + Adjustments) + PM Notes Adjustments.
    - Cleaner Base Fee: 100% pass-through of cleaning fee.
    - Cleaner Extra Guest Fee: $5/extra guest/night for total guests > 4.
    - Notes Adjustments: Allocated to cleaner or PM based on regex.
    """
    start_fetch = f"{year}-{month-1:02d}-01" if month > 1 else f"{year-1}-12-01"
    end_fetch = f"{year}-{month+1:02d}-28" if month < 12 else f"{year+1}-01-28"

    all_reservations = fetch_reservations(start_fetch, end_fetch)

    # Filter by checkout date rule
    start_check = f"{year}-{month:02d}-01"
    if month == 12:
        end_check = f"{year+1}-01-01"
    else:
        end_check = f"{year}-{month+1:02d}-01"

    filtered_reservations = []
    for r in all_reservations:
        dep = (r.get('departure_date') or r.get('check_out') or "")[:10]
        if start_check < dep <= end_check:
            filtered_reservations.append(r)

    filtered_reservations.sort(key=lambda x: (x.get('arrival_date') or x.get('check_in') or ""))

    rows = []
    for r in filtered_reservations:
        code = r.get('code')
        platform = r.get('platform')
        guest_name = f"{r.get('guest', {}).get('first_name', '')} {r.get('guest', {}).get('last_name', '')}".strip()
        arr = (r.get('arrival_date') or r.get('check_in'))[:10]
        dep = (r.get('departure_date') or r.get('check_out'))[:10]
        nights = r.get('nights', 0)
        total_guests = r.get('guests', {}).get('total', 0)
        
        fin = r.get('financials', {})
        host_fin = fin.get('host', {})

        # Check if reservation is cancelled (do not include cancelled bookings)
        status = r.get('status', '').lower()
        curr_category = (r.get('reservation_status', {}).get('current', {}).get('category') or '').lower()
        if status == 'cancelled' or curr_category == 'cancelled':
            continue

        # Gross Accommodation
        acc = host_fin.get('accommodation', {}).get('amount', 0) / 100.0
        
        # Discounts & Adjustments
        discounts = sum([d.get('amount', 0) for d in host_fin.get('discounts', [])]) / 100.0
        adjustments = sum([a.get('amount', 0) for a in host_fin.get('adjustments', [])]) / 100.0

        # Net Accommodation Rent
        net_accommodation = round(acc + discounts + adjustments, 2)
        
        # Guest fees
        cleaning_fee = 0.0
        extra_guest_fee = 0.0
        for gf in host_fin.get('guest_fees', []):
            lbl = gf.get('label', '').lower()
            amt = gf.get('amount', 0) / 100.0
            if 'clean' in lbl:
                cleaning_fee += amt
            elif 'extra' in lbl or 'additional guest' in lbl:
                extra_guest_fee += amt
                
        # Host fees (platform fees)
        host_fees = sum([hf.get('amount', 0) for hf in host_fin.get('host_fees', [])]) / 100.0
        platform_fee = abs(host_fees)
        
        # Taxes
        host_taxes = sum([t.get('amount', 0) for t in host_fin.get('taxes', [])]) / 100.0
        
        # Net Rental Revenue & Gross Revenue
        net_rental_revenue = round(net_accommodation + extra_guest_fee, 2)
        gross_revenue = round(net_rental_revenue + cleaning_fee, 2)

        # Parse Notes for Adjustments
        note_str = r.get('notes') or ""
        
        # 1) Property Manager Payout
        pm_base_fee = round(net_accommodation * 0.15, 2)
        pm_notes_adj = 0.0
        match_pm = re.search(r'(?:pm|manager)\s*(?:adjustment|fee)?:\s*([+-]?\$?\d+(?:\.\d{2})?)', note_str, re.IGNORECASE)
        if match_pm:
            pm_notes_adj = float(match_pm.group(1).replace('$', ''))
        pm_payout = round(pm_base_fee + pm_notes_adj, 2)

        # 2) Cleaner Payout (Base cleaning fee + Notes adjustment; extra guest fees are not paid to cleaner)
        cleaner_base = round(cleaning_fee, 2)
        cleaner_extra_guest_payout = 0.0

        # 3) Cleaner Notes Adjustment
        cleaner_notes_adj = 0.0
        match_clean = re.search(r'(?:cleaner|clean)\s*(?:adjustment|fee)?:\s*([+-]?\$?\d+(?:\.\d{2})?)', note_str, re.IGNORECASE)
        if match_clean:
            cleaner_notes_adj = float(match_clean.group(1).replace('$', ''))

        cleaner_payout = round(cleaner_base + cleaner_notes_adj, 2)

        # Net Owner Income
        net_owner_income = round(gross_revenue - platform_fee - host_taxes - pm_payout - cleaner_payout, 2)

        rows.append({
            'Reservation Code': code,
            'Platform': platform,
            'Guest Name': guest_name,
            'Check-In': arr,
            'Check-Out': dep,
            'Nights': nights,
            'Total Guests': total_guests,
            'Gross Accommodation': round(acc, 2),
            'Discounts': round(discounts, 2),
            'Adjustments': round(adjustments, 2),
            'Net Accommodation Rent': net_accommodation,
            'Extra Guest Fee (Collected)': round(extra_guest_fee, 2),
            'Cleaning Fee (Collected)': round(cleaning_fee, 2),
            'Gross Revenue': gross_revenue,
            'Platform Fee': round(platform_fee, 2),
            'Taxes': round(host_taxes, 2),
            'PM Base Fee (15% Net Acc)': pm_base_fee,
            'PM Notes Adjustment': pm_notes_adj,
            'PM Total Payout': pm_payout,
            'Cleaner Base Fee': cleaner_base,
            'Cleaner Notes Adjustment': cleaner_notes_adj,
            'Cleaner Total Payout': cleaner_payout,
            'Net Owner Income': net_owner_income,
            'Notes': note_str
        })

    # Prepare CSV Output
    month_name = datetime(year, month, 1).strftime('%B')
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, f"{month_name}_{year}_PL.csv")

    headers = [
        'Reservation Code', 'Platform', 'Guest Name', 'Check-In', 'Check-Out', 'Nights', 'Total Guests',
        'Gross Accommodation', 'Discounts', 'Adjustments', 'Net Accommodation Rent',
        'Extra Guest Fee (Collected)', 'Cleaning Fee (Collected)', 'Gross Revenue',
        'Platform Fee', 'Taxes',
        'PM Base Fee (15% Net Acc)', 'PM Notes Adjustment', 'PM Total Payout',
        'Cleaner Base Fee', 'Cleaner Notes Adjustment', 'Cleaner Total Payout',
        'Net Owner Income', 'Notes'
    ]

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
    tot_pm = round(sum(r['PM Total Payout'] for r in rows), 2)

    tot_cleaner_base = round(sum(r['Cleaner Base Fee'] for r in rows), 2)
    tot_cleaner_notes = round(sum(r['Cleaner Notes Adjustment'] for r in rows), 2)
    tot_cleaner = round(sum(r['Cleaner Total Payout'] for r in rows), 2)

    tot_net_owner = round(sum(r['Net Owner Income'] for r in rows), 2)

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for r in rows:
            writer.writerow([r[h] for h in headers])
        writer.writerow([
            'TOTALS', '', '', '', '', tot_nights, tot_guests,
            f"{tot_gross_acc:.2f}", f"{tot_disc:.2f}", f"{tot_adj:.2f}", f"{tot_net_acc:.2f}",
            f"{tot_extra:.2f}", f"{tot_clean:.2f}", f"{tot_gross:.2f}",
            f"{tot_plat:.2f}", f"{tot_taxes:.2f}",
            f"{tot_pm_base:.2f}", f"{tot_pm_notes:.2f}", f"{tot_pm:.2f}",
            f"{tot_cleaner_base:.2f}", f"{tot_cleaner_notes:.2f}", f"{tot_cleaner:.2f}",
            f"{tot_net_owner:.2f}", ''
        ])

    # Prepare Melio Ready-to-Upload CSV Import
    melio_csv_path = os.path.join(output_dir, f"Melio_Bills_{month_name}_{year}.csv")
    melio_headers = ['Vendor Name', 'Invoice Number', 'Invoice Date', 'Due Date', 'Amount', 'Note']
    
    # Calculate payout dates (Rule 5 & 6: Due date = Today's date + 3 days)
    from datetime import timedelta
    now = datetime.now()
    payout_inv_date = now.strftime('%Y-%m-%d')
    payout_due_date = (now + timedelta(days=3)).strftime('%Y-%m-%d')
        
    month_abbr = month_name[:3].upper()
    yr_short = str(year)[-2:]

    melio_rows = [
        [
            'Sondra Owens',
            f'CLEAN-PAYOUT-{month_abbr}{yr_short}',
            payout_inv_date,
            payout_due_date,
            f"{tot_cleaner:.2f}",
            f"Base Cleaning: ${tot_cleaner_base:,.2f} | Notes Adj: ${tot_cleaner_notes:,.2f}"
        ],
        [
            'Gigi Property Management',
            f'PM-PAYOUT-{month_abbr}{yr_short}',
            payout_inv_date,
            payout_due_date,
            f"{tot_pm:.2f}",
            f"15% Net Acc Rent (${tot_net_acc:,.2f}): ${tot_pm_base:,.2f} | Notes Adj: ${tot_pm_notes:,.2f}"
        ]
    ]

    with open(melio_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(melio_headers)
        for r in melio_rows:
            writer.writerow(r)

    res_dict = {
        'month_name': month_name,
        'year': year,
        'rows': rows,
        'csv_path': csv_path,
        'melio_csv_path': melio_csv_path,
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
            'pm_total': tot_pm,
            'cleaner_base': tot_cleaner_base,
            'cleaner_notes': tot_cleaner_notes,
            'cleaner_total': tot_cleaner,
            'net_owner_income': tot_net_owner
        }
    }

    # Generate PDF Invoices for Melio Auto-Import (Rule 5 & 6: PDF format, 1 invoice per file, <10MB)
    from src.pdf_generator import generate_pdf_invoices
    from src.invoice_generator import create_monthly_invoices
    from src.email_sender import send_invoice_email

    pdf_invoices = generate_pdf_invoices(res_dict, output_dir)
    html_invoices = create_monthly_invoices(res_dict, output_dir)
    
    res_dict['invoices'] = pdf_invoices
    res_dict['html_invoices'] = html_invoices

    # Email separate PDF attachments directly to searetreatpa_7498@invoicesmelio.com (1 PDF per email for Melio)
    import time
    recipient = "searetreatpa_7498@invoicesmelio.com"
    sent_all = True
    for inv_num, vendor, amount, pdf_path in pdf_invoices:
        subj = f"Invoice {inv_num} - {vendor}"
        body = f"Attached is invoice {inv_num} for {vendor} (${amount:,.2f})."
        success = send_invoice_email(recipient, subj, body, attachments=[pdf_path])
        if not success:
            sent_all = False
        time.sleep(1)
    res_dict['email_sent'] = sent_all

    return res_dict

def print_markdown_report(result: dict):
    """Print clean formatted Markdown report in console."""
    t = result['totals']
    print("\n" + "="*80)
    print(f" {result['month_name'].upper()} {result['year']} P&L AND PAYOUT SUMMARY REPORT - 722 MILWAUKEE DR")
    print("================================================================================")
    print(f"Target Month: {result['month_name']} {result['year']}")
    print(f"Total Reservations Processed: {len(result['rows'])}")
    print(f"Total Booked Nights: {t['nights']}")
    print("-" * 80)
    
    print("\n### FINANCIAL OVERVIEW")
    print(f"- Gross Revenue: ${t['gross_revenue']:,.2f}")
    print(f"  - Net Accommodation Rent: ${t['net_acc']:,.2f}")
    print(f"  - Extra Guest Fees Collected: ${t['extra_fees']:,.2f}")
    print(f"  - Cleaning Fees Collected: ${t['cleaning_fees']:,.2f}")
    
    print(f"\n### DEDUCTIONS")
    print(f"- Platform Fees: ${t['platform_fees']:,.2f}")
    print(f"- Taxes: ${t['taxes']:,.2f}")
    print(f"- Property Manager Payout (15% Net Acc + Notes): ${t['pm_total']:,.2f}")
    print(f"  - PM Base Fee (15% Net Acc): ${t['pm_base']:,.2f}")
    print(f"  - PM Notes Adjustments: ${t['pm_notes']:,.2f}")
    print(f"- Cleaner Payout (Base + Notes): ${t['cleaner_total']:,.2f}")
    print(f"  - Base Cleaning Fees: ${t['cleaner_base']:,.2f}")
    print(f"  - Cleaner Notes Adjustments: ${t['cleaner_notes']:,.2f}")
    tot_deductions = t['platform_fees'] + t['taxes'] + t['pm_total'] + t['cleaner_total']
    print(f"- Total Deductions: ${tot_deductions:,.2f}")
    
    print(f"\n### OWNER NET DISTRIBUTION")
    print(f"- Net Owner Income: ${t['net_owner_income']:,.2f}")
    print("="*80)
    print(f"P&L CSV: {result['csv_path']}")
    print(f"Melio Import CSV: {result['melio_csv_path']}")
    for inv in result.get('invoices', []):
        print(f"Melio PDF Invoice ({inv[1]}): {inv[3]}")
    print("="*80 + "\n")
