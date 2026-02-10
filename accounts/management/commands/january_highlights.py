from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging
import os

User = get_user_model()
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Send January highlights email to all active users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending emails',
        )
        parser.add_argument(
            '--test-email',
            type=str,
            help='Send test email to a specific email address',
        )
        parser.add_argument(
            '--days-since-registration',
            type=int,
            default=7,
            help='Minimum days since registration (default: 7)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Maximum number of emails to send',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        test_email = options['test_email']
        days_since_registration = options['days_since_registration']
        limit = options['limit']
        
        # Find users who registered at least X days ago (to avoid sending to brand new users)
        cutoff_date = timezone.now() - timedelta(days=days_since_registration)
        
        # Get all users registered before the cutoff date
        eligible_users = User.objects.filter(
            date_joined__lt=cutoff_date,
            email_verified=True,  # Only send to verified emails
        ).order_by('-date_joined')
        
        # Apply limit if specified
        if limit:
            eligible_users = eligible_users[:limit]
        
        # Debug: Show what we're finding
        self.stdout.write('\n' + '='*60)
        self.stdout.write('JANUARY HIGHLIGHTS EMAIL CAMPAIGN')
        self.stdout.write('='*60)
        self.stdout.write(
            f"Found {eligible_users.count()} eligible users "
            f"(registered before {cutoff_date.strftime('%Y-%m-%d %H:%M')})"
        )
        
        if limit:
            self.stdout.write(f'Limit applied: Will send to maximum {limit} users')
        
        if test_email:
            # Send test email to specific address
            self.send_test_email(test_email, dry_run)
            return
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN MODE - No emails will be sent'))
            self.show_preview(eligible_users.first())
            self.show_all_emails(eligible_users[:20])  # Show first 20
            return
        
        # Show all emails that will be sent (informational)
        self.stdout.write('\n' + '='*60)
        self.stdout.write('EMAILS TO BE SENT')
        self.stdout.write('='*60)
        self.show_all_emails(eligible_users)
        
        # Confirm before sending
        if not self.confirm_send(eligible_users.count()):
            self.stdout.write(self.style.WARNING('Sending cancelled by user'))
            return
        
        # Send emails
        success_count = 0
        error_count = 0
        
        self.stdout.write('\n' + self.style.SUCCESS('=== SENDING EMAILS ==='))
        for user in eligible_users:
            try:
                if self.send_january_highlights_email(user):
                    success_count += 1
                    self.stdout.write(f'✓ Sent to {user.email}')
                else:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f'✗ Failed to send to {user.email}'))
                    
            except Exception as e:
                error_count += 1
                logger.error(f'Error sending email to {user.email}: {e}')
                self.stdout.write(self.style.ERROR(f'✗ Error sending to {user.email}: {e}'))
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write('EMAIL SENDING SUMMARY')
        self.stdout.write('='*50)
        self.stdout.write(f'Total users: {eligible_users.count()}')
        self.stdout.write(f'Successfully sent: {success_count}')
        self.stdout.write(f'Failed: {error_count}')
        self.stdout.write('='*50)

    def send_january_highlights_email(self, user):
        """Send the January highlights email to a user"""
        try:
            # Get base URL
            base_url = getattr(settings, 'BASE_URL', 'https://www.meettoad.co.uk')
            
            # Render the email template
            html_message = render_to_string('accounts/email/follow_up/january_highlights_email.html', {
                'user': user,
                'base_url': base_url
            })
            
            # Get personal email settings
            personal_email_host = os.environ.get('PERSONAL_EMAIL_HOST', settings.EMAIL_HOST)
            personal_email_port = int(os.environ.get('PERSONAL_EMAIL_PORT', settings.EMAIL_PORT))
            personal_email_user = os.environ.get('PERSONAL_EMAIL_HOST_USER', settings.EMAIL_HOST_USER)
            personal_email_password = os.environ.get('PERSONAL_EMAIL_HOST_PASSWORD', settings.EMAIL_HOST_PASSWORD)
            
            # Create email message with personal email settings
            email = EmailMessage(
                subject='Three quiet improvements to Toad',
                body=html_message,
                from_email=personal_email_user,
                to=[user.email],
                connection=None  # We'll create a custom connection
            )
            email.content_subtype = "html"
            
            # Create connection with personal email settings
            from django.core.mail import get_connection
            connection = get_connection(
                host=personal_email_host,
                port=personal_email_port,
                username=personal_email_user,
                password=personal_email_password,
                use_tls=True
            )
            
            # Send email using personal connection
            email.connection = connection
            email.send()
            
            logger.info(f'January highlights email sent to {user.email}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to send January highlights email to {user.email}: {e}')
            return False

    def send_test_email(self, test_email, dry_run):
        """Send a test email to verify the template"""
        self.stdout.write(f'Sending test email to {test_email}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - Would send test email'))
            return
        
        # Create a test user for rendering
        test_user, created = User.objects.get_or_create(
            email=test_email,
            defaults={
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        try:
            base_url = getattr(settings, 'BASE_URL', 'https://www.meettoad.co.uk')
            
            html_message = render_to_string('accounts/email/follow_up/january_highlights_email.html', {
                'user': test_user,
                'base_url': base_url
            })
            
            # Get personal email settings
            personal_email_host = os.environ.get('PERSONAL_EMAIL_HOST', settings.EMAIL_HOST)
            personal_email_port = int(os.environ.get('PERSONAL_EMAIL_PORT', settings.EMAIL_PORT))
            personal_email_user = os.environ.get('PERSONAL_EMAIL_HOST_USER', settings.EMAIL_HOST_USER)
            personal_email_password = os.environ.get('PERSONAL_EMAIL_HOST_PASSWORD', settings.EMAIL_HOST_PASSWORD)
            
            # Create email message with personal email settings
            email = EmailMessage(
                subject='[TEST] Three quiet improvements to Toad',
                body=html_message,
                from_email=personal_email_user,
                to=[test_email],
                connection=None  # We'll create a custom connection
            )
            email.content_subtype = "html"
            
            # Create connection with personal email settings
            from django.core.mail import get_connection
            connection = get_connection(
                host=personal_email_host,
                port=personal_email_port,
                username=personal_email_user,
                password=personal_email_password,
                use_tls=True
            )
            
            # Send email using personal connection
            email.connection = connection
            email.send()
            
            self.stdout.write(self.style.SUCCESS(f'✓ Test email sent to {test_email}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed to send test email: {e}'))

    def show_all_emails(self, users):
        """Show all email addresses that will be sent to"""
        for i, user in enumerate(users, 1):
            self.stdout.write(f'{i:3d}. {user.get_full_name()} - {user.email}')
        
        if users.count() > len(list(users)):
            self.stdout.write(f'... and {users.count() - len(list(users))} more')

    def show_preview(self, user):
        """Show preview of what would be sent"""
        if not user:
            self.stdout.write(self.style.WARNING('No users found for preview'))
            return
        
        base_url = getattr(settings, 'BASE_URL', 'https://www.meettoad.co.uk')
        
        html_content = render_to_string('accounts/email/follow_up/january_highlights_email.html', {
            'user': user,
            'base_url': base_url
        })
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write('EMAIL PREVIEW')
        self.stdout.write('='*50)
        self.stdout.write(f'To: {user.email}')
        self.stdout.write(f'Subject: Three quiet improvements to Toad')
        self.stdout.write(f'Content Length: {len(html_content)} characters')
        self.stdout.write('='*50 + '\n')

    def confirm_send(self, total_users):
        """Ask for confirmation before sending emails"""
        self.stdout.write(
            self.style.WARNING(
                f'\n⚠️  You are about to send January highlights emails to {total_users} users.'
                f'\nThis action cannot be undone.'
                f'\n'
            )
        )
        
        response = input('Are you sure you want to proceed? (type "yes" to confirm): ')
        return response.lower() == 'yes'
