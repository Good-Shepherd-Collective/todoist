# Stripe Invoice System

A complete Stripe integration for creating invoices with payment links.

## Features

- **Quick Invoice Creation**: Create invoices with minimal parameters
- **Detailed Invoices**: Support for multiple line items
- **Customer Management**: Create, update, and retrieve customers
- **Payment Links**: Automatic generation of hosted payment links
- **PDF Generation**: Automatic PDF invoice generation
- **Email Sending**: Optional automatic invoice emailing

## Setup

1. Ensure your `.env` file contains:
   ```
   STRIPE_RESTRICTED=your_stripe_secret_key_here
   ```

2. Install requirements:
   ```bash
   pip install stripe python-dotenv
   ```

## Usage Examples

### 1. Quick Invoice (Command Line)

```bash
# Basic invoice
python stripe/create_invoice_cli.py "client@example.com" 500 "Consulting services"

# With customer name
python stripe/create_invoice_cli.py "client@example.com" 500 "Consulting services" --name "John Doe"

# Without auto-sending email
python stripe/create_invoice_cli.py "client@example.com" 500 "Consulting services" --no-send
```

### 2. Python Code Examples

```python
from stripe.invoice_creator import InvoiceCreator

# Quick invoice
invoice_creator = InvoiceCreator()
result = invoice_creator.create_quick_invoice(
    customer_email="client@example.com",
    amount=250.00,  # $250.00
    description="5 hours of consulting",
    customer_name="Jane Doe"
)

if result["success"]:
    print(f"Payment Link: {result['payment_link']}")
```

### 3. Detailed Invoice with Multiple Items

```python
from stripe.invoice_creator import InvoiceCreator
from stripe.customer_manager import CustomerManager

# Get or create customer
customer_manager = CustomerManager()
customer = customer_manager.get_or_create_customer(
    email="client@company.com",
    name="Company LLC"
)

# Create invoice with multiple items
invoice_creator = InvoiceCreator()
items = [
    {"description": "Frontend Development", "amount": 150000, "quantity": 1},
    {"description": "Backend API", "amount": 200000, "quantity": 1},
    {"description": "Support Hours", "amount": 7500, "quantity": 3}
]

result = invoice_creator.create_invoice_with_link(
    customer_id=customer["customer_id"],
    items=items,
    description="January 2025 Development Work",
    due_days=15,
    auto_send=True
)
```

### 4. Run Interactive Examples

```bash
python stripe/example_usage.py
```

This will show a menu with different examples:
1. Quick invoice creation
2. Detailed invoice with multiple items
3. List recent invoices
4. Hourly billing invoice

## API Reference

### InvoiceCreator

- `create_quick_invoice(email, amount, description, name)` - Quick invoice creation
- `create_invoice_with_link(customer_id, items, description, due_days, auto_send)` - Detailed invoice
- `list_invoices(customer_id, limit)` - List recent invoices

### CustomerManager

- `create_customer(email, name, phone, address, metadata)` - Create new customer
- `get_or_create_customer(email, name)` - Get existing or create new
- `update_customer(customer_id, **kwargs)` - Update customer details
- `get_customer(customer_id)` - Retrieve customer info
- `list_customers(limit, email)` - List customers
- `delete_customer(customer_id)` - Delete a customer

## Response Format

Successful invoice creation returns:
```python
{
    "success": True,
    "invoice_id": "inv_xxx",
    "invoice_number": "INV-0001",
    "amount_due": 250.00,
    "currency": "usd",
    "payment_link": "https://invoice.stripe.com/...",
    "pdf_link": "https://invoice.stripe.com/.../pdf",
    "status": "open",
    "customer_email": "client@example.com"
}
```

## Integration with Todoist Time Tracking

You can integrate this with your existing Todoist billing data:

```python
import json
from stripe.invoice_creator import InvoiceCreator

# Load your billing data
with open("billing_report.txt", "r") as f:
    billing_data = json.load(f)

# Create invoice from time tracking
hours = billing_data["total_hours"]
rate = 50  # $/hour
amount = hours * rate

invoice_creator = InvoiceCreator()
result = invoice_creator.create_quick_invoice(
    customer_email="client@example.com",
    amount=amount,
    description=f"Development work - {hours} hours @ ${rate}/hour"
)
```

## Testing

Test the system with Stripe's test mode by using test API keys and test card numbers:
- Test card: 4242 4242 4242 4242
- Any future expiry date
- Any 3-digit CVC

## Error Handling

All methods return a dictionary with `"success": False` and an `"error"` message on failure:

```python
result = invoice_creator.create_quick_invoice(...)
if not result["success"]:
    print(f"Error: {result['error']}")
```