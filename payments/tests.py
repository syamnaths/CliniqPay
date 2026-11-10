from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from enrollment.models import EnrollmentRequest
from setup_hospital.models import Hospital
from billing.models import Patient, Bill
from payments.models import PaymentTransaction

class PaymentCollectionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='cashier@bnv.com',
            email='cashier@bnv.com',
            password='Password123!'
        )
        self.enrollment = EnrollmentRequest.objects.create(
            hospital_name='BNV Hospital',
            city='Thiruvananthapuram',
            state='Kerala',
            contact_phone='7510726715',
            contact_email='cashier@bnv.com',
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
        self.patient = Patient.objects.create(
            hospital=self.hospital,
            name='Rajesh Kumar',
            phone='9876543210'
        )
        self.bill = Bill.objects.create(
            hospital=self.hospital,
            patient=self.patient,
            bill_number='BNV-1001',
            total_amount=500.00,
            status=Bill.Status.UNPAID
        )

    def test_payment_checkout_screen_loads(self):
        """Step s1: Open payment collection screen for unpaid bill."""
        self.client.login(username='cashier@bnv.com', password='Password123!')
        url = reverse('payments:checkout', kwargs={'slug': self.hospital.slug, 'bill_number': self.bill.bill_number})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Collect Payment')
        self.assertContains(response, '₹500.00')
        self.assertContains(response, 'bnv@upi')

    def test_record_cash_payment(self):
        """Step s2 & s3: Record verified physical cash payment."""
        self.client.login(username='cashier@bnv.com', password='Password123!')
        url = reverse('payments:record_cash', kwargs={'slug': self.hospital.slug, 'bill_number': self.bill.bill_number})
        payload = {
            'cash_tendered': '1000.00',
        }
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 302)

        self.bill.refresh_from_db()
        self.assertEqual(self.bill.status, Bill.Status.PAID)

        tx = PaymentTransaction.objects.get(bill=self.bill)
        self.assertEqual(tx.method, PaymentTransaction.Method.CASH)
        self.assertEqual(tx.status, PaymentTransaction.Status.SUCCESS)
        self.assertEqual(float(tx.cash_tendered), 1000.00)
        self.assertEqual(float(tx.cash_change), 500.00)

    def test_confirm_upi_payment(self):
        """Step s3 & s4: Confirm dynamic UPI scan payment match."""
        self.client.login(username='cashier@bnv.com', password='Password123!')
        url = reverse('payments:confirm_upi', kwargs={'slug': self.hospital.slug, 'bill_number': self.bill.bill_number})
        payload = {
            'utr_number': 'UPI123456789012',
        }
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 302)

        self.bill.refresh_from_db()
        self.assertEqual(self.bill.status, Bill.Status.PAID)

        tx = PaymentTransaction.objects.get(bill=self.bill)
        self.assertEqual(tx.method, PaymentTransaction.Method.UPI)
        self.assertEqual(tx.status, PaymentTransaction.Status.SUCCESS)
        self.assertEqual(tx.utr_number, 'UPI123456789012')

    def test_counter_display_security_without_token_or_session_fails(self):
        """Display screen without valid token or staff session returns 403 Forbidden."""
        self.hospital.display_token = 'secret_token_abc123'
        self.hospital.save()
        url = reverse('payments:counter_display', kwargs={'slug': self.hospital.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_counter_display_with_valid_token_succeeds(self):
        """Display screen with valid token parameter returns 200 OK without user login."""
        self.hospital.display_token = 'secret_token_abc123'
        self.hospital.save()
        url = f"{reverse('payments:counter_display', kwargs={'slug': self.hospital.slug})}?token=secret_token_abc123"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Patient Counter Display')
        self.assertContains(response, 'BNV Hospital')

    def test_youpi_webhook_signature_and_settlement(self):
        """Test YouPI-PG HMAC-SHA256 authenticated webhook settlement."""
        self.hospital.upi_gateway_provider = Hospital.UpiGatewayProvider.YOUPI
        self.hospital.youpi_webhook_secret = 'test_webhook_secret_key_123'
        self.hospital.save()

        from payments.services.youpi import YoupiPaymentGateway
        gateway = YoupiPaymentGateway(self.hospital)
        packet = gateway.generate_test_webhook_payload(self.bill, event='OBSERVED_SUCCESS', utr='UPI987654321000')

        url = reverse('payments:youpi_webhook', kwargs={'slug': self.hospital.slug})
        response = self.client.post(
            url,
            data=packet['raw_bytes'],
            content_type='application/json',
            HTTP_X_GATEWAY_SIGNATURE=packet['headers']['X-Gateway-Signature'],
            HTTP_X_GATEWAY_EVENT=packet['headers']['X-Gateway-Event'],
            HTTP_X_GATEWAY_DELIVERY_ID=packet['headers']['X-Gateway-Delivery-Id'],
        )

        self.assertEqual(response.status_code, 200)
        res_json = response.json()
        self.assertTrue(res_json.get('received'))
        self.assertEqual(res_json.get('status'), 'settled')

        self.bill.refresh_from_db()
        self.assertEqual(self.bill.status, Bill.Status.PAID)

        tx = PaymentTransaction.objects.get(bill=self.bill)
        self.assertEqual(tx.method, PaymentTransaction.Method.UPI)
        self.assertEqual(tx.gateway_provider, 'youpi')
        self.assertEqual(tx.utr_number, 'UPI987654321000')
        self.assertTrue(tx.is_verified_webhook)

    def test_youpi_webhook_invalid_signature_rejected(self):
        """Test that forged or tampered webhook signatures return 401 Unauthorized."""
        self.hospital.upi_gateway_provider = Hospital.UpiGatewayProvider.YOUPI
        self.hospital.youpi_webhook_secret = 'super_secret_key'
        self.hospital.save()

        import json
        payload = {'order_id': self.bill.bill_number, 'event': 'OBSERVED_SUCCESS'}
        url = reverse('payments:youpi_webhook', kwargs={'slug': self.hospital.slug})
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_GATEWAY_SIGNATURE='sha256=invalid_forged_signature_hash',
        )

        self.assertEqual(response.status_code, 401)
        self.bill.refresh_from_db()
        self.assertEqual(self.bill.status, Bill.Status.UNPAID)
