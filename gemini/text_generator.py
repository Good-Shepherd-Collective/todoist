"""
Text generation module using Gemini AI for billing reports
"""

import os
import json
import requests
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
try:
    from .prompts import get_enhancement_prompt
except ImportError:
    from prompts import get_enhancement_prompt

# Load environment variables
load_dotenv()

# PDF imports - with fallback if not installed
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# Turso database imports
try:
    from ..turso_db.connection import TursoConnection
    TURSO_AVAILABLE = True
except ImportError:
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from turso_db.connection import TursoConnection
        TURSO_AVAILABLE = True
    except ImportError:
        TURSO_AVAILABLE = False


class TextGenerator:
    """Generate enhanced billing text using Gemini AI"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_2_5_FLASH')
        if not self.api_key:
            raise ValueError("GEMINI_API_2_5_FLASH environment variable not set")
        
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
        self.db = None
    
    def enhance_description(self, title: str, description: str) -> str:
        """Enhance a task description using Gemini AI"""
        try:
            prompt = get_enhancement_prompt(title, description)
            
            headers = {
                'Content-Type': 'application/json',
            }
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.3,
                    "topK": 32,
                    "topP": 1,
                    "maxOutputTokens": 200,
                }
            }
            
            response = requests.post(
                f"{self.base_url}?key={self.api_key}",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    enhanced_text = result['candidates'][0]['content']['parts'][0]['text']
                    return enhanced_text.strip()
                else:
                    print(f"⚠️  No enhancement available for: {title}")
                    return description
            else:
                print(f"⚠️  API Error ({response.status_code}): {response.text}")
                return description
                
        except Exception as e:
            print(f"⚠️  Error enhancing description for '{title}': {e}")
            return description
    
    def process_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process all tasks and enhance their descriptions"""
        enhanced_tasks = []
        
        for task in tasks:
            title = task.get('content', '')
            description = task.get('description', '')
            
            if title:
                print(f"🔄 Enhancing: {title[:50]}...")
                enhanced_description = self.enhance_description(title, description)
                
                enhanced_task = task.copy()
                enhanced_task['enhanced_description'] = enhanced_description
                enhanced_tasks.append(enhanced_task)
            else:
                enhanced_tasks.append(task)
        
        return enhanced_tasks
    
    def format_duration(self, labels: List[str]) -> str:
        """Extract duration from labels"""
        for label in labels:
            if 'mins' in label or 'min' in label:
                return label
        return "Time not specified"
    
    def extract_hours_from_labels(self, labels: List[str]) -> float:
        """Extract hours from time labels (e.g., '45 mins' -> 0.75)"""
        for label in labels:
            if 'mins' in label or 'min' in label:
                # Extract number from label like "15 mins" or "45 min"
                import re
                match = re.search(r'(\d+)', label)
                if match:
                    minutes = int(match.group(1))
                    return round(minutes / 60.0, 2)  # Convert to hours
        return 0.0
    
    def generate_invoice_number(self) -> str:
        """Generate a unique invoice number based on current date and UUID"""
        current_date = datetime.now()
        date_prefix = current_date.strftime("%Y%m")
        unique_suffix = str(uuid.uuid4())[:8].upper()
        return f"INV-{date_prefix}-{unique_suffix}"
    
    def get_billing_period(self) -> str:
        """Get billing period as current month in YYYY-MM format"""
        return datetime.now().strftime("%Y-%m")
    
    def get_billing_date(self) -> str:
        """Get current date as billing date in ISO format"""
        return datetime.now().isoformat()
    
    def init_database(self) -> bool:
        """Initialize database connection and create tasks table if needed"""
        if not TURSO_AVAILABLE:
            print("⚠️  Turso database not available. Install turso_db module.")
            return False
        
        try:
            self.db = TursoConnection()
            if not self.db.connect():
                return False
            
            # Create tasks table if it doesn't exist
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                content TEXT,
                description TEXT,
                completed_at TEXT,
                created_at TEXT,
                labels TEXT,
                project_id TEXT,
                priority INTEGER,
                billed TEXT,
                paid TEXT,
                billed_date TEXT,
                billing_period_start TEXT,
                billing_period_end TEXT,
                invoice_number TEXT,
                enhanced_description TEXT,
                uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            return self.db.execute_command(create_table_sql)
            
        except Exception as e:
            print(f"❌ Failed to initialize database: {e}")
            return False
    
    def upload_tasks_to_db(self, tasks: List[Dict[str, Any]], invoice_number: str) -> bool:
        """Upload tasks to Turso database with billing information"""
        if not self.db and not self.init_database():
            return False
        
        try:
            billing_date = self.get_billing_date()
            billing_period = self.get_billing_period()
            
            for task in tasks:
                # Prepare task data for database
                task_id = str(task.get('id', ''))
                labels_str = ', '.join(task.get('labels', [])) if task.get('labels') else ''
                
                insert_sql = """
                INSERT OR REPLACE INTO tasks (
                    id, content, description, completed_at, created_at, labels,
                    project_id, priority, billed, paid, billed_date,
                    billing_period_start, billing_period_end, invoice_number,
                    enhanced_description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                params = (
                    task_id,
                    task.get('content', ''),
                    task.get('description', ''),
                    task.get('completed_at', ''),
                    task.get('created_at', ''),
                    labels_str,
                    task.get('project_id', ''),
                    task.get('priority', 0),
                    'yes',  # Mark as billed
                    '',     # Not paid yet
                    billing_date,
                    billing_period,
                    billing_period,  # billing_period_end same as start for monthly billing
                    invoice_number,
                    task.get('enhanced_description', task.get('description', ''))
                )
                
                if not self.db.execute_command(insert_sql, params):
                    print(f"⚠️  Failed to upload task: {task.get('content', 'Unknown')}")
                    return False
            
            print(f"✅ Successfully uploaded {len(tasks)} tasks to database")
            return True
            
        except Exception as e:
            print(f"❌ Error uploading tasks to database: {e}")
            return False
    
    def generate_billing_text(self, json_file_path: str, output_file: str = "billing_report.txt") -> str:
        """Generate a billing text file from JSON data"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            completed_tasks = data.get('completed_tasks', [])
            if not completed_tasks:
                return "No completed tasks found for billing."
            
            # Generate invoice number
            invoice_number = self.generate_invoice_number()
            print(f"📋 Generated invoice number: {invoice_number}")
            
            # Process tasks with AI enhancement
            print(f"🤖 Processing {len(completed_tasks)} tasks with Gemini AI...")
            enhanced_tasks = self.process_tasks(completed_tasks)
            
            # Upload tasks to database
            print(f"💾 Uploading tasks to Turso database...")
            self.upload_tasks_to_db(enhanced_tasks, invoice_number)
            
            # Generate the billing text
            text_content = self._format_billing_text(enhanced_tasks, data.get('metadata', {}), invoice_number)
            
            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            print(f"✅ Billing report generated: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"❌ Error generating billing text: {e}")
            return None
    
    def _format_billing_text(self, tasks: List[Dict[str, Any]], metadata: Dict[str, Any], invoice_number: str) -> str:
        """Format the enhanced tasks into a billing-friendly text"""
        
        # Header - always use AISC as project name
        project_name = "AISC"
        export_date = metadata.get('export_date', datetime.now().isoformat())
        total_tasks = len(tasks)
        
        # Calculate total hours and amount
        total_hours = sum(self.extract_hours_from_labels(task.get('labels', [])) for task in tasks)
        hourly_rate = float(os.getenv('HOURLY_RATE', 40))
        total_amount = total_hours * hourly_rate
        
        content = f"""
BILLING REPORT: {project_name}
Invoice Number: {invoice_number}
Generated: {datetime.fromisoformat(export_date.replace('Z', '+00:00')).strftime('%B %d, %Y')}
Billing Period: {self.get_billing_period()}
Total Completed Tasks: {total_tasks}

{'='*60}

COMPLETED WORK SUMMARY:
"""
        
        # Task details
        for i, task in enumerate(tasks, 1):
            title = task.get('content', 'Untitled Task')
            enhanced_desc = task.get('enhanced_description', task.get('description', ''))
            duration = self.format_duration(task.get('labels', []))
            completed_date = task.get('completed_at', '')
            
            if completed_date:
                date_obj = datetime.fromisoformat(completed_date.replace('Z', '+00:00'))
                formatted_date = date_obj.strftime('%m/%d/%Y')
            else:
                formatted_date = "Date not available"
            
            content += f"""
{i}. {title}
   Duration: {duration}
   Completed: {formatted_date}
   
   Description: {enhanced_desc}
   
{'-'*40}
"""
        
        # Footer
        content += f"""

SUMMARY:
- Total tasks completed: {total_tasks}
- Project: {project_name}
- Total hours: {total_hours:.2f}
- Amount due: ${total_amount:.2f}
- Report generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

For questions about this billing report, please contact the project administrator.
"""
        
        return content
    
    def generate_billing_pdf(self, json_file_path: str, output_file: str = "billing_report.pdf") -> Optional[str]:
        """Generate a billing PDF file from JSON data"""
        if not PDF_AVAILABLE:
            print("❌ PDF generation requires reportlab. Install with: pip install reportlab")
            return None
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            completed_tasks = data.get('completed_tasks', [])
            if not completed_tasks:
                print("No completed tasks found for billing.")
                return None
            
            # Generate invoice number
            invoice_number = self.generate_invoice_number()
            print(f"📋 Generated invoice number: {invoice_number}")
            
            # Process tasks with AI enhancement
            print(f"🤖 Processing {len(completed_tasks)} tasks with Gemini AI for PDF...")
            enhanced_tasks = self.process_tasks(completed_tasks)
            
            # Upload tasks to database
            print(f"💾 Uploading tasks to Turso database...")
            self.upload_tasks_to_db(enhanced_tasks, invoice_number)
            
            # Generate the PDF
            self._create_pdf(enhanced_tasks, data.get('metadata', {}), output_file, invoice_number)
            
            print(f"✅ Billing PDF generated: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"❌ Error generating billing PDF: {e}")
            return None
    
    def _create_pdf(self, tasks: List[Dict[str, Any]], metadata: Dict[str, Any], output_file: str, invoice_number: str):
        """Create PDF document from enhanced tasks"""
        doc = SimpleDocTemplate(output_file, pagesize=letter, 
                              rightMargin=72, leftMargin=72, 
                              topMargin=72, bottomMargin=18)
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.HexColor('#2c3e50')
        )
        
        normal_style = styles['Normal']
        
        # Calculate totals
        project_name = "AISC"
        export_date = metadata.get('export_date', datetime.now().isoformat())
        total_tasks = len(tasks)
        total_hours = sum(self.extract_hours_from_labels(task.get('labels', [])) for task in tasks)
        hourly_rate = float(os.getenv('HOURLY_RATE', 40))
        total_amount = total_hours * hourly_rate
        
        # Build story
        story = []
        
        # Title
        story.append(Paragraph(f"BILLING REPORT: {project_name}", title_style))
        story.append(Spacer(1, 12))
        
        # Header info
        date_str = datetime.fromisoformat(export_date.replace('Z', '+00:00')).strftime('%B %d, %Y')
        story.append(Paragraph(f"Invoice Number: {invoice_number}", normal_style))
        story.append(Paragraph(f"Generated: {date_str}", normal_style))
        story.append(Paragraph(f"Billing Period: {self.get_billing_period()}", normal_style))
        story.append(Paragraph(f"Total Completed Tasks: {total_tasks}", normal_style))
        story.append(Spacer(1, 24))
        
        # Work summary header
        story.append(Paragraph("COMPLETED WORK SUMMARY", heading_style))
        story.append(Spacer(1, 12))
        
        # Tasks
        for i, task in enumerate(tasks, 1):
            title = task.get('content', 'Untitled Task')
            enhanced_desc = task.get('enhanced_description', task.get('description', ''))
            duration = self.format_duration(task.get('labels', []))
            completed_date = task.get('completed_at', '')
            
            if completed_date:
                date_obj = datetime.fromisoformat(completed_date.replace('Z', '+00:00'))
                formatted_date = date_obj.strftime('%m/%d/%Y')
            else:
                formatted_date = "Date not available"
            
            # Task header
            task_title = f"{i}. {title}"
            story.append(Paragraph(task_title, ParagraphStyle('TaskTitle', 
                parent=normal_style, fontSize=11, textColor=colors.HexColor('#34495e'), 
                spaceAfter=6, leftIndent=0)))
            
            # Task details
            story.append(Paragraph(f"Duration: {duration}", normal_style))
            story.append(Paragraph(f"Completed: {formatted_date}", normal_style))
            story.append(Spacer(1, 6))
            
            # Description
            story.append(Paragraph(f"Description: {enhanced_desc}", normal_style))
            story.append(Spacer(1, 18))
        
        # Summary section
        story.append(Spacer(1, 12))
        story.append(Paragraph("SUMMARY", heading_style))
        
        # Summary table
        summary_data = [
            ['Total tasks completed:', str(total_tasks)],
            ['Project:', project_name],
            ['Total hours:', f"{total_hours:.2f}"],
            ['Amount due:', f"${total_amount:.2f}"],
            ['Report generated:', datetime.now().strftime('%B %d, %Y at %I:%M %p')]
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 24))
        
        # Footer
        story.append(Paragraph("For questions about this billing report, please contact the project administrator.", 
                             ParagraphStyle('Footer', parent=normal_style, fontSize=9, 
                                          textColor=colors.HexColor('#7f8c8d'))))
        
        # Build PDF
        doc.build(story)


