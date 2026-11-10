import uuid
from django.db import models
from django.utils import timezone
from setup_hospital.models import Hospital, Doctor, ServiceItem

class Patient(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='patients')
    patient_id = models.CharField(max_length=50, blank=True, null=True)
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], default='M')
    
    # Inpatient (IPD) Status & Admission Tracking (Standard & Enterprise Plans)
    is_inpatient = models.BooleanField(default=False)
    admission_date = models.DateTimeField(null=True, blank=True)
    discharge_date = models.DateTimeField(null=True, blank=True)
    room_bed_number = models.CharField(max_length=50, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['hospital', 'patient_id'], name='unique_hospital_patient_id')
        ]

    def save(self, *args, **kwargs):
        if not self.patient_id and self.hospital_id:
            # Generate clean hospital UHID e.g. P1001 using hospital's configured prefix
            prefix = getattr(self.hospital, 'patient_id_prefix', 'P') or 'P'
            count = Patient.objects.filter(hospital=self.hospital).count() + 1
            code = f"{prefix}{1000 + count}"
            while Patient.objects.filter(hospital=self.hospital, patient_id=code).exists():
                count += 1
                code = f"{prefix}{1000 + count}"
            self.patient_id = code
        super().save(*args, **kwargs)

    def __str__(self):
        inpatient_tag = f" [IPD: {self.room_bed_number}]" if self.is_inpatient else ""
        return f"{self.patient_id or ''} {self.name} (+91 {self.phone}){inpatient_tag}".strip()

class Bill(models.Model):
    class Status(models.TextChoices):
        UNPAID = 'unpaid', 'Unpaid / Pending'
        PAID = 'paid', 'Paid'
        CANCELLED = 'cancelled', 'Cancelled'

    class BillType(models.TextChoices):
        OPD = 'opd', 'OPD / Outpatient'
        IPD = 'ipd', 'Inpatient (IPD)'

    class QueueStatus(models.TextChoices):
        WAITING = 'waiting', 'Waiting'
        ENGAGED = 'engaged', 'In Consultation'
        COMPLETED = 'completed', 'Completed'
        SKIPPED = 'skipped', 'Skipped'

    id = models.BigAutoField(primary_key=True)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='bills')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='bills')
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True, related_name='bills')
    bill_type = models.CharField(max_length=10, choices=BillType.choices, default=BillType.OPD)
    room_bed_number = models.CharField(max_length=50, blank=True, null=True)
    bill_number = models.CharField(max_length=50)
    token_number = models.PositiveIntegerField(null=True, blank=True, help_text="Daily sequence token number for doctor consultation queue")
    queue_status = models.CharField(max_length=20, choices=QueueStatus.choices, default=QueueStatus.WAITING)
    estimated_wait_minutes = models.PositiveIntegerField(default=0, help_text="Estimated wait time in minutes at booking")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    doctor_share_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    billed_by = models.CharField(max_length=150, blank=True, null=True)
    is_discharge_bill = models.BooleanField(default=False, help_text="True if this is the final discharge invoice that settles and discharges the inpatient upon payment")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UNPAID)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['hospital', 'bill_number'], name='unique_hospital_bill_number')
        ]

    def __str__(self):
        return f"{self.bill_number} - {self.patient.name} (₹{self.total_amount})"

class BillItem(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='items')
    service = models.ForeignKey(ServiceItem, on_delete=models.SET_NULL, null=True, blank=True)
    item_name = models.CharField(max_length=200)
    billing_unit = models.CharField(max_length=20, default='count')
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    # Dedicated Pharmacy & Dispensing Fields (Compliance with Drugs & Cosmetics Act)
    batch_number = models.CharField(max_length=50, blank=True, null=True, help_text="Medicine batch number")
    expiry_date = models.CharField(max_length=20, blank=True, null=True, help_text="Medicine expiry date (e.g. MM/YY)")

    @property
    def formatted_quantity(self):
        unit_map = {
            'hour': f"{self.quantity} hr{'s' if self.quantity > 1 else ''}",
            'day': f"{self.quantity} day{'s' if self.quantity > 1 else ''}",
            'session': f"{self.quantity} session{'s' if self.quantity > 1 else ''}",
            'test': f"{self.quantity} test{'s' if self.quantity > 1 else ''}",
            'visit': f"{self.quantity} visit{'s' if self.quantity > 1 else ''}",
            'strip': f"{self.quantity} strip{'s' if self.quantity > 1 else ''}",
            'count': f"{self.quantity}",
        }
        return unit_map.get(self.billing_unit, f"{self.quantity}")

    def __str__(self):
        return f"{self.item_name} x {self.formatted_quantity}"

