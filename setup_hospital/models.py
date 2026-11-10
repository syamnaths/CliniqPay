import uuid
from django.db import models
from django.utils.text import slugify
from enrollment.models import EnrollmentRequest

class Hospital(models.Model):
    class PlanTier(models.TextChoices):
        STARTER = 'starter', 'Starter'
        STANDARD = 'standard', 'Standard Hospital'
        ENTERPRISE = 'enterprise', 'Enterprise Chain'

    enrollment = models.OneToOneField(
        EnrollmentRequest,
        on_delete=models.CASCADE,
        related_name='hospital',
        null=True,
        blank=True
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    plan_tier = models.CharField(max_length=20, choices=PlanTier.choices, default=PlanTier.STANDARD)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    gstin = models.CharField(max_length=20, blank=True, null=True)
    bed_count = models.PositiveIntegerField(default=20)
    starting_room_number = models.PositiveIntegerField(default=101)
    closing_time = models.TimeField(default='20:00:00')
    upi_id = models.CharField(max_length=100, blank=True, null=True)
    patient_id_prefix = models.CharField(max_length=10, default='P', help_text="e.g. 'P' for P1001 or 'UHID' for UHID1001")
    bill_prefix = models.CharField(max_length=10, default='INV')
    next_bill_number = models.PositiveIntegerField(default=1001)
    default_tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    display_token = models.CharField(max_length=64, blank=True, null=True, unique=True)
    class UpiGatewayProvider(models.TextChoices):
        NATIVE = 'native', 'Direct Merchant VPA (Default)'
        YOUPI = 'youpi', 'YouPI-PG Sovereign UPI Gateway'

    upi_gateway_provider = models.CharField(
        max_length=20,
        choices=UpiGatewayProvider.choices,
        default=UpiGatewayProvider.NATIVE,
        help_text="Payment processing engine for dynamic UPI transactions"
    )
    youpi_api_url = models.CharField(
        max_length=255,
        default='http://localhost:6100',
        blank=True,
        null=True,
        help_text="Base URL of self-hosted YouPI-PG Core API instance"
    )
    youpi_merchant_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Merchant UUID assigned in YouPI-PG admin panel"
    )
    youpi_webhook_secret = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Secret key used to verify HMAC-SHA256 signatures of YouPI webhooks"
    )
    youpi_sandbox_mode = models.BooleanField(
        default=True,
        help_text="Enable simulated/sandbox testing when external YouPI daemon is offline"
    )

    whatsapp_api_provider = models.CharField(max_length=50, default='meta_cloud', choices=[('meta_cloud', 'Meta Cloud API'), ('gupshup', 'Gupshup BSP'), ('twilio', 'Twilio WhatsApp')])
    whatsapp_api_key = models.CharField(max_length=255, blank=True, null=True)
    whatsapp_phone_number_id = models.CharField(max_length=100, blank=True, null=True)
    whatsapp_business_account_id = models.CharField(max_length=100, blank=True, null=True)
    logo = models.FileField(upload_to='hospital_logos/', blank=True, null=True, help_text="Hospital official brand logo for header, POS counter, and receipts")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.display_token:
            self.display_token = uuid.uuid4().hex
        if not self.slug:
            base_slug = slugify(self.name) or 'clinic'
            unique_slug = base_slug
            num = 1
            while Hospital.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{num}"
                num += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class ServiceItem(models.Model):
    class Department(models.TextChoices):
        OPD = 'opd', 'OPD / Consultation'
        PHARMACY = 'pharmacy', 'Pharmacy'
        LAB = 'lab', 'Diagnostic Lab'
        RADIOLOGY = 'radiology', 'Radiology / Imaging'
        IPD = 'ipd', 'IPD / Nursing Procedures'
        EMERGENCY = 'emergency', 'Emergency & Casualty (24/7)'
        OT_SURGERY = 'ot_surgery', 'Operation Theatre & Surgery (OT)'
        MISC = 'misc', 'Miscellaneous & Ad-Hoc Charges'

    class BillingUnit(models.TextChoices):
        COUNT = 'count', 'Units / Count'
        HOUR = 'hour', 'Hours (hrs)'
        DAY = 'day', 'Days (days)'
        SESSION = 'session', 'Sessions (sess)'
        TEST = 'test', 'Tests (tests)'
        VISIT = 'visit', 'Visits (visits)'
        STRIP = 'strip', 'Strips (strips)'

    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='services')
    department = models.CharField(max_length=30, choices=Department.choices, default=Department.OPD)
    billing_unit = models.CharField(max_length=20, choices=BillingUnit.choices, default=BillingUnit.COUNT)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)

    # Storage & Pharmacy-Lite categorization
    storage_location = models.CharField(max_length=80, blank=True, help_text="Physical storage/rack coordinate, e.g., 'Rack A2', 'Shelf 3', 'Cold Fridge 1'")
    is_pharmacy_lite = models.BooleanField(default=False, help_text="True if safe/designated for quick OTC reception dispensing (Pharmacy-Lite)")

    @property
    def unit_short_label(self):
        labels = {
            'hour': 'hr',
            'day': 'day',
            'session': 'sess',
            'test': 'test',
            'visit': 'visit',
            'strip': 'strip',
            'count': 'qty',
        }
        return labels.get(self.billing_unit, 'qty')

    def __str__(self):
        return f"[{self.get_department_display()}] {self.name} - ₹{self.price}/{self.unit_short_label} ({self.hospital.name})"

