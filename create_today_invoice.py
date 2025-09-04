#!/usr/bin/env python3
"""
Create invoice for today's completed tasks - without Stripe integration
Uses the same structure as stripe/invoice_creator.py but generates local files
"""

import json
import os
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
import random
import string

class LocalInvoiceCreator:
    def __init__(self):
        self.invoice_base_dir = "invoices"
    
    def generate_invoice_number(self) -> str:
        """Generate a unique invoice number"""
        date_part = datetime.now().strftime("%Y%m")
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return f"INV-{date_part}-{random_part}"
    
    def estimate_task_duration(self, task: Dict) -> float:
        """Get actual task duration from labels, or estimate based on content"""
        # First, try to get actual time from labels
        labels = task.get('labels', [])
        for label in labels:
            label_lower = label.lower()
            if 'hour' in label_lower or 'min' in label_lower:
                # Parse time from label
                if '1.5 hour' in label_lower:
                    return 1.5
                elif 'hour' in label_lower:
                    try:
                        hours = float(label_lower.split()[0])
                        return hours
                    except:
                        pass
                elif 'min' in label_lower:
                    try:
                        minutes = float(label_lower.split()[0])
                        return minutes / 60.0
                    except:
                        pass
        
        # Fall back to estimation based on content
        content = task.get('content', '').lower()
        description = task.get('description', '').lower()
        
        # Default durations based on task type
        if any(word in content for word in ['quick', 'brief', 'check', 'minor']):
            return 0.25  # 15 minutes
        elif any(word in content for word in ['meeting', 'call', 'discussion', 'zoom']):
            return 1.0  # 1 hour
        elif any(word in content for word in ['research', 'write', 'draft', 'create', 'develop']):
            return 2.0  # 2 hours
        elif any(word in content for word in ['plan', 'organize', 'coordinate', 'schedule']):
            return 1.5  # 1.5 hours
        elif any(word in content for word in ['administration', 'admin', 'document']):
            return 0.5  # 30 minutes
        else:
            return 0.5  # 30 minutes default
    
    def create_invoice_with_tasks(
        self,
        customer_email: str,
        tasks: List[Dict],
        customer_name: Optional[str] = "AISC",
        hourly_rate: float = 40.0,
        due_days: int = 30,
        invoice_number: Optional[str] = None
    ) -> Dict:
        """
        Create an invoice from completed tasks.
        
        Args:
            customer_email: Customer's email address
            tasks: List of completed tasks from Todoist
            customer_name: Customer name (default: AISC)
            hourly_rate: Hourly rate in dollars
            due_days: Days until invoice is due (default 30)
            invoice_number: Optional custom invoice number
            
        Returns:
            Dict with invoice details
        """
        try:
            # Generate invoice number if not provided
            if not invoice_number:
                invoice_number = self.generate_invoice_number()
            
            # Process tasks and calculate totals
            invoice_items = []
            total_hours = 0
            
            for task in tasks:
                duration_hours = self.estimate_task_duration(task)
                total_hours += duration_hours
                
                # Format duration for display
                hours = int(duration_hours)
                minutes = int((duration_hours - hours) * 60)
                if hours > 0:
                    duration_str = f"{hours}h"
                    if minutes > 0:
                        duration_str += f" {minutes}m"
                else:
                    duration_str = f"{minutes}m"
                
                # Get or generate description
                description = task.get('description', '')
                if not description:
                    description = f"Completed task: {task.get('content', 'Task')}"
                
                invoice_items.append({
                    "content": task.get('content', 'No title'),
                    "description": description,
                    "duration_hours": duration_hours,
                    "duration_str": duration_str,
                    "amount": duration_hours * hourly_rate,
                    "completed_at": task.get('completed_at', '')
                })
            
            total_amount = total_hours * hourly_rate
            
            # Determine invoice directory (next available number)
            invoice_num = 1
            while os.path.exists(os.path.join(self.invoice_base_dir, str(invoice_num))):
                invoice_num += 1
            
            invoice_dir = os.path.join(self.invoice_base_dir, str(invoice_num))
            os.makedirs(invoice_dir, exist_ok=True)
            
            # Create invoice files
            self._create_text_invoice(
                invoice_dir, invoice_number, customer_name, customer_email,
                invoice_items, total_hours, hourly_rate, total_amount, due_days
            )
            
            self._create_pdf_invoice(
                invoice_dir, invoice_number, customer_name, customer_email,
                invoice_items, total_hours, hourly_rate, total_amount, due_days
            )
            
            # Create notes file
            notes_file = os.path.join(invoice_dir, "notes.txt")
            with open(notes_file, 'w') as f:
                f.write(f"Invoice generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Invoice number: {invoice_number}\n")
                f.write(f"Customer: {customer_name}\n")
                f.write(f"Tasks from: {date.today().strftime('%Y-%m-%d')}\n")
                f.write(f"Total tasks: {len(tasks)}\n")
                f.write(f"Total hours: {total_hours:.2f}\n")
                f.write(f"Hourly rate: ${hourly_rate:.2f}\n")
                f.write(f"Total amount: ${total_amount:.2f}\n")
            
            return {
                "success": True,
                "invoice_id": invoice_number,
                "invoice_number": invoice_number,
                "invoice_dir": invoice_dir,
                "amount_due": total_amount,
                "total_hours": total_hours,
                "currency": "usd",
                "status": "draft",
                "customer_email": customer_email,
                "customer_name": customer_name,
                "pdf_file": os.path.join(invoice_dir, "billing_report.pdf"),
                "text_file": os.path.join(invoice_dir, "billing_report.txt")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_text_invoice(
        self, invoice_dir: str, invoice_number: str, customer_name: str,
        customer_email: str, items: List[Dict], total_hours: float,
        hourly_rate: float, total_amount: float, due_days: int
    ):
        """Create text version of the invoice"""
        text_file = os.path.join(invoice_dir, "billing_report.txt")
        
        with open(text_file, 'w') as f:
            f.write(f"\nBILLING REPORT: {customer_name}\n")
            f.write(f"Invoice Number: {invoice_number}\n")
            f.write(f"Generated: {datetime.now().strftime('%B %d, %Y')}\n")
            f.write(f"Billing Period: {date.today().strftime('%Y-%m-%d')}\n")
            f.write(f"Due Date: {(date.today() + timedelta(days=due_days)).strftime('%Y-%m-%d')}\n")
            f.write(f"Total Completed Tasks: {len(items)}\n")
            f.write("\n" + "="*60 + "\n\n")
            f.write("COMPLETED WORK SUMMARY:\n\n")
            
            for i, item in enumerate(items, 1):
                f.write(f"{i}. {item['content']}\n")
                f.write(f"   Duration: {item['duration_str']}\n")
                
                if item['completed_at']:
                    completed_date = datetime.fromisoformat(item['completed_at'].replace('Z', '+00:00'))
                    f.write(f"   Completed: {completed_date.strftime('%m/%d/%Y')}\n")
                
                f.write("   \n")
                f.write(f"   Description: {item['description']}\n")
                f.write("   \n")
                f.write("-"*40 + "\n\n")
            
            f.write("\nSUMMARY:\n")
            f.write(f"- Total tasks completed: {len(items)}\n")
            f.write(f"- Project: {customer_name}\n")
            f.write(f"- Total hours: {total_hours:.2f}\n")
            f.write(f"- Rate: ${hourly_rate:.2f}/hr\n")
            f.write(f"- Amount due: ${total_amount:.2f}\n")
            f.write(f"- Report generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n")
            f.write("\nFor questions about this billing report, please contact Cody\n")
    
    def _create_pdf_invoice(
        self, invoice_dir: str, invoice_number: str, customer_name: str,
        customer_email: str, items: List[Dict], total_hours: float,
        hourly_rate: float, total_amount: float, due_days: int
    ):
        """Create PDF version of the invoice"""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_RIGHT
            from datetime import timedelta
            
            pdf_file = os.path.join(invoice_dir, "billing_report.pdf")
            doc = SimpleDocTemplate(pdf_file, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#2E4053'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            header_style = ParagraphStyle(
                'Header',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#34495E'),
                spaceAfter=12
            )
            
            # Title
            story.append(Paragraph(f"BILLING REPORT: {customer_name}", title_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Invoice details
            invoice_date = datetime.now().strftime("%B %d, %Y")
            billing_period = date.today().strftime("%Y-%m-%d")
            due_date = (date.today() + timedelta(days=due_days)).strftime("%Y-%m-%d")
            
            details = [
                ['Invoice Number:', invoice_number],
                ['Generated:', invoice_date],
                ['Billing Period:', billing_period],
                ['Due Date:', due_date],
                ['Total Completed Tasks:', str(len(items))],
            ]
            
            details_table = Table(details, colWidths=[2*inch, 4*inch])
            details_table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#5D6D7E')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(details_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Separator
            story.append(Paragraph("="*70, styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
            
            # Tasks section
            story.append(Paragraph("COMPLETED WORK SUMMARY:", header_style))
            story.append(Spacer(1, 0.2*inch))
            
            for i, item in enumerate(items, 1):
                # Task title
                task_title = f"{i}. {item['content']}"
                story.append(Paragraph(task_title, styles['Heading3']))
                
                # Duration and completion date
                info_text = f"Duration: {item['duration_str']}"
                if item['completed_at']:
                    completed_date = datetime.fromisoformat(item['completed_at'].replace('Z', '+00:00'))
                    info_text += f"<br/>Completed: {completed_date.strftime('%m/%d/%Y')}"
                
                story.append(Paragraph(info_text, styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
                
                # Description
                desc_style = ParagraphStyle(
                    'Description',
                    parent=styles['Normal'],
                    fontSize=10,
                    textColor=colors.HexColor('#5D6D7E'),
                    leftIndent=20
                )
                story.append(Paragraph(f"Description: {item['description']}", desc_style))
                story.append(Spacer(1, 0.2*inch))
                
                # Separator between tasks
                story.append(Paragraph("-"*40, styles['Normal']))
                story.append(Spacer(1, 0.2*inch))
            
            # Summary section
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph("SUMMARY:", header_style))
            
            summary_data = [
                ['Total tasks completed:', str(len(items))],
                ['Project:', customer_name],
                ['Total hours:', f"{total_hours:.2f}"],
                ['Rate:', f"${hourly_rate:.2f}/hr"],
                ['Amount due:', f"${total_amount:.2f}"],
                ['Report generated:', datetime.now().strftime("%B %d, %Y at %I:%M %p")]
            ]
            
            summary_table = Table(summary_data, colWidths=[2*inch, 3*inch])
            summary_table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#34495E')),
                ('FONTWEIGHT', (-1, -1), (-1, -1), 'BOLD'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(summary_table)
            
            story.append(Spacer(1, 0.5*inch))
            story.append(Paragraph("For questions about this billing report, please contact Cody", styles['Normal']))
            
            # Build PDF
            doc.build(story)
            
        except ImportError:
            # If reportlab is not installed, skip PDF creation
            print("Note: reportlab not installed, skipping PDF generation")
            pass

def main():
    # Load Todoist data
    with open('todoist_output.json', 'r') as f:
        data = json.load(f)
    
    # Get today's date
    today = date.today()
    
    # Filter completed tasks for today
    today_tasks = []
    for task in data['completed_tasks']:
        if task['completed_at']:
            completed_date = datetime.fromisoformat(task['completed_at'].replace('Z', '+00:00')).date()
            if completed_date == today:
                today_tasks.append(task)
    
    if not today_tasks:
        print(f"No tasks completed today ({today.strftime('%B %d, %Y')})")
        return
    
    print(f"Found {len(today_tasks)} tasks completed today:")
    for i, task in enumerate(today_tasks, 1):
        print(f"  {i}. {task['content']}")
    
    # Create invoice
    invoice_creator = LocalInvoiceCreator()
    result = invoice_creator.create_invoice_with_tasks(
        customer_email="client@example.com",  # You can update this
        tasks=today_tasks,
        customer_name="AISC",
        hourly_rate=40.0,
        due_days=30
    )
    
    if result['success']:
        print(f"\n✅ Invoice created successfully!")
        print(f"   Invoice Number: {result['invoice_number']}")
        print(f"   Location: {result['invoice_dir']}")
        print(f"   Total Hours: {result['total_hours']:.2f}")
        print(f"   Amount Due: ${result['amount_due']:.2f}")
        print(f"   Files created:")
        print(f"     - {result['text_file']}")
        if 'pdf_file' in result:
            print(f"     - {result['pdf_file']}")
    else:
        print(f"❌ Error creating invoice: {result['error']}")

if __name__ == "__main__":
    main()