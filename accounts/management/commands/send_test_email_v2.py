from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from accounts.models import User
from accounts.email_utils import send_test_email
from accounts.tom_email_utils import send_tom_test_email
import base64
import os


class Command(BaseCommand):
    help = 'Send a test email from either accounts@meettoad.co.uk or tom@meettoad.co.uk'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            required=True,
            help='Email address to send test email to',
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['verification', 'password_reset', 'joining', 'beta_update', 'simple'],
            default='simple',
            help='Type of test email to send (default: simple)',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='User ID to use for user-specific emails (optional)',
        )
        parser.add_argument(
            '--sender',
            type=str,
            choices=['accounts', 'personal'],
            default='accounts',
            help='Sender: accounts (EMAIL_HOST_USER) or personal (PERSONAL_EMAIL_HOST_USER) (default: accounts)',
        )

    def handle(self, *args, **options):
        email = options['email']
        email_type = options['type']
        user_id = options.get('user_id')
        sender = options['sender']
        
        sender_display = f"{sender} account ({'EMAIL_HOST_USER' if sender == 'accounts' else 'PERSONAL_EMAIL_HOST_USER'})"
        self.stdout.write(f'Sending {email_type} test email to {email} from {sender_display}')
        
        # Get user if provided
        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                self.stdout.write(f'Using user: {user.email} ({user.first_name} {user.last_name})')
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User with ID {user_id} not found'))
                return
        
        # Send email based on sender choice
        if sender == 'personal':
            success = self.send_personal_email(email, email_type, user)
        else:  # accounts
            success = self.send_accounts_email(email, email_type, user)
        
        if success:
            self.stdout.write(self.style.SUCCESS(f'✓ Test email sent successfully to {email} from {sender_display}'))
        else:
            self.stdout.write(self.style.ERROR(f'✗ Failed to send test email to {email} from {sender_display}'))

    def send_accounts_email(self, email, email_type, user):
        """Send email from accounts@meettoad.co.uk"""
        try:
            if email_type == 'simple':
                return send_test_email(email, 'simple')
            elif email_type in ['verification', 'password_reset', 'joining'] and user:
                return send_test_email(email, email_type, user)
            else:
                self.stdout.write(self.style.ERROR(f'Invalid email type "{email_type}" or missing user for user-specific email'))
                return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error sending accounts email: {e}'))
            return False

    def send_personal_email(self, email, email_type, user):
        """Send email from personal account (PERSONAL_EMAIL_HOST_USER)"""
        try:
            if email_type == 'simple':
                return send_tom_test_email(email, 'simple')
            elif email_type in ['verification', 'password_reset', 'joining'] and user:
                return send_tom_test_email(email, email_type, user)
            else:
                self.stdout.write(self.style.ERROR(f'Invalid email type "{email_type}" or missing user for user-specific email'))
                return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error sending personal email: {e}'))
            return False
