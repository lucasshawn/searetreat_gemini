from src.pl_calculator import calculate_pl_for_month, print_markdown_report

if __name__ == '__main__':
    result = calculate_pl_for_month(2026, 6)
    print_markdown_report(result)
