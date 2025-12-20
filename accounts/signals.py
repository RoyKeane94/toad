from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import User


@receiver(pre_save, sender=User)
def capture_old_tier(sender, instance, **kwargs):
    """
    Capture the old tier value before save to detect tier changes.
    """
    if instance.pk:
        try:
            old_instance = User.objects.get(pk=instance.pk)
            instance._old_tier = old_instance.tier
        except User.DoesNotExist:
            instance._old_tier = None
    else:
        instance._old_tier = None


@receiver(post_save, sender=User)
def handle_tier_downgrade(sender, instance, created, **kwargs):
    """
    Handle tier downgrades from pro tiers to non-pro tiers.
    When a user downgrades from pro/pro_trial/society_pro/beta to free/personal/personal_trial/personal_3_month_trial:
    1. Remove them from all team_toad_user relationships
    2. Set assigned_to to null for all tasks where they are assigned
    """
    # Skip if this is a new user (created=True)
    if created:
        return
    
    # Get the old tier from the pre_save signal
    old_tier = getattr(instance, '_old_tier', None)
    new_tier = instance.tier
    
    # If old_tier wasn't captured, skip (shouldn't happen, but be defensive)
    if old_tier is None:
        return
    
    # Define pro tiers and non-pro tiers
    pro_tiers = ['pro', 'pro_trial', 'society_pro', 'beta']
    non_pro_tiers = ['free', 'personal', 'personal_trial', 'personal_3_month_trial']
    
    # Check if user downgraded from a pro tier to a non-pro tier
    # Only process if we have an old_tier and it's different from new_tier
    if old_tier != new_tier and old_tier in pro_tiers and new_tier in non_pro_tiers:
        from pages.models import Project, Task
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Check if user is part of a team subscription (has team_admin)
            # If they are, delete all their grids
            if instance.team_admin:
                # User is part of a team - delete all their grids
                user_projects = Project.objects.filter(user=instance)
                grids_deleted = user_projects.count()
                user_projects.delete()
                logger.info(f"User {instance.email} downgraded from {old_tier} to {new_tier}. Deleted {grids_deleted} grid(s) due to team subscription cancellation.")
            else:
                # User is not part of a team - just remove from team_toad_user relationships
                # Remove user from all team_toad_user relationships
                # Use distinct() to avoid duplicates if user is in multiple projects
                projects_with_user = Project.objects.filter(team_toad_user=instance).distinct()
                removed_count = 0
                for project in projects_with_user:
                    if instance in project.team_toad_user.all():
                        project.team_toad_user.remove(instance)
                        removed_count += 1
                
                # Set assigned_to to null for all tasks where user is assigned
                # Use update() to avoid triggering signals and to do it in a single query
                tasks_updated = Task.objects.filter(assigned_to=instance).update(assigned_to=None)
                
                logger.info(f"User {instance.email} downgraded from {old_tier} to {new_tier}. Removed from {removed_count} project(s) team_toad_user and unassigned from {tasks_updated} task(s).")
        except Exception as e:
            logger.error(f"Error handling tier downgrade for user {instance.email}: {e}", exc_info=True)


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
