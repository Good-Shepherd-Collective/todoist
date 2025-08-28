from todoist_api_python.api import TodoistAPI
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class TodoistClient:
    def __init__(self, api_token):
        self.api = TodoistAPI(api_token)
        
    def get_completed_tasks(self, since=None):
        try:
            completed_tasks = []
            
            activity = self.api.get_activity(
                object_type='item',
                event_type='completed',
                limit=100,
                since=since if since else datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            )
            
            for event in activity.events:
                task_data = {
                    'task_id': event.object_id,
                    'content': event.extra_data.get('content', ''),
                    'completed_at': event.event_date,
                    'project_id': event.extra_data.get('project_id'),
                    'labels': event.extra_data.get('labels', []),
                    'priority': event.extra_data.get('priority', 1),
                    'description': event.extra_data.get('description', '')
                }
                completed_tasks.append(task_data)
                
            logger.info(f"Retrieved {len(completed_tasks)} completed tasks")
            return completed_tasks
            
        except Exception as e:
            logger.error(f"Error fetching completed tasks: {e}")
            raise
            
    def get_project_name(self, project_id):
        if not project_id:
            return 'Inbox'
        try:
            project = self.api.get_project(project_id)
            return project.name
        except:
            return 'Unknown Project'