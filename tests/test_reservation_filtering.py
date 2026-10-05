import pytest
from unittest.mock import patch
from src.pl_calculator import calculate_pl_for_month

def test_expired_and_cancelled_reservations_excluded(tmp_path):
    mock_reservations = [
        # Accepted reservation ending on Oct 1 (should be in September)
        {
            "code": "HA-NM4CXV",
            "platform": "homeaway",
            "guest": {"first_name": "David", "last_name": "Jones"},
            "arrival_date": "2026-09-29T16:00:00-07:00",
            "departure_date": "2026-10-01T11:00:00-07:00",
            "status": "accepted",
            "reservation_status": {"current": {"category": "accepted"}},
            "nights": 2,
            "guests": {"total": 4},
            "financials": {
                "host": {
                    "accommodation": {"amount": 79235},
                    "discounts": [{"amount": -7924}],
                    "adjustments": [],
                    "guest_fees": [{"amount": 25000, "label": "Cleaning fee"}],
                    "host_fees": [{"amount": -8020}],
                    "taxes": [],
                }
            },
        },
        # Expired / unaccepted inquiry (Kathy Mix, HOST-ONLFU3 - must be EXCLUDED)
        {
            "code": "HOST-ONLFU3",
            "platform": "direct",
            "guest": {"first_name": "Kathy", "last_name": "Mix"},
            "arrival_date": "2026-09-29T15:00:00-07:00",
            "departure_date": "2026-10-01T11:00:00-07:00",
            "status": "expired",
            "reservation_status": {"current": {"category": "not accepted"}},
            "nights": 2,
            "guests": {"total": 6},
            "financials": {
                "host": {
                    "accommodation": {"amount": 68700},
                    "discounts": [],
                    "adjustments": [],
                    "guest_fees": [{"amount": 20700, "label": "Cleaning fee"}],
                    "host_fees": [],
                    "taxes": [],
                }
            },
        },
        # Cancelled booking (must be EXCLUDED)
        {
            "code": "HA-PX86WJ",
            "platform": "homeaway",
            "guest": {"first_name": "Kathy", "last_name": "West"},
            "arrival_date": "2026-09-16T16:00:00-07:00",
            "departure_date": "2026-09-20T11:00:00-07:00",
            "status": "cancelled",
            "reservation_status": {"current": {"category": "cancelled"}},
            "nights": 4,
            "guests": {"total": 6},
            "financials": {
                "host": {
                    "accommodation": {"amount": 100000},
                    "discounts": [],
                    "adjustments": [],
                    "guest_fees": [{"amount": 18000, "label": "Cleaning fee"}],
                    "host_fees": [],
                    "taxes": [],
                }
            },
        },
        # Booking ending in October (Madeleine Oudin, Oct 1 - Oct 4 - must be EXCLUDED from Sep)
        {
            "code": "HM3JEC982D",
            "platform": "airbnb",
            "guest": {"first_name": "Madeleine", "last_name": "Oudin"},
            "arrival_date": "2026-10-01T15:00:00-07:00",
            "departure_date": "2026-10-04T11:00:00-07:00",
            "status": "accepted",
            "reservation_status": {"current": {"category": "accepted"}},
            "nights": 3,
            "guests": {"total": 4},
            "financials": {
                "host": {
                    "accommodation": {"amount": 120000},
                    "discounts": [],
                    "adjustments": [],
                    "guest_fees": [{"amount": 20700, "label": "Cleaning fee"}],
                    "host_fees": [],
                    "taxes": [],
                }
            },
        },
    ]

    with patch("src.pl_calculator.fetch_reservations", return_value=mock_reservations):
        res = calculate_pl_for_month(2026, 9, output_dir=str(tmp_path), send_email=False)
        codes = [r["Reservation Code"] for r in res["rows"]]
        
        # Only David Jones should be included for September
        assert "HA-NM4CXV" in codes
        assert "HOST-ONLFU3" not in codes, "Expired booking HOST-ONLFU3 must not be included"
        assert "HA-PX86WJ" not in codes, "Cancelled booking HA-PX86WJ must not be included"
        assert "HM3JEC982D" not in codes, "October booking HM3JEC982D must not be included in September"
        assert len(res["rows"]) == 1
