# Generated by Django 5.0.2 on 2025-07-30 21:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_usertier_user_tier'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_verification_sent_at',
            field=models.DateTimeField(blank=True, help_text='When the verification email was sent.', null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='email_verification_token',
            field=models.CharField(blank=True, help_text='Token for email verification.', max_length=100, null=True),
        ),
    ]
