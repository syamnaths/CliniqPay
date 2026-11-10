from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymenttransaction',
            name='gateway_provider',
            field=models.CharField(
                default='native',
                help_text='Underlying gateway engine that processed this transaction',
                max_length=50
            ),
        ),
        migrations.AddField(
            model_name='paymenttransaction',
            name='youpi_payment_id',
            field=models.CharField(
                blank=True,
                help_text='Payment ID issued by YouPI-PG',
                max_length=100,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='paymenttransaction',
            name='webhook_delivery_id',
            field=models.CharField(
                blank=True,
                help_text='X-Gateway-Delivery-Id received for idempotency and deduplication',
                max_length=100,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='paymenttransaction',
            name='is_verified_webhook',
            field=models.BooleanField(
                default=False,
                help_text='True if confirmed via cryptographic HMAC-SHA256 webhook callback'
            ),
        ),
    ]
