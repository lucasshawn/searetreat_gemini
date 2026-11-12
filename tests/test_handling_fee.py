import pytest
import os
import sys
import csv
from unittest.mock import patch

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from src.pl_calculator import calculate_pl_for_month

@pytest.fixture
def mock_reservations():
    return [
        {
            "code": "RES-001",
            "platform": "homeaway",
            "guest": {"first_name": "Alice", "last_name": "Smith"},
            "arrival_date": "2026-09-01T16:00:00-07:00",
            "departure_date": "2026-09-05T11:00:00-07:00",
            "status": "accepted",
            "reservation_status": {"current": {"category": "accepted"}},
            "nights": 4,
            "guests": {"total": 4},
            "financials": {
                "host": {
                    "accommodation": {"amount": 200000},  # $2,000.00
                    "discounts": [],
                    "adjustments": [],
                    "guest_fees": [
                        {"amount": 20000, "label": "Cleaning fee"}  # $200.00
                    ],
                    "host_fees": [{"amount": -10000}],
                    "taxes": [],
                }
            },
            "notes": "PM adjustment: +$50.00\nCleaner adjustment: +$20.00",
        },
        {
            "code": "RES-002",
            "platform": "airbnb",
            "guest": {"first_name": "Bob", "last_name": "Jones"},
            "arrival_date": "2026-09-05T16:00:00-07:00",
            "departure_date": "2026-09-10T11:00:00-07:00",
            "status": "accepted",
            "reservation_status": {"current": {"category": "accepted"}},
            "nights": 5,
            "guests": {"total": 2},
            "financials": {
                "host": {
                    "accommodation": {"amount": 100000},  # $1,000.00
                    "discounts": [],
                    "adjustments": [],
                    "guest_fees": [
                        {"amount": 15000, "label": "Cleaning fee"}  # $150.00
                    ],
                    "host_fees": [{"amount": -5000}],
                    "taxes": [],
                }
            },
            "notes": "",
        },
    ]

def test_handling_fee_in_pl_calculator(tmp_path, mock_reservations):
    out_dir = str(tmp_path / "output")
    with patch("src.pl_calculator.fetch_reservations", return_value=mock_reservations):
        res = calculate_pl_for_month(2026, 9, output_dir=out_dir, send_email=False)
    t = res['totals']

    # RES-001: Net Acc = 2000. PM base = 300. PM notes = +50. PM total = 350.
    # RES-001: Clean base = 200. Clean notes = +20. Clean total = 220.
    # RES-002: Net Acc = 1000. PM base = 150. PM notes = 0. PM total = 150.
    # RES-002: Clean base = 150. Clean notes = 0. Clean total = 150.
    # Total PM: 350 + 150 = 500.00 (NO 3% handling fee added to vendor)
    assert t['pm_base'] == 450.00
    assert t['pm_notes'] == 50.00
    assert t['pm_total'] == 500.00

    # Total Cleaner: 220 + 150 = 370.00 (NO 3% handling fee added to vendor)
    assert t['cleaner_base'] == 350.00
    assert t['cleaner_notes'] == 20.00
    assert t['cleaner_total'] == 370.00

    # 3% Credit Card Transaction Fee factored into P&L:
    # Total billing = 500 + 370 = 870.00. 3% = 26.10
    expected_cc_fee = round(sum(r['Credit Card Fee (3%)'] for r in res['rows']), 2)
    assert t['cc_fee'] == 26.10
    assert t['cc_fee'] == expected_cc_fee

    # Net Owner Income:
    # Gross Revenue: 3000 (acc) + 350 (clean) = 3350.00
    # Platform fees: 150.00
    # Deductions: 150 (platform) + 500 (pm) + 370 (cleaner) + 26.10 (cc_fee) = 1046.10
    # NOI: 3350.00 - 1046.10 = 2303.90
    assert t['gross_revenue'] == 3350.00
    assert t['platform_fees'] == 150.00
    assert t['net_owner_income'] == 2303.90

def test_invoices_and_melio_bills_have_no_handling_fee(tmp_path, mock_reservations):
    out_dir = str(tmp_path / "output")
    with patch("src.pl_calculator.fetch_reservations", return_value=mock_reservations):
        res = calculate_pl_for_month(2026, 9, output_dir=out_dir, send_email=False)
    t = res['totals']

    # Melio bills must strictly match vendor payouts without 3%
    with open(res['melio_csv_path'], 'r', encoding='utf-8') as f:
        reader = list(csv.reader(f))
    cleaner_melio = [row for row in reader if row and row[0] == 'Sondra Owens'][0]
    pm_melio = [row for row in reader if row and row[0] == 'Gigi Property Management'][0]

    assert float(cleaner_melio[4]) == 370.00
    assert "3% Handling" not in cleaner_melio[5]

    assert float(pm_melio[4]) == 500.00
    assert "3% Handling" not in pm_melio[5]
