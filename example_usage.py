#!/usr/bin/env python3
"""
Example usage of the Gemini text generation for billing
"""

from gemini import generate_billing_text

def main():
    """Example of how to use the billing text generator"""
    
    # Generate billing text from the existing JSON file
    json_file = "anti_imperialists_tasks.json"
    output_file = "billing_report.txt"
    
    print("🤖 Generating AI-enhanced billing report...")
    print(f"📄 Input: {json_file}")
    print(f"📝 Output: {output_file}")
    print("-" * 50)
    
    result = generate_billing_text(json_file, output_file)
    
    if result:
        print(f"\n✅ Success! Billing report saved to: {result}")
        print("\n📧 This file is ready to be sent for billing purposes.")
    else:
        print("\n❌ Failed to generate billing report.")

if __name__ == "__main__":
    main()