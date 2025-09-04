"""Test invoice creation with a single task to isolate duplication issue."""

from billing_report_converter import BillingReportConverter
from customer_manager import CustomerManager

def test_single_task():
    converter = BillingReportConverter()
    
    # Test with a single task
    single_task_items = [{
        "description": "Test task - 15 minutes",
        "amount": 1000,  # $10.00 (15 mins * $40/hour)
        "currency": "usd"
    }]
    
    # Get customer
    customer_result = converter.customer_manager.get_or_create_customer(
        email="singletest@example.com",
        name="Single Test"
    )
    
    if not customer_result["success"]:
        print(f"Customer error: {customer_result['error']}")
        return
    
    customer_id = customer_result["customer_id"]
    print(f"Customer ID: {customer_id}")
    
    # Create invoice with single task
    import time
    test_invoice_number = f"TEST-SINGLE-{int(time.time())}"
    
    result = converter.create_detailed_invoice(
        customer_id=customer_id,
        items=single_task_items,
        invoice_number=test_invoice_number,
        description="Single task test",
        auto_send=False  # Don't send
    )
    
    if result["success"]:
        print(f"\n✅ Single task invoice created!")
        print(f"Invoice Number: {result['invoice_number']}")
        print(f"Line Items: {result['line_items_count']}")
        print(f"Amount Due: ${result['amount_due']:.2f}")
        print(f"Expected: $10.00")
        if result['amount_due'] != 10.0:
            print(f"❌ DUPLICATION DETECTED! Expected $10.00, got ${result['amount_due']:.2f}")
        else:
            print(f"✅ Amount is correct!")
    else:
        print(f"❌ Error: {result['error']}")

if __name__ == "__main__":
    test_single_task()