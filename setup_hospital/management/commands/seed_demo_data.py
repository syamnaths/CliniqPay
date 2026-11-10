from decimal import Decimal
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from setup_hospital.models import Hospital, HospitalStaff, Doctor, HospitalWardCadre, RoomBedStatus, ServiceItem
from billing.models import Patient, Bill, BillItem, Prescription, PrescriptionItem, ClinicalNote, MedicineBatch
from payments.models import PaymentTransaction
from platform_admin.models import SupportTicket
from enrollment.models import EnrollmentRequest
from setup_hospital.views import seed_hospital_services

class Command(BaseCommand):
    help = "Seeds initial showcase demo accounts and data if database is empty"

    def handle(self, *args, **options):
        # Ensure platform superuser exists
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@cliniqpay.com', 'is_staff': True, 'is_superuser': True}
        )
        admin_user.set_password('Admin1234!')
        admin_user.email = 'admin@cliniqpay.com'
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()

        if Hospital.objects.exists():
            self.stdout.write(self.style.SUCCESS("Hospitals already exist. Skipping seed."))
            return

        self.stdout.write("Seeding showcase demo accounts...")
        DEMO_PASSWORD = "DemoPassword123!"
        now = timezone.now()
        today = now.date()

        # 1. STARTER PLAN - Arogya Daycare Clinic
        enr_s = EnrollmentRequest.objects.create(
            hospital_name="Arogya Daycare Clinic",
            plan_tier=EnrollmentRequest.PlanTier.STARTER,
            bed_count=5,
            city="Kochi",
            state="Kerala",
            contact_phone="9847012345",
            contact_email="arogya@demo.in",
            admin_full_name="Dr. Anjali Nair",
            status=EnrollmentRequest.Status.ACTIVATED,
        )
        hosp_s = Hospital.objects.create(
            enrollment=enr_s,
            name="Arogya Daycare Clinic",
            slug="arogya-daycare",
            plan_tier=Hospital.PlanTier.STARTER,
            city="Kochi",
            state="Kerala",
            gstin="32AAACA1234A1Z5",
            bed_count=5,
            starting_room_number=101,
            closing_time="20:00:00",
            upi_id="arogyaclinic@upi",
            patient_id_prefix="AR",
            bill_prefix="ARO",
            next_bill_number=1005,
            upi_gateway_provider=Hospital.UpiGatewayProvider.YOUPI,
            youpi_sandbox_mode=True,
            youpi_webhook_secret="sec_arogya_demo",
        )
        seed_hospital_services(hosp_s, Hospital.PlanTier.STARTER)

        u_arogya_admin, _ = User.objects.get_or_create(username="arogya_admin", defaults={'email': "arogya@demo.in", 'first_name': "Dr. Anjali Nair"})
        u_arogya_admin.set_password(DEMO_PASSWORD)
        u_arogya_admin.save()
        HospitalStaff.objects.create(hospital=hosp_s, user=u_arogya_admin, role=HospitalStaff.Role.ADMIN, department_scope="all")
        doc_anjali = Doctor.objects.create(
            hospital=hosp_s, title="Dr.", name="Anjali Nair", specialization="General Medicine & Diabetology",
            phone="9847012345", registration_number="TCMC-45892", cut_type=Doctor.CutType.PERCENTAGE, cut_value=Decimal("80.00"),
            user=u_arogya_admin
        )

        u_arogya_cashier, _ = User.objects.get_or_create(username="arogya_cashier", defaults={'email': "cashier.arogya@demo.in", 'first_name': "Pooja Sharma"})
        u_arogya_cashier.set_password(DEMO_PASSWORD)
        u_arogya_cashier.save()
        HospitalStaff.objects.create(hospital=hosp_s, user=u_arogya_cashier, role=HospitalStaff.Role.CASHIER, department_scope="opd,misc")

        p_s1 = Patient.objects.create(hospital=hosp_s, patient_id="AR1001", name="Kavitha Menon", phone="9847112233", age=34, gender="F")
        p_s2 = Patient.objects.create(hospital=hosp_s, patient_id="AR1002", name="Gopalakrishnan K", phone="9447223344", age=58, gender="M")
        p_s3 = Patient.objects.create(hospital=hosp_s, patient_id="AR1003", name="Suresh Babu", phone="9946334455", age=45, gender="M")

        srv_opd_s = hosp_s.services.filter(department="opd").first() or hosp_s.services.first()

        b_s1 = Bill.objects.create(
            hospital=hosp_s, patient=p_s1, doctor=doc_anjali, bill_number="ARO-1001",
            bill_type=Bill.BillType.OPD, status=Bill.Status.PAID, total_amount=Decimal("500.00"),
            token_number=1, queue_status=Bill.QueueStatus.COMPLETED, billed_by="pooja_cashier"
        )
        BillItem.objects.create(bill=b_s1, service=srv_opd_s, quantity=1, unit_price=Decimal("500.00"), total_price=Decimal("500.00"))
        PaymentTransaction.objects.create(
            hospital=hosp_s, bill=b_s1, amount=Decimal("500.00"),
            method=PaymentTransaction.Method.UPI, status=PaymentTransaction.Status.SUCCESS,
            utr_number="UPI432198760011", gateway_provider="youpi", is_verified_webhook=True,
            recorded_by="youpi_webhook_relay", completed_at=now - timedelta(hours=3)
        )

        b_s2 = Bill.objects.create(
            hospital=hosp_s, patient=p_s2, doctor=doc_anjali, bill_number="ARO-1002",
            bill_type=Bill.BillType.OPD, status=Bill.Status.PAID, total_amount=Decimal("850.00"),
            token_number=2, queue_status=Bill.QueueStatus.ENGAGED, billed_by="pooja_cashier"
        )
        BillItem.objects.create(bill=b_s2, service=srv_opd_s, quantity=1, unit_price=Decimal("500.00"), total_price=Decimal("500.00"))
        PaymentTransaction.objects.create(
            hospital=hosp_s, bill=b_s2, amount=Decimal("850.00"),
            method=PaymentTransaction.Method.CASH, status=PaymentTransaction.Status.SUCCESS,
            cash_tendered=Decimal("1000.00"), cash_change=Decimal("150.00"),
            recorded_by="pooja_cashier", completed_at=now - timedelta(hours=1)
        )
        ClinicalNote.objects.create(
            hospital=hosp_s, patient=p_s2, doctor=doc_anjali, note_date=today,
            provisional_diagnosis="Type 2 Diabetes Mellitus with mild neuropathy",
            note_text="BP: 130/84, Pulse: 76 bpm. Patient presents with elevated fasting glucose (168 mg/dL). Advised HbA1c test and dietary carbohydrate control."
        )

        b_s3 = Bill.objects.create(
            hospital=hosp_s, patient=p_s3, doctor=doc_anjali, bill_number="ARO-1003",
            bill_type=Bill.BillType.OPD, status=Bill.Status.UNPAID, total_amount=Decimal("500.00"),
            token_number=3, queue_status=Bill.QueueStatus.WAITING, billed_by="pooja_cashier"
        )
        BillItem.objects.create(bill=b_s3, service=srv_opd_s, quantity=1, unit_price=Decimal("500.00"), total_price=Decimal("500.00"))

        # 2. STANDARD PLAN - City Care Hospital
        enr_std = EnrollmentRequest.objects.create(
            hospital_name="City Care Hospital",
            plan_tier=EnrollmentRequest.PlanTier.STANDARD,
            bed_count=20,
            city="Bengaluru",
            state="Karnataka",
            contact_phone="9880123456",
            contact_email="citycare@demo.in",
            admin_full_name="Dr. Vikram Rao",
            status=EnrollmentRequest.Status.ACTIVATED,
        )
        hosp_std = Hospital.objects.create(
            enrollment=enr_std,
            name="City Care Hospital",
            slug="city-care",
            plan_tier=Hospital.PlanTier.STANDARD,
            city="Bengaluru",
            state="Karnataka",
            gstin="29AABCC5678B1Z9",
            bed_count=20,
            starting_room_number=201,
            closing_time="20:00:00",
            upi_id="citycare@okhdfcbank",
            patient_id_prefix="CC",
            bill_prefix="INV",
            next_bill_number=2010,
            upi_gateway_provider=Hospital.UpiGatewayProvider.YOUPI,
            youpi_sandbox_mode=True,
            youpi_webhook_secret="sec_citycare_demo",
        )
        seed_hospital_services(hosp_std, Hospital.PlanTier.STANDARD)

        srv_ipd_std = hosp_std.services.filter(department="ipd").first()
        HospitalWardCadre.objects.create(hospital=hosp_std, name="General Ward (Shared)", prefix="GEN", number_from=201, number_to=210, service_item=srv_ipd_std)
        HospitalWardCadre.objects.create(hospital=hosp_std, name="Semi-Private Room", prefix="SEMI", number_from=211, number_to=216, service_item=srv_ipd_std)
        HospitalWardCadre.objects.create(hospital=hosp_std, name="Deluxe Private AC", prefix="DLX", number_from=217, number_to=220, service_item=srv_ipd_std)

        u_city_admin, _ = User.objects.get_or_create(username="city_admin", defaults={'email': "citycare@demo.in", 'first_name': "Dr. Vikram Rao"})
        u_city_admin.set_password(DEMO_PASSWORD)
        u_city_admin.save()
        HospitalStaff.objects.create(hospital=hosp_std, user=u_city_admin, role=HospitalStaff.Role.ADMIN, department_scope="all")
        doc_vikram = Doctor.objects.create(
            hospital=hosp_std, title="Dr.", name="Vikram Rao", specialization="General Surgery & Orthopaedics",
            phone="9880123456", registration_number="KMC-67123", cut_type=Doctor.CutType.PERCENTAGE, cut_value=Decimal("75.00"),
            user=u_city_admin
        )

        u_city_doc, _ = User.objects.get_or_create(username="dr_shalini", defaults={'email': "shalini@demo.in", 'first_name': "Dr. Shalini V"})
        u_city_doc.set_password(DEMO_PASSWORD)
        u_city_doc.save()
        HospitalStaff.objects.create(hospital=hosp_std, user=u_city_doc, role=HospitalStaff.Role.DOCTOR, department_scope="opd,ipd")
        doc_shalini = Doctor.objects.create(
            hospital=hosp_std, title="Dr.", name="Shalini V", specialization="Internal Medicine",
            phone="9880654321", registration_number="KMC-89456", cut_type=Doctor.CutType.PERCENTAGE, cut_value=Decimal("70.00"),
            user=u_city_doc
        )

        u_city_cashier, _ = User.objects.get_or_create(username="city_cashier", defaults={'email': "cashier@citycare.in", 'first_name': "Ramesh Gowda"})
        u_city_cashier.set_password(DEMO_PASSWORD)
        u_city_cashier.save()
        HospitalStaff.objects.create(hospital=hosp_std, user=u_city_cashier, role=HospitalStaff.Role.CASHIER, department_scope="all")

        u_city_pharma, _ = User.objects.get_or_create(username="city_pharma", defaults={'email': "pharma@citycare.in", 'first_name': "Deepa Nayak (R.Ph)"})
        u_city_pharma.set_password(DEMO_PASSWORD)
        u_city_pharma.save()
        HospitalStaff.objects.create(hospital=hosp_std, user=u_city_pharma, role=HospitalStaff.Role.PHARMACIST, department_scope="pharmacy")

        u_city_clean, _ = User.objects.get_or_create(username="city_clean", defaults={'email': "clean@citycare.in", 'first_name': "Sunil Kumar"})
        u_city_clean.set_password(DEMO_PASSWORD)
        u_city_clean.save()
        HospitalStaff.objects.create(hospital=hosp_std, user=u_city_clean, role=HospitalStaff.Role.HOUSEKEEPING, department_scope="housekeeping")

        srv_pcm = hosp_std.services.filter(name__icontains="Paracetamol").first()
        if srv_pcm:
            MedicineBatch.objects.create(hospital=hosp_std, service_item=srv_pcm, batch_number="PCM-2026A", expiry_date="11/27", stock_quantity=150, is_active=True)
        srv_amox = hosp_std.services.filter(name__icontains="Amoxicillin").first()
        if srv_amox:
            MedicineBatch.objects.create(hospital=hosp_std, service_item=srv_amox, batch_number="AMX-882", expiry_date="06/28", stock_quantity=80, is_active=True)

        RoomBedStatus.objects.create(hospital=hosp_std, room_number="201", status=RoomBedStatus.Status.OCCUPIED, notes="Post-op recovery")
        RoomBedStatus.objects.create(hospital=hosp_std, room_number="202", status=RoomBedStatus.Status.CLEANING, notes="Turnover sanitization in progress")
        RoomBedStatus.objects.create(hospital=hosp_std, room_number="203", status=RoomBedStatus.Status.AVAILABLE, notes="Sanitized and ready")

        p_c1 = Patient.objects.create(hospital=hosp_std, patient_id="CC2001", name="Arun Prasath", phone="9880112233", age=42, gender="M", is_inpatient=True, admission_date=now - timedelta(days=2), room_bed_number="201")
        p_c2 = Patient.objects.create(hospital=hosp_std, patient_id="CC2002", name="Priyanka Sen", phone="9880223344", age=29, gender="F")
        p_c3 = Patient.objects.create(hospital=hosp_std, patient_id="CC2003", name="Manohar Joshi", phone="9880334455", age=63, gender="M")

        b_ipd = Bill.objects.create(hospital=hosp_std, patient=p_c1, doctor=doc_vikram, bill_number="INV-2001", bill_type=Bill.BillType.IPD, room_bed_number="201", status=Bill.Status.PAID, total_amount=Decimal("4400.00"), billed_by="city_cashier")
        BillItem.objects.create(bill=b_ipd, item_name="Semi-Private Room Rent (2 Days)", quantity=2, unit_price=Decimal("2200.00"), total_price=Decimal("4400.00"))
        PaymentTransaction.objects.create(hospital=hosp_std, bill=b_ipd, amount=Decimal("4400.00"), method=PaymentTransaction.Method.UPI, status=PaymentTransaction.Status.SUCCESS, utr_number="UPI778899001122", gateway_provider="youpi", is_verified_webhook=True, recorded_by="city_cashier", completed_at=now - timedelta(hours=6))

        rx_c2 = Prescription.objects.create(hospital=hosp_std, patient=p_c2, doctor=doc_shalini, rx_number="RX-CC-101", diagnosis="Acute Bronchitis & Pharyngitis", vitals_bp="118/76", vitals_pulse="80", vitals_temp="100.2 F", clinical_notes="Drink warm fluids. Return for review in 5 days if fever persists.")
        PrescriptionItem.objects.create(prescription=rx_c2, medicine_name="Amoxicillin 500mg Capsule", dosage="1-0-1", timing="After Food", duration="5 Days", quantity=10)
        PrescriptionItem.objects.create(prescription=rx_c2, medicine_name="Paracetamol 650mg Tablet", dosage="1-1-1", timing="After Food", duration="3 Days", quantity=6)

        b_c3 = Bill.objects.create(hospital=hosp_std, patient=p_c3, doctor=doc_shalini, bill_number="INV-2003", bill_type=Bill.BillType.OPD, status=Bill.Status.UNPAID, total_amount=Decimal("600.00"), token_number=1, queue_status=Bill.QueueStatus.WAITING, billed_by="city_cashier")
        srv_opd_std = hosp_std.services.filter(department="opd").first()
        BillItem.objects.create(bill=b_c3, service=srv_opd_std, quantity=1, unit_price=Decimal("600.00"), total_price=Decimal("600.00"))

        # 3. ENTERPRISE PLAN - Apex Multi-Specialty Hospital
        enr_ent = EnrollmentRequest.objects.create(
            hospital_name="Apex Multi-Specialty Hospital",
            plan_tier=EnrollmentRequest.PlanTier.ENTERPRISE,
            bed_count=50,
            city="Mumbai",
            state="Maharashtra",
            contact_phone="9820123456",
            contact_email="apex@demo.in",
            admin_full_name="Dr. Cyrus Mehta",
            status=EnrollmentRequest.Status.ACTIVATED,
        )
        hosp_ent = Hospital.objects.create(
            enrollment=enr_ent,
            name="Apex Multi-Specialty Hospital",
            slug="apex-hospital",
            plan_tier=Hospital.PlanTier.ENTERPRISE,
            city="Mumbai",
            state="Maharashtra",
            gstin="27AAAPA9876C1Z3",
            bed_count=50,
            starting_room_number=301,
            closing_time="20:00:00",
            upi_id="apexhospital@icici",
            patient_id_prefix="APX",
            bill_prefix="APX",
            next_bill_number=3015,
            upi_gateway_provider=Hospital.UpiGatewayProvider.YOUPI,
            youpi_sandbox_mode=True,
            youpi_webhook_secret="sec_apex_demo",
        )
        seed_hospital_services(hosp_ent, Hospital.PlanTier.ENTERPRISE)

        srv_ipd_ent = hosp_ent.services.filter(department="ipd").first()
        HospitalWardCadre.objects.create(hospital=hosp_ent, name="Semi-Private AC Ward", prefix="SP", number_from=301, number_to=320, service_item=srv_ipd_ent)
        HospitalWardCadre.objects.create(hospital=hosp_ent, name="Executive Suite", prefix="EXE", number_from=321, number_to=340, service_item=srv_ipd_ent)
        HospitalWardCadre.objects.create(hospital=hosp_ent, name="ICU High Dependency", prefix="ICU", number_from=341, number_to=350, service_item=srv_ipd_ent)

        u_apex_admin, _ = User.objects.get_or_create(username="apex_admin", defaults={'email': "apex@demo.in", 'first_name': "Dr. Cyrus Mehta"})
        u_apex_admin.set_password(DEMO_PASSWORD)
        u_apex_admin.save()
        HospitalStaff.objects.create(hospital=hosp_ent, user=u_apex_admin, role=HospitalStaff.Role.ADMIN, department_scope="all")
        doc_cyrus = Doctor.objects.create(
            hospital=hosp_ent, title="Dr.", name="Cyrus Mehta", specialization="Chief of Cardiology",
            phone="9820123456", registration_number="MMC-12984", cut_type=Doctor.CutType.PERCENTAGE, cut_value=Decimal("80.00"),
            user=u_apex_admin
        )

        u_apex_neuro, _ = User.objects.get_or_create(username="dr_tanya", defaults={'email': "tanya@demo.in", 'first_name': "Dr. Tanya Shroff"})
        u_apex_neuro.set_password(DEMO_PASSWORD)
        u_apex_neuro.save()
        HospitalStaff.objects.create(hospital=hosp_ent, user=u_apex_neuro, role=HospitalStaff.Role.DOCTOR, department_scope="opd,ipd")
        Doctor.objects.create(
            hospital=hosp_ent, title="Dr.", name="Tanya Shroff", specialization="Neurology & Stroke Care",
            phone="9820876543", registration_number="MMC-34789", cut_type=Doctor.CutType.PERCENTAGE, cut_value=Decimal("75.00"),
            user=u_apex_neuro
        )

        u_apex_cashier, _ = User.objects.get_or_create(username="apex_cashier", defaults={'email': "cashier@apex.in", 'first_name': "Amitabh Kulkarni"})
        u_apex_cashier.set_password(DEMO_PASSWORD)
        u_apex_cashier.save()
        HospitalStaff.objects.create(hospital=hosp_ent, user=u_apex_cashier, role=HospitalStaff.Role.CASHIER, department_scope="all")

        u_apex_pharma, _ = User.objects.get_or_create(username="apex_pharma", defaults={'email': "pharmacy@apex.in", 'first_name': "Farhan Qureshi (Pharm.D)"})
        u_apex_pharma.set_password(DEMO_PASSWORD)
        u_apex_pharma.save()
        HospitalStaff.objects.create(hospital=hosp_ent, user=u_apex_pharma, role=HospitalStaff.Role.PHARMACIST, department_scope="pharmacy")

        u_apex_clean, _ = User.objects.get_or_create(username="apex_clean", defaults={'email': "housekeeping@apex.in", 'first_name': "Sanjay Pawar"})
        u_apex_clean.set_password(DEMO_PASSWORD)
        u_apex_clean.save()
        HospitalStaff.objects.create(hospital=hosp_ent, user=u_apex_clean, role=HospitalStaff.Role.HOUSEKEEPING, department_scope="housekeeping")

        RoomBedStatus.objects.create(hospital=hosp_ent, room_number="301", status=RoomBedStatus.Status.OCCUPIED, notes="Cardiac ICU Monitor Bed")
        RoomBedStatus.objects.create(hospital=hosp_ent, room_number="302", status=RoomBedStatus.Status.CLEANING, notes="Deep sanitization after discharge")
        RoomBedStatus.objects.create(hospital=hosp_ent, room_number="303", status=RoomBedStatus.Status.AVAILABLE, notes="Executive Suite ready")

        p_e1 = Patient.objects.create(hospital=hosp_ent, patient_id="APX3001", name="Ratan Wadia", phone="9820112233", age=68, gender="M", is_inpatient=True, admission_date=now - timedelta(days=3), room_bed_number="301")
        p_e2 = Patient.objects.create(hospital=hosp_ent, patient_id="APX3002", name="Natasha D'Souza", phone="9820223344", age=36, gender="F")
        p_e3 = Patient.objects.create(hospital=hosp_ent, patient_id="APX3003", name="Vikramaditya Singhania", phone="9820334455", age=52, gender="M")

        b_e1 = Bill.objects.create(hospital=hosp_ent, patient=p_e2, doctor=doc_cyrus, bill_number="APX-3001", bill_type=Bill.BillType.OPD, status=Bill.Status.PAID, total_amount=Decimal("3500.00"), token_number=1, queue_status=Bill.QueueStatus.COMPLETED, billed_by="apex_cashier")
        BillItem.objects.create(bill=b_e1, item_name="Comprehensive 2D Echocardiography & Doppler", quantity=1, unit_price=Decimal("3500.00"), total_price=Decimal("3500.00"))
        PaymentTransaction.objects.create(hospital=hosp_ent, bill=b_e1, amount=Decimal("3500.00"), method=PaymentTransaction.Method.UPI, status=PaymentTransaction.Status.SUCCESS, utr_number="UPI990011223344", gateway_provider="youpi", is_verified_webhook=True, recorded_by="youpi_webhook_relay", completed_at=now - timedelta(hours=2))

        SupportTicket.objects.create(
            hospital=hosp_ent,
            ticket_number="TCK-APX-101",
            created_by=u_apex_admin,
            staff_name="Dr. Cyrus Mehta",
            contact_email="apex@demo.in",
            category=SupportTicket.Category.BILLING_POS,
            priority=SupportTicket.Priority.MEDIUM,
            status=SupportTicket.Status.OPEN,
            subject="NABH accreditation tariff tag display inquiry",
            description="We would like to display NABH certified accreditation badge on patient counter tablet displays and PDF invoice receipts."
        )

        self.stdout.write(self.style.SUCCESS("Showcase demo data provisioned successfully!"))
