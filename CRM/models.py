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
    updated_at = models.DateTimeField(auto_now=True)

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

    status_choices = [
        ('Customer', 'Customer'),
        ('Prospect', 'Prospect'),
        ('Rejected but follow up', 'Rejected but follow up'),
        ('No response', 'No response'),
        ('Rejected', 'Rejected'),
    ]

    email_status_choices = [
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
    ]
    
    company_name = models.CharField(max_length=200)
    status = models.CharField(choices=status_choices, default='Prospect')
    email_status = models.CharField(choices=email_status_choices, null=True, blank=True)
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
    
    # Email sequence tracking
    initial_email_sent = models.BooleanField(default=False)
    initial_email_sent_date = models.DateField(null=True, blank=True)
    second_email_sent_date = models.DateField(null=True, blank=True, help_text="Date second follow-up email was sent")
    third_email_sent_date = models.DateField(null=True, blank=True, help_text="Date third follow-up email was sent")
    fourth_email_sent_date = models.DateField(null=True, blank=True, help_text="Date fourth/final email was sent")
    
    # Email response tracking
    initial_email_response = models.BooleanField(default=False)
    initial_email_response_date = models.DateField(null=True, blank=True)
    
    # Email threading - stores the Message-ID and subject of the first email for threading replies
    first_email_message_id = models.CharField(
        max_length=255, 
        blank=True, 
        help_text="Message-ID header from first email, used for threading subsequent emails"
    )
    first_email_subject = models.CharField(
        max_length=255,
        blank=True,
        help_text="Subject of first email, follow-ups use 'Re: [this subject]' for threading"
    )
    last_email_body = models.TextField(
        blank=True,
        help_text="Body of the last email sent, used to quote in follow-up replies"
    )
    last_email_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="DateTime of the last email sent, used for 'On [date], [name] wrote:' quote"
    )
    
    # Error tracking
    email_failed_date = models.DateField(null=True, blank=True, help_text="Date of last email send failure")
    
    template_view_count = models.IntegerField(default=0, help_text="Number of times this company's template has been viewed")
    template_sign_up_click_count = models.IntegerField(default=0, help_text="Number of times sign-up links were clicked on this company's template")
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
    
    def get_personalized_template_url(self, lead_id=None, request=None, base_url=None):
        """
        Get the personalized template URL for this company based on its sector.
        
        Args:
            lead_id: Optional lead ID for backward compatibility
            request: Optional request object to build absolute URI
            base_url: Optional base URL (e.g., from settings.SITE_URL) for building full URLs
            
        Returns:
            Full URL to the personalized template, or None if no template exists
        """
        if not self.company_sector:
            return None
        
        # Find the CustomerTemplate for this sector
        try:
            template = CustomerTemplate.objects.get(company_sector=self.company_sector)
        except CustomerTemplate.DoesNotExist:
            return None
        except CustomerTemplate.MultipleObjectsReturned:
            template = CustomerTemplate.objects.filter(company_sector=self.company_sector).first()
            if not template:
                return None
        
        from django.urls import reverse
        url = reverse('crm:customer_template_public', kwargs={'pk': template.pk})
        
        # Add company_id as query parameter (preferred) or lead_id for backward compatibility
        if lead_id:
            url += f'?id={lead_id}'
        else:
            url += f'?company_id={self.pk}'
        
        # Build full URL
        if request:
            return request.build_absolute_uri(url)
        elif base_url:
            # Use provided base URL (e.g., settings.SITE_URL)
            base_url = base_url.rstrip('/')
            return f"{base_url}{url}"
        return url
    
    def get_last_email_sent_date(self):
        """Get the date of the most recent email sent to this company."""
        dates = [
            self.fourth_email_sent_date,
            self.third_email_sent_date,
            self.second_email_sent_date,
            self.initial_email_sent_date,
        ]
        for date in dates:
            if date:
                return date
        return None
    
    def get_next_email_number(self):
        """
        Determine which email should be sent next based on email_status.
        Returns 1-4, or None if all emails have been sent.
        """
        if not self.email_status:
            return 1
        try:
            current = int(self.email_status)
            if current < 4:
                return current + 1
            return None  # All 4 emails sent
        except (ValueError, TypeError):
            return 1

class EmailTemplate(models.Model):
    """
    Email templates for automated CRM email sequences.
    Each sector can have up to 4 email templates (email 1, 2, 3, 4).
    
    Supported placeholders in subject and body:
    - {company_name} - The company's name
    - {contact_person} - The contact person's name
    - {personalised_template_url} - The raw personalized landing page URL
    - {personalised_link} - Bold linked text: "Toad x Company Name" with embedded URL
    """
    EMAIL_NUMBER_CHOICES = [
        (1, 'Email 1 (Initial)'),
        (2, 'Email 2 (Follow-up 1)'),
        (3, 'Email 3 (Follow-up 2)'),
        (4, 'Email 4 (Final)'),
    ]
    
    name = models.CharField(max_length=150, help_text="Internal name for this template")
    company_sector = models.ForeignKey(
        CompanySector, 
        on_delete=models.CASCADE, 
        related_name='email_templates',
        null=True,  # Allow null for migration of existing templates
        blank=True,
        help_text="The sector this template belongs to"
    )
    email_number = models.IntegerField(
        choices=EMAIL_NUMBER_CHOICES,
        default=1,  # Default for migration
        help_text="Which email in the sequence (1-4)"
    )
    subject = models.CharField(
        max_length=200, 
        default='',  # Default for migration
        blank=True,
        help_text="Email subject line. Use {company_name}, {contact_person} for personalization"
    )
    body = models.TextField(
        default='',  # Default for migration
        blank=True,
        help_text="Email body text. Use {company_name}, {contact_person}, {personalised_template_url} for personalization"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['company_sector', 'email_number']
        verbose_name = 'Email Template'
        verbose_name_plural = 'Email Templates'
        # Note: unique_together with nullable field allows multiple nulls
        unique_together = ['company_sector', 'email_number']

    def __str__(self):
        if self.company_sector:
            return f"{self.company_sector.name} - Email {self.email_number}: {self.name}"
        return f"(No Sector) - Email {self.email_number}: {self.name}"
    
    def render_subject(self, company):
        """Render the subject line with company data."""
        return self._render_template(self.subject, company)
    
    def render_body(self, company, template_url=None):
        """Render the body with company data and optional template URL."""
        return self._render_template(self.body, company, template_url)
    
    def _render_template(self, template_text, company, template_url=None):
        """Replace placeholders with actual values."""
        result = template_text
        company_name = company.company_name or ''
        result = result.replace('{company_name}', company_name)
        result = result.replace('{contact_person}', company.contact_person or '')
        
        if template_url:
            # {personalised_template_url} - raw URL
            result = result.replace('{personalised_template_url}', template_url)
            # {personalised_link} - bold linked text: "Toad x Company Name"
            personalised_link = f'<b><a href="{template_url}">Toad x {company_name}</a></b>'
            result = result.replace('{personalised_link}', personalised_link)
        else:
            result = result.replace('{personalised_template_url}', '')
            result = result.replace('{personalised_link}', '')
        return result

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
    
    