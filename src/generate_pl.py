import sys
import argparse
from datetime import datetime
from src.pl_calculator import calculate_pl_for_month, print_markdown_report

def main():
    parser = argparse.ArgumentParser(description="Generate P&L and Payout Report for 722 Milwaukee Dr.")
    parser.add_argument('--month', type=int, help="Month number (1-12)", default=datetime.now().month)
    parser.add_argument('--year', type=int, help="Year (e.g. 2026)", default=datetime.now().year)
    args = parser.parse_args()

    result = calculate_pl_for_month(args.year, args.month)
    print_markdown_report(result)

if __name__ == '__main__':
    main()
