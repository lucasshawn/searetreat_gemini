# Design Spec: Windows Task Scheduler Monthly Payout Automation

## Overview
Automate monthly short-term rental P&L calculation, PDF invoice generation, and Melio email dispatch for Sea Retreat on the **2nd day of every month**. The automation dynamically target the previous calendar month (`current_month - 1`), processes reservations from Hospitable API, generates CSV reports and PDF invoices, and emails the PDF invoices directly to `searetreatpa_7498@invoicesmelio.com`.

## Architecture & Components

```
Task Scheduler (Every 2nd of month @ 9:00 AM)
       │
       ▼
run_automation.bat
       │
       ▼
src/monthly_automation.py
       ├── 1. Dynamic Date Resolver (Month - 1)
       ├── 2. Hospitable API Fetcher (load_pat / fetch_reservations)
       ├── 3. P&L Calculator & CSV Exporter (calculate_pl)
       ├── 4. Invoice Generator & PDF Converter (Gigi PM & Sondra Owens)
       ├── 5. Email Dispatcher to Melio (searetreatpa_7498@invoicesmelio.com)
       └── 6. Logging System (logs/monthly_automation.log)
```

### 1. `src/monthly_automation.py`
A standalone Python script executing the full end-to-end pipeline:
* **Date Logic:**
  - Reads system date when run (e.g. `2026-09-02`).
  - Calculates previous month range:
    - Target Year/Month: If current month is 1 (January), target month = 12, target year = current_year - 1. Otherwise target month = current_month - 1, target year = current_year.
    - `start_date`: `{target_year}-{target_month:02d}-01`
    - `end_date`: `{current_year}-{current_month:02d}-01`
* **Execution Workflow:**
  - Loads credentials from `.env` using `os.getenv` / fallback file parser.
  - Fetches Hospitable reservation data for date window (`start_date` to `end_date`).
  - Filters out cancelled bookings and calculates revenue, cleaning fees, 15% Net Acc Rent PM base fee, and notes adjustments.
  - Exports `July_2026_PL.csv` (or target month equivalent) and Melio CSV to `722 Milwaukee/`.
  - Generates HTML/PDF invoices for:
    1. **Gigi Property Management** (PM Payout)
    2. **Sondra Owens** (Cleaner Payout)
  - Emails each PDF individually to `searetreatpa_7498@invoicesmelio.com` using `send_invoice_email()` from `src/email_sender.py`.
  - Logs execution details to `logs/monthly_automation.log`.

### 2. `run_automation.bat`
Batch script located in project root:
```cmd
@echo off
cd /d "C:\Users\lucas\source\repos\searetreat_gemini"
python src/monthly_automation.py >> logs\monthly_automation.log 2>&1
```

### 3. `setup_task_scheduler.ps1`
PowerShell installer script to create the Windows Scheduled Task:
* Task Name: `SeaRetreat_Monthly_Melio_Automation`
* Trigger: Monthly on the 2nd day of every month at 09:00 AM local time.
* Action: Execute `run_automation.bat`.

## Verification & Testing Plan
1. **Dry-Run Mode (`--dry-run` or `--month YYYY-MM`):**
   - Allow manually specifying target month for testing (e.g. `python src/monthly_automation.py --month 2026-07`).
   - Allow `--no-email` flag to test full PDF/CSV generation without emailing Melio.
2. **Task Registration Test:**
   - Execute `setup_task_scheduler.ps1` and verify task presence via `schtasks /Query /TN "SeaRetreat_Monthly_Melio_Automation"`.
3. **Execution Test:**
   - Run task on demand via `schtasks /Run /TN "SeaRetreat_Monthly_Melio_Automation"` and inspect `logs/monthly_automation.log` and `722 Milwaukee/`.
