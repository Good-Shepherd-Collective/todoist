"""Debug the billing report parser to see what tasks are being extracted."""

from billing_report_converter import BillingReportConverter

def debug_parsing():
    converter = BillingReportConverter()
    
    # Parse the report and show what we get
    report_data = converter.parse_billing_report("../billing_report.txt")
    
    print("=== PARSED REPORT DATA ===")
    print(f"Invoice Number: {report_data['invoice_number']}")
    print(f"Project: {report_data['project']}")
    print(f"Total Tasks: {report_data['total_tasks']}")
    print(f"Total Hours: {report_data['total_hours']}")
    print(f"Amount Due: ${report_data['amount_due']}")
    
    print(f"\n=== PARSED TASKS ({len(report_data['tasks'])}) ===")
    total_minutes = 0
    for i, task in enumerate(report_data['tasks'], 1):
        print(f"{i}. {task['title']}")
        print(f"   Duration: {task['duration_minutes']} mins ({task['duration_hours']} hrs)")
        print(f"   Description: {task['description'][:50]}...")
        print()
        total_minutes += task['duration_minutes']
    
    total_hours_calculated = total_minutes / 60
    print(f"=== CALCULATED TOTALS ===")
    print(f"Total minutes: {total_minutes}")
    print(f"Total hours calculated: {round(total_hours_calculated, 2)}")
    print(f"Total hours from report: {report_data['total_hours']}")
    print(f"At $40/hour: ${round(total_hours_calculated * 40, 2)}")

if __name__ == "__main__":
    debug_parsing()