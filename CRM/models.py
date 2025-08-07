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
    
class LeadMessage(models.Model):
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.message

class Lead(models.Model):
    name = models.CharField(max_length=20)
    message = models.ForeignKey(LeadMessage, on_delete=models.CASCADE)
    lead_focus = models.ForeignKey(LeadFocus, on_delete=models.CASCADE)
    contact_method = models.ForeignKey(ContactMethod, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"