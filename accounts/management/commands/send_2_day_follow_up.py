from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from accounts.email_utils import send_2_day_follow_up_email
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Send 2-day follow-up email to non-student users who joined between 2-3 days ago'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending emails',
        )
        parser.add_argument(
            '--test-email',
            type=str,
            help='Send test email to specific address instead of all users',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        test_email = options.get('test_email')
        
        if test_email:
            # Send test email to specific address
            try:
                test_user = User.objects.filter(email=test_email).first()
                if not test_user:
                    # Create a mock user for testing
                    test_user = User(
                        email=test_email,
                        first_name='Test',
                        last_name='User',
                        email_subscribed=True
                    )
                
                self.stdout.write(f'Sending test 2-day follow-up email to {test_email}...')
                
                if not dry_run:
                    success = send_2_day_follow_up_email(test_user)
                    if success:
                        self.stdout.write(self.style.SUCCESS(f'Test email sent successfully to {test_email}'))
                    else:
                        self.stdout.write(self.style.ERROR(f'Failed to send test email to {test_email}'))
                else:
                    self.stdout.write(f'[DRY RUN] Would send test email to {test_email}')
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error sending test email: {e}'))
            return
        
        # Calculate the date range for users who joined between 2-3 days ago
        now = timezone.now()
        two_days_ago = now - timedelta(days=2)
        three_days_ago = now - timedelta(days=3)
        
        # Get users who joined between 2-3 days ago (with some tolerance)
        start_date = three_days_ago.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = two_days_ago.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        users_to_email = User.objects.filter(
            date_joined__range=[start_date, end_date],
            email_subscribed=True,
            email_verified=True,
            second_email_sent=False  # Only users who haven't received the second email
        ).exclude(
            email__isnull=True
        ).exclude(
            email=''
        ).exclude(
            associated_university__isnull=False  # Exclude students (users with associated university)
        )
        
        self.stdout.write('='*50)
        self.stdout.write('2-Day Follow-up Email Campaign (Non-Students)')
        self.stdout.write('='*50)
        self.stdout.write(f'Date range: {start_date} to {end_date}')
        self.stdout.write(f'Total non-student users to email: {users_to_email.count()}')
        
        if dry_run:
            self.stdout.write('\n[DRY RUN MODE - No emails will be sent]')
            for user in users_to_email:
                self.stdout.write(f'Would send to: {user.email} ({user.get_full_name()})')
            return
        
        success_count = 0
        error_count = 0
        
        for user in users_to_email:
            try:
                self.stdout.write(f'Sending to: {user.email} ({user.get_full_name()})')
                
                success = send_2_day_follow_up_email(user)
                
                if success:
                    success_count += 1
                    self.stdout.write(self.style.SUCCESS(f'✓ Sent to {user.email}'))
                else:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f'✗ Failed to send to {user.email}'))
                    
            except Exception as e:
                error_count += 1
                logger.error(f'Error sending 2-day follow-up email to {user.email}: {e}')
                self.stdout.write(self.style.ERROR(f'✗ Error sending to {user.email}: {e}'))
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write('Campaign Summary')
        self.stdout.write('='*50)
        self.stdout.write(f'Total users: {users_to_email.count()}')
        self.stdout.write(f'Successfully sent: {success_count}')
        self.stdout.write(f'Failed: {error_count}')
        self.stdout.write('='*50)
