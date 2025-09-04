#!/usr/bin/env python3

import os
import sys
import json
import csv
import requests
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

class AntiImperialistsAnalyzer:
    def __init__(self):
        self.api_token = os.getenv('TODOIST_API_TOKEN')
        self.headers = {'Authorization': f'Bearer {self.api_token}'}
        self.project_id = '6cjfRCgwFQWGmv3C'  # Anti-Imperialists project ID (v1 format)
        
    def get_completed_items(self):
        """Get completed items using API v1 completed tasks endpoint"""
        try:
            print(f"🔍 Fetching completed tasks from Todoist API v1...")
            print(f"   Project ID: {self.project_id}")
            
            # Get tasks completed in the last 90 days
            since_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%dT%H:%M:%S')
            until_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            
            response = requests.get(
                'https://api.todoist.com/api/v1/tasks/completed/by_completion_date',
                headers=self.headers,
                params={
                    'project_id': self.project_id,
                    'since': since_date,
                    'until': until_date,
                    'limit': 200
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                # v1 completed tasks endpoint returns 'items' key
                items = data.get('items', [])
                print(f"✅ API Response: Found {len(items)} completed items")
                if len(items) > 0:
                    print(f"   First item example: {items[0].get('content', 'No content')[:50]}...")
                return items
            else:
                print(f"❌ Failed to get completed items: {response.status_code}")
                print(f"Response: {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Error getting completed items: {e}")
            return []
    
    def get_active_tasks(self):
        """Get active tasks using API v1"""
        try:
            # Get all tasks and filter by project ID
            response = requests.get(
                'https://api.todoist.com/api/v1/tasks',
                headers=self.headers
            )
            
            if response.status_code == 200:
                response_data = response.json()
                # v1 API wraps results in 'results' key
                all_tasks = response_data.get('results', []) if isinstance(response_data, dict) else response_data
                
                # Filter tasks for this specific project
                tasks = [task for task in all_tasks if task.get('project_id') == self.project_id]
                print(f"✅ Found {len(tasks)} active tasks in project (from {len(all_tasks)} total)")
                return tasks
            else:
                print(f"❌ Failed to get active tasks: {response.status_code}")
                print(f"Response: {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Error getting active tasks: {e}")
            return []
    
    def enhance_description(self, task_content, labels=None):
        """Enhanced task categorization for organizing work"""
        labels = labels or []
        content_lower = task_content.lower()
        
        # Detailed categorization for anti-imperialist organizing
        category_keywords = {
            'Direct Action': ['protest', 'rally', 'march', 'demonstration', 'action', 'blockade', 'occupation', 'strike'],
            'Education': ['read', 'study', 'research', 'learn', 'book', 'article', 'theory', 'analysis', 'teach'],
            'Meeting/Communication': ['meet', 'call', 'discussion', 'zoom', 'conference', 'talk', 'phone'],
            'Content Creation': ['write', 'draft', 'edit', 'post', 'blog', 'statement', 'article', 'flyer'],
            'Organizing': ['organize', 'plan', 'coordinate', 'schedule', 'logistics', 'prepare'],
            'Outreach': ['email', 'contact', 'reach out', 'follow up', 'outreach', 'connect'],
            'Fundraising': ['fund', 'donate', 'money', 'budget', 'fundraiser', 'donation'],
            'Digital Work': ['website', 'social media', 'online', 'digital', 'internet', 'dns', 'substack']
        }
        
        category = 'Other'
        for cat, keywords in category_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                category = cat
                break
        
        # More specific task types
        task_type_map = {
            'meeting': 'Coalition Meeting',
            'zoom': 'Virtual Meeting',
            'call': 'Phone Call',
            'protest': 'Street Action',
            'rally': 'Mass Mobilization',
            'march': 'Public Demonstration',
            'research': 'Political Research',
            'read': 'Political Education',
            'study': 'Theory Study',
            'write': 'Content Creation',
            'draft': 'Document Preparation',
            'social media': 'Digital Organizing',
            'website': 'Digital Infrastructure',
            'dns': 'Technical Setup',
            'substack': 'Publishing Platform',
            'fundrais': 'Resource Development',
            'mutual aid': 'Community Support',
            'solidarity': 'Solidarity Work',
            'coalition': 'Alliance Building',
            'statement': 'Political Communication',
            'email': 'Digital Outreach',
            'organize': 'Community Organizing',
            'plan': 'Strategic Planning'
        }
        
        task_type = 'General Organizing'
        for keyword, t_type in task_type_map.items():
            if keyword in content_lower:
                task_type = t_type
                break
        
        # Focus areas for anti-imperialist work
        focus_keywords = {
            'Palestine Solidarity': ['palestine', 'gaza', 'israel', 'bds', 'apartheid', 'zionism', 'occupation'],
            'Anti-War': ['war', 'military', 'pentagon', 'intervention', 'nato', 'sanctions', 'imperialism'],
            'Racial Justice': ['blm', 'black lives', 'racism', 'police', 'white supremacy', 'racial'],
            'Climate Justice': ['climate', 'environment', 'pipeline', 'fossil', 'carbon', 'green'],
            'Labor Rights': ['labor', 'union', 'strike', 'worker', 'wages', 'workplace'],
            'Immigration Justice': ['immigration', 'migrant', 'refugee', 'ice', 'border', 'deportation'],
            'Housing Justice': ['housing', 'tenant', 'rent', 'eviction', 'gentrification', 'homeless'],
            'Indigenous Solidarity': ['indigenous', 'native', 'tribal', 'land back', 'sovereignty'],
            'Digital Organizing': ['website', 'online', 'digital', 'internet', 'social media', 'substack']
        }
        
        focus_area = 'General Anti-Imperialism'
        for focus, keywords in focus_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                focus_area = focus
                break
        
        # Priority assessment based on content
        priority_level = 'Normal'
        if any(word in content_lower for word in ['urgent', 'important', 'critical', 'deadline', 'asap']):
            priority_level = 'High'
        elif any(word in content_lower for word in ['soon', 'this week', 'follow up', 'check']):
            priority_level = 'Medium'
        
        return {
            'category': category,
            'task_type': task_type,
            'focus_area': focus_area,
            'priority': priority_level,
            'labels': labels
        }
    
    def estimate_duration(self, task_content, category):
        """Estimate task duration based on content and category"""
        duration_map = {
            'Direct Action': 4.0,
            'Education': 2.0,
            'Meeting/Communication': 1.5,
            'Content Creation': 3.0,
            'Organizing': 2.5,
            'Outreach': 1.0,
            'Fundraising': 1.5,
            'Digital Work': 2.0,
            'Other': 1.0
        }
        
        base = duration_map.get(category, 1.0)
        
        content_lower = task_content.lower()
        # Adjust based on complexity indicators
        if any(word in content_lower for word in ['quick', 'brief', 'short', 'simple']):
            base *= 0.5
        elif any(word in content_lower for word in ['major', 'comprehensive', 'deep', 'detailed', 'complex']):
            base *= 1.5
        elif any(word in content_lower for word in ['setup', 'install', 'configure']):
            base *= 1.2
        
        return round(base, 1)
    
    def calculate_actual_duration(self, completed_at, item_date):
        """Calculate actual duration if we have both timestamps"""
        try:
            if completed_at and item_date:
                completed_time = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                created_time = datetime.fromisoformat(item_date.replace('Z', '+00:00'))
                
                duration = completed_time - created_time
                hours = duration.total_seconds() / 3600
                
                # Only return if duration seems reasonable (less than 30 days)
                if 0 < hours < (24 * 30):
                    return round(hours, 1)
        except:
            pass
        return None
    
    def generate_report(self):
        """Generate comprehensive report with real completed tasks"""
        print("\n" + "="*85)
        print(" "*20 + "🌍 ANTI-IMPERIALISTS PROJECT ANALYSIS 🌍")
        print(" "*25 + "(Real Completed Tasks Data)")
        print("="*85)
        
        # Get completed items
        completed_items = self.get_completed_items()
        active_tasks = self.get_active_tasks()
        
        print(f"\n📊 PROJECT OVERVIEW: Anti-Imperialists")
        print("-"*85)
        print(f"  ✅ Completed tasks: {len(completed_items)}")
        print(f"  🔥 Active tasks: {len(active_tasks)}")
        print(f"  📈 Total tracked: {len(completed_items) + len(active_tasks)}")
        
        if not completed_items:
            print("\n⚠️  No completed tasks found")
            print("   This could indicate the project is new or tasks are in other projects")
            if active_tasks:
                self.display_active_tasks(active_tasks)
            return []
        
        # Process completed tasks - keep only Todoist data
        completed_analysis = []
        
        for item in completed_items:
            # Only keep actual Todoist fields
            task_data = {
                'id': item.get('id'),
                'content': item.get('content', 'No content'),
                'description': item.get('description', ''),
                'completed_at': item.get('completed_at'),
                'created_at': item.get('created_at'),
                'labels': item.get('labels', []),
                'project_id': item.get('project_id')
            }
            
            completed_analysis.append(task_data)
        
        # Sort by completion date (most recent first)
        completed_analysis.sort(
            key=lambda x: x['completed_at'] if x['completed_at'] else datetime.min, 
            reverse=True
        )
        
        # Display results
        self.display_completed_tasks(completed_analysis)
        
        if active_tasks:
            self.display_active_tasks(active_tasks)
        
        return completed_analysis
    
    def display_completed_tasks(self, tasks):
        """Display completed tasks"""
        print(f"\n📝 COMPLETED TASKS:")
        print("-"*85)
        
        for i, task in enumerate(tasks, 1):
            print(f"\n{i:2}. Task Name: {task.get('content', 'No content')}")
            print(f"     Description: {task.get('description', 'No description')}")
            print(f"     Labels: {', '.join(task.get('labels', [])) if task.get('labels') else 'None'}")
            
            if task.get('completed_at'):
                # Parse the date if it's a string
                if isinstance(task['completed_at'], str):
                    completed_date = datetime.fromisoformat(task['completed_at'].replace('Z', '+00:00'))
                else:
                    completed_date = task['completed_at']
                    
                days_ago = (datetime.now() - completed_date.replace(tzinfo=None)).days
                time_desc = f"{days_ago} days ago" if days_ago > 0 else "Today"
                print(f"     Status: ✅ Completed")
                print(f"     Completed on: {completed_date.strftime('%Y-%m-%d at %H:%M')} ({time_desc})")
            else:
                print(f"     Status: ✅ Completed (date not available)")
    
    def display_statistics(self, tasks):
        """Generate detailed productivity statistics"""
        print(f"\n📊 PRODUCTIVITY & ORGANIZING STATISTICS:")
        print("-"*85)
        
        total_estimated = sum(t['estimated_duration_hours'] for t in tasks)
        tasks_with_actual = [t for t in tasks if t['actual_duration_hours']]
        
        print(f"  ⏰ Total estimated organizing time: {total_estimated:.1f} hours")
        print(f"  💼 Equivalent full work days (8h): {total_estimated/8:.1f} days")
        print(f"  📅 Average per task: {total_estimated/len(tasks):.1f} hours")
        
        if tasks_with_actual:
            total_actual = sum(t['actual_duration_hours'] for t in tasks_with_actual)
            avg_actual = total_actual / len(tasks_with_actual)
            print(f"  ⏱️  Actual time tracked: {total_actual:.1f}h ({len(tasks_with_actual)} tasks)")
            print(f"  📈 Average actual duration: {avg_actual:.1f}h")
        
        # Category breakdown
        self.show_category_breakdown(tasks)
        
        # Focus area analysis
        self.show_focus_analysis(tasks)
        
        # Time trends if we have enough data
        if len(tasks) >= 5:
            self.show_time_trends(tasks)
    
    def show_category_breakdown(self, tasks):
        """Show detailed category breakdown"""
        print(f"\n📈 ORGANIZING CATEGORY BREAKDOWN:")
        print("-"*85)
        
        categories = defaultdict(int)
        cat_hours = defaultdict(float)
        
        for task in tasks:
            categories[task['category']] += 1
            cat_hours[task['category']] += task['estimated_duration_hours']
        
        for category in sorted(categories.keys(), key=lambda x: categories[x], reverse=True):
            count = categories[category]
            hours = cat_hours[category]
            pct = (count / len(tasks)) * 100
            avg_hours = hours / count
            
            print(f"  {category:20} | {count:2} tasks ({pct:4.1f}%) | {hours:5.1f}h total | {avg_hours:4.1f}h avg")
    
    def show_focus_analysis(self, tasks):
        """Show focus area analysis"""
        print(f"\n🌍 ANTI-IMPERIALIST FOCUS AREAS:")
        print("-"*85)
        
        focus_areas = defaultdict(int)
        focus_hours = defaultdict(float)
        
        for task in tasks:
            focus = task['focus_area']
            focus_areas[focus] += 1
            focus_hours[focus] += task['estimated_duration_hours']
        
        for focus in sorted(focus_areas.keys(), key=lambda x: focus_areas[x], reverse=True):
            count = focus_areas[focus]
            hours = focus_hours[focus]
            pct = (count / len(tasks)) * 100
            bar = "█" * int(pct / 2)
            
            print(f"  {focus:30} | {count:2} tasks ({pct:4.1f}%) | {hours:5.1f}h {bar}")
    
    def show_time_trends(self, tasks):
        """Show completion trends over time"""
        print(f"\n📅 COMPLETION TIMELINE:")
        print("-"*85)
        
        # Group by month for longer-term trends
        monthly_counts = defaultdict(int)
        monthly_hours = defaultdict(float)
        
        for task in tasks:
            if task['completed_at']:
                month_key = task['completed_at'].strftime('%Y-%m')
                monthly_counts[month_key] += 1
                monthly_hours[month_key] += task['estimated_duration_hours']
        
        # Show last 6 months or available data
        recent_months = sorted(monthly_counts.keys(), reverse=True)[:6]
        
        for month in recent_months:
            count = monthly_counts[month]
            hours = monthly_hours[month]
            month_name = datetime.strptime(month, '%Y-%m').strftime('%B %Y')
            bar = "█" * count
            
            print(f"  {month_name:15} | {count:2} tasks | {hours:5.1f}h {bar}")
    
    def display_active_tasks(self, tasks):
        """Display current active tasks"""
        print(f"\n🔥 CURRENT ACTIVE TASKS:")
        print("-"*85)
        
        for i, task in enumerate(tasks[:15], 1):
            # Priority indicators
            priority_map = {1: '🔴', 2: '🟠', 3: '🟡', 4: '⚪'}
            p_emoji = priority_map.get(task.get('priority', 1), '⚪')
            
            print(f"  {i:2}. {p_emoji} {task.get('content', 'No content')}")
            
            if task.get('description'):
                print(f"      Description: {task.get('description')}")
            
            if task.get('labels'):
                print(f"      Labels: {', '.join(task['labels'])}")
            print()
    
    def export_data(self, data, base_filename="anti_imperialists_complete"):
        """Export comprehensive data to CSV and JSON"""
        if not data:
            print("❌ No data to export")
            return
        
        # CSV Export - only Todoist fields
        csv_filename = f"{base_filename}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['id', 'content', 'description', 'completed_at', 'created_at', 'labels', 'project_id']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for task in data:
                row = {k: task.get(k, '') for k in fieldnames}
                if row['completed_at']:
                    row['completed_at'] = row['completed_at']
                if row['labels']:
                    row['labels'] = ', '.join(row['labels']) if isinstance(row['labels'], list) else row['labels']
                writer.writerow(row)
        
        # JSON Export - only Todoist data
        json_filename = f"{base_filename}.json"
        
        export_data = {
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'project_name': 'Anti-Imperialists',
                'project_id': self.project_id,
                'total_completed_tasks': len(data),
                'data_source': 'Todoist API v1'
            },
            'tasks': data
        }
        
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Data exported:")
        print(f"  • {csv_filename} - Spreadsheet format")
        print(f"  • {json_filename} - Structured data with metadata")

def main():
    analyzer = AntiImperialistsAnalyzer()
    
    # Get completed and active tasks
    completed_items = analyzer.get_completed_items()
    active_tasks = analyzer.get_active_tasks()
    
    # Create JSON output
    output = {
        'metadata': {
            'export_date': datetime.now().isoformat(),
            'project_name': 'Anti-Imperialists',
            'project_id': analyzer.project_id,
            'total_completed_tasks': len(completed_items),
            'total_active_tasks': len(active_tasks),
            'data_source': 'Todoist API v1'
        },
        'completed_tasks': [],
        'active_tasks': []
    }
    
    # Process completed tasks
    for item in completed_items:
        task_data = {
            'id': item.get('id'),
            'content': item.get('content', ''),
            'description': item.get('description', ''),
            'completed_at': item.get('completed_at'),
            'created_at': item.get('added_at'),
            'labels': item.get('labels', []),
            'project_id': item.get('project_id'),
            'priority': item.get('priority'),
            'billed': '',
            'paid': '',
            'billed_date': '',
            'billing_period_start': '',
            'billing_period_end': ''
        }
        output['completed_tasks'].append(task_data)
    
    # Process active tasks
    for task in active_tasks:
        task_data = {
            'id': task.get('id'),
            'content': task.get('content', ''),
            'description': task.get('description', ''),
            'created_at': task.get('added_at'),  # Active tasks use 'added_at' field
            'labels': task.get('labels', []),
            'project_id': task.get('project_id'),
            'priority': task.get('priority'),
            'billed': '',
            'paid': '',
            'billed_date': '',
            'billing_period_start': '',
            'billing_period_end': ''
        }
        output['active_tasks'].append(task_data)
    
    # Output as JSON to console
    json_output = json.dumps(output, indent=2, ensure_ascii=False)
    print(json_output)
    
    # Also save to file
    json_filename = "anti_imperialists_tasks.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        f.write(json_output)
    
    print(f"\n✅ JSON file saved as: {json_filename}", file=sys.stderr)

if __name__ == "__main__":
    main()