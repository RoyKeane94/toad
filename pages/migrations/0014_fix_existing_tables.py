from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('pages', '0013_personaltemplate_alter_templatecolumnheader_template_and_more'),
    ]

    operations = [
        # This migration is designed to handle existing tables in production
        # It will be applied as a no-op since the tables already exist
        migrations.RunSQL(
            sql="SELECT 1;",  # No-op SQL that works on all databases
            reverse_sql="SELECT 1;",
        ),
    ]