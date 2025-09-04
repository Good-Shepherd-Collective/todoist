"""Stripe configuration module."""

import os
import stripe
from dotenv import load_dotenv

load_dotenv()

# Use test keys by default for safety
stripe.api_key = os.getenv("STRIPE_SECRET_TEST")

if not stripe.api_key:
    raise ValueError("STRIPE_SECRET_TEST key not found in .env file")

def get_stripe_client():
    """Return configured Stripe client."""
    return stripe