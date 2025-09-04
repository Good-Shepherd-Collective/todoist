"""Command-line tool for creating Stripe invoices quickly."""

import sys
import argparse
from invoice_creator import InvoiceCreator
from customer_manager import CustomerManager

def main():
    parser = argparse.ArgumentParser(description="Create Stripe invoice with payment link")
    
    # Required arguments
    parser.add_argument("email", help="Customer email address")
    parser.add_argument("amount", type=float, help="Invoice amount in dollars")
    parser.add_argument("description", help="Description of service/product")
    
    # Optional arguments
    parser.add_argument("--name", help="Customer name", default=None)
    parser.add_argument("--invoice-number", help="Custom invoice number", default=None)
    parser.add_argument("--due-days", type=int, help="Days until due (default: 30)", default=30)
    parser.add_argument("--no-send", action="store_true", help="Don't auto-send the invoice")
    
    args = parser.parse_args()
    
    # Create invoice
    invoice_creator = InvoiceCreator()
    
    print(f"\nCreating invoice for {args.email}...")
    print(f"Amount: ${args.amount:.2f}")
    print(f"Description: {args.description}")
    if args.invoice_number:
        print(f"Invoice Number: {args.invoice_number}")
    
    result = invoice_creator.create_quick_invoice(
        customer_email=args.email,
        amount=args.amount,
        description=args.description,
        customer_name=args.name,
        invoice_number=args.invoice_number
    )
    
    if result["success"]:
        print("\n✅ Invoice created successfully!")
        print("-" * 50)
        print(f"Invoice Number: {result['invoice_number']}")
        print(f"Amount Due: ${result['amount_due']:.2f}")
        print(f"Status: {result['status']}")
        print(f"\n📧 Payment Link:")
        print(f"   {result['payment_link']}")
        print(f"\n📄 PDF Link:")
        print(f"   {result['pdf_link']}")
        
        if not args.no_send:
            print(f"\n✉️  Invoice has been emailed to {args.email}")
    else:
        print(f"\n❌ Error creating invoice: {result['error']}")
        sys.exit(1)

if __name__ == "__main__":
    main()