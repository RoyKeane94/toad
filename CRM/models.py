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
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='society_links/', null=True, blank=True)
    
    def __str__(self):
        return self.name or f"SocietyLink-{self.id}" if self.id else "SocietyLink-New"

class TestSocietyLink(models.Model):
    title = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='test_society_links/', null=True, blank=True)
    
    def __str__(self):
        return self.title or f"TestSocietyLink-{self.id}" if self.id else "TestSocietyLink-New"