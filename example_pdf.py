#!/usr/bin/env python3
"""
Example usage of PDF billing generation
"""

from gemini import generate_billing_pdf, generate_billing_text

def main():
    """Example of how to use both text and PDF billing generators"""
    
    json_file = "anti_imperialists_tasks.json"
    
    print("🤖 Generating billing reports...")
    print(f"📄 Input: {json_file}")
    print("-" * 50)
    
    # Generate text version
    print("📝 Generating text version...")
    text_file = generate_billing_text(json_file, "billing_report.txt")
    
    # Generate PDF version  
    print("\n📄 Generating PDF version...")
    pdf_file = generate_billing_pdf(json_file, "billing_report.pdf")
    
    print("\n✅ Results:")
    if text_file:
        print(f"   📝 Text: {text_file}")
    if pdf_file:
        print(f"   📄 PDF:  {pdf_file}")
    
    if text_file or pdf_file:
        print("\n📧 Files are ready for billing purposes!")
    else:
        print("\n❌ Failed to generate billing reports.")

if __name__ == "__main__":
    main()