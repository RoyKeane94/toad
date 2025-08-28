from django.db import models
from django.conf import settings

def get_storage_backend():
    """Get the appropriate storage backend based on settings"""
    try:
        # Only try to get settings if Django is fully configured
        from django.conf import settings
        from django.core.exceptions import ImproperlyConfigured
        
        # Check if settings are ready
        if not hasattr(settings, 'DEFAULT_FILE_STORAGE'):
            return None
            
        if getattr(settings, 'FORCE_S3_TESTING', False) or getattr(settings, 'IS_PRODUCTION', False):
            # Import and return the actual storage class, not the string
            storage_path = settings.DEFAULT_FILE_STORAGE
            if storage_path:
                try:
                    module_path, class_name = storage_path.rsplit('.', 1)
                    module = __import__(module_path, fromlist=[class_name])
                    storage_class = getattr(module, class_name)
                    return storage_class()
                except (ImportError, AttributeError) as e:
                    print(f"Error importing storage class {storage_path}: {e}")
                    return None
            else:
                return None
        else:
            return None  # Use Django's default
    except Exception as e:
        print(f"Error getting storage backend: {e}")
        return None  # Fallback to Django's default

# Create your models here.

class LeadFocus(models.Model):
    name = models.CharField(max_length=20)
    
    def __str__(self):
        return self.name
    
class ContactMethod(models.Model):
    name = models.CharField(max_length=20)
    
    def __str__(self):
        return self.name

class Lead(models.Model):
    name = models.CharField(max_length=20)
    lead_focus = models.ForeignKey(LeadFocus, on_delete=models.CASCADE)
    contact_method = models.ForeignKey(ContactMethod, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class LeadMessage(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        if self.lead:
            return f"Message for {self.lead.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
        return f"Message - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
class SocietyLink(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(
        upload_to='society_links/', 
        null=True, 
        blank=True,
        storage=get_storage_backend()
    )
    
    def __str__(self):
        return self.name or f"SocietyLink-{self.id}" if self.id else "SocietyLink-New"

class TestSocietyLink(models.Model):
    title = models.CharField(max_length=100)
    photo = models.ImageField(
        upload_to='test_society_links/', 
        null=True, 
        blank=True,
        storage=get_storage_backend()
    )
    
    def __str__(self):
        return self.title or f"TestSocietyLink-{self.id}" if self.id else "TestSocietyLink-New"

class SimpleTestModel(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name or f"SimpleTest-{self.id}" if self.id else "SimpleTest-New"