# Monthly Task Scheduler Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows Task Scheduler monthly automation pipeline that runs on the 2nd of every month to process short-term rental P&L for the previous month (`current_month - 1`), export CSV reports, generate PDF invoices for PM & Cleaner, and email PDF attachments to Melio (`searetreatpa_7498@invoicesmelio.com`).

**Architecture:** A standalone entry script (`src/monthly_automation.py`) encapsulates date calculation, data fetching via Hospitable API, P&L calculations, PDF rendering, email dispatching, and file logging. A batch runner (`run_automation.bat`) and PowerShell setup script (`setup_task_scheduler.ps1`) register and invoke the task via Windows Task Scheduler.

**Tech Stack:** Python 3.11+, Standard Library (`urllib`, `json`, `datetime`, `smtplib`, `argparse`, `logging`), `pdfkit` / HTML template rendering, Windows Task Scheduler (`schtasks` / PowerShell `Register-ScheduledTask`).

## Global Constraints
- Target date range must compute `current_month - 1` automatically (handling January → December boundary).
- Support CLI flags `--month YYYY-MM` (override target month) and `--no-email` (skip SMTP email dispatch for local testing).
- Maintain invoice due date as `today + 3 days`.
- Log execution details to `logs/monthly_automation.log`.

---

### Task 1: Create Master Monthly Automation Script (`src/monthly_automation.py`)

**Files:**
- Create: `src/monthly_automation.py`
- Create: `src/helpers/test_monthly_automation.py`

**Interfaces:**
- Consumes: `src.hospitable_api.fetch_reservations`, `src.pl_calculator.calculate_pl`, `src.pdf_generator.generate_pm_invoice`, `src.pdf_generator.generate_cleaner_invoice`, `src.email_sender.send_invoice_email`
- Produces: `calculate_target_month_range(today: datetime) -> (str, str, str)`, `run_monthly_pipeline(target_month_str: str, send_email: bool) -> bool`

- [ ] **Step 1: Write failing unit test for target month date range calculation**

Create `src/helpers/test_monthly_automation.py`:
```python
from datetime import date
from src.monthly_automation import calculate_target_month_range

def test_calculate_target_month_range_normal_month():
    # August 2, 2026 -> Target July 2026
    today = date(2026, 8, 2)
    start_date, end_date, month_label = calculate_target_month_range(today)
    assert start_date == "2026-07-01"
    assert end_date == "2026-08-01"
    assert month_label == "July 2026"

def test_calculate_target_month_range_january_rollover():
    # January 2, 2027 -> Target December 2026
    today = date(2027, 1, 2)
    start_date, end_date, month_label = calculate_target_month_range(today)
    assert start_date == "2026-12-01"
    assert end_date == "2027-01-01"
    assert month_label == "December 2026"

if __name__ == "__main__":
    test_calculate_target_month_range_normal_month()
    test_calculate_target_month_range_january_rollover()
    print("All date range tests passed!")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python src/helpers/test_monthly_automation.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.monthly_automation'`

- [ ] **Step 3: Implement `src/monthly_automation.py`**

Create `src/monthly_automation.py`:
```python
import os
import sys
import logging
import argparse
from datetime import date, datetime, timedelta

# Ensure src is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.hospitable_api import fetch_reservations, load_pat
from src.pl_calculator import calculate_pl
from src.pdf_generator import generate_pm_invoice, generate_cleaner_invoice
from src.email_sender import send_invoice_email

MONTH_NAMES = ["January", "February", "March", "April", "May", "June", 
               "July", "August", "September", "October", "November", "December"]

def calculate_target_month_range(today: date = None):
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
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

def run_monthly_pipeline(target_month_override: str = None, send_email: bool = True):
    setup_logging()
    logging.info("==========================================")
    logging.info("Starting Monthly Payout & Melio Automation")
    
    if target_month_override:
        # Expected format YYYY-MM
        year_str, month_str = target_month_override.split("-")
        target_year = int(year_str)
        target_month = int(month_str)
        if target_month == 12:
            next_year = target_year + 1
            next_month = 1
        else:
            next_year = target_year
            next_month = target_month + 1
        start_date = f"{target_year}-{target_month:02d}-01"
        end_date = f"{next_year}-{next_month:02d}-01"
        month_label = f"{MONTH_NAMES[target_month - 1]} {target_year}"
    else:
        start_date, end_date, month_label = calculate_target_month_range()

    logging.info(f"Target Month: {month_label} (Checkout Range: {start_date} to {end_date})")
    
    pat = load_pat()
    if not pat:
        logging.error("HOSPITABLE_PAT missing from environment or .env file!")
        return False

    logging.info("Fetching reservations from Hospitable API...")
    reservations = fetch_reservations(start_date, end_date, pat=pat)
    logging.info(f"Retrieved {len(reservations)} reservations.")

    logging.info("Calculating P&L summary and generating CSVs...")
    summary, pl_rows = calculate_pl(reservations, month_label)
    
    logging.info(f"Gross Revenue: ${summary['gross_revenue']:,.2f}")
    logging.info(f"Cleaner Payout: ${summary['cleaner_payout']:,.2f}")
    logging.info(f"PM Payout: ${summary['pm_payout']:,.2f}")
    logging.info(f"Net Owner Income: ${summary['net_owner_income']:,.2f}")

    due_date = (date.today() + timedelta(days=3)).strftime("%Y-%m-%d")
    output_dir = "722 Milwaukee"
    os.makedirs(output_dir, exist_ok=True)
    
    cleaner_pdf = os.path.join(output_dir, f"Invoice_Sondra_Owens_CLEAN-PAYOUT-{target_month_override or start_date[:7]}.pdf")
    pm_pdf = os.path.join(output_dir, f"Invoice_Gigi_PM_PM-PAYOUT-{target_month_override or start_date[:7]}.pdf")

    logging.info("Generating PDF invoices...")
    generate_cleaner_invoice(summary, pl_rows, month_label, due_date, cleaner_pdf)
    generate_pm_invoice(summary, pl_rows, month_label, due_date, pm_pdf)

    if send_email:
        melio_recipient = "searetreatpa_7498@invoicesmelio.com"
        logging.info(f"Dispatching PDF invoices to Melio ({melio_recipient})...")
        
        # Send Cleaner Invoice
        c_sent = send_invoice_email(
            recipient_email=melio_recipient,
            subject=f"Invoice CLEAN-PAYOUT - Sondra Owens",
            body_html=f"<p>Invoice for Sondra Owens ({month_label}). Amount: ${summary['cleaner_payout']:,.2f}</p>",
            attachments=[cleaner_pdf]
        )
        
        # Send PM Invoice
        pm_sent = send_invoice_email(
            recipient_email=melio_recipient,
            subject=f"Invoice PM-PAYOUT - Gigi Property Management",
            body_html=f"<p>Invoice for Gigi Property Management ({month_label}). Amount: ${summary['pm_payout']:,.2f}</p>",
            attachments=[pm_pdf]
        )
        
        if c_sent and pm_sent:
            logging.info("All invoice emails successfully delivered to Melio.")
        else:
            logging.warning("One or more email deliveries failed. Check SMTP configuration.")
    else:
        logging.info("Skipping email dispatch (--no-email specified).")

    logging.info("Automation completed successfully.")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monthly Payout & Melio Automation")
    parser.add_argument("--month", type=str, help="Target month in YYYY-MM format (e.g. 2026-07)")
    parser.add_argument("--no-email", action="store_true", help="Skip sending emails to Melio")
    args = parser.parse_args()

    success = run_monthly_pipeline(target_month_override=args.month, send_email=not args.no_email)
    sys.exit(0 if success else 1)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python src/helpers/test_monthly_automation.py`
