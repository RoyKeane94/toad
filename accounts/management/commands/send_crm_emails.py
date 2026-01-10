"""
CRM Email Automation Command
============================
Sends automated email sequences to B2B companies based on sector templates.

Email Sequence (Production):
- Email 1: Initial outreach (sent immediately when eligible)
- Email 2: First follow-up (4 days after Email 1)
- Email 3: Second follow-up (5 days after Email 2)
- Email 4: Final follow-up (10 days after Email 3)

Emails are only sent on Tuesday, Wednesday, and Thursday.
If the scheduled date falls on Fri/Sat/Sun/Mon, it will be sent on the next Tuesday.

Test Mode (--test-mode):
- All delay requirements are bypassed (send next email immediately)
- Day restrictions are ignored
- Run the command multiple times to send each email in sequence

Usage:
    python manage.py send_crm_emails                    # Send all eligible emails
    python manage.py send_crm_emails --dry-run          # Preview what would be sent
    python manage.py send_crm_emails --limit 10         # Send max 10 emails
    python manage.py send_crm_emails --sector "Wedding Venues"  # Only this sector
    python manage.py send_crm_emails --test-mode        # 1-minute delays for testing
"""

from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta
import logging
import uuid
import os

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send automated CRM email sequences to B2B companies'

    # Days required between emails (production mode)
    EMAIL_DELAYS_DAYS = {
        1: 0,   # Email 1: Send immediately
        2: 4,   # Email 2: 4 days after Email 1
        3: 5,   # Email 3: 5 days after Email 2
        4: 10,  # Email 4: 10 days after Email 3
    }
    
    # Valid days for sending (0=Monday, 1=Tuesday, etc.)
    VALID_SEND_DAYS = {1, 2, 3}  # Tuesday, Wednesday, Thursday

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be sent without actually sending emails',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Maximum number of emails to send in this run',
        )
        parser.add_argument(
            '--sector',
            type=str,
            default=None,
            help='Only process companies in this sector (exact name match)',
        )
        parser.add_argument(
            '--force-day',
            action='store_true',
            help='Force sending even if today is not Tue/Wed/Thu (for testing)',
        )
        parser.add_argument(
            '--test-mode',
            action='store_true',
            help='Test mode: 1-minute delays between emails instead of days, ignores day restrictions',
        )
        parser.add_argument(
            '--test-email',
            type=str,
            default=None,
            help='Send a test email to this address using the first available template',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']
        sector_filter = options['sector']
        force_day = options['force_day']
        test_mode = options['test_mode']
        test_email = options['test_email']
        
        # Store test_mode as instance variable for use in other methods
        self.test_mode = test_mode
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('CRM EMAIL AUTOMATION')
        self.stdout.write('=' * 60)
        
        if test_mode:
            self.stdout.write(self.style.WARNING('\n🧪 TEST MODE ENABLED'))
            self.stdout.write(self.style.WARNING('   - All delay requirements bypassed'))
            self.stdout.write(self.style.WARNING('   - Day restrictions disabled'))
            self.stdout.write(self.style.WARNING('   - Run command multiple times to send full sequence'))
            force_day = True  # Test mode implies force_day
        
        # Check if today is a valid send day
        now = timezone.now()
        today = now.date()
        day_of_week = today.weekday()
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        self.stdout.write(f'Today: {today.strftime("%A, %B %d, %Y")}')
        if test_mode:
            self.stdout.write(f'Current time: {now.strftime("%H:%M:%S")}')
        
        if day_of_week not in self.VALID_SEND_DAYS and not force_day:
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️  Today is {day_names[day_of_week]}. '
                    f'Emails are only sent on Tuesday, Wednesday, and Thursday.'
                    f'\nUse --force-day or --test-mode to override.'
                )
            )
            return
        
        if force_day and day_of_week not in self.VALID_SEND_DAYS and not test_mode:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Force mode: Sending on {day_names[day_of_week]}')
            )
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n📋 DRY RUN MODE - No emails will be sent'))
        
        if test_email:
            self.send_test_email(test_email, dry_run)
            return
        
        # Import models here to avoid circular imports
        from CRM.models import Company, CompanySector, EmailTemplate, CustomerTemplate
        
        # Get companies to process
        companies = Company.objects.select_related('company_sector').filter(
            company_sector__isnull=False,
            contact_email__isnull=False,
            initial_email_response=False,  # Don't email if they've responded
        ).exclude(
            contact_email=''  # Must have email
        ).exclude(
            status='Rejected'  # Don't email rejected companies
        ).exclude(
            status='Customer'  # Don't email customers (they've already converted)
        )
        
        # Filter by sector if specified
        if sector_filter:
            companies = companies.filter(company_sector__name__iexact=sector_filter)
            self.stdout.write(f'Filtering by sector: {sector_filter}')
        
        # Separate companies by which email they need
        email_1_companies = []
        email_2_companies = []
        email_3_companies = []
        email_4_companies = []
        
        for company in companies:
            # Check if sector has templates
            templates = EmailTemplate.objects.filter(company_sector=company.company_sector)
            if not templates.exists():
                continue
            
            next_email = self.get_next_email_to_send(company, today)
            if next_email == 1:
                email_1_companies.append(company)
            elif next_email == 2:
                email_2_companies.append(company)
            elif next_email == 3:
                email_3_companies.append(company)
            elif next_email == 4:
                email_4_companies.append(company)
        
        # Show summary
        self.stdout.write('\n' + '-' * 40)
        self.stdout.write('ELIGIBLE COMPANIES:')
        self.stdout.write(f'  Email 1 (Initial):      {len(email_1_companies)}')
        self.stdout.write(f'  Email 2 (Follow-up 1):  {len(email_2_companies)}')
        self.stdout.write(f'  Email 3 (Follow-up 2):  {len(email_3_companies)}')
        self.stdout.write(f'  Email 4 (Final):        {len(email_4_companies)}')
        self.stdout.write('-' * 40)
        
        total_eligible = (
            len(email_1_companies) + len(email_2_companies) + 
            len(email_3_companies) + len(email_4_companies)
        )
        
        if total_eligible == 0:
            self.stdout.write(self.style.SUCCESS('\n✓ No emails to send at this time.'))
            return
        
        # Apply limit
        all_companies = []
        for email_num, company_list in [
            (1, email_1_companies),
            (2, email_2_companies),
            (3, email_3_companies),
            (4, email_4_companies),
        ]:
            for company in company_list:
                all_companies.append((email_num, company))
        
        if limit:
            all_companies = all_companies[:limit]
            self.stdout.write(f'\nLimit applied: Processing {len(all_companies)} of {total_eligible}')
        
        # Process and send emails
        success_count = 0
        error_count = 0
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('PROCESSING EMAILS')
        self.stdout.write('=' * 60)
        
        for email_num, company in all_companies:
            result = self.process_company_email(company, email_num, dry_run, today)
            if result:
                success_count += 1
            else:
                error_count += 1
        
        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('SUMMARY')
        self.stdout.write('=' * 60)
        self.stdout.write(f'Total processed: {len(all_companies)}')
        self.stdout.write(f'Successful: {success_count}')
        self.stdout.write(f'Failed: {error_count}')
        self.stdout.write('=' * 60 + '\n')

    def get_next_email_to_send(self, company, today):
        """
        Determine which email number should be sent next for a company.
        Returns 1-4, or None if no email should be sent.
        """
        # Check if company has responded - don't send any more emails
        if company.initial_email_response:
            return None
        
        # Email 1: Never sent initial email
        if not company.initial_email_sent or not company.initial_email_sent_date:
            return 1
        
        # Email 2: Sent initial but not second
        if not company.second_email_sent_date:
            if self.is_email_due(company.initial_email_sent_date, 2, today):
                return 2
            return None
        
        # Email 3: Sent second but not third
        if not company.third_email_sent_date:
            if self.is_email_due(company.second_email_sent_date, 3, today):
                return 3
            return None
        
        # Email 4: Sent third but not fourth
        if not company.fourth_email_sent_date:
            if self.is_email_due(company.third_email_sent_date, 4, today):
                return 4
            return None
        
        # All 4 emails sent
        return None

    def is_email_due(self, last_sent_date, email_number, current_time):
        """
        Check if enough time has passed since the last email.
        
        In production mode: Uses days and checks valid send days
        In test mode: Always returns True (send immediately when previous email exists)
        
        Note: Test mode allows immediate sending because the model uses DateField,
        not DateTimeField, so minute-level tracking isn't possible. Run the command
        multiple times with 1 minute gap to test the full sequence.
        """
        if not last_sent_date:
            return email_number == 1
        
        if getattr(self, 'test_mode', False):
            # Test mode: Always allow if previous email was sent
            # User should wait 1 minute between command runs to test sequence
            return True
        else:
            # Production mode: Use days
            delay_days = self.EMAIL_DELAYS_DAYS.get(email_number, 0)
            today = current_time if isinstance(current_time, type(last_sent_date)) else current_time.date() if hasattr(current_time, 'date') else current_time
            scheduled_date = last_sent_date + timedelta(days=delay_days)
            
            # Adjust to next valid day if scheduled date falls on invalid day
            adjusted_date = self.adjust_to_valid_day(scheduled_date)
            
            return today >= adjusted_date

    def adjust_to_valid_day(self, date):
        """
        Adjust a date to the next valid send day (Tue/Wed/Thu).
        If date falls on Fri/Sat/Sun/Mon, move to next Tuesday.
        """
        day_of_week = date.weekday()
        
        if day_of_week in self.VALID_SEND_DAYS:
            return date
        
        # Calculate days until next Tuesday
        if day_of_week == 0:  # Monday -> Tuesday (+1)
            return date + timedelta(days=1)
        elif day_of_week == 4:  # Friday -> Tuesday (+4)
            return date + timedelta(days=4)
        elif day_of_week == 5:  # Saturday -> Tuesday (+3)
            return date + timedelta(days=3)
        elif day_of_week == 6:  # Sunday -> Tuesday (+2)
            return date + timedelta(days=2)
        
        return date

    def process_company_email(self, company, email_number, dry_run, today):
        """
        Process and send an email to a company.
        Returns True on success, False on failure.
        """
        from CRM.models import EmailTemplate, CustomerTemplate
        
        self.stdout.write(f'\n[Email {email_number}] {company.company_name}')
        self.stdout.write(f'  To: {company.contact_email}')
        
        # Get the template for this sector and email number
        try:
            template = EmailTemplate.objects.get(
                company_sector=company.company_sector,
                email_number=email_number
            )
        except EmailTemplate.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(f'  ⚠️  No template found for {company.company_sector.name} Email {email_number}')
            )
            return False
        
        # Get personalized template URL
        base_url = getattr(settings, 'SITE_URL', 'https://www.meettoad.co.uk')
        template_url = company.get_personalized_template_url(base_url=base_url)
        
        # Render email content
        new_body = template.render_body(company, template_url)
        
        # For threading: Email 1 uses template subject, follow-ups use "Re: [original subject]"
        if email_number == 1:
            subject = template.render_subject(company)
            body = new_body
        else:
            # Use "Re: [first email subject]" for threading
            if company.first_email_subject:
                subject = f"Re: {company.first_email_subject}"
            else:
                # Fallback to template subject if first subject not stored
                subject = template.render_subject(company)
            
            # Include quoted previous email for threading
            body = self.add_quoted_reply(new_body, company)
        
        self.stdout.write(f'  Subject: {subject[:50]}...' if len(subject) > 50 else f'  Subject: {subject}')
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS('  ✓ Would send (dry run)'))
            return True
        
        # Send the email
        try:
            message_id = self.send_email(
                to_email=company.contact_email,
                subject=subject,
                body=body,
                company=company,
                email_number=email_number,
            )
            
            if message_id:
                # Update company record (pass subject and body for threading)
                # Store the new message body (without quoted replies) for future quoting
                self.update_company_after_send(company, email_number, today, message_id, subject=subject, body=template.render_body(company, template_url))
                self.stdout.write(self.style.SUCCESS('  ✓ Sent successfully'))
                return True
            else:
                # Email failed
                company.email_failed_date = today
                company.save(update_fields=['email_failed_date'])
                self.stdout.write(self.style.ERROR('  ✗ Send failed'))
                return False
                
        except Exception as e:
            logger.error(f'Error sending email to {company.contact_email}: {e}')
            company.email_failed_date = today
            company.save(update_fields=['email_failed_date'])
            self.stdout.write(self.style.ERROR(f'  ✗ Error: {e}'))
            return False

    def send_email(self, to_email, subject, body, company, email_number):
        """
        Send an HTML email using Tom's email backend.
        Returns the Message-ID on success, None on failure.
        """
        from accounts.tom_email_backend import TomEmailBackend
        
        # Generate Message-ID
        message_id = f'<{uuid.uuid4()}@meettoad.co.uk>'
        
        # Get email settings
        email_host = getattr(settings, 'TOM_EMAIL_HOST', settings.EMAIL_HOST)
        email_port = getattr(settings, 'TOM_EMAIL_PORT', settings.EMAIL_PORT)
        email_user = getattr(settings, 'TOM_EMAIL_USER', settings.EMAIL_HOST_USER)
        email_password = getattr(settings, 'TOM_EMAIL_PASSWORD', settings.EMAIL_HOST_PASSWORD)
        use_tls = getattr(settings, 'TOM_EMAIL_USE_TLS', settings.EMAIL_USE_TLS)
        use_ssl = getattr(settings, 'TOM_EMAIL_USE_SSL', getattr(settings, 'EMAIL_USE_SSL', False))
        
        # Convert plain text body to HTML (preserve line breaks)
        html_body = self.convert_to_html(body)
        
        # Create email message
        email = EmailMessage(
            subject=subject,
            body=html_body,
            from_email=email_user,
            to=[to_email],
        )
        
        # Set content type to HTML
        email.content_subtype = 'html'
        
        # Set headers for threading
        email.extra_headers = {
            'Message-ID': message_id,
        }
        
        # For follow-up emails, add threading headers
        if email_number > 1 and company.first_email_message_id:
            email.extra_headers['In-Reply-To'] = company.first_email_message_id
            email.extra_headers['References'] = company.first_email_message_id
        
        # Create backend
        try:
            backend = TomEmailBackend(
                host=email_host,
                port=email_port,
                username=email_user,
                password=email_password,
                use_tls=use_tls,
                use_ssl=use_ssl,
                fail_silently=False,
            )
            
            email.connection = backend
            email.send()
            
            logger.info(f'CRM email {email_number} sent to {to_email} for {company.company_name}')
            return message_id
            
        except Exception as e:
            logger.error(f'Failed to send CRM email to {to_email}: {e}')
            return None

    def add_quoted_reply(self, new_body, company):
        """
        Add the previous email below the new message.
        Creates the standard email reply format with "On [date], [sender] wrote:"
        """
        if not company.last_email_body:
            return new_body
        
        # Get the date of the last email
        if company.last_email_date:
            date_str = company.last_email_date.strftime('%a, %b %d, %Y at %I:%M %p')
        else:
            date_str = 'a previous date'
        
        # Get sender info
        sender_email = getattr(settings, 'TOM_EMAIL_USER', settings.EMAIL_HOST_USER)
        
        # Combine new message with previous email
        full_body = f"""{new_body}

---

On {date_str}, {sender_email} wrote:

{company.last_email_body}"""
        
        return full_body

    def convert_to_html(self, text):
        """
        Convert plain text to HTML, preserving line breaks and handling the 
        embedded link placeholders which are already HTML.
        """
        import re
        
        # Temporarily protect HTML tags (like our personalised_link)
        html_tags = []
        def protect_html(match):
            html_tags.append(match.group(0))
            return f'__HTML_TAG_{len(html_tags) - 1}__'
        
        # Protect any existing HTML tags
        text = re.sub(r'<[^>]+>', protect_html, text)
        
        # Escape remaining HTML entities
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        
        # Convert line breaks to <br>
        text = text.replace('\n', '<br>\n')
        
        # Restore protected HTML tags
        for i, tag in enumerate(html_tags):
            text = text.replace(f'__HTML_TAG_{i}__', tag)
        
        # Wrap in minimal HTML structure
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.5; color: #333;">
{text}
</body>
</html>"""
        return html

    def update_company_after_send(self, company, email_number, today, message_id, subject=None, body=None):
        """
        Update the company record after successfully sending an email.
        """
        update_fields = []
        
        if email_number == 1:
            company.initial_email_sent = True
            company.initial_email_sent_date = today
            company.email_status = '1'
            company.first_email_message_id = message_id
            # Store the subject for threading follow-up emails
            if subject:
                company.first_email_subject = subject
            update_fields = ['initial_email_sent', 'initial_email_sent_date', 'email_status', 'first_email_message_id', 'first_email_subject']
        elif email_number == 2:
            company.second_email_sent_date = today
            company.email_status = '2'
            update_fields = ['second_email_sent_date', 'email_status']
        elif email_number == 3:
            company.third_email_sent_date = today
            company.email_status = '3'
            update_fields = ['third_email_sent_date', 'email_status']
        elif email_number == 4:
            company.fourth_email_sent_date = today
            company.email_status = '4'
            update_fields = ['fourth_email_sent_date', 'email_status']
        
        # Store the email body and timestamp for quoting in next email
        if body:
            company.last_email_body = body
            company.last_email_date = timezone.now()
            update_fields.extend(['last_email_body', 'last_email_date'])
        
        # Clear any previous failure date
        company.email_failed_date = None
        update_fields.append('email_failed_date')
        
        company.save(update_fields=update_fields)

    def send_test_email(self, test_email, dry_run):
        """
        Send a test email to verify the setup is working.
        """
        from CRM.models import EmailTemplate, CompanySector
        
        self.stdout.write(f'\nSending test email to: {test_email}')
        
        # Find first available template
        template = EmailTemplate.objects.first()
        if not template:
            self.stdout.write(self.style.ERROR('No email templates found. Create one first.'))
            return
        
        self.stdout.write(f'Using template: {template.name}')
        
        # Create sample data
        test_url = 'https://meettoad.co.uk/crm/links/templates/1/?company_id=test'
        subject = template.subject.replace('{company_name}', 'Test Company')
        subject = subject.replace('{contact_person}', 'Test User')
        subject = f'[TEST] {subject}'
        
        body = template.body.replace('{company_name}', 'Test Company')
        body = body.replace('{contact_person}', 'Test User')
        body = body.replace('{personalised_template_url}', test_url)
        body = body.replace('{personalised_link}', f'<b><a href="{test_url}">Toad x Test Company</a></b>')
        
        self.stdout.write(f'Subject: {subject}')
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS('✓ Would send test email (dry run)'))
            self.stdout.write('\nEmail body preview:')
            self.stdout.write('-' * 40)
            self.stdout.write(body[:500] + ('...' if len(body) > 500 else ''))
            self.stdout.write('-' * 40)
            return
        
        from accounts.tom_email_backend import TomEmailBackend
        
        email_host = getattr(settings, 'TOM_EMAIL_HOST', settings.EMAIL_HOST)
        email_port = getattr(settings, 'TOM_EMAIL_PORT', settings.EMAIL_PORT)
        email_user = getattr(settings, 'TOM_EMAIL_USER', settings.EMAIL_HOST_USER)
        email_password = getattr(settings, 'TOM_EMAIL_PASSWORD', settings.EMAIL_HOST_PASSWORD)
        use_tls = getattr(settings, 'TOM_EMAIL_USE_TLS', settings.EMAIL_USE_TLS)
        use_ssl = getattr(settings, 'TOM_EMAIL_USE_SSL', getattr(settings, 'EMAIL_USE_SSL', False))
        
        try:
            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=email_user,
                to=[test_email],
            )
            
            backend = TomEmailBackend(
                host=email_host,
                port=email_port,
                username=email_user,
                password=email_password,
                use_tls=use_tls,
                use_ssl=use_ssl,
                fail_silently=False,
            )
            
            email.connection = backend
            email.send()
            
            self.stdout.write(self.style.SUCCESS(f'✓ Test email sent to {test_email}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed to send test email: {e}'))

