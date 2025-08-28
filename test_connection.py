#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from todoist_api_python.api import TodoistAPI

load_dotenv()

def test_connection():
    api_token = os.getenv('TODOIST_API_TOKEN')
    
    if not api_token:
        print("❌ TODOIST_API_TOKEN not found in .env file")
        return
        
    print(f"✓ API token found: {api_token[:10]}...")
    
    try:
        api = TodoistAPI(api_token)
        
        # Get all projects
        projects = api.get_projects()
        
        print(f"\n✓ Successfully connected to Todoist!")
        print(f"\n📁 You have {len(projects)} projects:\n")
        
        for project in projects:
            print(f"  • {project.name}")
            print(f"    ID: {project.id}")
            if project.parent_id:
                print(f"    Parent: {project.parent_id}")
            print(f"    Color: {project.color}")
            print(f"    Order: {project.order}")
            print()
            
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        print("\nPlease check your API token in the .env file")

if __name__ == "__main__":
    test_connection()