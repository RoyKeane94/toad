#!/usr/bin/env python
"""
List all projects for all users
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'toad.settings')
django.setup()

from accounts.models import User
from pages.models import Project

def list_all_projects():
    print("📋 All Projects in Database")
    print("=" * 50)
    
    users = User.objects.all().order_by('email')
    
    for user in users:
        projects = Project.objects.filter(user=user, is_archived=False).order_by('created_at')
        
        print(f"\n👤 User: {user.email}")
        print(f"   Name: {user.first_name} {user.last_name}")
        print(f"   Tier: {user.tier}")
        
        if projects.exists():
            print(f"   Projects ({projects.count()}):")
            for project in projects:
                print(f"     • ID: {project.id} | Name: '{project.name}' | Created: {project.created_at.strftime('%Y-%m-%d %H:%M')}")
                print(f"       URL: /projects/{project.id}/")
        else:
            print("   No projects found")
    
    print(f"\n📊 Summary:")
    total_projects = Project.objects.filter(is_archived=False).count()
    print(f"Total active projects: {total_projects}")

if __name__ == "__main__":
    list_all_projects()
