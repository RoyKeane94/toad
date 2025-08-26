from django.db import models

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
    name = models.CharField(max_length=100, null=False, blank=False)
    url_identifier = models.CharField(max_length=50, unique=True, blank=True)
    image = models.ImageField(upload_to='society_links/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.url_identifier:
            # Generate a unique URL identifier based on name
            base_identifier = self.name.lower().replace(' ', '-').replace('&', 'and')
            # Remove special characters
            import re
            base_identifier = re.sub(r'[^a-z0-9-]', '', base_identifier)
            
            # Ensure uniqueness
            counter = 1
            identifier = base_identifier
            while SocietyLink.objects.filter(url_identifier=identifier).exists():
                identifier = f"{base_identifier}-{counter}"
                counter += 1
            
            self.url_identifier = identifier
        
        super().save(*args, **kwargs)
    
    @property
    def public_url(self):
        """Generate the full public URL for this society link"""
        from django.urls import reverse
        return reverse('crm:society_link_public', kwargs={'pk': self.pk})
    
    class Meta:
        ordering = ['-created_at']