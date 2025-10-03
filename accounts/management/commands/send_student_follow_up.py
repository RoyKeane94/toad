from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
import logging
import os

User = get_user_model()
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Send student follow-up email to all users with an associated university'

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
        
        # Step 1: Find users with associated university
        users_with_university = User.objects.filter(
            associated_university__isnull=False
        )
        
        # Debug: Let's see what we're actually finding
        self.stdout.write(f'Found {users_with_university.count()} users with associated university')
        
        # Debug: Show some examples
        if users_with_university.exists():
            self.stdout.write('Examples of users with universities:')
            for user in users_with_university[:5]:  # Show first 5
                self.stdout.write(f'  - {user.email}: {user.associated_university}')
        else:
            self.stdout.write('No users found with associated university')
            # Let's check if there are any users at all
            total_users = User.objects.count()
            self.stdout.write(f'Total users in database: {total_users}')
            
            # Check if any users have the field but it's None
            users_with_none = User.objects.filter(associated_university__isnull=True)
            self.stdout.write(f'Users with associated_university=None: {users_with_none.count()}')
            
            # Check if there are any SocietyUniversity records
            from CRM.models import SocietyUniversity
            total_universities = SocietyUniversity.objects.count()
            self.stdout.write(f'Total universities in database: {total_universities}')
            
            if total_universities > 0:
                self.stdout.write('Available universities:')
                for uni in SocietyUniversity.objects.all()[:5]:
                    self.stdout.write(f'  - {uni.name}')
        
        if test_email:
            # Send test email to specific address
            self.send_test_email(test_email, dry_run)
            return
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No emails will be sent'))
            self.show_preview(users_with_university.first())
            return
        
        # Show all emails that will be sent
        self.show_all_emails(users_with_university)
        
        # Confirm before sending
        if not self.confirm_send(users_with_university.count()):
            self.stdout.write(self.style.WARNING('Operation cancelled'))
            return
        
        # Step 2: Send emails and mark as second email sent
        success_count = 0
        error_count = 0
        
        for user in users_with_university:
            try:
                # Send email
                if self.send_student_follow_up_email(user):
                    # Step 3: Mark as second email sent
                    user.second_grid_email_sent = True
                    user.save(update_fields=['second_grid_email_sent'])
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
        self.stdout.write(f'Total users: {users_with_university.count()}')
        self.stdout.write(f'Successfully sent: {success_count}')
        self.stdout.write(f'Failed: {error_count}')
        self.stdout.write('='*50)

    def send_student_follow_up_email(self, user):
        """Send the student follow-up email to a user"""
        try:
            # Render the email template
            html_message = render_to_string('accounts/email/student/student_follow_up_prompt_email.html', {
                'user': user
            })
            
            # Get personal email settings
            personal_email_host = os.environ.get('PERSONAL_EMAIL_HOST', settings.EMAIL_HOST)
            personal_email_port = int(os.environ.get('PERSONAL_EMAIL_PORT', settings.EMAIL_PORT))
            personal_email_user = os.environ.get('PERSONAL_EMAIL_HOST_USER', settings.EMAIL_HOST_USER)
            personal_email_password = os.environ.get('PERSONAL_EMAIL_HOST_PASSWORD', settings.EMAIL_HOST_PASSWORD)
            
            # Create email message with personal email settings
            email = EmailMessage(
                subject='Thanks for being part of Toad!',
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
            
            logger.info(f'Student follow-up email sent to {user.email}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to send student follow-up email to {user.email}: {e}')
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
            html_message = render_to_string('accounts/email/student/student_follow_up_prompt_email.html', {
                'user': test_user
            })
            
            # Get personal email settings
            personal_email_host = os.environ.get('PERSONAL_EMAIL_HOST', settings.EMAIL_HOST)
            personal_email_port = int(os.environ.get('PERSONAL_EMAIL_PORT', settings.EMAIL_PORT))
            personal_email_user = os.environ.get('PERSONAL_EMAIL_HOST_USER', settings.EMAIL_HOST_USER)
            personal_email_password = os.environ.get('PERSONAL_EMAIL_HOST_PASSWORD', settings.EMAIL_HOST_PASSWORD)
            
            # Create email message with personal email settings
            email = EmailMessage(
                subject='[TEST] Thanks for being part of Toad!',
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
        self.stdout.write('\n' + '='*60)
        self.stdout.write('EMAILS TO BE SENT')
        self.stdout.write('='*60)
        
        for i, user in enumerate(users, 1):
            self.stdout.write(f'{i:3d}. {user.get_full_name()} - {user.email}')
        
        self.stdout.write('='*60 + '\n')

    def show_preview(self, user):
        """Show preview of what would be sent"""
        if not user:
            self.stdout.write(self.style.WARNING('No users found for preview'))
            return
        
        html_content = render_to_string('accounts/email/student/student_follow_up_prompt_email.html', {
            'user': user
        })
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write('EMAIL PREVIEW')
        self.stdout.write('='*50)
        self.stdout.write(f'To: {user.email}')
        self.stdout.write(f'Subject: Thanks for being part of Toad!')
        self.stdout.write(f'Content Length: {len(html_content)} characters')
        self.stdout.write('='*50 + '\n')

    def confirm_send(self, total_users):
        """Ask for confirmation before sending emails"""
        self.stdout.write(
            self.style.WARNING(
                f'\n⚠️  You are about to send student follow-up emails to {total_users} users.'
                f'\nThis action cannot be undone.'
                f'\n'
            )
        )
        
        response = input('Are you sure you want to proceed? (type "yes" to confirm): ')
        return response.lower() == 'yes'