class Doctor(models.Model):
    class Title(models.TextChoices):
        DR = 'Dr.', 'Dr.'
        PROF_DR = 'Prof. Dr.', 'Prof. Dr.'
        SURGEON = 'Surgeon', 'Surgeon'
        MR = 'Mr.', 'Mr.'
        MS = 'Ms.', 'Ms.'

    class CutType(models.TextChoices):
        PERCENTAGE = 'percentage', 'Percentage (%)'
        FIXED = 'fixed', 'Fixed Amount (₹)'

    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='doctors')
    title = models.CharField(max_length=20, choices=Title.choices, default=Title.DR)
    name = models.CharField(max_length=150)
    specialization = models.CharField(max_length=150, default='General Medicine')
    phone = models.CharField(max_length=15, blank=True)
    cut_type = models.CharField(max_length=20, choices=CutType.choices, default=CutType.PERCENTAGE)
    cut_value = models.DecimalField(max_digits=8, decimal_places=2, default=70.00)
    user = models.OneToOneField('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='doctor_profile')
    registration_number = models.CharField(max_length=60, blank=True, help_text="State Medical Council / MCI / NMC Reg No.")

    @property
    def full_name(self):
        if self.title:
            return f"{self.title} {self.name}".strip()
        return self.name

    def __str__(self):
        return f"{self.full_name} ({self.specialization})"

class HospitalStaff(models.Model):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Hospital Admin / Owner'
        DOCTOR = 'doctor', 'Consultant Doctor / Physician'
        FRONT_DESK = 'front_desk', 'Front Desk / Receptionist'
        CASHIER = 'cashier', 'Counter Cashier'
        PHARMACIST = 'pharmacist', 'Registered Pharmacist'
        HOUSEKEEPING = 'housekeeping', 'Housekeeping / Cleaning Staff'

    class DepartmentScope(models.TextChoices):
        ALL = 'all', 'All Counters (General)'
        OPD = 'opd', 'OPD Reception Counter'
        PHARMACY = 'pharmacy', 'Pharmacy Counter'
        LAB = 'lab', 'Diagnostic Lab Desk'
        RADIOLOGY = 'radiology', 'Radiology Desk'
        IPD = 'ipd', 'IPD Cashier Desk'
        EMERGENCY = 'emergency', 'Emergency / Casualty Desk'
        OT_SURGERY = 'ot_surgery', 'OT & Surgical Billing Desk'
        HOUSEKEEPING = 'housekeeping', 'Housekeeping Counter (Room Sanitization)'

    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='staff_members')
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='hospital_staff')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CASHIER)
    department_scope = models.CharField(max_length=150, default='all')
    created_at = models.DateTimeField(auto_now_add=True)

    def get_scoped_departments_list(self):
        """Returns list of allowed department codes."""
        if self.role == self.Role.PHARMACIST:
            return ['pharmacy']
        if self.role == self.Role.HOUSEKEEPING:
            return ['housekeeping']
        if self.role == self.Role.DOCTOR:
            return ['opd', 'ipd']
        if not self.department_scope or self.department_scope == 'all' or self.role == self.Role.ADMIN:
            return ['all', 'opd', 'pharmacy', 'lab', 'radiology', 'ipd', 'emergency', 'ot_surgery']
        return [d.strip() for d in self.department_scope.split(',') if d.strip()]

    def can_access_department(self, dept_code):
        """Checks if staff member is authorized to bill or access this department."""
        if self.role == self.Role.ADMIN or not self.department_scope or self.department_scope == 'all':
            return True
        if self.role == self.Role.PHARMACIST:
            return dept_code == 'pharmacy'
        if self.role == self.Role.HOUSEKEEPING:
            return dept_code == 'housekeeping'
        if self.role == self.Role.DOCTOR:
            return dept_code in ['opd', 'ipd']
        allowed = self.get_scoped_departments_list()
        return dept_code in allowed

    def get_department_scope_display_custom(self):
        """Friendly display of assigned department scopes."""
        if not self.department_scope or self.department_scope == 'all':
            return 'All Counters'
        labels = {
            'opd': 'OPD',
            'pharmacy': 'Pharmacy',
            'lab': 'Lab',
            'radiology': 'Radiology',
            'ipd': 'IPD',
            'emergency': 'Emergency',
            'ot_surgery': 'OT/Surgery',
            'housekeeping': 'Housekeeping',
        }
        parts = [labels.get(d.strip(), d.strip().upper()) for d in self.department_scope.split(',') if d.strip()]
        return ' • '.join(parts) if parts else 'All Counters'

    def __str__(self):
        return f"{self.user.username} ({self.role} - {self.get_department_scope_display_custom()}) - {self.hospital.name}"

