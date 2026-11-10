from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from enrollment.models import EnrollmentRequest
from setup_hospital.models import Hospital, Doctor, ServiceItem, RoomBedStatus
from billing.models import Patient, Bill, BillItem

class QuickBillingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='admin@bnv.com',
            email='admin@bnv.com',
            password='TestPassword123!'
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
            bill_prefix='BNV',
            next_bill_number=1001,
        )
        self.doctor = Doctor.objects.create(
            hospital=self.hospital,
            name='Dr. Ramesh Kumar',
            specialization='General Medicine',
            cut_type='percentage',
            cut_value=70.00
        )
        self.service1 = ServiceItem.objects.create(
            hospital=self.hospital,
            name='General OPD Consultation',
            code='OPD-01',
            price=500.00,
            tax_percent=0.00
        )
        self.service2 = ServiceItem.objects.create(
            hospital=self.hospital,
            name='ECG Test',
            code='ECG-01',
            price=350.00,
            tax_percent=0.00
        )

    def test_cashier_desk_loads(self):
        """Step s1: Cashier billing counter loads for authorized staff."""
        self.client.login(username='admin@bnv.com', password='TestPassword123!')
        url = reverse('billing:counter', kwargs={'slug': self.hospital.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Quick Billing Counter')
        self.assertContains(response, 'BNV-1001')

    def test_create_bill_auto_serial_number(self):
        """Step s2 & s3: Create bill with services; verifies serial auto-increment and doctor cut calculation."""
        self.client.login(username='admin@bnv.com', password='TestPassword123!')
        url = reverse('billing:create_bill', kwargs={'slug': self.hospital.slug})
        payload = {
            'patient_name': 'Ananthu Krishna',
            'patient_phone': '9876543210',
            'patient_age': '32',
            'patient_gender': 'M',
            'doctor_id': self.doctor.id,
            'services': [str(self.service1.id), str(self.service2.id)],
        }
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 302)

        bill = Bill.objects.get(bill_number='BNV-1001')
        self.assertEqual(bill.patient.name, 'Ananthu Krishna')
        self.assertEqual(float(bill.total_amount), 850.00) # 500 + 350
        self.assertEqual(float(bill.doctor_share_amount), 350.00) # 70% of 500

        # Hospital next serial should have auto-incremented to 1002
        self.hospital.refresh_from_db()
        self.assertEqual(self.hospital.next_bill_number, 1002)

    def test_save_patient_ajax_registration_without_services(self):
        """Receptionist can save patient registration without generating a bill."""
        self.client.login(username='admin@bnv.com', password='TestPassword123!')
        url = reverse('billing:save_patient_ajax', kwargs={'slug': self.hospital.slug})

        # Save new patient
        payload = {
            'patient_name': 'Meera Nambiar',
            'patient_phone': '9847112233',
            'patient_age': '28',
            'patient_gender': 'F',
        }
        res = self.client.post(url, data=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['created'])
        self.assertEqual(data['patient']['name'], 'Meera Nambiar')
        self.assertTrue(data['patient']['patient_id'].startswith(self.hospital.patient_id_prefix))

        patient = Patient.objects.get(hospital=self.hospital, phone='9847112233')
        self.assertEqual(patient.name, 'Meera Nambiar')
        self.assertEqual(patient.bills.count(), 0)

    def test_search_patients_api_by_name_phone_and_id(self):
        """API finds patients matching name, 10-digit phone, or Patient ID."""
        self.client.login(username='admin@bnv.com', password='TestPassword123!')
        p = Patient.objects.create(
            hospital=self.hospital,
            name='Kavya S',
            phone='9447001122',
            age=24,
            gender='F',
        )

        search_url = reverse('billing:search_patients_api', kwargs={'slug': self.hospital.slug})
        # Search by name
        res_name = self.client.get(f"{search_url}?q=Kavya")
        self.assertEqual(res_name.status_code, 200)
        self.assertEqual(len(res_name.json()['patients']), 1)
        self.assertEqual(res_name.json()['patients'][0]['name'], 'Kavya S')

        # Search by phone
        res_phone = self.client.get(f"{search_url}?q=9447")
        self.assertEqual(res_phone.status_code, 200)
        self.assertEqual(len(res_phone.json()['patients']), 1)

        # Search by Patient ID
        res_id = self.client.get(f"{search_url}?q={p.patient_id}")
        self.assertEqual(res_id.status_code, 200)
        self.assertEqual(len(res_id.json()['patients']), 1)

    def test_discharge_generates_bill_and_only_discharges_upon_payment(self):
        """Confirming discharge generates the final stay bill and only discharges inpatient after bill is paid."""
        self.client.login(username='admin@bnv.com', password='TestPassword123!')
        patient = Patient.objects.create(
            hospital=self.hospital,
            name='Vinod Menon',
            phone='9847119988',
            is_inpatient=True,
            room_bed_number='Room 102'
        )
        RoomBedStatus.objects.create(
            hospital=self.hospital,
            room_number='Room 102',
            status=RoomBedStatus.Status.OCCUPIED,
            current_patient=patient,
        )

        # 1. Post to discharge endpoint
        discharge_url = reverse('billing:discharge_patient', kwargs={'slug': self.hospital.slug, 'patient_id': patient.id})
        res = self.client.post(discharge_url)
        # Should redirect to payment checkout for the generated final bill
        self.assertEqual(res.status_code, 302)
        self.assertIn('/payments/', res.url)

        # Patient must STILL be an inpatient until paid! Room must STILL be OCCUPIED!
        patient.refresh_from_db()
        self.assertTrue(patient.is_inpatient)
        self.assertIsNone(patient.discharge_date)
        room_st = RoomBedStatus.objects.get(hospital=self.hospital, room_number='Room 102')
        self.assertEqual(room_st.status, RoomBedStatus.Status.OCCUPIED)

        # 2. Get the generated discharge bill
        bill = Bill.objects.filter(hospital=self.hospital, patient=patient, is_discharge_bill=True).first()
        self.assertIsNotNone(bill)
        self.assertEqual(bill.status, Bill.Status.UNPAID)

        # 3. Pay the bill via Cash
        record_cash_url = reverse('payments:record_cash', kwargs={'slug': self.hospital.slug, 'bill_number': bill.bill_number})
        res_pay = self.client.post(record_cash_url, {'cash_tendered': str(bill.total_amount)})
        self.assertEqual(res_pay.status_code, 302)

        # 4. NOW the patient MUST be officially discharged and room moved to CLEANING!
        patient.refresh_from_db()
        self.assertFalse(patient.is_inpatient)
        self.assertIsNotNone(patient.discharge_date)
        room_st.refresh_from_db()
        self.assertEqual(room_st.status, RoomBedStatus.Status.CLEANING)
        self.assertIsNone(room_st.current_patient)

