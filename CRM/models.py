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
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"=== SOCIETY LINK SAVE DEBUG ===")
        logger.info(f"Saving society link: {self.name}")
        logger.info(f"Current url_identifier: {getattr(self, 'url_identifier', 'NOT SET')}")
        
        # Add print statements for Railway logs
        print(f"=== SOCIETY LINK SAVE DEBUG ===")
        print(f"Saving society link: {self.name}")
        print(f"Name type: {type(self.name)}")
        print(f"Current url_identifier: {getattr(self, 'url_identifier', 'NOT SET')}")
        
        if not self.url_identifier:
            logger.info("No url_identifier, generating one...")
            print("No url_identifier, generating one...")
            
            # Ensure we have a name to work with
            if not self.name:
                logger.error("Name is None, cannot generate url_identifier")
                print("❌ ERROR: Name is None, cannot generate url_identifier")
                print(f"❌ Current instance state: {self.__dict__}")
                raise ValueError("SocietyLink name cannot be None when saving")
            
            # Generate a unique URL identifier based on name
            base_identifier = self.name.lower().replace(' ', '-').replace('&', 'and')
            # Remove special characters
            import re
            base_identifier = re.sub(r'[^a-z0-9-]', '', base_identifier)
            logger.info(f"Base identifier: {base_identifier}")
            print(f"Base identifier: {base_identifier}")
            
            # Ensure uniqueness
            counter = 1
            identifier = base_identifier
            while SocietyLink.objects.filter(url_identifier=identifier).exists():
                identifier = f"{base_identifier}-{counter}"
                counter += 1
                logger.info(f"Identifier {identifier} already exists, trying {identifier}")
                print(f"Identifier {identifier} already exists, trying {identifier}")
            
            self.url_identifier = identifier
            logger.info(f"Final url_identifier set to: {self.url_identifier}")
            print(f"Final url_identifier set to: {self.url_identifier}")
        else:
            logger.info(f"url_identifier already exists: {self.url_identifier}")
            print(f"url_identifier already exists: {self.url_identifier}")
        
        logger.info("Calling super().save()...")
        print("Calling super().save()...")
        super().save(*args, **kwargs)
        logger.info("Save completed successfully")
        print("✅ Save completed successfully")
    
    @property
    def public_url(self):
        """Generate the full public URL for this society link"""
        from django.urls import reverse
        return reverse('crm:society_link_public', kwargs={'pk': self.pk})
    
    class Meta:
        ordering = ['-created_at']