from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('setup_hospital', '0023_remove_hospitalstaff_raw_password'),
    ]

    operations = [
        migrations.AddField(
            model_name='hospital',
            name='upi_gateway_provider',
            field=models.CharField(
                choices=[('native', 'Direct Merchant VPA (Default)'), ('youpi', 'YouPI-PG Sovereign UPI Gateway')],
                default='native',
                max_length=20,
                help_text='Payment processing engine for dynamic UPI transactions'
            ),
        ),
        migrations.AddField(
            model_name='hospital',
            name='youpi_api_url',
            field=models.CharField(
                blank=True,
                default='http://localhost:6100',
                help_text='Base URL of self-hosted YouPI-PG Core API instance',
                max_length=255,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='hospital',
            name='youpi_merchant_id',
            field=models.CharField(
                blank=True,
                help_text='Merchant UUID assigned in YouPI-PG admin panel',
                max_length=100,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='hospital',
            name='youpi_webhook_secret',
            field=models.CharField(
                blank=True,
                help_text='Secret key used to verify HMAC-SHA256 signatures of YouPI webhooks',
                max_length=100,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='hospital',
            name='youpi_sandbox_mode',
            field=models.BooleanField(
                default=True,
                help_text='Enable simulated/sandbox testing when external YouPI daemon is offline'
            ),
        ),
    ]