class HospitalWardCadre(models.Model):
    """
    Physical Ward Cadre & Room Range configuration (for Standard & Enterprise plans).
    Allows front desk staff to select assigned rooms/beds with linked IPD tariff rates
    and real-time occupancy status.
    """
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='ward_cadres')
    name = models.CharField(max_length=100) # e.g. "Deluxe Ward", "ICU", "General Ward"
    service_item = models.ForeignKey(ServiceItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='cadres')
    prefix = models.CharField(max_length=20, default='Room ', help_text="e.g. 'Room ', 'Bed ', 'ICU-'")
    number_from = models.PositiveIntegerField(default=101)
    number_to = models.PositiveIntegerField(default=110)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['number_from']

    def get_bed_numbers(self):
        """Generates list of individual bed strings in this cadre."""
        if self.number_to < self.number_from:
            return [f"{self.prefix}{self.number_from}"]
        # Limit safety guard to 100 rooms per cadre
        end = min(self.number_to, self.number_from + 99)
        return [f"{self.prefix}{num}" for num in range(self.number_from, end + 1)]

    def __str__(self):
        return f"{self.name} ({self.prefix}{self.number_from} to {self.prefix}{self.number_to})"

class RoomBedStatus(models.Model):
    """
    Lifecycle status of physical rooms and beds (Available, Occupied, Cleaning in Progress).
    Updated on discharge, room transfer, or completion of sanitization by housekeeping.
    """
    class Status(models.TextChoices):
        AVAILABLE = 'available', 'Ready & Available'
        OCCUPIED = 'occupied', 'Occupied by Patient'
        CLEANING = 'cleaning', 'Cleaning / Sanitization in Progress'

    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='room_statuses')
    room_number = models.CharField(max_length=50) # e.g. "Room 101", "ICU Bed 168"
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    current_patient = models.ForeignKey('billing.Patient', on_delete=models.SET_NULL, null=True, blank=True, related_name='active_bed_status')
    last_cleaned_at = models.DateTimeField(null=True, blank=True)
    last_cleaned_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='cleaned_rooms')
    notes = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['hospital', 'room_number'], name='unique_hospital_room_number_status')
        ]

    def __str__(self):
        return f"{self.hospital.slug} - {self.room_number}: {self.get_status_display()}"
