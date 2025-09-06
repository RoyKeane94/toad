from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_alter_user_tier_delete_usertier'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='trial_started_at',
            field=models.DateTimeField(null=True, blank=True, help_text='When the user started their trial period.'),
        ),
        migrations.AddField(
            model_name='user',
            name='trial_ends_at',
            field=models.DateTimeField(null=True, blank=True, help_text='When the user trial period ends.'),
        ),
        migrations.AddField(
            model_name='user',
            name='stripe_customer_id',
            field=models.CharField(max_length=100, blank=True, null=True, help_text='Stripe customer ID for billing management.'),
        ),
        migrations.AddField(
            model_name='user',
            name='stripe_subscription_id',
            field=models.CharField(max_length=100, blank=True, null=True, help_text='Stripe subscription ID for billing management.'),
        ),
    ]
