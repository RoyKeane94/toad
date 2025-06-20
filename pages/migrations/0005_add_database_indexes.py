# Generated by Django 5.2.2 on 2025-06-18 19:03

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0004_remove_template_icon'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddIndex(
            model_name='columnheader',
            index=models.Index(fields=['project', 'is_category_column', 'order'], name='pages_colum_project_3dc729_idx'),
        ),
        migrations.AddIndex(
            model_name='project',
            index=models.Index(fields=['user', '-created_at'], name='pages_proje_user_id_0609cb_idx'),
        ),
        migrations.AddIndex(
            model_name='project',
            index=models.Index(fields=['user', 'id'], name='pages_proje_user_id_898f07_idx'),
        ),
        migrations.AddIndex(
            model_name='rowheader',
            index=models.Index(fields=['project', 'order'], name='pages_rowhe_project_89cb1e_idx'),
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['project', 'row_header', 'column_header'], name='pages_task_project_13cc9d_idx'),
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['project', 'completed'], name='pages_task_project_c3acfc_idx'),
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['project', 'created_at'], name='pages_task_project_c90bbf_idx'),
        ),
    ]
