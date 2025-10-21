from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from accounts.models import User
import base64
import os
import time
from django.utils import timezone


class Command(BaseCommand):
    help = 'Send beta update email to all users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending emails',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Number of emails to send per batch (default: 50)',
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=1.0,
            help='Delay between batches in seconds (default: 1.0)',
        )
        parser.add_argument(
            '--test-email',
            type=str,
            help='Send test email to specific email address only',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting beta update email campaign...'))
        
        # Load the Toad image
        toad_image_data = self.load_toad_image()
        
        if options['test_email']:
            # Send test email to specific address
            self.send_test_email(options['test_email'], toad_image_data, options['dry_run'])
            return
        
        # Get all users (you might want to filter this based on your needs)
        users = User.objects.filter(
            is_active=True,
            email_verified=True  # Only send to verified users
        ).order_by('id')
        
        total_users = users.count()
        self.stdout.write(f'Found {total_users} users to email')
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No emails will be sent'))
            self.show_preview(users.first(), toad_image_data)
            return
        
        # Confirm before sending
        if not self.confirm_send(total_users):
            self.stdout.write(self.style.WARNING('Email campaign cancelled'))
            return
        
        # Send emails in batches
        batch_size = options['batch_size']
        delay = options['delay']
        sent_count = 0
        failed_count = 0
        
        for i in range(0, total_users, batch_size):
            batch = users[i:i + batch_size]
            self.stdout.write(f'Sending batch {i // batch_size + 1} ({len(batch)} emails)...')
            
            for user in batch:
                try:
                    self.send_email_to_user(user, toad_image_data)
                    sent_count += 1
                    self.stdout.write(f'✓ Sent to {user.email}')
                except Exception as e:
                    failed_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'✗ Failed to send to {user.email}: {str(e)}')
                    )
            
            # Add delay between batches to avoid overwhelming email server
            if i + batch_size < total_users:
                self.stdout.write(f'Waiting {delay} seconds before next batch...')
                time.sleep(delay)
        
        # Summary
        self.stdout.write(self.style.SUCCESS(
            f'\nEmail campaign completed!'
            f'\n✓ Successfully sent: {sent_count}'
            f'\n✗ Failed: {failed_count}'
            f'\n📧 Total processed: {sent_count + failed_count}'
        ))

    def load_toad_image(self):
        """Load and encode the Toad email image"""
        try:
            image_path = os.path.join(settings.STATICFILES_DIRS[0], 'img', 'Toad Email Image.png')
            if os.path.exists(image_path):
                with open(image_path, 'rb') as image_file:
                    return base64.b64encode(image_file.read()).decode('utf-8')
        except (IndexError, FileNotFoundError):
            pass
        
        self.stdout.write(self.style.WARNING('Toad email image not found - emails will be sent without image'))
        return None

    def send_email_to_user(self, user, toad_image_data):
        """Send beta update email to a specific user"""
        # Render the email template
        html_content = render_to_string('accounts/email/beta_update_email.html', {
            'user': user,
            'toad_image_data': toad_image_data
        })
        
        # Create email
        email = EmailMessage(
            subject='Your feedback is making Toad better. Here\'s what\'s new.',
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.content_subtype = 'html'  # Set content type to HTML
        
        # Send email
        email.send()

    def send_test_email(self, test_email, toad_image_data, dry_run):
        """Send test email to specific address"""
        self.stdout.write(f'Sending test email to: {test_email}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - Test email not sent'))
            return
        
        # Create a mock user for the test
        class MockUser:
            email = test_email
            first_name = 'Test User'
        
        try:
            self.send_email_to_user(MockUser(), toad_image_data)
            self.stdout.write(self.style.SUCCESS('✓ Test email sent successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed to send test email: {str(e)}'))

    def show_preview(self, user, toad_image_data):
        """Show preview of what would be sent"""
        if not user:
            self.stdout.write(self.style.WARNING('No users found for preview'))
            return
        
        html_content = render_to_string('accounts/email/beta_update_email.html', {
            'user': user,
            'toad_image_data': toad_image_data
        })
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write('EMAIL PREVIEW')
        self.stdout.write('='*50)
        self.stdout.write(f'To: {user.email}')
        self.stdout.write(f'Subject: Your feedback is making Toad better. Here\'s what\'s new.')
        self.stdout.write(f'Content Length: {len(html_content)} characters')
        self.stdout.write('='*50 + '\n')

    def confirm_send(self, total_users):
        """Ask for confirmation before sending emails"""
        self.stdout.write(
            self.style.WARNING(
                f'\n⚠️  You are about to send emails to {total_users} users.'
                f'\nThis action cannot be undone.'
                f'\n'
            )
        )
        
        response = input('Are you sure you want to proceed? (type "yes" to confirm): ')
        return response.lower() == 'yes'
