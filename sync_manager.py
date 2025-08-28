from todoist_client import TodoistClient
from database import Database
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SyncManager:
    def __init__(self, api_token, db_url='sqlite:///todoist_sync.db'):
        self.todoist = TodoistClient(api_token)
        self.db = Database(db_url)
        
    def sync_completed_tasks(self, lookback_days=7):
        try:
            latest_sync = self.db.get_latest_sync_time()
            
            if latest_sync:
                since = latest_sync - timedelta(hours=1)
                logger.info(f"Syncing tasks completed since {since}")
            else:
                since = datetime.utcnow() - timedelta(days=lookback_days)
                logger.info(f"Initial sync - looking back {lookback_days} days")
                
            completed_tasks = self.todoist.get_completed_tasks(since=since)
            
            new_tasks = 0
            for task in completed_tasks:
                project_name = self.todoist.get_project_name(task.get('project_id'))
                if self.db.save_task(task, project_name):
                    new_tasks += 1
                    
            logger.info(f"Sync complete. Added {new_tasks} new tasks.")
            logger.info(f"Total tasks in database: {self.db.get_tasks_count()}")
            
            return {
                'new_tasks': new_tasks,
                'total_tasks': self.db.get_tasks_count(),
                'sync_time': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            raise
            
    def get_stats(self):
        return {
            'total_tasks': self.db.get_tasks_count(),
            'latest_sync': self.db.get_latest_sync_time()
        }
        
    def close(self):
        self.db.close()