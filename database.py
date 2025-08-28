from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

Base = declarative_base()

class CompletedTask(Base):
    __tablename__ = 'completed_tasks'
    
    id = Column(Integer, primary_key=True)
    task_id = Column(String(50), unique=True, nullable=False)
    content = Column(Text, nullable=False)
    completed_at = Column(DateTime, nullable=False)
    project_id = Column(String(50))
    project_name = Column(String(200))
    labels = Column(JSON)
    priority = Column(Integer)
    description = Column(Text)
    synced_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<CompletedTask(task_id='{self.task_id}', content='{self.content[:30]}...')>"

class Database:
    def __init__(self, db_url='sqlite:///todoist_sync.db'):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        logger.info(f"Database initialized: {db_url}")
        
    def task_exists(self, task_id):
        return self.session.query(CompletedTask).filter_by(task_id=task_id).first() is not None
        
    def save_task(self, task_data, project_name=None):
        if self.task_exists(task_data['task_id']):
            logger.debug(f"Task {task_data['task_id']} already exists in database")
            return False
            
        task = CompletedTask(
            task_id=task_data['task_id'],
            content=task_data['content'],
            completed_at=task_data['completed_at'],
            project_id=task_data.get('project_id'),
            project_name=project_name,
            labels=json.dumps(task_data.get('labels', [])),
            priority=task_data.get('priority', 1),
            description=task_data.get('description', '')
        )
        
        self.session.add(task)
        self.session.commit()
        logger.info(f"Saved task: {task_data['content'][:50]}...")
        return True
        
    def get_latest_sync_time(self):
        latest = self.session.query(CompletedTask).order_by(
            CompletedTask.completed_at.desc()
        ).first()
        
        if latest:
            return latest.completed_at
        return None
        
    def get_tasks_count(self):
        return self.session.query(CompletedTask).count()
        
    def close(self):
        self.session.close()