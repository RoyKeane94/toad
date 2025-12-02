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
    LEAD_TYPE_CHOICES = [
        ('b2b', 'B2B'),
        ('society', 'Society'),
    ]
    
    name = models.CharField(max_length=100)
    lead_type = models.CharField(max_length=10, choices=LEAD_TYPE_CHOICES, default='b2b')
    company = models.ForeignKey('Company', on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    society_university = models.ForeignKey(SocietyUniversity, on_delete=models.CASCADE, null=True, blank=True)
    toad_customer = models.BooleanField(default=False)
    toad_customer_date = models.DateField(null=True, blank=True)
    initial_message_sent = models.BooleanField(default=False)
    initial_message_sent_date = models.DateField(null=True, blank=True)
    no_response = models.BooleanField(default=False)
    no_response_date = models.DateField(null=True, blank=True)
    lead_focus = models.ForeignKey(LeadFocus, on_delete=models.CASCADE, null=True, blank=True)
    contact_method = models.ForeignKey(ContactMethod, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.lead_type == 'society' and self.society_university:
            return f"{self.name} - {self.society_university.name}"
        elif self.lead_type == 'b2b':
            if self.company:
                return f"{self.name} - {self.company.company_name}"
        return self.name
    
    def get_personalized_template_url(self, request=None):
        """
        Get the personalized template URL for this lead based on its company's sector.
        Returns None if no company or template exists.
        """
        if not self.company:
            return None
        return self.company.get_personalized_template_url(lead_id=self.pk, request=request)

class SocietyLink(models.Model):
    name = models.CharField(max_length=100)

    image = models.ImageField(
        upload_to='society_links/', 
        null=True, 
        blank=True,
        storage=get_storage_backend()
    )
    
    society_university = models.ForeignKey(SocietyUniversity, null=True, blank=True, on_delete=models.CASCADE)
    lead = models.OneToOneField(Lead, on_delete=models.CASCADE, null=True, blank=True, related_name='society_link')
    
    def __str__(self):
        return self.name or f"SocietyLink-{self.id}" if self.id else "SocietyLink-New"

# B2B Models

class CompanySector(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Company Sector'
        verbose_name_plural = 'Company Sectors'

    def __str__(self):
        return self.name

class Company(models.Model):
    company_name = models.CharField(max_length=200)
    company_sector = models.ForeignKey(CompanySector, on_delete=models.CASCADE, related_name='companies', null=True, blank=True, help_text="The company sector this company is for")
    contact_person = models.CharField(max_length=100, blank=True)
    contact_email = models.EmailField(blank=True)
    email_template = models.ForeignKey(
        'EmailTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='companies'
    )
    email_subject = models.CharField(max_length=200, blank=True)
    personalised_email_text = models.TextField(blank=True)
    initial_email_sent = models.BooleanField(default=False)
    initial_email_sent_date = models.DateField(null=True, blank=True)
    initial_email_response = models.BooleanField(default=False)
    initial_email_response_date = models.DateField(null=True, blank=True)
    template_view_count = models.IntegerField(default=0, help_text="Number of times this company's template has been viewed")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['company_name']
        verbose_name_plural = 'Companies'
    
    def __str__(self):
        return self.company_name
    
    @property
    def name(self):
        """Backward compatibility property"""
        return self.company_name
    
    def get_personalized_template_url(self, lead_id=None, request=None):
        """
        Get the personalized template URL for this company based on its sector.
        Requires a lead_id to generate the personalized URL.
        Returns None if no template exists for the sector.
        """
        if not self.company_sector or not lead_id:
            return None
        
        # Find the CustomerTemplate for this sector
        # CustomerTemplate is defined later in this file, but Python resolves it at runtime
        try:
            template = CustomerTemplate.objects.get(company_sector=self.company_sector)
            from django.urls import reverse
            url = reverse('crm:customer_template_public', kwargs={'pk': template.pk})
            # Add lead ID as query parameter
            url += f'?id={lead_id}'
            if request:
                return request.build_absolute_uri(url)
            return url
        except CustomerTemplate.DoesNotExist:
            return None
        except CustomerTemplate.MultipleObjectsReturned:
            # If multiple templates exist, use the first one
            template = CustomerTemplate.objects.filter(company_sector=self.company_sector).first()
            if template:
                from django.urls import reverse
                url = reverse('crm:customer_template_public', kwargs={'pk': template.pk})
                url += f'?id={lead_id}'
                if request:
                    return request.build_absolute_uri(url)
                return url
            return None

class EmailTemplate(models.Model):
    name = models.CharField(max_length=150, unique=True)
    text = models.TextField(help_text="Template body text")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Email Template'
        verbose_name_plural = 'Email Templates'

    def __str__(self):
        return self.name

class LeadMessage(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(lead__isnull=False) | models.Q(company__isnull=False),
                name='lead_or_company_required'
            )
        ]
    
    def __str__(self):
        if self.lead:
            return f"Message for {self.lead.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
        elif self.company:
            return f"Message for {self.company.company_name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
        return f"Message - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class CustomerTemplate(models.Model):
    company_sector = models.ForeignKey(CompanySector, on_delete=models.CASCADE, related_name='customer_templates', null=True, blank=True, help_text="The company sector this template is for")
    playbook_name = models.CharField(max_length=100, help_text="The name of the playbook")
    main_header_description = models.TextField(help_text="The description of the header")
    video_1=models.FileField(upload_to='customer_templates/', null=True, blank=True, storage=get_storage_backend())
    used_by = models.CharField(max_length=100, help_text="Used by event teams, venues and planners")

    grid_header = models.CharField(max_length=100, help_text="What Toad looks like for [x]")

    grid_1_title = models.CharField(max_length=100, help_text="The title of the first grid")
    grid_1_header_description = models.TextField(help_text="The description of the header")
    grid_1_subheader = models.CharField(max_length=100, help_text="The subheader of the first grid")
    grid_1_bullet_1 = models.CharField(max_length=100, help_text="The first bullet point of the first grid")
    grid_1_bullet_2 = models.CharField(max_length=100, help_text="The second bullet point of the first grid")
    grid_1_bullet_3 = models.CharField(max_length=100, help_text="The third bullet point of the first grid")
    grid_1_bullet_4 = models.CharField(max_length=100, help_text="The fourth bullet point of the first grid")
    grid_1_video = models.FileField(upload_to='customer_templates/', null=True, blank=True, storage=get_storage_backend())

    grid_2_title = models.CharField(max_length=100, help_text="The title of the second grid")
    grid_2_header_description = models.TextField(help_text="The description of the header")
    grid_2_subheader = models.CharField(max_length=100, help_text="The subheader of the second grid")
    grid_2_bullet_1 = models.CharField(max_length=100, help_text="The first bullet point of the second grid")
    grid_2_bullet_2 = models.CharField(max_length=100, help_text="The second bullet point of the second grid")
    grid_2_bullet_3 = models.CharField(max_length=100, help_text="The third bullet point of the second grid")
    grid_2_bullet_4 = models.CharField(max_length=100, help_text="The fourth bullet point of the second grid")
    grid_2_video = models.FileField(upload_to='customer_templates/', null=True, blank=True, storage=get_storage_backend())

    grid_3_title = models.CharField(max_length=100, help_text="The title of the third grid")
    grid_3_header_description = models.TextField(help_text="The description of the header")
    grid_3_subheader = models.CharField(max_length=100, help_text="The subheader of the third grid")
    grid_3_bullet_1 = models.CharField(max_length=100, help_text="The first bullet point of the third grid")
    grid_3_bullet_2 = models.CharField(max_length=100, help_text="The second bullet point of the third grid")
    grid_3_bullet_3 = models.CharField(max_length=100, help_text="The third bullet point of the third grid")
    grid_3_bullet_4 = models.CharField(max_length=100, help_text="The fourth bullet point of the third grid")
    grid_3_video = models.FileField(upload_to='customer_templates/', null=True, blank=True, storage=get_storage_backend())

    section_2_title = models.CharField(max_length=100, help_text="Why venues love Toad")
    section_2_card_1_title = models.CharField(max_length=100, help_text="The title of the first card")
    section_2_card_1_description = models.TextField(help_text="The description of the first card")
    section_2_card_2_title = models.CharField(max_length=100, help_text="The title of the second card")
    section_2_card_2_description = models.TextField(help_text="The description of the second card")
    section_2_card_3_title = models.CharField(max_length=100, help_text="The title of the third card")
    section_2_card_3_description = models.TextField(help_text="The description of the third card")
    section_2_card_4_title = models.CharField(max_length=100, help_text="The title of the fourth card")
    section_2_card_4_description = models.TextField(help_text="The description of the fourth card")
    
    
    def __str__(self):
        return self.playbook_name
    
    