Expected: PASS with "All date range tests passed!"

- [ ] **Step 5: Commit**

```bash
git add src/monthly_automation.py src/helpers/test_monthly_automation.py
git commit -m "feat: add monthly automation script with dynamic date calculation and CLI options"
```

---

### Task 2: Create Windows Batch Runner Wrapper (`run_automation.bat`)

**Files:**
- Create: `run_automation.bat`

**Interfaces:**
- Consumes: `src/monthly_automation.py`
- Produces: Executable Windows batch script for Task Scheduler

- [ ] **Step 1: Create `run_automation.bat`**

Create `run_automation.bat`:
```cmd
@echo off
REM ===================================================
REM Sea Retreat Monthly Melio Automation Runner
REM ===================================================
cd /d "%~dp0"

if not exist "logs" mkdir "logs"

echo [%DATE% %TIME%] Starting Sea Retreat Monthly Automation >> logs\monthly_automation.log
python src\monthly_automation.py >> logs\monthly_automation.log 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [%DATE% %TIME%] ERROR: Monthly automation failed with code %ERRORLEVEL% >> logs\monthly_automation.log
    exit /b %ERRORLEVEL%
)

echo [%DATE% %TIME%] Monthly automation completed successfully >> logs\monthly_automation.log
```

- [ ] **Step 2: Test `run_automation.bat` execution with `--no-email`**

Run: `python src/monthly_automation.py --month 2026-07 --no-email`
Expected: Output logged to `logs/monthly_automation.log` and exit code 0.

- [ ] **Step 3: Commit**

```bash
git add run_automation.bat
git commit -m "feat: add run_automation.bat wrapper for Windows Task Scheduler"
```

---

### Task 3: Create Task Scheduler PowerShell Installer (`setup_task_scheduler.ps1`)

**Files:**
- Create: `setup_task_scheduler.ps1`

**Interfaces:**
- Consumes: `run_automation.bat`
- Produces: Windows Scheduled Task `SeaRetreat_Monthly_Melio_Automation`

- [ ] **Step 1: Create `setup_task_scheduler.ps1`**

Create `setup_task_scheduler.ps1`:
```powershell
# ===================================================
# Sea Retreat Windows Task Scheduler Registration
# ===================================================

$TaskName = "SeaRetreat_Monthly_Melio_Automation"
$ScriptPath = Join-Path -Path $PSScriptRoot -ChildPath "run_automation.bat"
$WorkingDirectory = $PSScriptRoot

Write-Host "Registering Scheduled Task: $TaskName"
Write-Host "Target Action: $ScriptPath"

# Define Trigger: Monthly on the 2nd day of every month at 9:00 AM
$Trigger = New-ScheduledTaskTrigger -Monthly -DaysOfMonth 2 -At "09:00AM"

# Define Action: Launch run_automation.bat
$Action = New-ScheduledTaskAction -Execute $ScriptPath -WorkingDirectory $WorkingDirectory

# Register Task
Register-ScheduledTask -TaskName $TaskName -Trigger $Trigger -Action $Action -Description "Sea Retreat Short-Term Rental Monthly Payout & Melio Invoice Automation" -Force

Write-Host "Task '$TaskName' successfully registered to run at 9:00 AM on the 2nd of every month."
```

- [ ] **Step 2: Commit**

```bash
git add setup_task_scheduler.ps1
git commit -m "feat: add setup_task_scheduler.ps1 script for registering monthly scheduled task"
```

---

## Execution Handoff
Plan complete and saved to [`docs/superpowers/plans/2026-08-10-monthly-task-scheduler-automation-plan.md`](file:///C:/Users/lucas/source/repos/searetreat_gemini/docs/superpowers/plans/2026-08-10-monthly-task-scheduler-automation-plan.md).
