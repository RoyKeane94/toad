#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/Users/tombarratt/Desktop/Coding_Projects/toad')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'toad.settings')
django.setup()

from CRM.models import SocietyLink

def test_simple_save():
    print("=== TESTING SIMPLE SOCIETY LINK SAVE ===")
    
    try:
        # Try to create a test society link with minimal fields
        test_link = SocietyLink(
            name="Test Society"
            # No image, let Django handle created_at and updated_at
        )
        
        print(f"Test link object created: {test_link}")
        print(f"Name: {test_link.name}")
        print(f"Image: {test_link.image}")
        print(f"Created at: {test_link.created_at}")
        print(f"Updated at: {test_link.updated_at}")
        
        # Try to save
        test_link.save()
        
        print(f"Save successful! ID: {test_link.pk}")
        
        # Clean up
        test_link.delete()
        print("Test link deleted successfully")
        
        return True
        
    except Exception as e:
        print(f"Error creating society link: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_save()
    if success:
        print("✅ Simple save test PASSED")
    else:
        print("❌ Simple save test FAILED")
