import os
import sys
import logging
import argparse
from datetime import date, datetime

# Ensure root directory is in python path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.hospitable_api import load_pat
from src.pl_calculator import calculate_pl_for_month

MONTH_NAMES = ["January", "February", "March", "April", "May", "June", 
               "July", "August", "September", "October", "November", "December"]

def calculate_target_month_range(today: date = None):
    """
    Calculate the previous month range (start_date, end_date, month_label).
    Example: If today is Aug 2, 2026 -> ('2026-07-01', '2026-08-01', 'July 2026')
    """
    if today is None:
        today = date.today()
    
    if today.month == 1:
        target_year = today.year - 1
        target_month = 12
        next_year = today.year
        next_month = 1
    else:
        target_year = today.year
        target_month = today.month - 1
        if target_month == 12:
            next_year = today.year + 1
            next_month = 1
        else:
            next_year = today.year
            next_month = target_month + 1

    start_date = f"{target_year}-{target_month:02d}-01"
    end_date = f"{next_year}-{next_month:02d}-01"
    month_label = f"{MONTH_NAMES[target_month - 1]} {target_year}"
    return start_date, end_date, month_label

def setup_logging():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "monthly_automation.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def run_monthly_pipeline(target_month_override: str = None, send_email: bool = True):
    setup_logging()
    logging.info("==========================================")
    logging.info("Starting Monthly Payout & Melio Automation")
    
    if target_month_override:
        year_str, month_str = target_month_override.split("-")
        target_year = int(year_str)
        target_month = int(month_str)
    else:
        today = date.today()
        if today.month == 1:
            target_year = today.year - 1
            target_month = 12
        else:
            target_year = today.year
            target_month = today.month - 1

    month_label = f"{MONTH_NAMES[target_month - 1]} {target_year}"
    logging.info(f"Target Month: {month_label} (Year: {target_year}, Month: {target_month})")
    
    pat = load_pat()
    if not pat:
        logging.error("HOSPITABLE_PAT missing from environment or .env file!")
        return False

    logging.info(f"Executing P&L calculation & PDF invoice generation for {month_label}...")
    res_dict = calculate_pl_for_month(target_year, target_month, output_dir="722 Milwaukee", send_email=send_email)

    
    totals = res_dict.get('totals', {})
    logging.info(f"Gross Revenue: ${totals.get('gross_revenue', 0):,.2f}")
    logging.info(f"Cleaner Payout: ${totals.get('cleaner_total', 0):,.2f}")
    logging.info(f"PM Payout: ${totals.get('pm_total', 0):,.2f}")
    logging.info(f"Net Owner Income: ${totals.get('net_owner_income', 0):,.2f}")
    logging.info(f"CSV Report: {res_dict.get('csv_path')}")
    logging.info(f"Melio CSV Import: {res_dict.get('melio_csv_path')}")

    for inv in res_dict.get('invoices', []):
        logging.info(f"Generated PDF Invoice ({inv[1]}): {inv[3]}")

    logging.info("Automation pipeline completed successfully.")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monthly Payout & Melio Automation")
    parser.add_argument("--month", type=str, help="Target month in YYYY-MM format (e.g. 2026-07)")
    parser.add_argument("--no-email", action="store_true", help="Skip sending emails to Melio")
    args = parser.parse_args()

    success = run_monthly_pipeline(target_month_override=args.month, send_email=not args.no_email)
    sys.exit(0 if success else 1)
