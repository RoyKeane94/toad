from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from pages.models import Task


class Command(BaseCommand):
    help = 'Update regular_user field based on task activity in the last week'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to look back for activity (default: 7)',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='Check only a specific user by ID',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        days = options['days']
        user_id = options.get('user_id')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Calculate the cutoff date
        cutoff_date = timezone.now() - timedelta(days=days)
        self.stdout.write(f'Looking for activity since: {cutoff_date.strftime("%Y-%m-%d %H:%M:%S")}')
        
        # Get users to check
        if user_id:
            try:
                users = [User.objects.get(id=user_id)]
                self.stdout.write(f'Checking user ID {user_id}: {users[0].email}')
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User with ID {user_id} not found'))
                return
        else:
            users = User.objects.all().order_by('id')
            self.stdout.write(f'Checking {users.count()} users...')
        
        # Statistics
        updated_to_regular = 0
        updated_to_inactive = 0
        already_correct_regular = 0
        already_correct_inactive = 0
        users_with_recent_activity = []
        users_without_recent_activity = []
        
        for user in users:
            # Check for recent task activity
            recent_activity = Task.objects.filter(
                Q(project__user=user) &  # Tasks in user's projects
                Q(
                    Q(created_at__gte=cutoff_date) |  # Created in last week
                    Q(updated_at__gte=cutoff_date)    # Updated in last week
                )
            ).exists()
            
            # Determine if user should be marked as regular
            should_be_regular = recent_activity
            current_state = user.regular_user
            
            # Update statistics
            if recent_activity:
                users_with_recent_activity.append({
                    'email': user.email,
                    'current_state': current_state,
                    'should_be': should_be_regular
                })
            else:
                users_without_recent_activity.append({
                    'email': user.email,
                    'current_state': current_state,
                    'should_be': should_be_regular
                })
            
            # Determine if update is needed
            needs_update = current_state != should_be_regular
            
            if needs_update:
                if not dry_run:
                    user.regular_user = should_be_regular
                    user.save(update_fields=['regular_user'])
                    
                    if should_be_regular:
                        updated_to_regular += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✓ Marked {user.email} as regular user (had recent activity)'
                            )
                        )
                    else:
                        updated_to_inactive += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f'✓ Marked {user.email} as inactive user (no recent activity)'
                            )
                        )
                else:
                    if should_be_regular:
                        updated_to_regular += 1
                        self.stdout.write(
                            f'[DRY RUN] Would mark {user.email} as regular user (has recent activity)'
                        )
                    else:
                        updated_to_inactive += 1
                        self.stdout.write(
                            f'[DRY RUN] Would mark {user.email} as inactive user (no recent activity)'
                        )
            else:
                if should_be_regular:
                    already_correct_regular += 1
                else:
                    already_correct_inactive += 1
        
        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write('SUMMARY:')
        self.stdout.write('='*60)
        self.stdout.write(f'Total users checked: {len(users)}')
        self.stdout.write(f'Users with recent activity: {len(users_with_recent_activity)}')
        self.stdout.write(f'Users without recent activity: {len(users_without_recent_activity)}')
        self.stdout.write(f'Would mark as regular: {updated_to_regular}')
        self.stdout.write(f'Would mark as inactive: {updated_to_inactive}')
        self.stdout.write(f'Already correct (regular): {already_correct_regular}')
        self.stdout.write(f'Already correct (inactive): {already_correct_inactive}')
        
        # List users with recent activity
        if users_with_recent_activity:
            self.stdout.write('\n' + '='*60)
            self.stdout.write('USERS WITH RECENT ACTIVITY:')
            self.stdout.write('='*60)
            for user_info in users_with_recent_activity:
                status = "✓ Regular" if user_info['current_state'] else "→ Will mark as Regular"
                self.stdout.write(f'• {user_info["email"]} ({status})')
        
        # List users without recent activity
        if users_without_recent_activity:
            self.stdout.write('\n' + '='*60)
            self.stdout.write('USERS WITHOUT RECENT ACTIVITY:')
            self.stdout.write('='*60)
            for user_info in users_without_recent_activity:
                status = "✓ Inactive" if not user_info['current_state'] else "→ Will mark as Inactive"
                self.stdout.write(f'• {user_info["email"]} ({status})')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN COMPLETED - No changes were made'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\n✓ Updated {updated_to_regular + updated_to_inactive} users'))
