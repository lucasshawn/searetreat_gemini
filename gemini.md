# Sea Retreat P&L & Payout Rules

## API & Environment Configuration

### Required Environment Variables (`.env`)
Create a `.env` file in the root directory (refer to [`.env.example`](file:///C:/Users/lucas/source/repos/searetreat_gemini/.env.example)):

```ini
# Hospitable API Authentication (Required)
# Endpoint: https://public.api.hospitable.com/v2/reservations
# Header: Authorization: Bearer $HOSPITABLE_PAT
HOSPITABLE_PAT=your_hospitable_pat_here

# Email / SMTP Configuration (Optional - for automated Melio invoice delivery)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password_here
```

### Environment Setup & Variable Reference
| Variable | Required? | Default | Description |
| :--- | :--- | :--- | :--- |
| `HOSPITABLE_PAT` | **Yes** | None | Personal Access Token from Hospitable Dashboard (`Settings > Developer / API Keys`). Required to pull reservation data. |
| `SMTP_SERVER` | Optional | `smtp.gmail.com` | SMTP host for sending Melio invoice attachment emails via [`src/email_sender.py`](file:///C:/Users/lucas/source/repos/searetreat_gemini/src/email_sender.py). |
| `SMTP_PORT` | Optional | `587` | SMTP port (typically 587 for TLS or 465 for SSL). |
| `SMTP_USER` | Optional | None | Sender email account (e.g. Gmail address). |
| `SMTP_PASS` | Optional | None | SMTP authentication password or App Password. |

---

### Onboarding Walkthrough for Antigravity (New Developers)
If a developer asks Antigravity to set up or verify their environment:
1. **Check for `.env`**: Antigravity should check if `.env` exists in the repository root.
2. **Copy `.env.example`**: If missing, create `.env` copied from [`.env.example`](file:///C:/Users/lucas/source/repos/searetreat_gemini/.env.example).
3. **Prompt for Hospitable PAT**: Ask the developer to supply their `HOSPITABLE_PAT`.
4. **Prompt for Optional SMTP Settings**: Ask if they wish to configure automated email invoice dispatches via SMTP.
5. **Verify API Connection**: Run [`python src/helpers/test_api.py`](file:///C:/Users/lucas/source/repos/searetreat_gemini/src/helpers/test_api.py) to confirm the token is active and retrieving data.


## Month Assignment Rule
- A reservation belongs to the target calculation month if its checkout date (departure date) falls AFTER the 1st of that month up to the 1st of the following month.

## Cancelled Bookings Rule
- Cancelled bookings (reservations with status `cancelled` or category `cancelled`) are completely excluded from P&L revenue and payout calculations (do not include cancelled bookings).

## Payout Rules & Financial Calculations


### 1. Property Manager Payout
- **Base Fee**: 15% of **Net Accommodation Rent** (`Gross Accommodation + Discounts + Adjustments`, excluding cleaning fees and extra guest fees).
- **PM Notes Adjustments**: Plus/minus any explicit property manager adjustments documented in reservation notes (e.g., `pm adjustment: +$50`).

### 2. Cleaner Payout
- 100% of the guest cleaning fee charged on the booking channel goes directly to the cleaner.
- Plus/minus any explicit cleaner notes adjustments (e.g., `cleaner adjustment: +$40`, `extra clean fee: $40`).
- **Extra Guest Fees are NOT paid to the cleaner** (do not include extra guest fees in cleaner totals or cleaner invoices).

### 3. Notes Adjustments (Cleaner & Property Manager)
- Any additional dollar amounts documented in the reservation `notes` field in Hospitable are allocated to either the cleaner or the property manager:
  - **Cleaner Adjustments**: e.g., `cleaner adjustment: +$40`, `extra clean fee: $40`, `cleaner: -$20`.
  - **Property Manager Adjustments**: e.g., `pm adjustment: +$50`, `manager fee: -$30`.

### 4. P&L Summary Breakdown
- **Gross Revenue**: Net Accommodation Rent + Extra Guest Fees + Cleaning Fees
- **Deductions**:
  - Platform Fees (Host Service Fees / Channel Fees)
  - Pass-through Taxes
  - Property Manager Payout (15% Net Acc Rent + PM Notes Adjustments)
  - Cleaner Payout (Base Cleaning Fee + Cleaner Notes Adjustments)
- **Net Owner Income**: Gross Revenue - Total Deductions

### 5. Generate an Invoice to Property Manager
- Generate the invoice for the requested time window for property manager using stated fee structure
- Add a line item per guest stay include the following: check in/check out/guest count/guest name/net rent acc
- Send via attachment a copy of this to the searetreatpa_7498@invoicesmelio.com inbox with vendor as: Gigi Property Management (Do not CC any email addresses)
- One invoice per file (no multiple invoices in one PDF)
- The file must be attached in an accepted format: PDF, JPEG, PNG, or GIF
- Maximum file size: 10MB
- Set the due date to today's date + 3

### 6. Generate an Invoice to the Cleaner
- Generate the invoice for the requested time window for the cleaner
- Add a line item per guest stay include the following: check in/check out/guest count/clean fee charged to guest/notes adj columns (do NOT include extra guest fee)
- Send via attachment a copy of this to the searetreatpa_7498@invoicesmelio.com inbox with vendor as: Sondra Owens (Do not CC any email addresses)
- One invoice per file (no multiple invoices in one PDF)
- The file must be attached in an accepted format: PDF, JPEG, PNG, or GIF
- Maximum file size: 10MB
- Set the due date to today's date + 3

### 7. Single Calculated Month Email Dispatch Rule
- **Strict Single-Month Scoping:** Every automated run or script execution MUST generate and email invoices ONLY for the single target calculation month (e.g. when processing July 2026, generate and email strictly `PM-PAYOUT-JUL26` and `CLEAN-PAYOUT-JUL26`).
- **No Historical / Multi-Month Resending:** Do NOT send invoices for previous months (such as June) during a monthly run, and do not trigger email dispatches during manual or historical test runs unless explicitly requested.



## Output Deliverables
- Generate a formatted markdown summary report in terminal.
- Export detailed CSV sheets to a folder named `722 Milwaukee`.