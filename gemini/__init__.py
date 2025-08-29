"""
Gemini AI text generation module for billing reports
"""

from .text_generator import TextGenerator, generate_billing_text, generate_billing_pdf

__all__ = ['TextGenerator', 'generate_billing_text', 'generate_billing_pdf']