def generate_billing_text(json_file_path: str, output_file: str = "billing_report.txt") -> Optional[str]:
    """Convenience function to generate billing text"""
    try:
        generator = TextGenerator()
        return generator.generate_billing_text(json_file_path, output_file)
    except Exception as e:
        print(f"❌ Failed to generate billing text: {e}")
        return None


def generate_billing_pdf(json_file_path: str, output_file: str = "billing_report.pdf") -> Optional[str]:
    """Convenience function to generate billing PDF"""
    try:
        generator = TextGenerator()
        return generator.generate_billing_pdf(json_file_path, output_file)
    except Exception as e:
        print(f"❌ Failed to generate billing PDF: {e}")
        return None


if __name__ == "__main__":
    import sys
    
    # Default JSON file path
    json_file = "anti_imperialists_tasks.json"
    
    # Check if a JSON file path was provided
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    
    # Check if file exists
    if not os.path.exists(json_file):
        print(f"❌ Error: File '{json_file}' not found")
        print("Usage: python text_generator.py [json_file_path]")
        sys.exit(1)
    
    print(f"📄 Processing file: {json_file}")
    print("-" * 60)
    
    # Generate billing text
    text_output = generate_billing_text(json_file)
    if text_output:
        print(f"✅ Text report saved: {text_output}")
    
    # Generate billing PDF
    pdf_output = generate_billing_pdf(json_file)
    if pdf_output:
        print(f"✅ PDF report saved: {pdf_output}")