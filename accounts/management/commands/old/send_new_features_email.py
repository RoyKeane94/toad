from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.utils import timezone
from accounts.models import User
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send new features email to all subscribed users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending emails',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit the number of emails to send (for testing)',
        )
        parser.add_argument(
            '--test-email',
            type=str,
            default=None,
            help='Send email to a specific email address for testing',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']
        test_email = options['test_email']
        
        # Get base URL from settings
        base_url = getattr(settings, 'SITE_URL', '').rstrip('/')
        
        # Get all subscribed users
        if test_email:
            # Test to specific email address
            users = User.objects.filter(email=test_email)
            if not users.exists():
                self.stdout.write(
                    self.style.ERROR(f'No user found with email: {test_email}')
                )
                return
        else:
            users = User.objects.filter(
                email_subscribed=True,
                email_verified=True
            ).order_by('id')
        
        if limit:
            users = users[:limit]
            self.stdout.write(f"Limited to {limit} users for testing")
        
        total_users = users.count()
        
        if total_users == 0:
            self.stdout.write(
                self.style.WARNING('No subscribed users found to send emails to')
            )
            return
        
        self.stdout.write(f"Found {total_users} subscribed users")
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No emails will be sent')
            )
            self.stdout.write("Users who would receive the email:")
            for user in users[:10]:  # Show first 10 users
                self.stdout.write(f"  - {user.email} ({user.get_full_name()})")
            if total_users > 10:
                self.stdout.write(f"  ... and {total_users - 10} more users")
            return
        
        # Confirm before sending
        if not self._confirm_sending(total_users):
            self.stdout.write(
                self.style.WARNING('Email sending cancelled by user')
            )
            return
        
        # Send emails
        sent_count = 0
        failed_count = 0
        
        for user in users:
            try:
                # Render the email template for each user
                html_content = render_to_string('accounts/email/features/new_features.html', {
                    'base_url': base_url,
                    'user': user
                })
                
                # Send the email using PERSONAL_EMAIL_HOST configuration
                email = EmailMultiAlternatives(
                    subject='🚀 Team Toad is Here! (+ Task Notes Added!)',
                    body='',  # We're sending HTML only
                    from_email=getattr(settings, 'PERSONAL_DEFAULT_FROM_EMAIL', getattr(settings, 'PERSONAL_EMAIL_HOST_USER', 'tom@meettoad.co.uk')),
                    to=[user.email],
                )
                
                # Add HTML content
                email.attach_alternative(html_content, "text/html")
                
                # Create personal email connection using PERSONAL_EMAIL_* settings
                personal_connection = get_connection(
                    host=getattr(settings, 'PERSONAL_EMAIL_HOST', 'smtp.office365.com'),
                    port=int(getattr(settings, 'PERSONAL_EMAIL_PORT', 587)),
                    username=getattr(settings, 'PERSONAL_EMAIL_HOST_USER', 'tom@meettoad.co.uk'),
                    password=getattr(settings, 'PERSONAL_EMAIL_HOST_PASSWORD', ''),
                    use_tls=getattr(settings, 'PERSONAL_EMAIL_USE_TLS', True),
                    fail_silently=False,
                )
                email.connection = personal_connection
                email.send()
                
                sent_count += 1
                
                # Print each person who receives the email
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Email sent to: {user.email} ({user.get_full_name()})")
                )
                
                # Log progress every 50 emails
                if sent_count % 50 == 0:
                    self.stdout.write(f"Sent {sent_count}/{total_users} emails...")
                
                # Log successful send
                logger.info(f"New features email sent to {user.email}")
                
            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f'Failed to send email to {user.email}: {e}')
                )
                logger.error(f"Failed to send new features email to {user.email}: {e}")
        
        # Final results
        self.stdout.write(
            self.style.SUCCESS(
                f'Email campaign completed!\n'
                f'Successfully sent: {sent_count}\n'
                f'Failed: {failed_count}\n'
                f'Total recipients: {total_users}'
            )
        )
        
        # Log campaign summary
        logger.info(
            f"New features email campaign completed. "
            f"Sent: {sent_count}, Failed: {failed_count}, Total: {total_users}"
        )

    def _confirm_sending(self, total_users):
        """Ask for confirmation before sending emails"""
        self.stdout.write(
            self.style.WARNING(
                f'You are about to send emails to {total_users} users.\n'
                'This action cannot be undone.'
            )
        )
        
        while True:
            response = input('Do you want to continue? (yes/no): ').lower().strip()
            if response in ['yes', 'y']:
                return True
            elif response in ['no', 'n']:
                return False
            else:
                self.stdout.write('Please enter "yes" or "no"')
