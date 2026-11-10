import uuid
from django.test import TestCase, Client
from django.urls import reverse
from enrollment.models import EnrollmentRequest

class HospitalEnrollmentTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_landing_page_accessible(self):
        """Step s1: Verify landing page / enrollment page is accessible."""
        response = self.client.get(reverse('enrollment:landing'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cliniqpay')
        self.assertContains(response, 'Enroll Hospital')

    def test_enrollment_submission_valid(self):
        """Step s2 & s3: Submit hospital and admin details; check valid save and pending_review state with plan tier and bed count."""
        payload = {
            'hospital_name': 'Lotus Care Clinic',
            'plan_tier': 'enterprise',
            'bed_count': 50,
            'city': 'Bengaluru',
            'state': 'Karnataka',
            'contact_phone': '9876543210',
            'contact_email': 'admin@lotuscare.in',
            'admin_full_name': 'Dr. Ramesh Kumar',
        }
        response = self.client.post(reverse('enrollment:submit'), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Application Received')
        self.assertContains(response, 'pending_review')

        # Check DB persistence
        enrollment = EnrollmentRequest.objects.get(contact_email='admin@lotuscare.in')
        self.assertEqual(enrollment.hospital_name, 'Lotus Care Clinic')
        self.assertEqual(enrollment.plan_tier, EnrollmentRequest.PlanTier.ENTERPRISE)
        self.assertEqual(enrollment.bed_count, 50)
        self.assertEqual(enrollment.status, EnrollmentRequest.Status.PENDING_REVIEW)
        self.assertTrue(len(str(enrollment.reference_token)) > 10)

    def test_enrollment_submission_invalid_phone(self):
        """Validation: Phone must be 10 digits."""
        payload = {
            'hospital_name': 'Lotus Care Clinic',
            'city': 'Bengaluru',
            'state': 'Karnataka',
            'contact_phone': '12345', # invalid
            'contact_email': 'admin@lotuscare.in',
            'admin_full_name': 'Dr. Ramesh Kumar',
        }
        response = self.client.post(reverse('enrollment:submit'), data=payload)
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'Valid 10-digit phone number is required', status_code=400)

    def test_track_enrollment_status(self):
        """Step s4: Track review or activation status via reference token."""
        enrollment = EnrollmentRequest.objects.create(
            hospital_name='Apollo Daycare',
            city='Chennai',
            state='Tamil Nadu',
            contact_phone='9888877777',
            contact_email='contact@apollodaycare.in',
            admin_full_name='Dr. Priya Sundaram',
            status=EnrollmentRequest.Status.PENDING_REVIEW,
        )
        url = reverse('enrollment:status', kwargs={'token': enrollment.reference_token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Apollo Daycare')
        self.assertContains(response, 'Under Review')

    def test_connected_legal_and_security_pages(self):
        """Test newly connected Terms of Service, Security Whitepaper, and Status pages."""
        terms_url = reverse('enrollment:terms_of_service')
        res_terms = self.client.get(terms_url)
        self.assertEqual(res_terms.status_code, 200)
        self.assertContains(res_terms, "Terms of Service & ABDM Compliance")

        sec_url = reverse('enrollment:security_whitepaper')
        res_sec = self.client.get(sec_url)
        self.assertEqual(res_sec.status_code, 200)
        self.assertContains(res_sec, "Enterprise Security, Encryption & DPDP Standards")

        status_url = reverse('enrollment:system_status')
        res_status = self.client.get(status_url)
        self.assertEqual(res_status.status_code, 200)
        self.assertContains(res_status, "All CliniqPay Systems Operational")
