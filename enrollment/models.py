import uuid
from django.db import models

class EnrollmentRequest(models.Model):
    class Status(models.TextChoices):
        PENDING_REVIEW = 'pending_review', 'Under Review'
        APPROVED = 'approved', 'Approved'
        ACTIVATED = 'activated', 'Activated'
        REJECTED = 'rejected', 'Rejected'

    class PlanTier(models.TextChoices):
        STARTER = 'starter', 'Starter (Solo / Daycare)'
        STANDARD = 'standard', 'Standard Hospital (10–30 Beds)'
        ENTERPRISE = 'enterprise', 'Enterprise Chain (Multi-Branch / Multi-Dept)'

    id = models.BigAutoField(primary_key=True)
    reference_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    hospital_name = models.CharField(max_length=255)
    plan_tier = models.CharField(
        max_length=20,
        choices=PlanTier.choices,
        default=PlanTier.STANDARD
    )
    bed_count = models.PositiveIntegerField(default=20)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=15)
    contact_email = models.EmailField()
    admin_full_name = models.CharField(max_length=150)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING_REVIEW
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.CharField(max_length=150, blank=True, null=True)
    temp_password = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.hospital_name} ({self.get_plan_tier_display()}) - {self.status}"
