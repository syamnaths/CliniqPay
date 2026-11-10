import uuid
from django.db import models
from django.utils import timezone
from setup_hospital.models import Hospital
from billing.models import Bill

class PaymentTransaction(models.Model):
    class Method(models.TextChoices):
        UPI = 'upi', 'Dynamic UPI QR'
        CASH = 'cash', 'Physical Cash'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SUCCESS = 'success', 'Successful / Confirmed'
        FAILED = 'failed', 'Failed'

    id = models.BigAutoField(primary_key=True)
    transaction_ref = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='payments')
    bill = models.OneToOneField(Bill, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=Method.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    utr_number = models.CharField(max_length=100, blank=True, null=True)
    gateway_provider = models.CharField(
        max_length=50,
        default='native',
        help_text="Underlying gateway engine that processed this transaction"
    )
    youpi_payment_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Payment ID issued by YouPI-PG"
    )
    webhook_delivery_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="X-Gateway-Delivery-Id received for idempotency and deduplication"
    )
    is_verified_webhook = models.BooleanField(
        default=False,
        help_text="True if confirmed via cryptographic HMAC-SHA256 webhook callback"
    )
    cash_tendered = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cash_change = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    recorded_by = models.CharField(max_length=150, blank=True, null=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.method} - ₹{self.amount} ({self.status}) for {self.bill.bill_number}"
