from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('pages', '0013_personaltemplate_alter_templatecolumnheader_template_and_more'),
    ]

    operations = [
        # This migration handles existing tables in production
        # It will work on both SQLite and PostgreSQL
        migrations.RunSQL(
            sql="SELECT 1;",  # No-op for SQLite
            reverse_sql="SELECT 1;",
        ),
    ]