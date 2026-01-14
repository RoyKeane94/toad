"""
Reset Template View Counts Command
===================================
Resets template view counts and sign-up click counts for Company objects.

Usage:
    python manage.py reset_template_view_counts                    # Reset all counts
    python manage.py reset_template_view_counts --views-only        # Reset only view counts
    python manage.py reset_template_view_counts --clicks-only       # Reset only click counts
    python manage.py reset_template_view_counts --dry-run          # Preview what would be reset
    python manage.py reset_template_view_counts --company-id 123    # Reset for specific company
"""

from django.core.management.base import BaseCommand
from CRM.models import Company


class Command(BaseCommand):
    help = 'Reset template view counts and sign-up click counts for Company objects'

    def add_arguments(self, parser):
        parser.add_argument(
            '--views-only',
            action='store_true',
            help='Reset only template_view_count (not click counts)',
        )
        parser.add_argument(
            '--clicks-only',
            action='store_true',
            help='Reset only template_sign_up_click_count (not view counts)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be reset without actually resetting',
        )
        parser.add_argument(
            '--company-id',
            type=int,
            default=None,
            help='Reset counts for a specific company ID only',
        )

    def handle(self, *args, **options):
        views_only = options['views_only']
        clicks_only = options['clicks_only']
        dry_run = options['dry_run']
        company_id = options['company_id']

        # Validate arguments
        if views_only and clicks_only:
            self.stdout.write(
                self.style.ERROR('Cannot use --views-only and --clicks-only together')
            )
            return

        # Get companies to reset
        if company_id:
            try:
                companies = Company.objects.filter(pk=company_id)
                if not companies.exists():
                    self.stdout.write(
                        self.style.ERROR(f'Company with ID {company_id} not found')
                    )
                    return
            except ValueError:
                self.stdout.write(
                    self.style.ERROR(f'Invalid company ID: {company_id}')
                )
                return
        else:
            companies = Company.objects.all()

        total_companies = companies.count()

        if total_companies == 0:
            self.stdout.write(self.style.WARNING('No companies found to reset'))
            return

        # Determine what to reset
        reset_views = not clicks_only
        reset_clicks = not views_only

        # Show what will be reset
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('RESET TEMPLATE VIEW COUNTS')
        self.stdout.write('=' * 60)
        
        if company_id:
            self.stdout.write(f'Company ID: {company_id}')
        else:
            self.stdout.write(f'Total companies: {total_companies}')
        
        self.stdout.write(f'Reset view counts: {reset_views}')
        self.stdout.write(f'Reset click counts: {reset_clicks}')
        self.stdout.write(f'Dry run: {dry_run}')
        self.stdout.write('=' * 60 + '\n')

        if dry_run:
            # Show current counts
            if reset_views:
                total_views = sum(company.template_view_count for company in companies)
                companies_with_views = companies.filter(template_view_count__gt=0).count()
                self.stdout.write(
                    self.style.WARNING(
                        f'Would reset {companies_with_views} companies with view counts '
                        f'(total views: {total_views})'
                    )
                )
            
            if reset_clicks:
                total_clicks = sum(company.template_sign_up_click_count for company in companies)
                companies_with_clicks = companies.filter(template_sign_up_click_count__gt=0).count()
                self.stdout.write(
                    self.style.WARNING(
                        f'Would reset {companies_with_clicks} companies with click counts '
                        f'(total clicks: {total_clicks})'
                    )
                )
            
            self.stdout.write(
                self.style.SUCCESS('\n✓ Dry run complete. Use without --dry-run to actually reset.')
            )
            return

        # Perform the reset
        updated_count = 0
        
        if reset_views and reset_clicks:
            # Reset both
            updated_count = companies.update(
                template_view_count=0,
                template_sign_up_click_count=0
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Reset view counts and click counts for {updated_count} companies'
                )
            )
        elif reset_views:
            # Reset only views
            updated_count = companies.update(template_view_count=0)
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Reset view counts for {updated_count} companies'
                )
            )
        elif reset_clicks:
            # Reset only clicks
            updated_count = companies.update(template_sign_up_click_count=0)
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Reset click counts for {updated_count} companies'
                )
            )

        self.stdout.write(
            self.style.SUCCESS('\n✓ Reset complete!')
        )


