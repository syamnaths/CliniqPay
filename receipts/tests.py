from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from enrollment.models import EnrollmentRequest
from setup_hospital.models import Hospital, Doctor, ServiceItem
from billing.models import Patient, Bill, BillItem
from payments.models import PaymentTransaction
from receipts.models import WhatsAppReceiptLog

class WhatsAppReceiptTests(TestCase):
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
            whatsapp_api_provider='meta_cloud',
            whatsapp_api_key='test_meta_key',
            whatsapp_phone_number_id='100234567890',
        )
        self.doctor = Doctor.objects.create(
            hospital=self.hospital,
            name='Dr. Syam Kumar',
            specialization='General Medicine',
            phone='9847012345',
            cut_type=Doctor.CutType.PERCENTAGE,
            cut_value=Decimal('70.00'),
        )
        self.patient = Patient.objects.create(
            hospital=self.hospital,
            name='Rajesh Kumar',
            phone='9876543210'
        )
        self.bill = Bill.objects.create(
            hospital=self.hospital,
            patient=self.patient,
            doctor=self.doctor,
            bill_number='INV-1001',
            total_amount=Decimal('500.00'),
            doctor_share_amount=Decimal('350.00'),
            status=Bill.Status.PAID
        )
        self.payment = PaymentTransaction.objects.create(
            hospital=self.hospital,
            bill=self.bill,
            amount=Decimal('500.00'),
            method=PaymentTransaction.Method.UPI,
            status=PaymentTransaction.Status.SUCCESS,
            utr_number='UPI999888777'
        )

    def test_view_receipt_page_renders_cleanly(self):
        """Step s1: Open printable tax invoice & receipt view."""
        url = reverse('receipts:view', kwargs={'slug': self.hospital.slug, 'bill_number': self.bill.bill_number})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'BNV Hospital')
        self.assertContains(response, 'INV-1001')
        self.assertContains(response, '500.00')

    def test_dispatch_whatsapp_receipt_validates_10_digits(self):
        """Step s2 & s3: Validates phone number and dispatches WhatsApp receipt."""
        self.client.login(username='admin@bnv.com', password='Password123!')
        url = reverse('receipts:dispatch', kwargs={'slug': self.hospital.slug, 'bill_number': self.bill.bill_number})
        
        # Test invalid number (less than 10 digits)
        bad_response = self.client.post(url, data={'phone': '12345'})
        self.assertEqual(bad_response.status_code, 302)
        self.assertEqual(WhatsAppReceiptLog.objects.count(), 0)

        # Test valid 10-digit number
        good_response = self.client.post(url, data={'phone': '9876543210'})
        self.assertEqual(good_response.status_code, 302)
        self.assertEqual(WhatsAppReceiptLog.objects.count(), 1)
        log = WhatsAppReceiptLog.objects.first()
        self.assertEqual(log.recipient_phone, '9876543210')
        self.assertEqual(log.status, WhatsAppReceiptLog.Status.SENT)

    def test_receipt_status_api(self):
        """Step s4: Check status endpoint."""
        WhatsAppReceiptLog.objects.create(
            hospital=self.hospital,
            bill=self.bill,
            recipient_phone='9876543210',
            status=WhatsAppReceiptLog.Status.DELIVERED
        )
        url = reverse('receipts:status', kwargs={'slug': self.hospital.slug, 'bill_number': self.bill.bill_number})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'delivered')
