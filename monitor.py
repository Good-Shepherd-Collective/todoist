#!/usr/bin/env python3

import os
import sys
import time
import schedule
import logging
from datetime import datetime
from dotenv import load_dotenv
from sync_manager import SyncManager

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('todoist_sync.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def run_sync():
    api_token = os.getenv('TODOIST_API_TOKEN')
    if not api_token:
        logger.error("TODOIST_API_TOKEN not found in environment variables")
        return
        
    db_url = os.getenv('DATABASE_URL', 'sqlite:///todoist_sync.db')
    
    try:
        manager = SyncManager(api_token, db_url)
        result = manager.sync_completed_tasks(lookback_days=30)
        
        logger.info(f"Sync successful: {result['new_tasks']} new tasks added")
        logger.info(f"Total tasks in database: {result['total_tasks']}")
        
        manager.close()
        
    except Exception as e:
        logger.error(f"Sync failed: {e}")

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'once'
    
    if mode == 'once':
        logger.info("Running one-time sync...")
        run_sync()
        
    elif mode == 'monitor':
        interval_minutes = int(os.getenv('SYNC_INTERVAL_MINUTES', '30'))
        logger.info(f"Starting monitor mode - syncing every {interval_minutes} minutes")
        
        run_sync()
        
        schedule.every(interval_minutes).minutes.do(run_sync)
        
        while True:
            schedule.run_pending()
            time.sleep(60)
            
    elif mode == 'daemon':
        logger.info("Starting in daemon mode (runs every hour)")
        
        run_sync()
        
        schedule.every().hour.do(run_sync)
        
        while True:
            schedule.run_pending()
            time.sleep(60)
            
    else:
        print("Usage: python monitor.py [once|monitor|daemon]")
        print("  once    - Run sync once and exit (default)")
        print("  monitor - Run continuously with custom interval")
        print("  daemon  - Run continuously, sync every hour")
        sys.exit(1)

if __name__ == "__main__":
    main()