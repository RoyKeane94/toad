from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
import os


class Command(BaseCommand):
    help = 'Check migration status and debug production issues'

    def handle(self, *args, **options):
        # Print environment info
        self.stdout.write("=== ENVIRONMENT DEBUG ===")
        self.stdout.write(f"DJANGO_DEBUG_ENVIRONMENT: {os.environ.get('DJANGO_DEBUG_ENVIRONMENT', 'NOT SET')}")
        
        from django.conf import settings
        self.stdout.write(f"IS_PRODUCTION: {getattr(settings, 'IS_PRODUCTION', 'NOT SET')}")
        self.stdout.write(f"DEBUG: {getattr(settings, 'DEBUG', 'NOT SET')}")
        self.stdout.write(f"Database ENGINE: {settings.DATABASES['default']['ENGINE']}")
        
        # Check if we can connect to database
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                self.stdout.write("✓ Database connection successful")
        except Exception as e:
            self.stdout.write(f"✗ Database connection failed: {e}")
            return

        # Check migration status
        self.stdout.write("\n=== MIGRATION STATUS ===")
        try:
            call_command('showmigrations', '--plan', verbosity=2)
        except Exception as e:
            self.stdout.write(f"Error checking migrations: {e}")

        # Check if the specific fields exist in the database
        self.stdout.write("\n=== TABLE STRUCTURE CHECK ===")
        try:
            with connection.cursor() as cursor:
                # Check if accounts_user table exists and has the new fields
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'accounts_user' 
                    AND column_name IN ('email_verified', 'last_login_ip', 'failed_login_attempts', 'account_locked_until')
                    ORDER BY column_name;
                """)
                fields = [row[0] for row in cursor.fetchall()]
                
                if fields:
                    self.stdout.write(f"✓ Found security fields: {', '.join(fields)}")
                else:
                    self.stdout.write("✗ Security fields not found in database")
                    
                    # Show all columns in accounts_user table
                    cursor.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'accounts_user' 
                        ORDER BY column_name;
                    """)
                    all_fields = [row[0] for row in cursor.fetchall()]
                    self.stdout.write(f"Available fields: {', '.join(all_fields)}")
                    
        except Exception as e:
            # Fallback for SQLite or other databases
            self.stdout.write(f"Could not check table structure (might be SQLite): {e}")
            try:
                from accounts.models import User
                user = User.objects.first()
                if user and hasattr(user, 'email_verified'):
                    self.stdout.write("✓ User model has email_verified field")
                else:
                    self.stdout.write("✗ User model missing email_verified field")
            except Exception as model_e:
                self.stdout.write(f"Error checking User model: {model_e}") 