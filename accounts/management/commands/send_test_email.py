from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from accounts.models import User
import base64
import os


class Command(BaseCommand):
    help = 'Send a test email to verify email functionality'

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

    def handle(self, *args, **options):
        email = options['email']
        email_type = options['type']
        user_id = options.get('user_id')
        
        self.stdout.write(f'Sending {email_type} test email to {email}')
        
        # Load the Toad image
        toad_image_data = self.load_toad_image()
        
        if email_type == 'simple':
            success = self.send_simple_test_email(email, toad_image_data)
        elif email_type == 'verification':
            success = self.send_verification_test_email(email, toad_image_data, user_id)
        elif email_type == 'password_reset':
            success = self.send_password_reset_test_email(email, toad_image_data, user_id)
        elif email_type == 'joining':
            success = self.send_joining_test_email(email, toad_image_data, user_id)
        elif email_type == 'beta_update':
            success = self.send_beta_update_test_email(email, toad_image_data, user_id)
        
        if success:
            self.stdout.write(self.style.SUCCESS(f'✓ Test email sent successfully to {email}'))
        else:
            self.stdout.write(self.style.ERROR(f'✗ Failed to send test email to {email}'))

    def load_toad_image(self):
        """Load and encode the Toad email image"""
        image_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'Toad Email Image.png')
        image_data = ""
        if os.path.exists(image_path):
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
        return image_data

    def send_simple_test_email(self, email, toad_image_data):
        """Send a simple test email"""
        subject = "Test Email - Toad Email System"
        
        text_message = f"""
Hi there!

This is a test email from the Toad email system.

If you're receiving this email, it means the email configuration is working correctly.

Email Details:
- From: {settings.DEFAULT_FROM_EMAIL}
- Backend: {settings.EMAIL_BACKEND}
- Host: {getattr(settings, 'EMAIL_HOST', 'Not set')}
- Port: {getattr(settings, 'EMAIL_PORT', 'Not set')}

This is an automated test email sent at {settings.SITE_URL}.

Best regards,
Toad Email System
        """
        
        html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Test Email - Toad</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 8px; }}
        .content {{ padding: 20px 0; }}
        .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center; border-radius: 8px; font-size: 12px; color: #666; }}
        .success {{ color: #28a745; font-weight: bold; }}
        .details {{ background-color: #e9ecef; padding: 15px; border-radius: 5px; margin: 15px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🐸 Test Email - Toad Email System</h1>
        </div>
        
        <div class="content">
            <p>Hi there!</p>
            
            <p>This is a test email from the Toad email system.</p>
            
            <p class="success">✓ If you're receiving this email, it means the email configuration is working correctly.</p>
            
            <div class="details">
                <h3>Email Configuration Details:</h3>
                <ul>
                    <li><strong>From:</strong> {settings.DEFAULT_FROM_EMAIL}</li>
                    <li><strong>Backend:</strong> {settings.EMAIL_BACKEND}</li>
                    <li><strong>Host:</strong> {getattr(settings, 'EMAIL_HOST', 'Not set')}</li>
                    <li><strong>Port:</strong> {getattr(settings, 'EMAIL_PORT', 'Not set')}</li>
                    <li><strong>Site URL:</strong> {settings.SITE_URL}</li>
                </ul>
            </div>
            
            <p>This is an automated test email sent to verify the email system is functioning properly.</p>
        </div>
        
        <div class="footer">
            <p>Best regards,<br>Toad Email System</p>
            <p>© 2024 Toad. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """
        
        try:
            # Use test email sender if configured, otherwise fall back to default
            from_email = getattr(settings, 'TEST_EMAIL_FROM', settings.DEFAULT_FROM_EMAIL)
            
            send_mail(
                subject=subject,
                message=text_message,
                from_email=from_email,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error sending simple test email: {e}'))
            return False

    def send_verification_test_email(self, email, toad_image_data, user_id):
        """Send a verification test email"""
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User with ID {user_id} not found'))
                return False
        else:
            # Create a mock user for testing
            user = type('MockUser', (), {
                'first_name': 'Test',
                'email': email,
                'generate_email_verification_token': lambda: 'test_token_123'
            })()
        
        # Use the existing verification email function
        from accounts.email_utils import send_verification_email
        return send_verification_email(user)

    def send_password_reset_test_email(self, email, toad_image_data, user_id):
        """Send a password reset test email"""
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User with ID {user_id} not found'))
                return False
        else:
            # Create a mock user for testing
            user = type('MockUser', (), {
                'first_name': 'Test',
                'email': email,
                'generate_password_reset_token': lambda: 'test_reset_token_123'
            })()
        
        # Use the existing password reset email function
        from accounts.email_utils import send_password_reset_email
        return send_password_reset_email(user)

    def send_joining_test_email(self, email, toad_image_data, user_id):
        """Send a joining test email"""
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User with ID {user_id} not found'))
                return False
        else:
            # Create a mock user for testing
            user = type('MockUser', (), {
                'first_name': 'Test',
                'email': email,
                'get_short_name': lambda: 'Test',
                'tier': 'free'
            })()
        
        # Use the existing joining email function
        from accounts.email_utils import send_joining_email
        return send_joining_email(user)

    def send_beta_update_test_email(self, email, toad_image_data, user_id):
        """Send a beta update test email"""
        # This would use the existing beta update email template
        subject = "Test Beta Update Email - Toad"
        
        text_message = f"""
Hi there!

This is a test beta update email from Toad.

This email is being sent to test the beta update email functionality.

If you're receiving this email, the beta update email system is working correctly.

Best regards,
Toad Team
        """
        
        try:
            # Use test email sender if configured, otherwise fall back to default
            from_email = getattr(settings, 'TEST_EMAIL_FROM', settings.DEFAULT_FROM_EMAIL)
            
            send_mail(
                subject=subject,
                message=text_message,
                from_email=from_email,
                recipient_list=[email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error sending beta update test email: {e}'))
            return False
