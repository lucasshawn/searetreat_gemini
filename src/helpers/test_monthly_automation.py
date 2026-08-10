from datetime import date
import sys
import os

# Add root directory to python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.monthly_automation import calculate_target_month_range

def test_calculate_target_month_range_normal_month():
    # August 2, 2026 -> Target July 2026
    today = date(2026, 8, 2)
    start_date, end_date, month_label = calculate_target_month_range(today)
    assert start_date == "2026-07-01", f"Expected 2026-07-01, got {start_date}"
    assert end_date == "2026-08-01", f"Expected 2026-08-01, got {end_date}"
    assert month_label == "July 2026", f"Expected July 2026, got {month_label}"

def test_calculate_target_month_range_january_rollover():
    # January 2, 2027 -> Target December 2026
    today = date(2027, 1, 2)
    start_date, end_date, month_label = calculate_target_month_range(today)
    assert start_date == "2026-12-01", f"Expected 2026-12-01, got {start_date}"
    assert end_date == "2027-01-01", f"Expected 2027-01-01, got {end_date}"
    assert month_label == "December 2026", f"Expected December 2026, got {month_label}"

if __name__ == "__main__":
    test_calculate_target_month_range_normal_month()
    test_calculate_target_month_range_january_rollover()
    print("All date range tests passed!")
