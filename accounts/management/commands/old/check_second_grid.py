from django.core.management.base import BaseCommand
from django.db.models import Count
from accounts.models import User
from pages.models import Project


class Command(BaseCommand):
    help = 'Check each user and update second_grid_created field based on whether they have more than one grid'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='Check only a specific user by ID',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        user_id = options.get('user_id')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
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
        updated_count = 0
        already_correct_count = 0
        users_with_multiple_grids = 0
        users_with_single_grid = 0
        users_with_no_second_grid = []
        
        for user in users:
            # Count non-archived projects (grids) for this user
            grid_count = Project.objects.filter(user=user, is_archived=False).count()
            
            # Determine if user has created a second grid
            has_second_grid = grid_count > 1
            
            # Check current state
            current_state = user.second_grid_created
            
            # Update statistics
            if has_second_grid:
                users_with_multiple_grids += 1
            else:
                users_with_single_grid += 1
                users_with_no_second_grid.append({
                    'email': user.email,
                    'grid_count': grid_count,
                    'current_state': current_state
                })
            
            # Determine if update is needed
            needs_update = current_state != has_second_grid
            
            if needs_update:
                if not dry_run:
                    user.second_grid_created = has_second_grid
                    user.save(update_fields=['second_grid_created'])
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Updated {user.email}: {current_state} → {has_second_grid} '
                            f'({grid_count} grids)'
                        )
                    )
                else:
                    updated_count += 1
                    self.stdout.write(
                        f'[DRY RUN] Would update {user.email}: {current_state} → {has_second_grid} '
                        f'({grid_count} grids)'
                    )
            else:
                already_correct_count += 1
                if grid_count > 0:  # Only show users who have grids
                    self.stdout.write(
                        f'  {user.email}: Already correct ({current_state}, {grid_count} grids)'
                    )
        
        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write('SUMMARY:')
        self.stdout.write('='*60)
        self.stdout.write(f'Total users checked: {len(users)}')
        self.stdout.write(f'Users with multiple grids: {users_with_multiple_grids}')
        self.stdout.write(f'Users with single grid: {users_with_single_grid}')
        self.stdout.write(f'Users with no grids: {len(users) - users_with_multiple_grids - users_with_single_grid}')
        self.stdout.write(f'Updates needed: {updated_count}')
        self.stdout.write(f'Already correct: {already_correct_count}')
        
        # List users who haven't created a second grid
        if users_with_no_second_grid:
            self.stdout.write('\n' + '='*60)
            self.stdout.write('USERS WHO HAVEN\'T CREATED A SECOND GRID:')
            self.stdout.write('='*60)
            for user_info in users_with_no_second_grid:
                self.stdout.write(f'• {user_info["email"]} ({user_info["grid_count"]} grids, second_grid_created={user_info["current_state"]})')
        else:
            self.stdout.write('\n✓ All users have created a second grid!')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN COMPLETED - No changes were made'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\n✓ Updated {updated_count} users'))
