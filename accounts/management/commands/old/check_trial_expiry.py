from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Check for expired trials and downgrade users to free tier'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()
        
        # Find users whose trials have expired
        expired_trials = User.objects.filter(
            trial_ends_at__lte=now,
            tier='personal',
            trial_ends_at__isnull=False
        )
        
        self.stdout.write(f"Found {expired_trials.count()} users with expired trials")
        
        for user in expired_trials:
            self.stdout.write(f"Processing user: {user.email} (trial ended: {user.trial_ends_at})")
            
            if not dry_run:
                # Downgrade to free tier
                user.tier = 'free'
                user.save()
                
                # Send notification email
                try:
                    send_mail(
                        subject='Your Toad trial has ended',
                        message=f"""
Hi {user.first_name},

Your 6-month free trial of Toad Personal has ended. You've been moved to our Free plan.

You can still:
- Create up to 3 grids
- Use basic templates
- Access core features

To continue with Personal features, upgrade anytime at:
{settings.SITE_URL}/accounts/register/personal/

Thanks for trying Toad!

Best regards,
The Toad Team
                        """,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=False,
                    )
                    self.stdout.write(f"  ✓ Downgraded and notified {user.email}")
                except Exception as e:
                    self.stdout.write(f"  ✗ Failed to notify {user.email}: {e}")
            else:
                self.stdout.write(f"  [DRY RUN] Would downgrade {user.email}")
        
        if dry_run:
            self.stdout.write("Dry run completed. No changes made.")
        else:
            self.stdout.write(f"Processed {expired_trials.count()} expired trials")
