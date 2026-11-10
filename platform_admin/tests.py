from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from enrollment.models import EnrollmentRequest

class PlatformAdminTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='masteradmin',
            email='master@cliniqpay.com',
            password='Password123!'
        )
        self.enrollment = EnrollmentRequest.objects.create(
            hospital_name='BNV Hospital',
            city='Thiruvananthapuram',
            state='Kerala',
            contact_phone='7510726715',
            contact_email='admin@bnv.com',
            admin_full_name='Dr. BNV Admin',
            status=EnrollmentRequest.Status.PENDING_REVIEW,
        )

    def test_anonymous_redirected_to_login(self):
        """Unauthorized access to platform dashboard redirects to login."""
        response = self.client.get(reverse('platform_admin:dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_admin_dashboard_lists_requests(self):
        """Authorized master admin sees pending hospital applications."""
        self.client.login(username='masteradmin', password='Password123!')
        response = self.client.get(reverse('platform_admin:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'BNV Hospital')
        self.assertContains(response, '7510726715')
        self.assertContains(response, 'Approve & Activate')

    def test_approve_enrollment_request(self):
        """Admin approves application; updates status to activated with 7-day trial."""
        self.client.login(username='masteradmin', password='Password123!')
        url = reverse('platform_admin:approve', kwargs={'pk': self.enrollment.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.status, EnrollmentRequest.Status.ACTIVATED)
        self.assertEqual(self.enrollment.reviewed_by, 'masteradmin')
        self.assertIsNotNone(self.enrollment.reviewed_at)
