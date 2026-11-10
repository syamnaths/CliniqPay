from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import date
from decimal import Decimal
from enrollment.models import EnrollmentRequest
from setup_hospital.models import Hospital, Doctor, ServiceItem
from billing.models import Patient, Bill, BillItem
from payments.models import PaymentTransaction

class DailySummaryTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='admin@bnv.com',
            email='admin@bnv.com',
            password='Password123!'
        )
        self.enrollment = EnrollmentRequest.objects.create(
            hospital_name='BNV Hospital',
            city='Thiruvananthapuram',
            state='Kerala',
            contact_phone='7510726715',
            contact_email='admin@bnv.com',
            admin_full_name='Dr. BNV Admin',
            status=EnrollmentRequest.Status.ACTIVATED,
        )
        self.hospital = Hospital.objects.create(
            enrollment=self.enrollment,
            name='BNV Hospital',
            city='Thiruvananthapuram',
            state='Kerala',
            upi_id='bnv@upi',
        )
        self.doctor = Doctor.objects.create(
            hospital=self.hospital,
            name='Dr. Syam Kumar',
            specialization='General Medicine',
            phone='9847012345',
            cut_type=Doctor.CutType.PERCENTAGE,
            cut_value=Decimal('70.00'),
        )
        self.service = ServiceItem.objects.create(
            hospital=self.hospital,
            name='OPD Consultation',
            price=Decimal('500.00'),
        )
        self.patient = Patient.objects.create(
            hospital=self.hospital,
            name='Rajesh Kumar',
            phone='9876543210'
        )

        # Create Bill 1: Paid via UPI
        self.bill1 = Bill.objects.create(
            hospital=self.hospital,
            patient=self.patient,
            doctor=self.doctor,
            bill_number='INV-1001',
            total_amount=Decimal('500.00'),
            doctor_share_amount=Decimal('350.00'),
            status=Bill.Status.PAID
        )
        PaymentTransaction.objects.create(
            hospital=self.hospital,
            bill=self.bill1,
            amount=Decimal('500.00'),
            method=PaymentTransaction.Method.UPI,
            status=PaymentTransaction.Status.SUCCESS,
            utr_number='UPI12345678',
            completed_at=timezone.now()
        )

        # Create Bill 2: Paid via Cash
        self.bill2 = Bill.objects.create(
            hospital=self.hospital,
            patient=self.patient,
            doctor=self.doctor,
            bill_number='INV-1002',
            total_amount=Decimal('300.00'),
            doctor_share_amount=Decimal('210.00'),
            status=Bill.Status.PAID
        )
        PaymentTransaction.objects.create(
            hospital=self.hospital,
            bill=self.bill2,
            amount=Decimal('300.00'),
            method=PaymentTransaction.Method.CASH,
            status=PaymentTransaction.Status.SUCCESS,
            cash_tendered=Decimal('500.00'),
            cash_change=Decimal('200.00'),
            completed_at=timezone.now()
        )

    def test_daily_summary_access_requires_staff_auth(self):
        """Unauthenticated access redirects to hospital login."""
        url = reverse('summary:daily_report', kwargs={'slug': self.hospital.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_cashier_cannot_access_daily_summary(self):
        """Cashier role is blocked from viewing confidential doctor shares & redirected to billing counter."""
        cashier_user = User.objects.create_user(username='cashier_staff', password='Password123!')
        from setup_hospital.models import HospitalStaff
        HospitalStaff.objects.create(
            hospital=self.hospital,
            user=cashier_user,
            role=HospitalStaff.Role.CASHIER
        )
        self.client.login(username='cashier_staff', password='Password123!')
        url = reverse('summary:daily_report', kwargs={'slug': self.hospital.slug})
        response = self.client.get(url)
        self.assertRedirects(response, reverse('billing:counter', kwargs={'slug': self.hospital.slug}))

    def test_daily_summary_computes_correct_breakdowns(self):
        """Step s1, s2 & s3: Computes UPI collections, Cash, Doctor shares, Hospital cut."""
        self.client.login(username='admin@bnv.com', password='Password123!')
        url = reverse('summary:daily_report', kwargs={'slug': self.hospital.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Daily 8 PM Summary')
        # Total = 800 (UPI: 500, Cash: 300)
        self.assertContains(response, '800.00')
        self.assertContains(response, '500.00')
        self.assertContains(response, '300.00')
        # Doctor share total = 350 + 210 = 560
        self.assertContains(response, '560.00')
        # Hospital cut total = 150 + 90 = 240
        self.assertContains(response, '240.00')

    def test_send_summary_whatsapp_dispatches(self):
        """Step s4: Dispatch WhatsApp 8 PM summary simulation."""
        self.client.login(username='admin@bnv.com', password='Password123!')
        url = reverse('summary:send_whatsapp', kwargs={'slug': self.hospital.slug})
        payload = {
            'phone': '7510726715',
            'report_date': date.today().isoformat()
        }
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 302)
