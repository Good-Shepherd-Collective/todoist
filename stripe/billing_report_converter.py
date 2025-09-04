"""Convert billing reports to Stripe invoices with detailed line items."""

import re
import json
from typing import Dict, List
from invoice_creator import InvoiceCreator
from customer_manager import CustomerManager

class BillingReportConverter:
    def __init__(self):
        self.invoice_creator = InvoiceCreator()
        self.customer_manager = CustomerManager()
    
    def parse_billing_report(self, report_path: str) -> Dict:
        """Parse billing report text file into structured data."""
        with open(report_path, 'r') as f:
            content = f.read()
        
        # Extract header information
        invoice_match = re.search(r'Invoice Number: (.*)', content)
        date_match = re.search(r'Generated: (.*)', content)
        period_match = re.search(r'Billing Period: (.*)', content)
        project_match = re.search(r'BILLING REPORT: (.*)', content)
        total_tasks_match = re.search(r'Total Completed Tasks: (\d+)', content)
        
        # Extract summary information
        hours_match = re.search(r'Total hours: ([\d.]+)', content)
        amount_match = re.search(r'Amount due: \$([\d.]+)', content)
        
        # Extract individual tasks
        tasks = []
        # Split content by task separators
        task_blocks = re.split(r'\n\s*----------------------------------------\s*\n', content)
        
        for block in task_blocks:
            task_match = re.search(
                r'(\d+)\.\s+(.+?)\n\s+Duration: (\d+) mins\n\s+Completed: ([\d/]+)\n\s+\n\s+Description: (.+?)(?:\n|$)', 
                block.strip(), 
                re.DOTALL
            )
            if task_match:
                task_num, title, duration, completed, description = task_match.groups()
                tasks.append({
                    "number": int(task_num),
                    "title": title.strip(),
                    "duration_minutes": int(duration),
                    "duration_hours": round(int(duration) / 60, 2),
                    "completed_date": completed.strip(),
                    "description": description.strip().replace('\n', ' ')
                })
        
        return {
            "invoice_number": invoice_match.group(1) if invoice_match else None,
            "generated_date": date_match.group(1) if date_match else None,
            "billing_period": period_match.group(1) if period_match else None,
            "project": project_match.group(1) if project_match else None,
            "total_tasks": int(total_tasks_match.group(1)) if total_tasks_match else 0,
            "total_hours": float(hours_match.group(1)) if hours_match else 0,
            "amount_due": float(amount_match.group(1)) if amount_match else 0,
            "tasks": tasks
        }
    
    def create_invoice_from_report(
        self, 
        report_path: str,
        customer_email: str,
        customer_name: str = None,
        hourly_rate: float = 40.0,
        auto_send: bool = True
    ) -> Dict:
        """Create a detailed Stripe invoice from billing report."""
        
        # Parse the report
        report_data = self.parse_billing_report(report_path)
        
        # Create customer
        customer_result = self.customer_manager.get_or_create_customer(
            email=customer_email,
            name=customer_name
        )
        
        if not customer_result["success"]:
            return customer_result
        
        customer_id = customer_result["customer_id"]
        
        # Create detailed line items for each task (like your billing report format)
        items = []
        for i, task in enumerate(report_data["tasks"], 1):
            task_amount = int(task["duration_hours"] * hourly_rate * 100)  # Convert to cents
            
            # Format with proper line breaks but keep under 500 char limit
            # Truncate description if needed but keep line break structure
            desc_limit = 350  # Leave room for other text
            truncated_desc = task['description'][:desc_limit]
            if len(task['description']) > desc_limit:
                truncated_desc += "..."
            
            detailed_description = (
                f"{i}. {task['title']}\n"
                f"   Duration: {task['duration_minutes']} mins\n"
                f"   Completed: {task['completed_date']}\n"
                f"   \n"
                f"   Description: {truncated_desc}"
            )
            
            items.append({
                "description": detailed_description,
                "amount": task_amount,
                "currency": "usd"
            })
        
        # Create custom fields for additional info
        custom_fields = [
            {"name": "Project", "value": report_data["project"]},
            {"name": "Billing Period", "value": report_data["billing_period"]},
            {"name": "Total Hours", "value": f"{report_data['total_hours']} hours"},
            {"name": "Tasks Completed", "value": str(report_data["total_tasks"])}
        ]
        
        # Create footer matching your billing report summary format
        footer = f"""SUMMARY:
- Total tasks completed: {report_data['total_tasks']}
- Project: {report_data['project']}
- Total hours: {report_data['total_hours']}
- Rate: ${hourly_rate}/hr
- Amount due: ${report_data['total_hours'] * hourly_rate:.2f}
- Report generated: {report_data['generated_date']}

For questions about this billing report, please contact Cody"""
        
        # Metadata for additional structured data
        metadata = {
            "project": report_data["project"],
            "billing_period": report_data["billing_period"],
            "total_tasks": str(report_data["total_tasks"]),
            "total_hours": str(report_data["total_hours"]),
            "hourly_rate": str(hourly_rate),
            "original_invoice_number": report_data["invoice_number"]
        }
        
        # Make invoice number unique but keep it under 26 chars
        import time
        timestamp = str(int(time.time()))[-6:]  # Last 6 digits
        base_number = report_data["invoice_number"][:19]  # Keep first 19 chars
        unique_invoice_number = f"{base_number}-{timestamp}"
        
        # Create the invoice using the detailed method (with custom fields, footer, etc.)
        return self.create_detailed_invoice(
            customer_id=customer_id,
            items=items,
            invoice_number=unique_invoice_number,
            description=f"BILLING REPORT: {report_data['project']} | Period: {report_data['billing_period']} | Tasks: {report_data['total_tasks']}",
            custom_fields=custom_fields,
            footer=footer,
            metadata=metadata,
            auto_send=auto_send
        )
    
    def create_detailed_invoice(
        self,
        customer_id: str,
        items: List[Dict],
        invoice_number: str = None,
        description: str = None,
        custom_fields: List[Dict] = None,
        footer: str = None,
        metadata: Dict = None,
        auto_send: bool = True
    ) -> Dict:
        """Create invoice with all the advanced Stripe features."""
        
        try:
            # First create invoice items as pending items (like the original InvoiceCreator does)
            for item in items:
                invoice_item_params = {
                    "customer": customer_id,
                    "description": item.get("description", "Service"),
                    "currency": item.get("currency", "usd")
                }
                
                # Use the same logic as the original InvoiceCreator
                if "quantity" in item and item["quantity"] != 1:
                    invoice_item_params["unit_amount"] = item["amount"]
                    invoice_item_params["quantity"] = item["quantity"]
                else:
                    invoice_item_params["amount"] = item["amount"]
                
                self.invoice_creator.stripe.InvoiceItem.create(**invoice_item_params)
            
            # Create invoice with advanced features
            invoice_params = {
                "customer": customer_id,
                "description": description,
                "collection_method": "send_invoice",
                "days_until_due": 30,
                "pending_invoice_items_behavior": "include",  # Include pending items
                "auto_advance": False
            }
            
            # Add optional advanced parameters
            if invoice_number:
                invoice_params["number"] = invoice_number
            if custom_fields:
                invoice_params["custom_fields"] = custom_fields[:4]  # Stripe limit: 4
            if footer:
                invoice_params["footer"] = footer[:5000]  # Character limit
            if metadata:
                invoice_params["metadata"] = metadata
            
            # Create, finalize, and optionally send
            invoice = self.invoice_creator.stripe.Invoice.create(**invoice_params)
            finalized_invoice = self.invoice_creator.stripe.Invoice.finalize_invoice(invoice.id)
            
            if auto_send:
                sent_invoice = self.invoice_creator.stripe.Invoice.send_invoice(finalized_invoice.id)
                invoice_data = sent_invoice
            else:
                invoice_data = finalized_invoice
            
            return {
                "success": True,
                "invoice_id": invoice_data.id,
                "invoice_number": invoice_data.number,
                "amount_due": invoice_data.amount_due / 100,
                "currency": invoice_data.currency,
                "payment_link": invoice_data.hosted_invoice_url,
                "pdf_link": invoice_data.invoice_pdf,
                "status": invoice_data.status,
                "line_items_count": len(items)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

def main():
    """CLI interface for converting billing report to invoice."""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python billing_report_converter.py <report_path> <customer_email> [customer_name] [hourly_rate]")
        return
    
    report_path = sys.argv[1]
    customer_email = sys.argv[2]
    customer_name = sys.argv[3] if len(sys.argv) > 3 else None
    hourly_rate = float(sys.argv[4]) if len(sys.argv) > 4 else 40.0
    
    converter = BillingReportConverter()
    
    print(f"Converting billing report to Stripe invoice...")
    print(f"Report: {report_path}")
    print(f"Customer: {customer_email}")
    print(f"Rate: ${hourly_rate}/hour")
    
    result = converter.create_invoice_from_report(
        report_path=report_path,
        customer_email=customer_email,
        customer_name=customer_name,
        hourly_rate=hourly_rate,
        auto_send=True
    )
    
    if result["success"]:
        print(f"\n✅ Invoice created successfully!")
        print(f"Invoice Number: {result['invoice_number']}")
        print(f"Amount Due: ${result['amount_due']:.2f}")
        print(f"Line Items: {result['line_items_count']}")
        print(f"Payment Link: {result['payment_link']}")
    else:
        print(f"\n❌ Error: {result['error']}")

if __name__ == "__main__":
    main()