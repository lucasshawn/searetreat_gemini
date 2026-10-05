import pytest
import os
import sys

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from src.pl_calculator import calculate_pl_for_month

def test_handling_fee_in_pl_calculator():
    res = calculate_pl_for_month(2026, 8, send_email=False)
    t = res['totals']

    expected_pm_handling = round(t['pm_base'] * 0.03, 2)
    assert t['pm_handling'] == expected_pm_handling
    assert t['pm_total'] == round(t['pm_base'] + t['pm_notes'] + t['pm_handling'], 2)

    expected_cleaner_handling = round(t['cleaner_base'] * 0.03, 2)
    assert t['cleaner_handling'] == expected_cleaner_handling
    assert t['cleaner_total'] == round(t['cleaner_base'] + t['cleaner_notes'] + t['cleaner_handling'], 2)

    expected_noi = round(t['gross_revenue'] - t['platform_fees'] - t['taxes'] - t['pm_total'] - t['cleaner_total'], 2)
    assert t['net_owner_income'] == expected_noi
