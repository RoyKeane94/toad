from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Test CRON functionality'

    def handle(self, *args, **options):
        self.stdout.write('CRON working')
        self.stdout.write(self.style.SUCCESS('✓ CRON test completed successfully!'))