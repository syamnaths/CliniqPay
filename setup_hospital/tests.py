from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from enrollment.models import EnrollmentRequest
from setup_hospital.models import Hospital, ServiceItem, Doctor, HospitalStaff, HospitalWardCadre, RoomBedStatus

class HospitalSetupTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='admin@citycare.in',
            email='admin@citycare.in',
            password='TestPassword123!'
        )
        self.enrollment = EnrollmentRequest.objects.create(
            hospital_name='City Care Hospital',
            city='Kochi',
            state='Kerala',
            contact_phone='9846001122',
            contact_email='admin@citycare.in',
            admin_full_name='Dr. Thomas Mathew',
            status=EnrollmentRequest.Status.ACTIVATED,
        )
        self.hospital = Hospital.objects.create(
            enrollment=self.enrollment,
            name='City Care Hospital',
            city='Kochi',
            state='Kerala',
            bed_count=35,
        )

    def test_anonymous_redirected_to_hospital_login(self):
        """Unauthenticated requests must be redirected to hospital login."""
        url = reverse('setup_hospital:dashboard', kwargs={'slug': self.hospital.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(f'/hospital/{self.hospital.slug}/login/', response.url)

    def test_setup_dashboard_loads_for_authorized_clinic_user(self):
        """Step s1: Hospital setup view loads with profile and initial services when logged in."""
        self.client.login(username='admin@citycare.in', password='TestPassword123!')
        url = reverse('setup_hospital:dashboard', kwargs={'slug': self.hospital.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'City Care Hospital')
        self.assertContains(response, 'Hospital Setup')

    def test_add_service_tariff(self):
        """Step s2: Add a new service item with department, price and tax."""
        self.client.login(username='admin@citycare.in', password='TestPassword123!')
        url = reverse('setup_hospital:add_service', kwargs={'slug': self.hospital.slug})
        payload = {
            'name': 'Ultrasound Abdomen',
            'department': 'radiology',
            'code': 'USG-01',
            'price': '1200.00',
            'tax_percent': '0.00',
        }
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 302)

        service = ServiceItem.objects.get(hospital=self.hospital, name='Ultrasound Abdomen')
        self.assertEqual(service.department, 'radiology')
        self.assertEqual(float(service.price), 1200.00)

    def test_edit_service_tariff(self):
        """Edit an existing service tariff and update price."""
        self.client.login(username='admin@citycare.in', password='TestPassword123!')
        service = ServiceItem.objects.create(
            hospital=self.hospital,
            name='Standard Consultation',
            code='OPD-999',
            price=300.00,
            tax_percent=0.00,
            department='opd'
        )
        url = reverse('setup_hospital:edit_service', kwargs={'slug': self.hospital.slug, 'service_id': service.id})
        payload = {
            'name': 'Senior Consultation',
            'code': 'OPD-999',
            'department': 'opd',
            'price': '450.00',
            'tax_percent': '5.00',
        }
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 302)

        service.refresh_from_db()
        self.assertEqual(service.name, 'Senior Consultation')
        self.assertEqual(float(service.price), 450.00)
        self.assertEqual(float(service.tax_percent), 5.00)

    def test_add_doctor_with_cut_rule(self):
        """Step s3: Add a doctor with courtesy title and percentage cut."""
        self.client.login(username='admin@citycare.in', password='TestPassword123!')
        url = reverse('setup_hospital:add_doctor', kwargs={'slug': self.hospital.slug})
        payload = {
            'title': 'Dr.',
            'name': 'Sarah Verghese',
            'specialization': 'Pediatrics',
            'cut_type': 'percentage',
            'cut_value': '70.00',
        }
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 302)

        doc = Doctor.objects.get(hospital=self.hospital, name='Sarah Verghese')
        self.assertEqual(doc.title, 'Dr.')
        self.assertEqual(doc.full_name, 'Dr. Sarah Verghese')
        self.assertEqual(float(doc.cut_value), 70.00)

    def test_add_doctor_strips_accidental_prefix_in_name(self):
        """If user inputs 'Dr. Sarah' in name field, strip Dr. and save cleanly."""
        self.client.login(username='admin@citycare.in', password='TestPassword123!')
        url = reverse('setup_hospital:add_doctor', kwargs={'slug': self.hospital.slug})
        payload = {
            'title': 'Dr.',
            'name': 'Dr. Sarah Verghese',
            'specialization': 'Pediatrics',
            'cut_type': 'percentage',
            'cut_value': '70.00',
        }
        self.client.post(url, data=payload)
        doc = Doctor.objects.get(hospital=self.hospital, name='Sarah Verghese')
        self.assertEqual(doc.title, 'Dr.')
        self.assertEqual(doc.name, 'Sarah Verghese')
        self.assertEqual(doc.full_name, 'Dr. Sarah Verghese')

    def test_edit_doctor_and_share_rule(self):
        """Edit an existing doctor's title, name, specialty, and cut rule."""
        self.client.login(username='admin@citycare.in', password='TestPassword123!')
        doctor = Doctor.objects.create(
            hospital=self.hospital,
            title='Dr.',
            name='Arvind Menon',
            specialization='Orthopedics',
            cut_type='percentage',
            cut_value=60.00,
        )
        url = reverse('setup_hospital:edit_doctor', kwargs={'slug': self.hospital.slug, 'doctor_id': doctor.id})
        payload = {
            'title': 'Prof. Dr.',
            'name': 'Arvind Menon MD',
            'specialization': 'Orthopedic Surgery',
            'phone': '9846011111',
            'cut_type': 'fixed',
            'cut_value': '500.00',
        }
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 302)

        doctor.refresh_from_db()
        self.assertEqual(doctor.title, 'Prof. Dr.')
        self.assertEqual(doctor.name, 'Arvind Menon MD')
        self.assertEqual(doctor.full_name, 'Prof. Dr. Arvind Menon MD')
        self.assertEqual(doctor.specialization, 'Orthopedic Surgery')
        self.assertEqual(doctor.cut_type, 'fixed')
        self.assertEqual(float(doctor.cut_value), 500.00)

    def test_delete_doctor(self):
        """Delete a doctor from the roster."""
        self.client.login(username='admin@citycare.in', password='TestPassword123!')
        doctor = Doctor.objects.create(
            hospital=self.hospital,
            name='Dr. Temporary',
            specialization='General',
        )
        url = reverse('setup_hospital:delete_doctor', kwargs={'slug': self.hospital.slug, 'doctor_id': doctor.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Doctor.objects.filter(id=doctor.id).exists())

    def test_update_payment_and_preferences(self):
        """Step s4: Update hospital UPI ID, default tax percent, and closing time."""
        self.client.login(username='admin@citycare.in', password='TestPassword123!')
        url = reverse('setup_hospital:update_profile', kwargs={'slug': self.hospital.slug})
        payload = {
            'gstin': '32ABCDE1234F1Z5',
            'bed_count': 45,
            'default_tax_percent': '18.00',
            'closing_time': '20:30',
            'upi_id': 'citycare@icici',
        }
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 302)

        self.hospital.refresh_from_db()
        self.assertEqual(self.hospital.upi_id, 'citycare@icici')
        self.assertEqual(self.hospital.bed_count, 45)
        self.assertEqual(float(self.hospital.default_tax_percent), 18.00)

    def test_plan_tier_catalogs_and_upgrades(self):
        """Test that different plans get appropriate catalog items and changing plan unlocks higher-tier items."""
        from setup_hospital.views import seed_hospital_services

        # 1. Create a starter clinic
        starter_hosp = Hospital.objects.create(
            name='Solo Daycare Clinic',
            slug='solo-daycare',
            plan_tier=Hospital.PlanTier.STARTER,
            city='Calicut',
            state='Kerala',
            bed_count=5,
        )
        seed_hospital_services(starter_hosp)
        starter_codes = set(starter_hosp.services.values_list('code', flat=True))
        self.assertIn('OPD-001', starter_codes)
        self.assertIn('LAB-001', starter_codes)
        self.assertIn('IPD-001', starter_codes)
        self.assertNotIn('ICU-004', starter_codes) # Not in starter

        # 2. Upgrade clinic to Enterprise
        starter_hosp.plan_tier = Hospital.PlanTier.ENTERPRISE
        starter_hosp.save()
        seed_hospital_services(starter_hosp)
        upgraded_codes = set(starter_hosp.services.values_list('code', flat=True))
        self.assertIn('IPD-004', upgraded_codes) # ICU Bed
        self.assertIn('IPD-005', upgraded_codes) # Major OT
        self.assertIn('RAD-002', upgraded_codes) # Digital X-Ray
        # Existing starter items are still preserved
        self.assertIn('LAB-001', upgraded_codes)

    def test_staff_custom_department_scope_checkboxes(self):
        """Staff can be assigned multiple custom department scopes via checkboxes."""
        self.client.login(username='admin@citycare.in', password='TestPassword123!')
        url = reverse('setup_hospital:add_staff', kwargs={'slug': self.hospital.slug})
        payload = {
            'name': 'Pharmacy & Lab Cashier',
            'username': 'pharm_lab_staff',
            'password': 'Password123!',
            'role': 'cashier',
            'department_scope': ['pharmacy', 'lab'],
        }
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 302)

        staff = HospitalStaff.objects.get(hospital=self.hospital, user__username='pharm_lab_staff')
        self.assertEqual(staff.department_scope, 'pharmacy,lab')
        self.assertEqual(staff.get_scoped_departments_list(), ['pharmacy', 'lab'])
        self.assertTrue(staff.can_access_department('pharmacy'))
        self.assertTrue(staff.can_access_department('lab'))
        self.assertFalse(staff.can_access_department('radiology'))
        self.assertIn('Pharmacy', staff.get_department_scope_display_custom())
        self.assertIn('Lab', staff.get_department_scope_display_custom())

    def test_room_types_and_range_validation(self):
        """Room Types & Range Config validates duplicates, gaps, and capacity bounds."""
        from setup_hospital.models import HospitalWardCadre

        self.hospital.bed_count = 100
        self.hospital.starting_room_number = 101
        self.hospital.save()

        # Create two IPD bed services
        s_deluxe = ServiceItem.objects.create(
            hospital=self.hospital,
            name='Deluxe Private Ward',
            department=ServiceItem.Department.IPD,
            billing_unit=ServiceItem.BillingUnit.DAY,
            price=3500.00
        )
        s_general = ServiceItem.objects.create(
            hospital=self.hospital,
            name='General Inpatient Ward',
            department=ServiceItem.Department.IPD,
            billing_unit=ServiceItem.BillingUnit.DAY,
            price=1200.00
        )

        self.client.login(username='admin@citycare.in', password='TestPassword123!')
        url = reverse('setup_hospital:update_profile', kwargs={'slug': self.hospital.slug})

        # 1. Attempt overlapping room numbers (101-150 and 140-200) -> Must reject duplicate and not save
        overlap_payload = {
            'gstin': '32AABCC1234D1Z5',
            'bed_count': '100',
            'starting_room_number': '101',
            'bill_prefix': 'INV',
            'next_bill_number': '1001',
            'closing_time': '20:00:00',
            'default_tax_percent': '0.00',
            'upi_id': 'citycare@icici',
            'whatsapp_api_provider': 'meta_cloud',
            f'room_prefix_{s_deluxe.id}': 'Room ',
            f'room_from_{s_deluxe.id}': '101',
            f'room_to_{s_deluxe.id}': '150',
            f'room_prefix_{s_general.id}': 'Room ',
            f'room_from_{s_general.id}': '140',
            f'room_to_{s_general.id}': '200',
        }
        res = self.client.post(url, data=overlap_payload, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Duplicate room assignment')
        self.assertEqual(HospitalWardCadre.objects.filter(hospital=self.hospital).count(), 0)

        # 2. Attempt valid non-overlapping allocation with gap (101-130 and 140-199) -> Saves with gap notice
        gap_payload = {
            'gstin': '32AABCC1234D1Z5',
            'bed_count': '100',
            'starting_room_number': '101',
            'bill_prefix': 'INV',
            'next_bill_number': '1001',
            'closing_time': '20:00:00',
            'default_tax_percent': '0.00',
            'upi_id': 'citycare@icici',
            'whatsapp_api_provider': 'meta_cloud',
            f'room_prefix_{s_deluxe.id}': 'Room ',
            f'room_from_{s_deluxe.id}': '101',
            f'room_to_{s_deluxe.id}': '130',
            f'room_prefix_{s_general.id}': 'Room ',
            f'room_from_{s_general.id}': '140',
            f'room_to_{s_general.id}': '199',
        }
        res2 = self.client.post(url, data=gap_payload, follow=True)
        self.assertEqual(res2.status_code, 200)
        self.assertContains(res2, 'Unassigned room gap detected')
        self.assertEqual(HospitalWardCadre.objects.filter(hospital=self.hospital).count(), 2)

        # 3. Save continuous 100% complete allocation (101-140 and 141-200) -> Saves clean
        complete_payload = {
            'gstin': '32AABCC1234D1Z5',
            'bed_count': '100',
            'starting_room_number': '101',
            'bill_prefix': 'INV',
            'next_bill_number': '1001',
            'closing_time': '20:00:00',
            'default_tax_percent': '0.00',
            'upi_id': 'citycare@icici',
            'whatsapp_api_provider': 'meta_cloud',
            f'room_prefix_{s_deluxe.id}': 'Room ',
            f'room_from_{s_deluxe.id}': '101',
            f'room_to_{s_deluxe.id}': '140',
            f'room_prefix_{s_general.id}': 'Room ',
            f'room_from_{s_general.id}': '141',
            f'room_to_{s_general.id}': '200',
        }
        res3 = self.client.post(url, data=complete_payload, follow=True)
        self.assertEqual(res3.status_code, 200)
        self.assertContains(res3, 'saved successfully')
        c_deluxe = HospitalWardCadre.objects.get(hospital=self.hospital, service_item=s_deluxe)
        c_general = HospitalWardCadre.objects.get(hospital=self.hospital, service_item=s_general)
        self.assertEqual((c_deluxe.number_from, c_deluxe.number_to), (101, 140))
        self.assertEqual((c_general.number_from, c_general.number_to), (141, 200))

    def test_housekeeping_role_creation_and_room_lifecycle(self):
        """Test adding housekeeping staff, room cleaning status tracking and mark clean workflow."""
        # 1. Admin creates a Housekeeping staff member
        self.client.login(username='admin@citycare.in', password='TestPassword123!')
        add_staff_url = reverse('setup_hospital:add_staff', kwargs={'slug': self.hospital.slug})
        resp = self.client.post(add_staff_url, {
            'name': 'Ramesh Clean',
            'username': 'ramesh.hk',
            'password': 'CleanerPass123!',
            'role': HospitalStaff.Role.HOUSEKEEPING,
            'department_scope': 'all',
        }, follow=True)
        self.assertEqual(resp.status_code, 200)

        hk_staff = HospitalStaff.objects.get(hospital=self.hospital, user__username='ramesh.hk')
        self.assertEqual(hk_staff.role, HospitalStaff.Role.HOUSEKEEPING)

        # 2. Login as Housekeeping staff -> redirects to housekeeping dashboard
        self.client.logout()
        login_url = reverse('setup_hospital:login', kwargs={'slug': self.hospital.slug})
        resp = self.client.post(login_url, {
            'username': 'ramesh.hk',
            'password': 'CleanerPass123!',
        })
        self.assertRedirects(resp, reverse('setup_hospital:housekeeping_dashboard', kwargs={'slug': self.hospital.slug}))

        # 3. Access housekeeping dashboard
        hk_dash_url = reverse('setup_hospital:housekeeping_dashboard', kwargs={'slug': self.hospital.slug})
        resp = self.client.get(hk_dash_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Housekeeping Desk')
        self.assertContains(resp, 'Needs Cleaning')

        # 4. Mark a room as cleaning
        RoomBedStatus.objects.create(
            hospital=self.hospital,
            room_number='Room 101',
            status=RoomBedStatus.Status.CLEANING
        )

        resp = self.client.get(hk_dash_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Needs Cleaning')

        # 5. Housekeeping marks room clean & ready via mark_room_ready endpoint
        mark_ready_url = reverse('setup_hospital:mark_room_ready', kwargs={'slug': self.hospital.slug})
        resp = self.client.post(mark_ready_url, {'room_number': 'Room 101'}, follow=True)
        self.assertEqual(resp.status_code, 200)

        room_st = RoomBedStatus.objects.get(hospital=self.hospital, room_number='Room 101')
        self.assertEqual(room_st.status, RoomBedStatus.Status.AVAILABLE)
        self.assertIsNotNone(room_st.last_cleaned_at)
        self.assertEqual(room_st.last_cleaned_by.username, 'ramesh.hk')

