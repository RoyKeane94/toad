from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import User


@receiver(post_save, sender=User)
def set_pro_trial_duration(sender, instance, created, **kwargs):
    """
    Signal to set the correct trial duration for Pro trial users based on trial_type.
    """
    # Only process Pro trial users
    if instance.tier == 'pro_trial' and instance.trial_type:
        from django.utils import timezone
        from datetime import timedelta
        
        # Set trial duration based on trial_type
        if instance.trial_type == '6_month':
            # Set 6-month trial (180 days)
            trial_days = 180
        elif instance.trial_type == '3_month':
            # Set 3-month trial (90 days)
            trial_days = 90
        elif instance.trial_type == '1_month':
            # Set 1-month trial (30 days)
            trial_days = 30
        else:
            # Default to 3 months if trial_type is not recognized
            trial_days = 90
        
        # Only update if trial_ends_at is not already set or if it's different
        expected_end = timezone.now() + timedelta(days=trial_days)
        if not instance.trial_ends_at or instance.trial_ends_at != expected_end:
            instance.trial_started_at = timezone.now()
            instance.trial_ends_at = expected_end
            # Use update_fields to avoid triggering the signal again
            User.objects.filter(pk=instance.pk).update(
                trial_started_at=instance.trial_started_at,
                trial_ends_at=instance.trial_ends_at
            )
