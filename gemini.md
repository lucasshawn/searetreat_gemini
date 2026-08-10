# Sea Retreat P&L & Payout Rules

## API Authentication
- Load Hospitable PAT from environment variable `HOSPITABLE_PAT`.
- Endpoint: `https://api.hospitable.com/v2/reservations`
- Headers: `Authorization: Bearer $HOSPITABLE_PAT`

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


## Output Deliverables
- Generate a formatted markdown summary report in terminal.
- Export detailed CSV sheets to a folder named `722 Milwaukee`.