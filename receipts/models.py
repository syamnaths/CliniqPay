import uuid
from django.db import models
from django.utils import timezone
from setup_hospital.models import Hospital
from billing.models import Bill

class WhatsAppReceiptLog(models.Model):
    class Status(models.TextChoices):
        QUEUED = 'queued', 'Queued'
        SENT = 'sent', 'Sent'
        DELIVERED = 'delivered', 'Delivered'
        READ = 'read', 'Read'
        FAILED = 'failed', 'Failed'

    id = models.BigAutoField(primary_key=True)
    receipt_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='whatsapp_receipts')
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='whatsapp_receipts')
    recipient_phone = models.CharField(max_length=15)
    provider = models.CharField(max_length=50, default='meta_cloud')
    message_id = models.CharField(max_length=120, blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SENT)
    pdf_url = models.CharField(max_length=255, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Receipt {self.bill.bill_number} -> +91 {self.recipient_phone} ({self.status})"
