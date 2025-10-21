from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from accounts.models import User


class Command(BaseCommand):
    help = 'Send a test 2-day follow-up email to a specific email address'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default=None,
            help='Email address to send the test email to',
        )

    def handle(self, *args, **options):
        test_email = options['email']
        
        if not test_email:
            self.stdout.write(
                self.style.ERROR('Please provide an email address using --email')
            )
            return
        
        # Try to find a user with this email, or use a default user
        try:
            user = User.objects.get(email=test_email)
            self.stdout.write(
                self.style.SUCCESS(f'Found user: {user.get_full_name()} ({user.email})')
            )
        except User.DoesNotExist:
            # Use the first user as a fallback for testing
            user = User.objects.first()
            if not user:
                self.stdout.write(
                    self.style.ERROR('No users found in database')
                )
                return
            self.stdout.write(
                self.style.WARNING(f'User not found, using: {user.get_full_name()} ({user.email}) for template data')
            )
        
        # Prepare context
        base_url = getattr(settings, 'BASE_URL', 'https://www.meettoad.co.uk')
        context = {
            'user': user,
            'base_url': base_url,
        }
        
        # Render email
        try:
            html_content = render_to_string(
                'accounts/email/follow_up/2_day_follow_up_email.html',
                context
            )
            
            # Create email
            subject = 'Getting the Most Out of Toad?'
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@meettoad.co.uk')
            
            email = EmailMultiAlternatives(
                subject=subject,
                body='This is an HTML email. Please view in an HTML-compatible email client.',
                from_email=from_email,
                to=[test_email],
            )
            email.attach_alternative(html_content, "text/html")
            
            # Send email
            email.send()
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Test email sent successfully to: {test_email}')
            )
            self.stdout.write(
                self.style.SUCCESS(f'Subject: {subject}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to send email: {str(e)}')
            )

