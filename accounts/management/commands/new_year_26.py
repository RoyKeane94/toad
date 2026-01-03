from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.core.mail import EmailMessage, get_connection
from django.conf import settings
import logging
import os

User = get_user_model()
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Send New Year 2026 email to all users'

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

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        test_email = options['test_email']
        
        if test_email:
            # Send test email to specific address
            self.send_test_email(test_email, dry_run)
            return
        
        # Get all users (ignoring unsubscribe status as requested)
        users = User.objects.all()
        
        self.stdout.write(f'Found {users.count()} users to send email to')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No emails will be sent'))
            if users.exists():
                self.show_preview(users.first())
            return
        
        # Show all emails that will be sent (informational)
        self.stdout.write('\n' + '='*60)
        self.stdout.write('EMAILS TO BE SENT')
        self.stdout.write('='*60)
        self.show_all_emails(users)
        
        # Send emails
        success_count = 0
        error_count = 0
        
        self.stdout.write('\n' + self.style.SUCCESS('=== SENDING EMAILS ==='))
        for user in users:
            try:
                if self.send_new_year_email(user):
                    success_count += 1
                    self.stdout.write(f'✓ Sent email to {user.email}')
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
        self.stdout.write(f'Total users: {users.count()}')
        self.stdout.write(f'  - Successfully sent: {success_count}')
        self.stdout.write(f'  - Failed: {error_count}')
        self.stdout.write('='*50)

    def send_new_year_email(self, user):
        """Send the New Year 2026 email to a user"""
        try:
            # Get base URL for URL reversing in template
            base_url = getattr(settings, 'BASE_URL', 'https://www.meettoad.co.uk')
            
            # Render the email template
            html_message = render_to_string('accounts/email/follow_up/new_year_26.html', {
                'user': user,
                'base_url': base_url
            })
            
            # Get personal email settings (same as 2_day_follow_up_email)
            personal_email_host = os.environ.get('PERSONAL_EMAIL_HOST', settings.EMAIL_HOST)
            personal_email_port = int(os.environ.get('PERSONAL_EMAIL_PORT', settings.EMAIL_PORT))
            personal_email_user = os.environ.get('PERSONAL_EMAIL_HOST_USER', settings.EMAIL_HOST_USER)
            personal_email_password = os.environ.get('PERSONAL_EMAIL_HOST_PASSWORD', settings.EMAIL_HOST_PASSWORD)
            
            # Create email message with personal email settings
            email = EmailMessage(
                subject='January is a good excuse',
                body=html_message,
                from_email=personal_email_user,
                to=[user.email],
                connection=None  # We'll create a custom connection
            )
            email.content_subtype = "html"
            
            # Create connection with personal email settings
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
            
            logger.info(f'New Year 2026 email sent to {user.email}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to send New Year 2026 email to {user.email}: {e}')
            return False

    def send_test_email(self, test_email, dry_run):
        """Send a test email to verify the template"""
        self.stdout.write(f'Sending test email to {test_email}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - Would send test email'))
            return
        
        # Create or get a test user for rendering
        test_user, created = User.objects.get_or_create(
            email=test_email,
            defaults={
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        try:
            if self.send_new_year_email(test_user):
                self.stdout.write(self.style.SUCCESS(f'✓ Test email sent to {test_email}'))
            else:
                self.stdout.write(self.style.ERROR(f'✗ Failed to send test email'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed to send test email: {e}'))

    def show_all_emails(self, users):
        """Show all email addresses that will be sent to"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write('EMAILS TO BE SENT')
        self.stdout.write('='*60)
        
        for i, user in enumerate(users, 1):
            self.stdout.write(f'{i:3d}. {user.get_full_name() or user.email} - {user.email}')
        
        self.stdout.write('='*60 + '\n')

    def show_preview(self, user):
        """Show preview of what would be sent"""
        if not user:
            self.stdout.write(self.style.WARNING('No users found for preview'))
            return
        
        base_url = getattr(settings, 'BASE_URL', 'https://www.meettoad.co.uk')
        html_content = render_to_string('accounts/email/follow_up/new_year_26.html', {
            'user': user,
            'base_url': base_url
        })
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write('EMAIL PREVIEW')
        self.stdout.write('='*50)
        self.stdout.write(f'To: {user.email}')
        self.stdout.write(f'Subject: January is a good excuse')
        self.stdout.write(f'Content Length: {len(html_content)} characters')
        self.stdout.write('='*50 + '\n')

