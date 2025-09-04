"""Example usage of Stripe invoice creation with payment links."""

from invoice_creator import InvoiceCreator
from customer_manager import CustomerManager

def example_quick_invoice():
    """Example of creating a quick invoice with minimal parameters."""
    print("\n=== Quick Invoice Example ===")
    
    invoice_creator = InvoiceCreator()
    
    # Create a quick invoice - this will create/find customer and send invoice
    result = invoice_creator.create_quick_invoice(
        customer_email="client@example.com",
        amount=250.00,  # $250.00
        description="Consulting services - 5 hours @ $50/hour",
        customer_name="John Doe"
    )
    
    if result["success"]:
        print(f"✅ Invoice created successfully!")
        print(f"Invoice ID: {result['invoice_id']}")
        print(f"Invoice Number: {result['invoice_number']}")
        print(f"Amount Due: ${result['amount_due']:.2f}")
        print(f"Payment Link: {result['payment_link']}")
        print(f"PDF Link: {result['pdf_link']}")
        print(f"Status: {result['status']}")
    else:
        print(f"❌ Error: {result['error']}")
    
    return result

def example_detailed_invoice():
    """Example of creating a detailed invoice with multiple line items."""
    print("\n=== Detailed Invoice Example ===")
    
    # Initialize managers
    customer_manager = CustomerManager()
    invoice_creator = InvoiceCreator()
    
    # Step 1: Get or create customer
    customer_result = customer_manager.get_or_create_customer(
        email="client@company.com",
        name="Jane Smith"
    )
    
    if not customer_result["success"]:
        print(f"❌ Error creating customer: {customer_result['error']}")
        return
    
    customer_id = customer_result["customer_id"]
    print(f"Customer ID: {customer_id}")
    print(f"Customer exists: {customer_result.get('existing', False)}")
    
    # Step 2: Create invoice with multiple items
    items = [
        {
            "description": "Website Development - Frontend",
            "amount": 150000,  # $1500.00 in cents
            "quantity": 1
        },
        {
            "description": "Website Development - Backend API",
            "amount": 200000,  # $2000.00 in cents
            "quantity": 1
        },
        {
            "description": "Hosting Setup (3 hours @ $75/hour)",
            "amount": 7500,  # $75.00 in cents
            "quantity": 3
        }
    ]
    
    result = invoice_creator.create_invoice_with_link(
        customer_id=customer_id,
        items=items,
        description="Website Development Project - January 2025",
        due_days=15,  # Due in 15 days
        auto_send=True  # Automatically email the invoice
    )
    
    if result["success"]:
        print(f"✅ Invoice created successfully!")
        print(f"Invoice ID: {result['invoice_id']}")
        print(f"Invoice Number: {result['invoice_number']}")
        print(f"Amount Due: ${result['amount_due']:.2f}")
        print(f"Payment Link: {result['payment_link']}")
        print(f"PDF Link: {result['pdf_link']}")
        print(f"Status: {result['status']}")
        print(f"Sent to: {result['customer_email']}")
    else:
        print(f"❌ Error: {result['error']}")
    
    return result

def example_list_invoices():
    """Example of listing recent invoices."""
    print("\n=== List Recent Invoices ===")
    
    invoice_creator = InvoiceCreator()
    
    # List last 5 invoices
    invoices = invoice_creator.list_invoices(limit=5)
    
    if invoices:
        print(f"Found {len(invoices)} invoices:")
        for inv in invoices:
            print(f"\n  Invoice #{inv['number']} (ID: {inv['id']})")
            print(f"  Customer: {inv['customer_email']}")
            print(f"  Amount: ${inv['amount']:.2f}")
            print(f"  Status: {inv['status']}")
            print(f"  Payment Link: {inv['payment_link']}")
    else:
        print("No invoices found")

def example_hourly_billing():
    """Example of creating invoice based on hourly billing."""
    print("\n=== Hourly Billing Invoice Example ===")
    
    invoice_creator = InvoiceCreator()
    
    # Calculate based on hours worked
    hours_worked = 12.5
    hourly_rate = 75.00
    total_amount = hours_worked * hourly_rate
    
    result = invoice_creator.create_quick_invoice(
        customer_email="hourly.client@example.com",
        amount=total_amount,
        description=f"Development work - {hours_worked} hours @ ${hourly_rate}/hour",
        customer_name="Hourly Client LLC"
    )
    
    if result["success"]:
        print(f"✅ Hourly invoice created!")
        print(f"Hours: {hours_worked}")
        print(f"Rate: ${hourly_rate}/hour")
        print(f"Total: ${total_amount:.2f}")
        print(f"Payment Link: {result['payment_link']}")
    else:
        print(f"❌ Error: {result['error']}")
    
    return result

if __name__ == "__main__":
    print("Stripe Invoice Creation Examples")
    print("=" * 40)
    
    # Choose which example to run
    print("\nSelect an example to run:")
    print("1. Quick invoice (simple, one-line)")
    print("2. Detailed invoice (multiple items)")
    print("3. List recent invoices")
    print("4. Hourly billing invoice")
    print("5. Run all examples")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == "1":
        example_quick_invoice()
    elif choice == "2":
        example_detailed_invoice()
    elif choice == "3":
        example_list_invoices()
    elif choice == "4":
        example_hourly_billing()
    elif choice == "5":
        example_quick_invoice()
        example_detailed_invoice()
        example_list_invoices()
        example_hourly_billing()
    else:
        print("Invalid choice. Running quick invoice example...")
        example_quick_invoice()