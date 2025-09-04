"""Module for creating Stripe invoices with payment links."""

from typing import List, Dict, Optional
from config import get_stripe_client

class InvoiceCreator:
    def __init__(self):
        self.stripe = get_stripe_client()
    
    def create_invoice_with_link(
        self,
        customer_id: str,
        items: List[Dict],
        description: Optional[str] = None,
        due_days: int = 30,
        auto_send: bool = False,
        invoice_number: Optional[str] = None
    ) -> Dict:
        """
        Create a Stripe invoice with a payment link.
        
        Args:
            customer_id: Stripe customer ID
            items: List of invoice items with 'description', 'amount' (in cents), 'quantity'
            description: Optional invoice description
            due_days: Days until invoice is due (default 30)
            auto_send: Whether to automatically email the invoice
            
        Returns:
            Dict with invoice details including payment link
        """
        try:
            # First create invoice items (pending items that will be included in the invoice)
            for item in items:
                invoice_item_params = {
                    "customer": customer_id,
                    "description": item.get("description", "Service"),
                    "currency": item.get("currency", "usd")
                }
                
                # Use either unit_amount with quantity, or just amount
                if "quantity" in item and item["quantity"] != 1:
                    invoice_item_params["unit_amount"] = item["amount"]
                    invoice_item_params["quantity"] = item["quantity"]
                else:
                    invoice_item_params["amount"] = item["amount"]
                
                self.stripe.InvoiceItem.create(**invoice_item_params)
            
            # Create the invoice with pending_invoice_items_behavior="include"
            invoice_params = {
                "customer": customer_id,
                "description": description,
                "collection_method": "send_invoice",
                "days_until_due": due_days,
                "pending_invoice_items_behavior": "include",  # Include the pending items we just created
                "auto_advance": False  # Don't auto-finalize yet
            }
            
            # Add custom invoice number if provided
            if invoice_number:
                invoice_params["number"] = invoice_number
            
            invoice = self.stripe.Invoice.create(**invoice_params)
            
            # Finalize the invoice to generate payment link
            finalized_invoice = self.stripe.Invoice.finalize_invoice(invoice.id)
            
            # Send invoice if requested
            if auto_send:
                sent_invoice = self.stripe.Invoice.send_invoice(finalized_invoice.id)
                invoice_data = sent_invoice
            else:
                invoice_data = finalized_invoice
            
            return {
                "success": True,
                "invoice_id": invoice_data.id,
                "invoice_number": invoice_data.number,
                "amount_due": invoice_data.amount_due / 100,  # Convert to dollars
                "currency": invoice_data.currency,
                "payment_link": invoice_data.hosted_invoice_url,
                "pdf_link": invoice_data.invoice_pdf,
                "status": invoice_data.status,
                "customer_email": self._get_customer_email(customer_id)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_quick_invoice(
        self,
        customer_email: str,
        amount: float,
        description: str,
        customer_name: Optional[str] = None,
        invoice_number: Optional[str] = None
    ) -> Dict:
        """
        Quick method to create invoice with minimal parameters.
        
        Args:
            customer_email: Customer's email address
            amount: Amount in dollars (will be converted to cents)
            description: Description of the service/product
            customer_name: Optional customer name
            
        Returns:
            Dict with invoice details including payment link
        """
        try:
            # Check if customer exists, if not create one
            customers = self.stripe.Customer.list(email=customer_email, limit=1)
            
            if customers.data:
                customer = customers.data[0]
            else:
                customer = self.stripe.Customer.create(
                    email=customer_email,
                    name=customer_name
                )
            
            # Create invoice with single item
            items = [{
                "description": description,
                "amount": int(amount * 100),  # Convert to cents
                "quantity": 1
            }]
            
            return self.create_invoice_with_link(
                customer_id=customer.id,
                items=items,
                description=f"Invoice for {customer_email}",
                auto_send=True,
                invoice_number=invoice_number
            )
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_customer_email(self, customer_id: str) -> Optional[str]:
        """Get customer email from customer ID."""
        try:
            customer = self.stripe.Customer.retrieve(customer_id)
            return customer.email
        except:
            return None
    
    def list_invoices(self, customer_id: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """
        List recent invoices.
        
        Args:
            customer_id: Optional customer ID to filter by
            limit: Number of invoices to return
            
        Returns:
            List of invoice dictionaries
        """
        try:
            params = {"limit": limit}
            if customer_id:
                params["customer"] = customer_id
            
            invoices = self.stripe.Invoice.list(**params)
            
            return [{
                "id": inv.id,
                "number": inv.number,
                "customer_email": self._get_customer_email(inv.customer),
                "amount": inv.amount_due / 100,
                "status": inv.status,
                "payment_link": inv.hosted_invoice_url,
                "created": inv.created
            } for inv in invoices.data]
            
        except Exception as e:
            return []