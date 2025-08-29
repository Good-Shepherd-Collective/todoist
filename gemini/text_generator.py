"""
Text generation module using Gemini AI for billing reports
"""

import os
import json
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from .prompts import get_enhancement_prompt

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


class TextGenerator:
    """Generate enhanced billing text using Gemini AI"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_2_5_FLASH')
        if not self.api_key:
            raise ValueError("GEMINI_API_2_5_FLASH environment variable not set")
        
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
    
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
    
    def generate_billing_text(self, json_file_path: str, output_file: str = "billing_report.txt") -> str:
        """Generate a billing text file from JSON data"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            completed_tasks = data.get('completed_tasks', [])
            if not completed_tasks:
                return "No completed tasks found for billing."
            
            # Process tasks with AI enhancement
            print(f"🤖 Processing {len(completed_tasks)} tasks with Gemini AI...")
            enhanced_tasks = self.process_tasks(completed_tasks)
            
            # Generate the billing text
            text_content = self._format_billing_text(enhanced_tasks, data.get('metadata', {}))
            
            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            print(f"✅ Billing report generated: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"❌ Error generating billing text: {e}")
            return None
    
    def _format_billing_text(self, tasks: List[Dict[str, Any]], metadata: Dict[str, Any]) -> str:
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
Generated: {datetime.fromisoformat(export_date.replace('Z', '+00:00')).strftime('%B %d, %Y')}
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
            
            # Process tasks with AI enhancement
            print(f"🤖 Processing {len(completed_tasks)} tasks with Gemini AI for PDF...")
            enhanced_tasks = self.process_tasks(completed_tasks)
            
            # Generate the PDF
            self._create_pdf(enhanced_tasks, data.get('metadata', {}), output_file)
            
            print(f"✅ Billing PDF generated: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"❌ Error generating billing PDF: {e}")
            return None
    
    def _create_pdf(self, tasks: List[Dict[str, Any]], metadata: Dict[str, Any], output_file: str):
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
        story.append(Paragraph(f"Generated: {date_str}", normal_style))
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