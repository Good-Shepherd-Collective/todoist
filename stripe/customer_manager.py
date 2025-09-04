"""Module for managing Stripe customers."""

from typing import Dict, List, Optional
from config import get_stripe_client

class CustomerManager:
    def __init__(self):
        self.stripe = get_stripe_client()
    
    def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Create a new Stripe customer.
        
        Args:
            email: Customer email
            name: Customer name
            phone: Customer phone number
            address: Customer address dict with 'line1', 'city', 'state', 'postal_code', 'country'
            metadata: Additional metadata to store with customer
            
        Returns:
            Dict with customer details
        """
        try:
            params = {"email": email}
            
            if name:
                params["name"] = name
            if phone:
                params["phone"] = phone
            if address:
                params["address"] = address
            if metadata:
                params["metadata"] = metadata
            
            customer = self.stripe.Customer.create(**params)
            
            return {
                "success": True,
                "customer_id": customer.id,
                "email": customer.email,
                "name": customer.name,
                "created": customer.created
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_or_create_customer(self, email: str, name: Optional[str] = None) -> Dict:
        """
        Get existing customer or create new one.
        
        Args:
            email: Customer email
            name: Customer name (used if creating new)
            
        Returns:
            Dict with customer details
        """
        try:
            # Search for existing customer
            customers = self.stripe.Customer.list(email=email, limit=1)
            
            if customers.data:
                customer = customers.data[0]
                return {
                    "success": True,
                    "customer_id": customer.id,
                    "email": customer.email,
                    "name": customer.name,
                    "existing": True
                }
            else:
                # Create new customer
                result = self.create_customer(email=email, name=name)
                if result["success"]:
                    result["existing"] = False
                return result
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_customer(
        self,
        customer_id: str,
        **kwargs
    ) -> Dict:
        """
        Update customer details.
        
        Args:
            customer_id: Stripe customer ID
            **kwargs: Fields to update (email, name, phone, address, metadata)
            
        Returns:
            Dict with updated customer details
        """
        try:
            customer = self.stripe.Customer.modify(customer_id, **kwargs)
            
            return {
                "success": True,
                "customer_id": customer.id,
                "email": customer.email,
                "name": customer.name
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_customer(self, customer_id: str) -> Dict:
        """
        Retrieve customer details.
        
        Args:
            customer_id: Stripe customer ID
            
        Returns:
            Dict with customer details
        """
        try:
            customer = self.stripe.Customer.retrieve(customer_id)
            
            return {
                "success": True,
                "customer_id": customer.id,
                "email": customer.email,
                "name": customer.name,
                "phone": customer.phone,
                "address": customer.address,
                "metadata": customer.metadata,
                "created": customer.created
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_customers(self, limit: int = 10, email: Optional[str] = None) -> List[Dict]:
        """
        List customers.
        
        Args:
            limit: Number of customers to return
            email: Optional email to filter by
            
        Returns:
            List of customer dictionaries
        """
        try:
            params = {"limit": limit}
            if email:
                params["email"] = email
            
            customers = self.stripe.Customer.list(**params)
            
            return [{
                "customer_id": cust.id,
                "email": cust.email,
                "name": cust.name,
                "created": cust.created
            } for cust in customers.data]
            
        except Exception as e:
            return []
    
    def delete_customer(self, customer_id: str) -> Dict:
        """
        Delete a customer.
        
        Args:
            customer_id: Stripe customer ID
            
        Returns:
            Dict with deletion status
        """
        try:
            deleted = self.stripe.Customer.delete(customer_id)
            
            return {
                "success": True,
                "deleted": deleted.deleted,
                "customer_id": deleted.id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }