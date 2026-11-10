from django.db import models
from django.utils import timezone
from setup_hospital.models import Hospital

class SupportTicket(models.Model):
    class Priority(models.TextChoices):
        LOW = 'low', 'Low / General Inquiry'
        MEDIUM = 'medium', 'Medium / Standard Issue'
        HIGH = 'high', 'High / Operational Impact'
        URGENT = 'urgent', 'Urgent / Counter Halted (Critical)'

    class Status(models.TextChoices):
        OPEN = 'open', 'New / Unassigned'
        IN_PROGRESS = 'in_progress', 'Under Investigation'
        WAITING_HOSPITAL = 'waiting_hospital', 'Awaiting Hospital Feedback'
        RESOLVED = 'resolved', 'Resolved'
        CLOSED = 'closed', 'Closed'

    class Category(models.TextChoices):
        BILLING_POS = 'billing_pos', 'Quick Billing & POS Counter'
        PAYMENTS_UPI = 'payments_upi', 'UPI / QR Payments & Reconciliation'
        IPD_BEDS = 'ipd_beds', 'Inpatient (IPD) & Bed Turnover'
        RECEIPTS_PRINTER = 'receipts_printer', 'Receipts, PDF & Thermal Printing'
        STAFF_ACCESS = 'staff_access', 'Staff Accounts & Login Scopes'
        OTHER = 'other', 'General / Other Inquiry'

    ticket_number = models.CharField(max_length=50, unique=True)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='support_tickets')
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='submitted_tickets')
    staff_name = models.CharField(max_length=150)
    contact_phone = models.CharField(max_length=20)
    contact_email = models.EmailField(blank=True, null=True)

    subject = models.CharField(max_length=255)
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.BILLING_POS)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.OPEN)

    # Detailed diagnostic information
    description = models.TextField(help_text="Detailed explanation of the problem or request")
    client_page_url = models.CharField(max_length=500, blank=True, null=True, help_text="Page URL where the error occurred")
    browser_env_info = models.TextField(blank=True, null=True, help_text="Browser user agent, screen resolution, OS")

    # Media attachments
    screenshot = models.FileField(upload_to='support_screenshots/', blank=True, null=True)
    audio_recording = models.FileField(upload_to='support_audio/', blank=True, null=True)

    # Resolution tracking
    assigned_to = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_support_tickets')
    resolution_notes = models.TextField(blank=True, null=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            count = SupportTicket.objects.count() + 1001
            code = f"TKT-{count}"
            while SupportTicket.objects.filter(ticket_number=code).exists():
                count += 1
                code = f"TKT-{count}"
            self.ticket_number = code
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.ticket_number}] {self.hospital.name} - {self.subject} ({self.get_status_display()})"

class TicketMessage(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    sender_name = models.CharField(max_length=150)
    is_staff_reply = models.BooleanField(default=False, help_text="True if posted by platform admin support engineer")
    is_internal_note = models.BooleanField(default=False, help_text="True if internal platform note not visible to hospital users")
    message = models.TextField()
    attachment = models.FileField(upload_to='support_replies/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message by {self.sender_name} on {self.ticket.ticket_number}"
