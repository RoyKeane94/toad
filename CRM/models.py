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

class SocietyUniversity(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class LeadFocus(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name
    
class ContactMethod(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Lead(models.Model):
    name = models.CharField(max_length=100)
    society_university = models.ForeignKey(SocietyUniversity, on_delete=models.CASCADE, null=True, blank=True)
    toad_customer = models.BooleanField(default=False)
    toad_customer_date = models.DateField(null=True, blank=True)
    initial_message_sent = models.BooleanField(default=False)
    initial_message_sent_date = models.DateField(null=True, blank=True)
    no_response = models.BooleanField(default=False)
    no_response_date = models.DateField(null=True, blank=True)
    lead_focus = models.ForeignKey(LeadFocus, on_delete=models.CASCADE)
    contact_method = models.ForeignKey(ContactMethod, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.society_university:
            return self.name + " - " + self.society_university.name
        return self.name + " - No University"

class SocietyLink(models.Model):
    name = models.CharField(max_length=100)

    image = models.ImageField(
        upload_to='society_links/', 
        null=True, 
        blank=True,
        storage=get_storage_backend()
    )
    
    society_university = models.ForeignKey(SocietyUniversity, null=True, blank=True, on_delete=models.CASCADE)
    lead = models.OneToOneField(Lead, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return self.name or f"SocietyLink-{self.id}" if self.id else "SocietyLink-New"

class LeadMessage(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        if self.lead:
            return f"Message for {self.lead.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
        return f"Message - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class Feedback(models.Model):
    # Organization method choices
    ORGANIZATION_CHOICES = [
        ('toad', 'Toad'),
        ('notes_phone', 'Notes on phone'),
        ('pen_paper', 'Pen and paper'),
        ('trello', 'Trello'),
        ('monday', 'Monday.com'),
        ('excel', 'Excel'),
        ('other', 'Other'),
    ]
    
    # User information (optional for anonymous feedback)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200, blank=True, help_text="Optional - share your name if you'd like")
    
    # Core feedback questions
    regularly_using_toad = models.BooleanField(
        verbose_name="Are you regularly using Toad?",
        help_text="Select Yes if you use Toad regularly, No if not"
    )
    usage_reason = models.TextField(
        verbose_name="If yes, why? If not, why not?",
        blank=True,
        help_text="Tell us about your experience with Toad"
    )
    
    # Organization preferences
    organization_method = models.CharField(
        max_length=50,
        choices=ORGANIZATION_CHOICES,
        verbose_name="How do you tend to organise?",
        blank=True
    )
    organization_other = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="If other, please specify"
    )
    
    # Improvement suggestions
    non_user_suggestion = models.TextField(
        verbose_name="If you're not using Toad, is there anything that would make you use it?",
        blank=True,
        help_text="What would convince you to use Toad?"
    )
    user_improvement = models.TextField(
        verbose_name="If you are using Toad, what could make it better?",
        blank=True,
        help_text="How can we improve Toad for you?"
    )
    
    # Team Toad and sharing
    team_toad_interest = models.TextField(
        verbose_name="Would you be interested in Team Toad?",
        blank=True,
        help_text="Team features for collaborative planning"
    )
    would_share = models.BooleanField(
        default=False,
        verbose_name="Would you share Toad with friends and/or colleagues?"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Feedback'
        verbose_name_plural = 'Feedback'
    
    def __str__(self):
        if self.user:
            return f"Feedback from {self.user.email} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
        elif self.name:
            return f"Feedback from {self.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
        return f"Anonymous Feedback - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