class MedicineBatch(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='medicine_batches')
    service_item = models.ForeignKey(ServiceItem, on_delete=models.CASCADE, related_name='batches')
    batch_number = models.CharField(max_length=60, help_text="Manufacturer batch number")
    expiry_date = models.CharField(max_length=20, help_text="Expiry Date (e.g. MM/YY or YYYY-MM)")
    stock_quantity = models.PositiveIntegerField(default=0, help_text="Current available unit count/strips")
    rack_location = models.CharField(max_length=80, blank=True, help_text="Specific rack/shelf location for this batch")
    mrp = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Maximum Retail Price")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['hospital', 'service_item', 'batch_number'], name='unique_hospital_item_batch')
        ]
        ordering = ['expiry_date', '-stock_quantity']

    def __str__(self):
        return f"{self.service_item.name} · Batch: {self.batch_number} (Exp: {self.expiry_date}, Qty: {self.stock_quantity})"

class Prescription(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active / Pending Fulfillment'
        DISPENSED = 'dispensed', 'Fulfilled / Dispensed'
        CANCELLED = 'cancelled', 'Cancelled'

    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='prescriptions')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='prescriptions')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='prescriptions')
    rx_number = models.CharField(max_length=50, blank=True)
    chief_complaints = models.TextField(blank=True, help_text="Symptoms & clinical presentation")
    diagnosis = models.CharField(max_length=255, blank=True, help_text="Provisional / Clinical diagnosis")
    vitals_bp = models.CharField(max_length=20, blank=True, help_text="e.g. 120/80 mmHg")
    vitals_pulse = models.CharField(max_length=20, blank=True, help_text="e.g. 76 bpm")
    vitals_temp = models.CharField(max_length=20, blank=True, help_text="e.g. 98.6 F")
    vitals_weight = models.CharField(max_length=20, blank=True, help_text="e.g. 68 kg")
    clinical_notes = models.TextField(blank=True, help_text="Physician's clinical notes, diet & lifestyle advice")
    follow_up_date = models.DateField(null=True, blank=True, help_text="Recommended follow-up visit")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    is_inpatient = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.rx_number and self.hospital_id:
            count = Prescription.objects.filter(hospital=self.hospital).count() + 1
            self.rx_number = f"RX-{count:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.rx_number} · {self.patient.name} ({self.doctor.full_name})"

class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='medications')
    service_item = models.ForeignKey(ServiceItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='prescription_items')
    medicine_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=50, default='1-0-1', help_text="e.g. 1-0-1, 1-1-1, Once Daily")
    timing = models.CharField(max_length=50, default='After Food', help_text="Before Food, After Food, With Food")
    duration = models.CharField(max_length=50, default='5 Days', help_text="e.g. 3 Days, 5 Days, 1 Month")
    quantity = models.PositiveIntegerField(default=10, help_text="Total units / tablets to dispense")
    notes = models.CharField(max_length=255, blank=True, help_text="Special instructions e.g. SOS, bedtime")

    def __str__(self):
        return f"{self.medicine_name} ({self.dosage}, {self.duration})"

class ClinicalNote(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='clinical_notes')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='clinical_notes')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='clinical_notes')
    note_date = models.DateField(default=timezone.now, help_text="Clinical date of note")
    note_text = models.TextField(blank=True, help_text="Physician written observations, symptoms & progression")
    provisional_diagnosis = models.CharField(max_length=255, blank=True)
    freehand_drawing = models.TextField(blank=True, help_text="Base64 data URL of freehand write pad canvas drawing")
    is_inpatient_round = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-note_date', '-created_at']

    def __str__(self):
        return f"{self.note_date} · {self.patient.name} by {self.doctor.full_name}"
