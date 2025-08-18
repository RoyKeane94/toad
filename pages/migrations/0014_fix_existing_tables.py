from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('pages', '0013_personaltemplate_alter_templatecolumnheader_template_and_more'),
    ]

    operations = [
        # This will check if tables exist and skip creation if they do
        migrations.RunSQL(
            sql="",  # No SQL needed
            reverse_sql="",  # No reverse SQL needed
            state_operations=[
                # These operations only update Django's state, not the database
                migrations.CreateModel(
                    name='ProjectGroup',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('name', models.CharField(max_length=100)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                    ],  # Added missing comma and closing bracket
                ),
                migrations.AddField(
                    model_name='project',
                    name='project_group',
                    field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='pages.projectgroup'),
                ),
            ],
        ),
    ]