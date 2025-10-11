"""
Management command to send feedback request emails to users.

Usage:
    # Send to all subscribed users
    python manage.py send_feedback_request

    # Send to specific user by email
    python manage.py send_feedback_request --email user@example.com

    # Send to multiple users
    python manage.py send_feedback_request --email user1@example.com --email user2@example.com

    # Dry run (don't actually send emails)
    python manage.py send_feedback_request --dry-run
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.email_utils import send_feedback_request_email

User = get_user_model()


class Command(BaseCommand):
    help = 'Send feedback request emails to users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            action='append',
            help='Email address of specific user(s) to send to. Can be used multiple times.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending emails',
        )
        parser.add_argument(
            '--all-users',
            action='store_true',
            help='Send to all users (including unsubscribed)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        specific_emails = options['email']
        all_users = options['all_users']

        # Get users to send to
        if specific_emails:
            users = User.objects.filter(email__in=specific_emails)
            if not users.exists():
                self.stdout.write(self.style.ERROR(f'No users found with emails: {", ".join(specific_emails)}'))
                return
        elif all_users:
            users = User.objects.filter(is_active=True, email_verified=True)
            self.stdout.write(self.style.WARNING('Sending to ALL users (including unsubscribed)'))
        else:
            # Default: send to subscribed users only
            users = User.objects.filter(
                is_active=True,
                email_verified=True,
                email_subscribed=True
            )

        total_users = users.count()
        
        if total_users == 0:
            self.stdout.write(self.style.WARNING('No users found matching the criteria'))
            return

        # Confirm before sending
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'\n🔍 DRY RUN - Would send feedback request emails to {total_users} users:'))
            for user in users:
                subscribed = '✅' if getattr(user, 'email_subscribed', True) else '❌'
                self.stdout.write(f'  {subscribed} {user.email} ({user.first_name or "No name"})')
            return

        self.stdout.write(self.style.WARNING(f'\n📧 About to send feedback request emails to {total_users} users'))
        
        if not specific_emails:
            confirm = input('Are you sure you want to continue? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Cancelled'))
                return

        # Send emails
        success_count = 0
        error_count = 0
        skipped_count = 0

        self.stdout.write(self.style.SUCCESS(f'\n🚀 Sending emails...\n'))

        for user in users:
            try:
                result = send_feedback_request_email(user)
                if result:
                    success_count += 1
                    self.stdout.write(self.style.SUCCESS(f'✅ Sent to {user.email}'))
                else:
                    skipped_count += 1
                    self.stdout.write(self.style.WARNING(f'⏭️  Skipped {user.email} (likely unsubscribed)'))
            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f'❌ Failed to send to {user.email}: {str(e)}'))

        # Summary
        self.stdout.write(self.style.SUCCESS(f'\n📊 Summary:'))
        self.stdout.write(self.style.SUCCESS(f'  ✅ Successfully sent: {success_count}'))
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f'  ⏭️  Skipped: {skipped_count}'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'  ❌ Errors: {error_count}'))
        self.stdout.write(self.style.SUCCESS(f'  📧 Total: {total_users}'))

