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

def test_society_link_creation():
    print("=== TESTING SOCIETY LINK CREATION ===")
    
    try:
        # Try to create a test society link
        test_link = SocietyLink(
            name="Test Society",
            image=None  # No image for this test
        )
        
        print(f"Test link object created: {test_link}")
        print(f"Name: {test_link.name}")
        print(f"URL identifier before save: {getattr(test_link, 'url_identifier', 'NOT SET')}")
        
        # Try to save
        test_link.save()
        
        print(f"Save successful! ID: {test_link.pk}")
        print(f"URL identifier after save: {test_link.url_identifier}")
        
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
    success = test_society_link_creation()
    if success:
        print("✅ Society link creation test PASSED")
    else:
        print("❌ Society link creation test FAILED")
