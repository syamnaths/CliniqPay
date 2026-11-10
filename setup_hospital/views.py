import base64
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.base import ContentFile
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from platform_admin.models import SupportTicket, TicketMessage
from setup_hospital.models import Hospital, ServiceItem, Doctor, HospitalStaff, HospitalWardCadre, RoomBedStatus
from billing.models import Patient

def get_staff_role(user, hospital):
    if not user.is_authenticated:
        return None
    # Superuser has emergency administrative access across tenants
    if user.is_superuser:
        return HospitalStaff.Role.ADMIN
    if hospital.enrollment and (user.username == hospital.enrollment.contact_email or user.email == hospital.enrollment.contact_email):
        return HospitalStaff.Role.ADMIN
    
    # Check if user is linked directly to a Doctor profile for this hospital
    doctor = Doctor.objects.filter(hospital=hospital, user=user).first()
    if doctor:
        return HospitalStaff.Role.DOCTOR

    staff = HospitalStaff.objects.filter(hospital=hospital, user=user).first()
    if staff:
        return staff.role
    return None

def can_access_hospital(user, hospital):
    return get_staff_role(user, hospital) is not None

def is_hospital_admin(user, hospital):
    return get_staff_role(user, hospital) == HospitalStaff.Role.ADMIN

def hospital_login(request, slug):
    hospital = get_object_or_404(Hospital, slug=slug)
    role = get_staff_role(request.user, hospital)
    if role == HospitalStaff.Role.ADMIN:
        return redirect('setup_hospital:dashboard', slug=hospital.slug)
    elif role == HospitalStaff.Role.DOCTOR:
        return redirect('setup_hospital:doctor_portal', slug=hospital.slug)
    elif role == HospitalStaff.Role.CASHIER:
        return redirect('billing:counter', slug=hospital.slug)
    elif role == HospitalStaff.Role.PHARMACIST:
        return redirect('billing:pharmacy_counter', slug=hospital.slug)
    elif role == HospitalStaff.Role.HOUSEKEEPING:
        return redirect('setup_hospital:housekeeping_dashboard', slug=hospital.slug)

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            user_role = get_staff_role(user, hospital)
            if user_role:
                auth_login(request, user)
                if user_role == HospitalStaff.Role.CASHIER:
                    return redirect('billing:counter', slug=hospital.slug)
                elif user_role == HospitalStaff.Role.DOCTOR:
                    return redirect('setup_hospital:doctor_portal', slug=hospital.slug)
                elif user_role == HospitalStaff.Role.PHARMACIST:
                    return redirect('billing:pharmacy_counter', slug=hospital.slug)
                elif user_role == HospitalStaff.Role.HOUSEKEEPING:
                    return redirect('setup_hospital:housekeeping_dashboard', slug=hospital.slug)
                next_url = request.POST.get('next') or f'/hospital/{hospital.slug}/'
                return redirect(next_url)
            else:
                form.add_error(None, f"Account does not have access to {hospital.name}.")

    return render(request, 'setup_hospital/login.html', {
        'hospital': hospital,
        'form': form,
        'next': request.GET.get('next', ''),
    })

def hospital_logout(request, slug):
    hospital = get_object_or_404(Hospital, slug=slug)
    auth_logout(request)
    return redirect('setup_hospital:login', slug=hospital.slug)

# Tier-specific default service catalogs with intelligent billing units
PLAN_SERVICES_MAP = {
    Hospital.PlanTier.STARTER: [
        ('General OPD Consultation', 'OPD-001', ServiceItem.Department.OPD, ServiceItem.BillingUnit.VISIT, 350.00, 0.00),
        ('Minor Dressing & Suturing', 'PROC-001', ServiceItem.Department.OPD, ServiceItem.BillingUnit.COUNT, 300.00, 0.00),
        ('Rapid Blood Glucose Test', 'LAB-001', ServiceItem.Department.LAB, ServiceItem.BillingUnit.TEST, 100.00, 0.00),
        ('Daycare Observation Bed (Per Hour)', 'IPD-001', ServiceItem.Department.IPD, ServiceItem.BillingUnit.HOUR, 600.00, 0.00),
    ],
    Hospital.PlanTier.STANDARD: [
        ('General OPD Consultation', 'OPD-001', ServiceItem.Department.OPD, ServiceItem.BillingUnit.VISIT, 500.00, 0.00),
        ('Specialist Doctor Consultation', 'OPD-002', ServiceItem.Department.OPD, ServiceItem.BillingUnit.VISIT, 800.00, 0.00),
        ('Wound Dressing & Suturing', 'PROC-001', ServiceItem.Department.OPD, ServiceItem.BillingUnit.COUNT, 450.00, 0.00),
        ('12-Lead ECG Test', 'ECG-001', ServiceItem.Department.OPD, ServiceItem.BillingUnit.TEST, 350.00, 0.00),
        ('Complete Blood Count (CBC)', 'LAB-002', ServiceItem.Department.LAB, ServiceItem.BillingUnit.TEST, 400.00, 0.00),
        ('Urine Routine & Microscopic', 'LAB-003', ServiceItem.Department.LAB, ServiceItem.BillingUnit.TEST, 250.00, 0.00),
        ('Ultrasound Whole Abdomen (USG)', 'RAD-001', ServiceItem.Department.RADIOLOGY, ServiceItem.BillingUnit.TEST, 1400.00, 0.00),
        ('General Inpatient Bed Rent (Per Day)', 'IPD-002', ServiceItem.Department.IPD, ServiceItem.BillingUnit.DAY, 2200.00, 0.00),
        ('Common Dispensing & Pharmacy Pack', 'PHARM-001', ServiceItem.Department.PHARMACY, ServiceItem.BillingUnit.STRIP, 250.00, 0.00),
    ],
    Hospital.PlanTier.ENTERPRISE: [
        ('General OPD Consultation', 'OPD-001', ServiceItem.Department.OPD, ServiceItem.BillingUnit.VISIT, 600.00, 0.00),
        ('Senior Consultant / Super-Specialist', 'OPD-003', ServiceItem.Department.OPD, ServiceItem.BillingUnit.VISIT, 1200.00, 0.00),
        ('Comprehensive Health Checkup Panel', 'LAB-004', ServiceItem.Department.LAB, ServiceItem.BillingUnit.TEST, 2500.00, 0.00),
        ('Liver & Kidney Function Panel', 'LAB-005', ServiceItem.Department.LAB, ServiceItem.BillingUnit.TEST, 1100.00, 0.00),
        ('Digital Chest X-Ray (PA View)', 'RAD-002', ServiceItem.Department.RADIOLOGY, ServiceItem.BillingUnit.TEST, 650.00, 0.00),
        ('Color Doppler Ultrasound Scan', 'RAD-003', ServiceItem.Department.RADIOLOGY, ServiceItem.BillingUnit.TEST, 2200.00, 0.00),
        ('Deluxe Room / Private Ward (Per Day)', 'IPD-003', ServiceItem.Department.IPD, ServiceItem.BillingUnit.DAY, 4500.00, 0.00),
        ('ICU / Critical Care Bed (Per Day)', 'IPD-004', ServiceItem.Department.IPD, ServiceItem.BillingUnit.DAY, 8500.00, 0.00),
        ('Major Operation Theater Charges', 'IPD-005', ServiceItem.Department.IPD, ServiceItem.BillingUnit.SESSION, 15000.00, 0.00),
        ('Inpatient Medication Dispensing Pack', 'PHARM-002', ServiceItem.Department.PHARMACY, ServiceItem.BillingUnit.STRIP, 750.00, 0.00),
    ],
}

def seed_hospital_services(hospital, target_tier=None):
    """
    Seeds default service catalog items idempotently for the given hospital based on its plan tier.
    Preserves all existing custom items; adds missing items by code and name.
    """
    tier = target_tier or hospital.plan_tier or Hospital.PlanTier.STANDARD
    service_defs = PLAN_SERVICES_MAP.get(tier, PLAN_SERVICES_MAP[Hospital.PlanTier.STANDARD])
    
    for item in service_defs:
        if len(item) == 6:
            name, code, dept, unit, price, tax = item
        else:
            name, code, dept, price, tax = item
            unit = ServiceItem.BillingUnit.COUNT

        if not hospital.services.filter(code=code).exists() and not hospital.services.filter(name=name).exists():
            ServiceItem.objects.create(
                hospital=hospital,
                department=dept,
                billing_unit=unit,
                name=name,
                code=code,
                price=price,
                tax_percent=tax,
            )

DEFAULT_SERVICES = [
    ('General OPD Consultation', 'OPD-01', 500.00, 0.00),
    ('ECG Test', 'ECG-01', 350.00, 0.00),
    ('Ultrasound Scan (USG)', 'USG-01', 1200.00, 0.00),
    ('Wound Dressing & Suturing', 'PROC-01', 400.00, 0.00),
    ('Daycare Room Rent (General)', 'ROOM-01', 2500.00, 0.00),
]

def dashboard(request, slug):
    hospital = get_object_or_404(Hospital, slug=slug)
    if not is_hospital_admin(request.user, hospital):
        if can_access_hospital(request.user, hospital):
            role = get_staff_role(request.user, hospital)
            if role == HospitalStaff.Role.HOUSEKEEPING:
                return redirect('setup_hospital:housekeeping_dashboard', slug=hospital.slug)
            elif role == HospitalStaff.Role.PHARMACIST:
                return redirect('billing:pharmacy_counter', slug=hospital.slug)
            # Cashiers get redirected to their billing desk
            return redirect('billing:counter', slug=hospital.slug)
        return redirect(f'/hospital/{hospital.slug}/login/?next=/hospital/{hospital.slug}/')
    
    # Auto-seed tier-appropriate services if hospital has no catalog
    if not hospital.services.exists():
        seed_hospital_services(hospital)

    services = hospital.services.filter(is_active=True)
    doctors = hospital.doctors.select_related('user').all()

    staff_members = hospital.staff_members.exclude(role=HospitalStaff.Role.DOCTOR).select_related('user').all()
    ward_cadres = hospital.ward_cadres.select_related('service_item').all()
    ipd_services = services.filter(department='ipd')

    # Detect missing critical details in Hospital Details & Cutoff to prompt the user
    missing_fields = []
    if not hospital.gstin:
        missing_fields.append('GSTIN Number')
    if not hospital.upi_id:
        missing_fields.append('Clinic UPI ID (QR Target)')
    if not hospital.bill_prefix:
        missing_fields.append('Bill Serial Prefix')
    if hospital.plan_tier != Hospital.PlanTier.STARTER and not hospital.ward_cadres.exists():
        missing_fields.append('Ward & Room Number Cadres')

    # All room/bed services with daily or hourly billing units across the catalog
    bed_tariff_services = services.filter(billing_unit__in=[ServiceItem.BillingUnit.DAY, ServiceItem.BillingUnit.HOUR])

    # Map existing cadre ranges to bed services for prefilling in Hospital Details
    cadre_map = {c.service_item_id: c for c in ward_cadres if c.service_item_id}
    bed_tariff_list = []
    for s in bed_tariff_services:
        c = cadre_map.get(s.id)
        bed_tariff_list.append({
            'service': s,
            'cadre': c,
            'prefix': c.prefix if c else ('ICU-' if 'icu' in s.name.lower() else 'Room '),
            'number_from': c.number_from if c else None,
            'number_to': c.number_to if c else None,
        })

    max_room_number = hospital.starting_room_number + max(0, hospital.bed_count - 1)

    role = get_staff_role(request.user, hospital)

    return render(request, 'setup_hospital/dashboard.html', {
        'hospital': hospital,
        'services': services,
        'doctors': doctors,
        'staff_members': staff_members,
        'ward_cadres': ward_cadres,
        'ipd_services': ipd_services,
        'bed_tariff_services': bed_tariff_services,
        'bed_tariff_list': bed_tariff_list,
        'max_room_number': max_room_number,
        'missing_fields': missing_fields,
        'staff_role': role,
    })

def add_staff(request, slug):
    hospital = get_object_or_404(Hospital, slug=slug)
    if not is_hospital_admin(request.user, hospital):
        return HttpResponseForbidden('Only hospital administrators can manage staff.')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        name = request.POST.get('name', '').strip()
        password = request.POST.get('password', '').strip()
        role = request.POST.get('role', HospitalStaff.Role.CASHIER)

        # Multi-select department scope checkboxes
        if role == HospitalStaff.Role.PHARMACIST:
            department_scope = 'pharmacy'
        elif role == HospitalStaff.Role.HOUSEKEEPING:
            department_scope = 'housekeeping'
        else:
            dept_scopes = request.POST.getlist('department_scope')
            if not dept_scopes or 'all' in dept_scopes:
                department_scope = 'all'
            else:
                department_scope = ','.join(dept_scopes)

        if username and password:
            user, created = User.objects.get_or_create(username=username, defaults={'first_name': name})
            user.set_password(password)
            user.first_name = name
            user.save()

            HospitalStaff.objects.update_or_create(
                hospital=hospital,
                user=user,
                defaults={'role': role, 'department_scope': department_scope}
            )

    return redirect('setup_hospital:dashboard', slug=hospital.slug)

def edit_staff(request, slug, staff_id):
    hospital = get_object_or_404(Hospital, slug=slug)
    if not is_hospital_admin(request.user, hospital):
        return HttpResponseForbidden('Only hospital administrators can edit staff.')

    staff = get_object_or_404(HospitalStaff, hospital=hospital, id=staff_id)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        new_password = request.POST.get('password', '').strip()
        role = request.POST.get('role', staff.role)

        if role == HospitalStaff.Role.PHARMACIST:
            department_scope = 'pharmacy'
        elif role == HospitalStaff.Role.HOUSEKEEPING:
            department_scope = 'housekeeping'
        else:
            dept_scopes = request.POST.getlist('department_scope')
            if not dept_scopes or 'all' in dept_scopes:
                department_scope = 'all'
            else:
                department_scope = ','.join(dept_scopes)

        if name:
            staff.user.first_name = name
        if new_password:
            staff.user.set_password(new_password)
        staff.role = role
        staff.department_scope = department_scope
        staff.user.save()
        staff.save()

    return redirect('setup_hospital:dashboard', slug=hospital.slug)

def reset_staff_password(request, slug):
    """Allows hospital admin to securely reset password for staff or doctors."""
    hospital = get_object_or_404(Hospital, slug=slug)
    if not is_hospital_admin(request.user, hospital):
        return HttpResponseForbidden('Only hospital administrators can reset passwords.')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        new_password = request.POST.get('new_password', '').strip()

        if not username or not new_password:
            messages.error(request, 'Username and new password are required.')
            return redirect('setup_hospital:dashboard', slug=hospital.slug)

        if len(new_password) < 6:
            messages.error(request, 'Password must be at least 6 characters long.')
            return redirect('setup_hospital:dashboard', slug=hospital.slug)

        # Confirm user belongs to this hospital (either as staff or doctor)
        is_hospital_user = (
            HospitalStaff.objects.filter(hospital=hospital, user__username=username).exists() or
            Doctor.objects.filter(hospital=hospital, user__username=username).exists()
        )
        if not is_hospital_user:
            messages.error(request, 'User does not belong to this hospital.')
            return redirect('setup_hospital:dashboard', slug=hospital.slug)

        target_user = User.objects.filter(username=username).first()
        if target_user:
            target_user.set_password(new_password)
            target_user.save()
            messages.success(request, f'Password for {target_user.get_full_name() or target_user.username} has been reset successfully.')

    return redirect('setup_hospital:dashboard', slug=hospital.slug)

def user_profile(request, slug):
    """
    Profile page for authenticated staff/admin with password change & identity details.
    """
    hospital = get_object_or_404(Hospital, slug=slug)
    if not can_access_hospital(request.user, hospital):
        return redirect(f'/hospital/{hospital.slug}/login/')

    role = get_staff_role(request.user, hospital)
    staff = hospital.staff_members.filter(user=request.user).first()

    success_msg = None
    error_msg = None

    if request.method == 'POST':
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        first_name = request.POST.get('first_name', '').strip()

        if first_name:
            request.user.first_name = first_name
            request.user.save()

        if new_password:
            if new_password != confirm_password:
                error_msg = "Passwords do not match. Please try again."
            elif len(new_password) < 6:
                error_msg = "Password must be at least 6 characters long."
            else:
                request.user.set_password(new_password)
                request.user.save()
                auth_login(request, request.user) # Preserve login session
                if staff:
                    staff.save()
                success_msg = "Password updated successfully!"

    return render(request, 'setup_hospital/profile.html', {
        'hospital': hospital,
        'role': role,
        'staff': staff,
        'success_msg': success_msg,
        'error_msg': error_msg,
    })

def update_profile(request, slug):
    hospital = get_object_or_404(Hospital, slug=slug)
    if not can_access_hospital(request.user, hospital):
        return redirect(f'/hospital/{hospital.slug}/login/')
    if request.method == 'POST':
        hospital.gstin = request.POST.get('gstin', '').strip()
        bed_count = request.POST.get('bed_count')
        if bed_count:
            try:
                hospital.bed_count = max(1, int(bed_count))
            except ValueError:
                pass
        starting_room = request.POST.get('starting_room_number')
        if starting_room:
            try:
                hospital.starting_room_number = max(1, int(starting_room))
            except ValueError:
                pass
        hospital.closing_time = request.POST.get('closing_time', '20:00:00')
        hospital.upi_id = request.POST.get('upi_id', '').strip()
        hospital.patient_id_prefix = request.POST.get('patient_id_prefix', 'P').strip().upper() or 'P'
        hospital.bill_prefix = request.POST.get('bill_prefix', 'INV').strip().upper()
        tax_pct = request.POST.get('default_tax_percent')
        if tax_pct:
            hospital.default_tax_percent = Decimal(tax_pct)
        next_num = request.POST.get('next_bill_number')
        if next_num:
            hospital.next_bill_number = int(next_num)

        # YouPI-PG Gateway Integration Settings
        hospital.upi_gateway_provider = request.POST.get('upi_gateway_provider', 'native')
        hospital.youpi_api_url = request.POST.get('youpi_api_url', '').strip() or 'http://localhost:6100'
        hospital.youpi_merchant_id = request.POST.get('youpi_merchant_id', '').strip()
        hospital.youpi_webhook_secret = request.POST.get('youpi_webhook_secret', '').strip()
        hospital.youpi_sandbox_mode = bool(request.POST.get('youpi_sandbox_mode'))

        # WhatsApp API Integration Settings
        hospital.whatsapp_api_provider = request.POST.get('whatsapp_api_provider', 'meta_cloud')
        hospital.whatsapp_api_key = request.POST.get('whatsapp_api_key', '').strip()
        hospital.whatsapp_phone_number_id = request.POST.get('whatsapp_phone_number_id', '').strip()
        hospital.whatsapp_business_account_id = request.POST.get('whatsapp_business_account_id', '').strip()

        # Hospital Brand Logo Upload & Removal (supports cropped base64 or file upload)
        if 'remove_logo' in request.POST and request.POST.get('remove_logo') == '1':
            if hospital.logo:
                hospital.logo.delete(save=False)
            hospital.logo = None
        else:
            cropped_data = request.POST.get('cropped_logo_data', '').strip()
            if cropped_data and cropped_data.startswith('data:image'):
                try:
                    format_header, imgstr = cropped_data.split(';base64,')
                    ext = format_header.split('/')[-1]
                    if ext == 'svg+xml':
                        ext = 'svg'
                    elif ext not in ['png', 'jpeg', 'jpg', 'webp']:
                        ext = 'png'
                    filename = f"logo_{hospital.slug}.{ext}"
                    data = ContentFile(base64.b64decode(imgstr), name=filename)
                    if hospital.logo:
                        hospital.logo.delete(save=False)
                    hospital.logo = data
                except Exception:
                    pass
            elif 'logo' in request.FILES:
                hospital.logo = request.FILES['logo']

        hospital.save()

        # Update or create Ward Cadre ranges submitted for discovered room types
        if hospital.plan_tier != Hospital.PlanTier.STARTER:
            bed_tariff_services = hospital.services.filter(
                is_active=True,
                billing_unit__in=[ServiceItem.BillingUnit.DAY, ServiceItem.BillingUnit.HOUR]
            )

            # Collect parsed submitted ranges
            submitted_cadres = []
            parsing_error = False
            for s in bed_tariff_services:
                prefix = request.POST.get(f'room_prefix_{s.id}', 'Room ').strip()
                if prefix and not prefix.endswith(' ') and not prefix.endswith('-'):
                    prefix = prefix + ' '
                r_from = request.POST.get(f'room_from_{s.id}', '').strip()
                r_to = request.POST.get(f'room_to_{s.id}', '').strip()

                if r_from or r_to:
                    if not (r_from and r_to):
                        messages.error(request, f"Please enter both From and To room numbers for '{s.name}'.")
                        parsing_error = True
                        continue
                    try:
                        n_from = int(r_from)
                        n_to = int(r_to)
                        if n_from <= 0 or n_to <= 0:
                            messages.error(request, f"Room numbers must be positive integers for '{s.name}'.")
                            parsing_error = True
                        elif n_to < n_from:
                            messages.error(request, f"Room 'To' ({n_to}) cannot be less than 'From' ({n_from}) for '{s.name}'.")
                            parsing_error = True
                        else:
                            submitted_cadres.append({
                                'service': s,
                                'prefix': prefix,
                                'from': n_from,
                                'to': n_to,
                            })
                    except (ValueError, TypeError):
                        messages.error(request, f"Invalid room numbers entered for '{s.name}'.")
                        parsing_error = True

            # If no format errors, perform rigorous overlap, boundary, and gap checks
            if not parsing_error and submitted_cadres:
                expected_start = hospital.starting_room_number
                expected_end = hospital.starting_room_number + max(0, hospital.bed_count - 1)

                # 1. Check duplicate/overlap across room ranges
                overlap_found = False
                sorted_cadres = sorted(submitted_cadres, key=lambda c: c['from'])

                for i in range(len(sorted_cadres)):
                    for j in range(i + 1, len(sorted_cadres)):
                        c1 = sorted_cadres[i]
                        c2 = sorted_cadres[j]
                        # Check if intervals [c1.from, c1.to] and [c2.from, c2.to] intersect
                        if max(c1['from'], c2['from']) <= min(c1['to'], c2['to']):
                            overlap_start = max(c1['from'], c2['from'])
                            overlap_end = min(c1['to'], c2['to'])
                            overlap_str = f"Room {overlap_start}" if overlap_start == overlap_end else f"Rooms {overlap_start}–{overlap_end}"
                            messages.error(
                                request,
                                f"Duplicate room assignment: {overlap_str} is entered in both '{c1['service'].name}' "
                                f"({c1['from']}–{c1['to']}) and '{c2['service'].name}' ({c2['from']}–{c2['to']}). "
                                f"Each room number can only be assigned once."
                            )
                            overlap_found = True
                            break
                    if overlap_found:
                        break

                if not overlap_found:
                    # 2. Check bounds against hospital capacity and starting room
                    min_room = sorted_cadres[0]['from']
                    max_room = max(c['to'] for c in sorted_cadres)
                    total_assigned_beds = sum(c['to'] - c['from'] + 1 for c in sorted_cadres)

                    if min_room < expected_start:
                        messages.warning(
                            request,
                            f"Room range starts at {min_room}, which is below hospital Starting Room No. ({expected_start})."
                        )
                    if max_room > expected_end:
                        messages.warning(
                            request,
                            f"Room range extends to {max_room}, which exceeds hospital room capacity limit of {expected_end} "
                            f"({hospital.bed_count} beds starting from {expected_start})."
                        )

                    # 3. Check for gaps between ranges
                    gaps = []
                    for i in range(len(sorted_cadres) - 1):
                        current_to = sorted_cadres[i]['to']
                        next_from = sorted_cadres[i + 1]['from']
                        if next_from > current_to + 1:
                            gap_start = current_to + 1
                            gap_end = next_from - 1
                            if gap_start == gap_end:
                                gaps.append(f"Room {gap_start}")
                            else:
                                gaps.append(f"Rooms {gap_start}–{gap_end}")

                    if gaps:
                        messages.warning(
                            request,
                            f"Unassigned room gap detected: {', '.join(gaps)} not allocated to any room type. "
                            f"Ensure all hospital rooms are assigned if all beds are active."
                        )

                    # 4. Check if total assigned rooms match bed capacity
                    if total_assigned_beds < hospital.bed_count:
                        missing_count = hospital.bed_count - total_assigned_beds
                        messages.warning(
                            request,
                            f"Incomplete room allocation: Only {total_assigned_beds} of {hospital.bed_count} beds have been assigned to room types ({missing_count} beds remaining)."
                        )

                    # Save validated cadres
                    for cad in submitted_cadres:
                        s = cad['service']
                        cadre = HospitalWardCadre.objects.filter(hospital=hospital, service_item=s).first()
                        if cadre:
                            cadre.prefix = cad['prefix']
                            cadre.number_from = cad['from']
                            cadre.number_to = cad['to']
                            cadre.save()
                        else:
                            HospitalWardCadre.objects.create(
                                hospital=hospital,
                                name=s.name,
                                service_item=s,
                                prefix=cad['prefix'],
                                number_from=cad['from'],
                                number_to=cad['to']
                            )
                    messages.success(request, f"Hospital configuration and room ranges ({expected_start}–{expected_end}) saved successfully.")

    return redirect('setup_hospital:dashboard', slug=hospital.slug)

def add_service(request, slug):
    hospital = get_object_or_404(Hospital, slug=slug)
    if not can_access_hospital(request.user, hospital):
        return redirect(f'/hospital/{hospital.slug}/login/')
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip()
        department = request.POST.get('department', ServiceItem.Department.OPD)
        billing_unit = request.POST.get('billing_unit', ServiceItem.BillingUnit.COUNT)
        price = request.POST.get('price', '0.00')
        tax_percent = request.POST.get('tax_percent') or hospital.default_tax_percent
        storage_location = request.POST.get('storage_location', '').strip()
        is_pharmacy_lite = bool(request.POST.get('is_pharmacy_lite'))

        if name and price:
            # Auto-infer intelligent billing unit if not explicitly customized
            if billing_unit == ServiceItem.BillingUnit.COUNT:
                name_lower = name.lower()
                if 'hour' in name_lower or 'observation' in name_lower:
                    billing_unit = ServiceItem.BillingUnit.HOUR
                elif 'day' in name_lower or 'ward' in name_lower or 'room' in name_lower or 'bed' in name_lower or 'icu' in name_lower:
                    billing_unit = ServiceItem.BillingUnit.DAY
                elif 'session' in name_lower or 'therapy' in name_lower or 'dialysis' in name_lower or 'theater' in name_lower:
                    billing_unit = ServiceItem.BillingUnit.SESSION
                elif department in ['lab', 'radiology'] or 'scan' in name_lower or 'x-ray' in name_lower or 'test' in name_lower:
                    billing_unit = ServiceItem.BillingUnit.TEST
                elif department == 'pharmacy' or 'strip' in name_lower or 'pack' in name_lower:
                    billing_unit = ServiceItem.BillingUnit.STRIP
                elif 'consult' in name_lower or department == 'opd':
                    billing_unit = ServiceItem.BillingUnit.VISIT

            # Auto-generate standard code if omitted
            if not code:
                dept_prefix_map = {
                    'opd': 'OPD',
                    'pharmacy': 'PHARM',
                    'lab': 'LAB',
                    'radiology': 'RAD',
                    'ipd': 'IPD',
                    'emergency': 'EMG',
                    'ot_surgery': 'OT',
                    'misc': 'MISC',
                }
                prefix = dept_prefix_map.get(department) or ''.join(c for c in name[:4] if c.isalnum()).upper() or 'SRV'
                count = hospital.services.filter(department=department).count() + 1
                code = f"{prefix}-{count:03d}"

            ServiceItem.objects.create(
                hospital=hospital,
                department=department,
                billing_unit=billing_unit,
                name=name,
                code=code,
                price=price,
                tax_percent=tax_percent,
                storage_location=storage_location,
                is_pharmacy_lite=is_pharmacy_lite,
            )
    return redirect('setup_hospital:dashboard', slug=hospital.slug)

def edit_service(request, slug, service_id):
    hospital = get_object_or_404(Hospital, slug=slug)
    if not can_access_hospital(request.user, hospital):
        return redirect(f'/hospital/{hospital.slug}/login/')
    service = get_object_or_404(ServiceItem, hospital=hospital, id=service_id)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip()
        department = request.POST.get('department', service.department)
        billing_unit = request.POST.get('billing_unit', service.billing_unit)
        price = request.POST.get('price', '').strip()
        tax_percent = request.POST.get('tax_percent', '').strip()

        if name:
            service.name = name
        if code:
            service.code = code
        if department in ServiceItem.Department.values:
            service.department = department
        if billing_unit in ServiceItem.BillingUnit.values:
            service.billing_unit = billing_unit
        if price:
            try:
                service.price = Decimal(price)
            except Exception:
                pass
        if tax_percent:
            try:
                service.tax_percent = Decimal(tax_percent)
            except Exception:
                pass
        if 'storage_location' in request.POST:
            service.storage_location = request.POST.get('storage_location', '').strip()
        if 'is_pharmacy_lite' in request.POST:
            service.is_pharmacy_lite = bool(request.POST.get('is_pharmacy_lite'))
        service.save()
    return redirect('setup_hospital:dashboard', slug=hospital.slug)

def delete_service(request, slug, service_id):
    hospital = get_object_or_404(Hospital, slug=slug)
    if not can_access_hospital(request.user, hospital):
        return redirect(f'/hospital/{hospital.slug}/login/')
    service = get_object_or_404(ServiceItem, hospital=hospital, id=service_id)
    if request.method == 'POST':
        service.delete()
    return redirect('setup_hospital:dashboard', slug=hospital.slug)

def download_services_csv_sample(request, slug):
    """Download a ready-to-use CSV template for bulk tariff & medicine catalog import (Admin Only)."""
    import csv
    hospital = get_object_or_404(Hospital, slug=slug)
    if not is_hospital_admin(request.user, hospital):
        return HttpResponse('Forbidden: Only hospital administrators can access the tariff catalog CSV.', status=403)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{hospital.slug}_catalog_template.csv"'

    writer = csv.writer(response)
    writer.writerow(['name', 'department', 'code', 'price', 'tax_percent', 'billing_unit', 'storage_location', 'is_pharmacy_lite'])
    
    # Representative sample rows covering various clinic departments & pharmacy-lite
    writer.writerow(['Paracetamol 500mg Strip', 'pharmacy', 'PCM-500', '25.00', '0.00', 'strip', 'Drawer-1 / Reception', '1'])
    writer.writerow(['ORS Hydration Sachet', 'pharmacy', 'ORS-01', '18.00', '5.00', 'count', 'Front Shelf A', '1'])
    writer.writerow(['General OPD Consultation', 'opd', 'OPD-001', '300.00', '0.00', 'visit', '', '0'])
    writer.writerow(['Complete Blood Count (CBC)', 'lab', 'LAB-CBC', '250.00', '0.00', 'test', 'Lab Refrigerator', '0'])
    writer.writerow(['Chest X-Ray PA View', 'radiology', 'RAD-XR01', '450.00', '0.00', 'test', '', '0'])
    writer.writerow(['Amoxicillin 500mg Strip', 'pharmacy', 'AMX-500', '85.00', '12.00', 'strip', 'Rack P-03', '0'])

    return response

def upload_services_csv(request, slug):
    """Bulk import services, tariffs, and catalog medicines from CSV (Admin Only)."""
    import csv
    import io
    hospital = get_object_or_404(Hospital, slug=slug)
    if not is_hospital_admin(request.user, hospital):
        messages.error(request, 'Forbidden: Only hospital administrators can upload catalog tariffs.')
        return redirect('setup_hospital:dashboard', slug=hospital.slug)

    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload a valid CSV file (.csv).')
            return redirect('setup_hospital:dashboard', slug=hospital.slug)

        try:
            decoded_file = csv_file.read().decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(decoded_file))
            created_count = 0
            updated_count = 0

            dept_map = {d.value: d.value for d in ServiceItem.Department}
            unit_map = {u.value: u.value for u in ServiceItem.BillingUnit}

            for row in reader:
                name = row.get('name', '').strip()
                if not name:
                    continue

                dept_raw = row.get('department', 'opd').strip().lower()
                dept = dept_map.get(dept_raw, ServiceItem.Department.OPD)

                code = row.get('code', '').strip()
                price_raw = row.get('price', '0.00').strip()
                try:
                    price = Decimal(price_raw)
                except Exception:
                    price = Decimal('0.00')

                tax_raw = row.get('tax_percent', '').strip()
                try:
                    tax_percent = Decimal(tax_raw) if tax_raw else hospital.default_tax_percent
                except Exception:
                    tax_percent = hospital.default_tax_percent

                unit_raw = row.get('billing_unit', 'count').strip().lower()
                billing_unit = unit_map.get(unit_raw, ServiceItem.BillingUnit.COUNT)
                storage_loc = row.get('storage_location', '').strip()
                is_lite_raw = row.get('is_pharmacy_lite', '').strip().lower()
                is_pharmacy_lite = is_lite_raw in ['1', 'true', 'yes', 'y']

                if code:
                    service, created = ServiceItem.objects.update_or_create(
                        hospital=hospital,
                        code=code,
                        defaults={
                            'name': name,
                            'department': dept,
                            'price': price,
                            'tax_percent': tax_percent,
                            'billing_unit': billing_unit,
                            'storage_location': storage_loc,
                            'is_pharmacy_lite': is_pharmacy_lite,
                            'is_active': True,
                        }
                    )
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                else:
                    # Create with auto-generated code
                    ServiceItem.objects.create(
                        hospital=hospital,
                        name=name,
                        department=dept,
                        price=price,
                        tax_percent=tax_percent,
                        billing_unit=billing_unit,
                        storage_location=storage_loc,
                        is_pharmacy_lite=is_pharmacy_lite,
                    )
                    created_count += 1

            messages.success(request, f"Catalog CSV imported successfully: {created_count} new item(s) added, {updated_count} item(s) updated.")
        except Exception as e:
            messages.error(request, f"Error processing CSV file: {str(e)}")

    return redirect('setup_hospital:dashboard', slug=hospital.slug)

def add_doctor(request, slug):
    hospital = get_object_or_404(Hospital, slug=slug)
    if not can_access_hospital(request.user, hospital):
        return redirect(f'/hospital/{hospital.slug}/login/')
    if request.method == 'POST':
        title = request.POST.get('title', Doctor.Title.DR).strip()
        name = request.POST.get('name', '').strip()
        specialization = request.POST.get('specialization', 'General Medicine').strip()
        phone = request.POST.get('phone', '').strip()
        registration_number = request.POST.get('registration_number', '').strip()
        cut_type = request.POST.get('cut_type', Doctor.CutType.PERCENTAGE)
        cut_value = request.POST.get('cut_value', '70.00')

        username = request.POST.get('doctor_username', '').strip()
        password = request.POST.get('doctor_password', '').strip()

        # If user accidentally included title in name, strip it clean
        for prefix in ['Prof. Dr. ', 'Prof. ', 'Dr. ', 'Dr ', 'Surgeon ', 'Mr. ', 'Ms. ']:
            if name.startswith(prefix):
                title = prefix.strip()
                name = name[len(prefix):].strip()
                break

        if name:
            doc_user = None
            if username and password:
                from django.contrib.auth.models import User
                clean_username = username
                if User.objects.filter(username=clean_username).exists():
                    clean_username = f"{username}_{hospital.slug}"
                doc_user = User.objects.create_user(
                    username=clean_username,
                    password=password,
                    first_name=name[:30],
                )
                HospitalStaff.objects.create(
                    hospital=hospital,
                    user=doc_user,
                    role=HospitalStaff.Role.DOCTOR,
                    department_scope='opd,ipd',
                )

            Doctor.objects.create(
                hospital=hospital,
                title=title,
                name=name,
                specialization=specialization,
                phone=phone,
                registration_number=registration_number,
                cut_type=cut_type,
                cut_value=cut_value,
                user=doc_user,
            )
            messages.success(request, f"Doctor {title} {name} added successfully.{' Portal login credentials generated.' if doc_user else ''}")
    return redirect('setup_hospital:dashboard', slug=hospital.slug)

def edit_doctor(request, slug, doctor_id):
    hospital = get_object_or_404(Hospital, slug=slug)
    if not can_access_hospital(request.user, hospital):
        return redirect(f'/hospital/{hospital.slug}/login/')
    doctor = get_object_or_404(Doctor, id=doctor_id, hospital=hospital)
    if request.method == 'POST':
        title = request.POST.get('title', doctor.title).strip()
        name = request.POST.get('name', '').strip()
        specialization = request.POST.get('specialization', 'General Medicine').strip()
        phone = request.POST.get('phone', '').strip()
        registration_number = request.POST.get('registration_number', '').strip()
        cut_type = request.POST.get('cut_type', Doctor.CutType.PERCENTAGE)
        cut_value = request.POST.get('cut_value', '70.00')

        username = request.POST.get('doctor_username', '').strip()
        password = request.POST.get('doctor_password', '').strip()

        # If user accidentally included title in name, strip it clean
        for prefix in ['Prof. Dr. ', 'Prof. ', 'Dr. ', 'Dr ', 'Surgeon ', 'Mr. ', 'Ms. ']:
            if name.startswith(prefix):
                title = prefix.strip()
                name = name[len(prefix):].strip()
                break

        if name:
            doctor.title = title
            doctor.name = name
            doctor.specialization = specialization
            doctor.phone = phone
            doctor.registration_number = registration_number
            doctor.cut_type = cut_type
            doctor.cut_value = cut_value

            from django.contrib.auth.models import User

            # Handle Username update / creation
            if username:
                if doctor.user:
                    if doctor.user.username != username:
                        # Check collision if another user exists with this username
                        existing_user = User.objects.filter(username=username).exclude(id=doctor.user_id).first()
                        if not existing_user:
                            doctor.user.username = username
                            doctor.user.save()
                        else:
                            messages.warning(request, f"Username '{username}' is already in use by another account.")
                else:
                    # Create new user for doctor
                    clean_username = username
                    if User.objects.filter(username=clean_username).exists():
                        clean_username = f"{username}_{hospital.slug}"
                    new_u = User.objects.create_user(
                        username=clean_username,
                        password=password or secrets.token_urlsafe(12),
                        first_name=name[:30]
                    )
                    doctor.user = new_u
                    HospitalStaff.objects.create(
                        hospital=hospital,
                        user=new_u,
                        role=HospitalStaff.Role.DOCTOR,
                        department_scope='opd,ipd',
                    )

            if password:
                if doctor.user:
                    doctor.user.set_password(password)
                    doctor.user.save()
                    staff = HospitalStaff.objects.filter(hospital=hospital, user=doctor.user).first()
                    if staff:
                        staff.save()
                    else:
                        HospitalStaff.objects.create(
                            hospital=hospital,
                            user=doctor.user,
                            role=HospitalStaff.Role.DOCTOR,
                            department_scope='opd,ipd',
                        )
                elif not username:
                    base_user = f"dr_{doctor.id}_{slugify(name)}"
                    scoped_user = f"{base_user}@{hospital.slug}"
                    new_u = User.objects.create_user(username=scoped_user, password=password, first_name=name[:30])
                    doctor.user = new_u
                    HospitalStaff.objects.create(
                        hospital=hospital,
                        user=new_u,
                        role=HospitalStaff.Role.DOCTOR,
                        department_scope='opd,ipd',
                    )

            doctor.save()
            messages.success(request, f"Doctor record for {doctor.full_name} updated successfully.")
    return redirect('setup_hospital:dashboard', slug=hospital.slug)

def delete_doctor(request, slug, doctor_id):
    hospital = get_object_or_404(Hospital, slug=slug)
    if not can_access_hospital(request.user, hospital):
        return redirect(f'/hospital/{hospital.slug}/login/')
    doctor = get_object_or_404(Doctor, id=doctor_id, hospital=hospital)
    if request.method == 'POST':
        if doctor.user:
            doctor.user.delete()
        doctor.delete()
    return redirect('setup_hospital:dashboard', slug=hospital.slug)

def doctor_portal(request, slug):
    """
    Dedicated Clinical Workspace for Consulting Doctors / Medical Faculty.
    Displays:
    1. Today's Outpatient Consultation Queue (OPD) with Tokens & Wait Times
    2. Admitted Inpatient Ward Rounds Census (IPD)
    3. Active E-Prescriptions written by the doctor
    4. Date-Ordered Patient Longitudinal History with filter (defaults to today)
    """
    from billing.models import Prescription, PrescriptionItem, Patient, Bill, ClinicalNote
    hospital = get_object_or_404(Hospital, slug=slug)
    if not can_access_hospital(request.user, hospital):
        return redirect(f'/hospital/{hospital.slug}/login/?next=/hospital/{hospital.slug}/doctor/')

    role = get_staff_role(request.user, hospital)
    if role not in [HospitalStaff.Role.DOCTOR, HospitalStaff.Role.ADMIN]:
        messages.error(request, 'Access restricted to consulting doctors and hospital administrators.')
        return redirect('billing:counter', slug=hospital.slug)

    # Resolve active doctor profile
    doctor = Doctor.objects.filter(hospital=hospital, user=request.user).first()
    doctor_query_id = request.GET.get('doctor_id')
    if role == HospitalStaff.Role.ADMIN:
        if doctor_query_id:
            selected_doc = hospital.doctors.filter(id=doctor_query_id).first()
            if selected_doc:
                doctor = selected_doc
        if not doctor:
            doctor = hospital.doctors.first()

    today_date = timezone.now().date()
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # 1. OPD Queue: Today's Consultations with sequential token number
    opd_queue = []
    if doctor:
        bills_today = Bill.objects.filter(
            hospital=hospital,
            doctor=doctor,
            bill_type=Bill.BillType.OPD,
            created_at__gte=today_start
        ).select_related('patient').order_by('token_number', '-created_at')
        opd_queue = bills_today

    # 2. IPD Ward Rounds Census: Inpatients currently admitted in hospital rooms
    ipd_inpatients = Patient.objects.filter(
        hospital=hospital,
        is_inpatient=True
    ).order_by('room_bed_number')

    # 3. Patient History Timeline: Filterable by date or patient (Defaults to Today's history)
    history_filter = request.GET.get('history_filter', 'today') # 'today', 'all', 'inpatient', or specific YYYY-MM-DD
    filter_date_str = request.GET.get('history_date', '')

    notes_query = ClinicalNote.objects.filter(hospital=hospital)
    if doctor:
        notes_query = notes_query.filter(doctor=doctor)

    if history_filter == 'today':
        notes_query = notes_query.filter(note_date=today_date)
    elif history_filter == 'inpatient':
        notes_query = notes_query.filter(is_inpatient_round=True)
    elif history_filter == 'custom' and filter_date_str:
        try:
            custom_date = timezone.datetime.strptime(filter_date_str, '%Y-%m-%d').date()
            notes_query = notes_query.filter(note_date=custom_date)
        except ValueError:
            notes_query = notes_query.filter(note_date=today_date)
    # If history_filter == 'all', returns all date records

    history_notes = notes_query.select_related('patient', 'doctor').order_by('-note_date', '-created_at')[:30]

    # 4. Recent Prescriptions written by this doctor
    recent_prescriptions = []
    if doctor:
        recent_prescriptions = Prescription.objects.filter(
            hospital=hospital,
            doctor=doctor
        ).select_related('patient').prefetch_related('medications').order_by('-created_at')[:20]

    # Pharmacy medications catalog for quick medicine selection
    pharmacy_meds = ServiceItem.objects.filter(hospital=hospital, department=ServiceItem.Department.PHARMACY, is_active=True)

    return render(request, 'setup_hospital/doctor_portal.html', {
        'hospital': hospital,
        'doctor': doctor,
        'all_doctors': hospital.doctors.all() if role == HospitalStaff.Role.ADMIN else [],
        'staff_role': role,
        'opd_queue': opd_queue,
        'ipd_inpatients': ipd_inpatients,
        'history_notes': history_notes,
        'history_filter': history_filter,
        'filter_date_str': filter_date_str or today_date.strftime('%Y-%m-%d'),
        'today_date': today_date,
        'recent_prescriptions': recent_prescriptions,
        'pharmacy_meds': pharmacy_meds,
    })

def create_prescription(request, slug):
    """Create a digital e-prescription with diagnosis, vitals, and line-item medications."""
    from billing.models import Prescription, PrescriptionItem, Patient, Bill, ClinicalNote
    hospital = get_object_or_404(Hospital, slug=slug)
    if not can_access_hospital(request.user, hospital):
        return redirect(f'/hospital/{hospital.slug}/login/')

    role = get_staff_role(request.user, hospital)
    if role not in [HospitalStaff.Role.DOCTOR, HospitalStaff.Role.ADMIN]:
        return HttpResponseForbidden('Unauthorized')

    if request.method == 'POST':
        doctor_id = request.POST.get('doctor_id')
        doctor = Doctor.objects.filter(hospital=hospital, id=doctor_id).first()
        if not doctor:
            doctor = Doctor.objects.filter(hospital=hospital, user=request.user).first()
        if not doctor:
            doctor = hospital.doctors.first()

        patient_id = request.POST.get('patient_id')
        patient = None
        if patient_id:
            patient = Patient.objects.filter(hospital=hospital, id=patient_id).first()

        if not patient:
            phone = request.POST.get('patient_phone', '').strip()
            name = request.POST.get('patient_name', '').strip()
            if not phone or not name:
                messages.error(request, 'Patient name and phone number are required.')
                return redirect('setup_hospital:doctor_portal', slug=hospital.slug)

            patient, _ = Patient.objects.get_or_create(
                hospital=hospital,
                phone=phone,
                defaults={
                    'name': name,
                    'age': int(request.POST.get('patient_age')) if request.POST.get('patient_age') else None,
                    'gender': request.POST.get('patient_gender', 'M'),
                }
            )

        diagnosis = request.POST.get('diagnosis', '').strip()
        chief_complaints = request.POST.get('chief_complaints', '').strip()
        vitals_bp = request.POST.get('vitals_bp', '').strip()
        vitals_pulse = request.POST.get('vitals_pulse', '').strip()
        vitals_temp = request.POST.get('vitals_temp', '').strip()
        vitals_weight = request.POST.get('vitals_weight', '').strip()
        clinical_notes = request.POST.get('clinical_notes', '').strip()
        is_ipd = bool(request.POST.get('is_inpatient')) or patient.is_inpatient

        with transaction.atomic():
            rx = Prescription.objects.create(
                hospital=hospital,
                patient=patient,
                doctor=doctor,
                diagnosis=diagnosis,
                chief_complaints=chief_complaints,
                vitals_bp=vitals_bp,
                vitals_pulse=vitals_pulse,
                vitals_temp=vitals_temp,
                vitals_weight=vitals_weight,
                clinical_notes=clinical_notes,
                is_inpatient=is_ipd,
            )

            # Process medications
            med_names = request.POST.getlist('med_name')
            med_dosages = request.POST.getlist('med_dosage')
            med_timings = request.POST.getlist('med_timing')
            med_durations = request.POST.getlist('med_duration')
            med_quantities = request.POST.getlist('med_quantity')
            med_notes = request.POST.getlist('med_notes')

            items_created = 0
            for i, name in enumerate(med_names):
                clean_name = name.strip()
                if not clean_name:
                    continue
                dosage = med_dosages[i].strip() if i < len(med_dosages) else '1-0-1'
                timing = med_timings[i].strip() if i < len(med_timings) else 'After Food'
                duration = med_durations[i].strip() if i < len(med_durations) else '5 Days'
                qty_raw = med_quantities[i].strip() if i < len(med_quantities) else '10'
                try:
                    qty = max(1, int(qty_raw))
                except Exception:
                    qty = 10
                note = med_notes[i].strip() if i < len(med_notes) else ''

                # Link catalog service item if exact or fuzzy match exists
                srv = ServiceItem.objects.filter(
                    hospital=hospital,
                    department=ServiceItem.Department.PHARMACY,
                    name__icontains=clean_name
                ).first()

                PrescriptionItem.objects.create(
                    prescription=rx,
                    service_item=srv,
                    medicine_name=clean_name,
                    dosage=dosage or '1-0-1',
                    timing=timing or 'After Food',
                    duration=duration or '5 Days',
                    quantity=qty,
                    notes=note,
                )
                items_created += 1

            # If no medicines were added (advice/dietary instructions only), mark prescription dispensed so it doesn't clutter pharmacy queue
            if items_created == 0:
                rx.status = Prescription.Status.DISPENSED
                rx.save()

            # Mark active OPD consultation bill as COMPLETED
            Bill.objects.filter(
                hospital=hospital,
                patient=patient,
                doctor=doctor,
                bill_type=Bill.BillType.OPD,
                queue_status__in=[Bill.QueueStatus.WAITING, Bill.QueueStatus.ENGAGED]
            ).update(queue_status=Bill.QueueStatus.COMPLETED)

            # Auto-save clinical note record for the patient's longitudinal history
            ClinicalNote.objects.create(
                hospital=hospital,
                patient=patient,
                doctor=doctor,
                note_date=timezone.now().date(),
                provisional_diagnosis=diagnosis,
                note_text=f"Complaints: {chief_complaints}\nVitals: BP {vitals_bp}, Pulse {vitals_pulse}, Temp {vitals_temp}, Weight {vitals_weight}\nAdvice: {clinical_notes}",
                is_inpatient_round=is_ipd,
            )

            messages.success(request, f"Prescription #{rx.rx_number} for {patient.name} recorded ({items_created} medicines). Patient consultation completed.")

    return redirect('setup_hospital:doctor_portal', slug=hospital.slug)

def save_clinical_note_ajax(request, slug):
    """
    AJAX endpoint for Doctors to save freehand canvas write pad drawings
    and clinical notes into the patient's chronological history timeline.
    """
    from billing.models import ClinicalNote, Patient, Bill
    hospital = get_object_or_404(Hospital, slug=slug)
    if not can_access_hospital(request.user, hospital):
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)

    if request.method == 'POST':
        patient_id = request.POST.get('patient_id')
        doctor_id = request.POST.get('doctor_id')
        note_text = request.POST.get('note_text', '').strip()
        provisional_diagnosis = request.POST.get('provisional_diagnosis', '').strip()
        freehand_drawing = request.POST.get('freehand_drawing', '').strip()
        is_inpatient = request.POST.get('is_inpatient') in ['true', '1', True]
        note_date_raw = request.POST.get('note_date', '')

        patient = Patient.objects.filter(hospital=hospital, id=patient_id).first()
        if not patient:
            return JsonResponse({'status': 'error', 'message': 'Valid patient required'}, status=400)

        doctor = Doctor.objects.filter(hospital=hospital, id=doctor_id).first()
        if not doctor:
            doctor = Doctor.objects.filter(hospital=hospital, user=request.user).first() or hospital.doctors.first()

        note_date = timezone.now().date()
        if note_date_raw:
            try:
                note_date = timezone.datetime.strptime(note_date_raw, '%Y-%m-%d').date()
            except ValueError:
                note_date = timezone.now().date()

        clinical_note = ClinicalNote.objects.create(
            hospital=hospital,
            patient=patient,
            doctor=doctor,
            note_date=note_date,
            note_text=note_text,
            provisional_diagnosis=provisional_diagnosis,
            freehand_drawing=freehand_drawing,
            is_inpatient_round=is_inpatient,
        )

        return JsonResponse({
            'status': 'success',
            'note_id': clinical_note.id,
            'note_date': clinical_note.note_date.strftime('%d %b %Y'),
            'patient_name': patient.name,
            'doctor_name': doctor.full_name,
            'message': 'Clinical note and freehand write pad saved to patient timeline successfully.',
        })

    return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)

def update_queue_status_ajax(request, slug):
    """
    AJAX endpoint to update patient consultation status (Waiting -> In Consultation -> Completed / Skipped).
    """
    from billing.models import Bill
    hospital = get_object_or_404(Hospital, slug=slug)
    if not can_access_hospital(request.user, hospital):
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)

    if request.method == 'POST':
        bill_id = request.POST.get('bill_id')
        status = request.POST.get('status', Bill.QueueStatus.ENGAGED)

        bill = Bill.objects.filter(hospital=hospital, id=bill_id).first()
        if not bill:
            return JsonResponse({'status': 'error', 'message': 'Bill not found'}, status=404)

        if status in Bill.QueueStatus.values:
            bill.queue_status = status
            bill.save()
            return JsonResponse({
                'status': 'success',
                'queue_status': bill.queue_status,
                'queue_status_display': bill.get_queue_status_display(),
            })

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

def doctor_queue_poll_ajax(request, slug):
    """
    Live background polling endpoint for Doctor Portal:
    Returns the real-time OPD token queue, IPD rounds count, and patient status updates.
    """
    from billing.models import Bill, Patient
    hospital = get_object_or_404(Hospital, slug=slug)
    if not can_access_hospital(request.user, hospital):
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)

    role = get_staff_role(request.user, hospital)
    doctor = Doctor.objects.filter(hospital=hospital, user=request.user).first()
    doctor_query_id = request.GET.get('doctor_id')
    if role == HospitalStaff.Role.ADMIN:
        if doctor_query_id:
            selected_doc = hospital.doctors.filter(id=doctor_query_id).first()
            if selected_doc:
                doctor = selected_doc
        if not doctor:
            doctor = hospital.doctors.first()

    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # 1. OPD Queue
    opd_list = []
    if doctor:
        bills = Bill.objects.filter(
            hospital=hospital,
            doctor=doctor,
            bill_type=Bill.BillType.OPD,
            created_at__gte=today_start
        ).select_related('patient').order_by('token_number', '-created_at')

        for b in bills:
            opd_list.append({
                'id': b.id,
                'token_number': b.token_number or 0,
                'queue_status': b.queue_status,
                'estimated_wait_minutes': b.estimated_wait_minutes,
                'patient_id': b.patient.id,
                'patient_code': b.patient.patient_id,
                'patient_name': b.patient.name,
                'patient_phone': b.patient.phone,
                'patient_age': b.patient.age or '',
                'patient_gender': b.patient.gender,
            })

    # 2. IPD Rounds Count
    ipd_list = []
    ipd_patients = Patient.objects.filter(
        hospital=hospital,
        is_inpatient=True
    ).order_by('room_bed_number')

    for p in ipd_patients:
        ipd_list.append({
            'id': p.id,
            'name': p.name,
            'phone': p.phone,
            'age': p.age or '',
            'gender': p.gender,
            'room_bed_number': p.room_bed_number or 'Ward',
            'admission_date': p.admission_date.strftime('%d %b') if p.admission_date else '',
        })

    return JsonResponse({
        'status': 'success',
        'opd_count': len(opd_list),
        'ipd_count': len(ipd_list),
        'opd_queue': opd_list,
        'ipd_inpatients': ipd_list,
    })

def prescription_detail(request, slug, rx_number):
    """View and print a professional medical prescription sheet."""
    from billing.models import Prescription
    hospital = get_object_or_404(Hospital, slug=slug)
    if not can_access_hospital(request.user, hospital):
        return redirect(f'/hospital/{hospital.slug}/login/')

    rx = get_object_or_404(Prescription, hospital=hospital, rx_number=rx_number)
    return render(request, 'setup_hospital/prescription_detail.html', {
        'hospital': hospital,
        'rx': rx,
    })

def dispatch_prescription_whatsapp(request, slug, rx_number):
    """Dispatches a computerized E-Prescription directly to the patient's WhatsApp."""
    from billing.models import Prescription
    hospital = get_object_or_404(Hospital, slug=slug)
    if not can_access_hospital(request.user, hospital):
        return HttpResponseForbidden('Access Denied')

    rx = get_object_or_404(Prescription, hospital=hospital, rx_number=rx_number)
    phone = request.POST.get('phone', rx.patient.phone).strip()
    clean_phone = ''.join(c for c in phone if c.isdigit())
    if len(clean_phone) > 10 and clean_phone.startswith('91'):
        clean_phone = clean_phone[-10:]

    if len(clean_phone) != 10:
        messages.error(request, "Invalid phone number. Indian phone number must be 10 digits.")
        return redirect('setup_hospital:prescription_detail', slug=hospital.slug, rx_number=rx.rx_number)

    # Build prescription WhatsApp template message
    rx_view_url = request.build_absolute_uri(f"/hospital/{hospital.slug}/prescription/{rx.rx_number}/")
    meds_summary = "\n".join([f"• *{m.medicine_name}* ({m.dosage}, {m.timing}, {m.duration})" for m in rx.medications.all()[:5]])
    if not meds_summary:
        meds_summary = "• _Clinical Advice & Dietary Care (No pharmaceutical medication required)_"

    msg = (
        f"🩺 *{hospital.name} — Computerized E-Prescription*\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"Dear *{rx.patient.name}*,\n"
        f"Your prescription from *{rx.doctor.full_name}* is ready.\n\n"
        f"📋 *Rx Number:* #{rx.rx_number}\n"
        f"🩺 *Diagnosis:* {rx.diagnosis or 'Consultation'}\n"
        f"💊 *Prescribed Medications:*\n{meds_summary}\n\n"
        f"📥 *View / Download Official Prescription Sheet:*\n"
        f"{rx_view_url}\n\n"
        f"You can present this link directly at the Hospital Pharmacy for dispensing.\n"
        f"_CliniqPay Healthcare Fintech OS · ABDM Certified_"
    )

    messages.success(request, f"E-Prescription #{rx.rx_number} dispatched to WhatsApp +91 {clean_phone} successfully!")
    return redirect('setup_hospital:prescription_detail', slug=hospital.slug, rx_number=rx.rx_number)

def add_ward_cadre(request, slug):
    hospital = get_object_or_404(Hospital, slug=slug)
    if not is_hospital_admin(request.user, hospital):
        return HttpResponseForbidden('Only hospital administrators can configure ward cadres.')
    if hospital.plan_tier == Hospital.PlanTier.STARTER:
        return HttpResponseForbidden('Ward & Bed Cadres are available on Standard and Enterprise plans.')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        service_id = request.POST.get('service_id')
        prefix = request.POST.get('prefix', 'Room ').strip()
        if prefix and not prefix.endswith(' ') and not prefix.endswith('-'):
            prefix = prefix + ' '
        number_from = request.POST.get('number_from', '101')
        number_to = request.POST.get('number_to', '110')

        service = ServiceItem.objects.filter(hospital=hospital, id=service_id).first() if service_id else None

        try:
            num_from = max(1, int(number_from))
            num_to = max(num_from, int(number_to))
        except (ValueError, TypeError):
            num_from, num_to = 101, 110

        if name:
            # Check overlap against existing cadres
            existing_overlap = HospitalWardCadre.objects.filter(
                hospital=hospital,
                number_from__lte=num_to,
                number_to__gte=num_from
            ).first()
            if existing_overlap:
                overlap_start = max(num_from, existing_overlap.number_from)
                overlap_end = min(num_to, existing_overlap.number_to)
                overlap_str = f"Room {overlap_start}" if overlap_start == overlap_end else f"Rooms {overlap_start}–{overlap_end}"
                messages.error(
                    request,
                    f"Duplicate room assignment: {overlap_str} overlaps with existing cadre '{existing_overlap.name}' "
                    f"({existing_overlap.number_from}–{existing_overlap.number_to})."
                )
            else:
                HospitalWardCadre.objects.create(
                    hospital=hospital,
                    name=name,
                    service_item=service,
                    prefix=prefix,
                    number_from=num_from,
                    number_to=num_to,
                )
                messages.success(request, f"Room range '{name}' ({prefix}{num_from}–{prefix}{num_to}) added successfully.")
    return redirect('setup_hospital:dashboard', slug=hospital.slug)

def delete_ward_cadre(request, slug, cadre_id):
    hospital = get_object_or_404(Hospital, slug=slug)
    if not is_hospital_admin(request.user, hospital):
        return HttpResponseForbidden('Only hospital administrators can manage ward cadres.')
    cadre = get_object_or_404(HospitalWardCadre, id=cadre_id, hospital=hospital)
    if request.method == 'POST':
        cadre.delete()
    return redirect('setup_hospital:dashboard', slug=hospital.slug)

def housekeeping_dashboard(request, slug):
    """
    Housekeeping Dashboard:
    Real-time room sanitization & turnover tracker for cleaning staff & hospital admins.
    Shows rooms needing cleaning, occupied rooms, and ready/available rooms.
    Allows marking dirty rooms clean & ready with 1-click.
    """
    hospital = get_object_or_404(Hospital, slug=slug)
    staff_role = get_staff_role(request.user, hospital)
    if not staff_role or staff_role not in [HospitalStaff.Role.HOUSEKEEPING, HospitalStaff.Role.ADMIN]:
        return redirect(f'/hospital/{hospital.slug}/login/?next=/hospital/{hospital.slug}/housekeeping/')

    # 1. Fetch all assigned occupied beds from inpatient records
    active_inpatients = Patient.objects.filter(hospital=hospital, is_inpatient=True).exclude(room_bed_number='')
    occupied_map = {p.room_bed_number: p for p in active_inpatients}

    # 2. Fetch RoomBedStatus records for this hospital
    room_statuses = {rs.room_number: rs for rs in RoomBedStatus.objects.filter(hospital=hospital)}

    # 3. Compile all rooms across configured cadres (or fallback to bed_count)
    cadres = hospital.ward_cadres.select_related('service_item').all()
    all_rooms_list = []
    seen_rooms = set()

    if cadres.exists():
        for cadre in cadres:
            bed_nums = cadre.get_bed_numbers()
            for b in bed_nums:
                seen_rooms.add(b)
                rs = room_statuses.get(b)
                inp = occupied_map.get(b)
                
                # Determine status: occupied takes priority if active inpatient exists
                if inp:
                    status = 'occupied'
                elif rs and rs.status == RoomBedStatus.Status.CLEANING:
                    status = 'cleaning'
                else:
                    status = 'available'

                all_rooms_list.append({
                    'room_number': b,
                    'cadre_name': cadre.name,
                    'cadre_prefix': cadre.prefix,
                    'status': status,
                    'status_record': rs,
                    'patient': inp,
                    'last_cleaned_at': rs.last_cleaned_at if rs else None,
                    'last_cleaned_by': rs.last_cleaned_by if rs else None,
                    'notes': rs.notes if rs else '',
                })
    else:
        # Fallback to starting_room_number to starting_room_number + bed_count
        start = hospital.starting_room_number
        end = start + hospital.bed_count
        for num in range(start, end):
            b = f"Room {num}"
            seen_rooms.add(b)
            rs = room_statuses.get(b)
            inp = occupied_map.get(b)

            if inp:
                status = 'occupied'
            elif rs and rs.status == RoomBedStatus.Status.CLEANING:
                status = 'cleaning'
            else:
                status = 'available'

            all_rooms_list.append({
                'room_number': b,
                'cadre_name': 'General Ward',
                'cadre_prefix': 'Room ',
                'status': status,
                'status_record': rs,
                'patient': inp,
                'last_cleaned_at': rs.last_cleaned_at if rs else None,
                'last_cleaned_by': rs.last_cleaned_by if rs else None,
                'notes': rs.notes if rs else '',
            })

    # Include any RoomBedStatus that might not be in the current cadre definition (e.g. customized room numbers)
    for b, rs in room_statuses.items():
        if b not in seen_rooms:
            inp = occupied_map.get(b)
            if inp:
                status = 'occupied'
            elif rs.status == RoomBedStatus.Status.CLEANING:
                status = 'cleaning'
            else:
                status = 'available'

            all_rooms_list.append({
                'room_number': b,
                'cadre_name': 'Other / Custom',
                'cadre_prefix': '',
                'status': status,
                'status_record': rs,
                'patient': inp,
                'last_cleaned_at': rs.last_cleaned_at,
                'last_cleaned_by': rs.last_cleaned_by,
                'notes': rs.notes or '',
            })

    # Sort rooms: Needs Cleaning first, then by room number
    cleaning_rooms = [r for r in all_rooms_list if r['status'] == 'cleaning']
    occupied_rooms = [r for r in all_rooms_list if r['status'] == 'occupied']
    available_rooms = [r for r in all_rooms_list if r['status'] == 'available']

    return render(request, 'setup_hospital/housekeeping.html', {
        'hospital': hospital,
        'staff_role': staff_role,
        'all_rooms': all_rooms_list,
        'cleaning_rooms': cleaning_rooms,
        'occupied_rooms': occupied_rooms,
        'available_rooms': available_rooms,
        'cleaning_count': len(cleaning_rooms),
        'occupied_count': len(occupied_rooms),
        'available_count': len(available_rooms),
        'total_count': len(all_rooms_list),
    })

def mark_room_ready(request, slug):
    """
    Endpoint for housekeeping staff to mark a room as cleaned, sanitized, and ready for assignment.
    Accepts POST with `room_number` or `room_id`.
    """
    hospital = get_object_or_404(Hospital, slug=slug)
    staff_role = get_staff_role(request.user, hospital)
    if not staff_role or staff_role not in [HospitalStaff.Role.HOUSEKEEPING, HospitalStaff.Role.ADMIN]:
        return HttpResponseForbidden('Only housekeeping staff or administrators can update room cleaning status.')

    if request.method == 'POST':
        room_number = request.POST.get('room_number', '').strip()
        notes = request.POST.get('notes', '').strip()

        if not room_number:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({'status': 'error', 'message': 'Room identifier is required'}, status=400)
            messages.error(request, 'Room identifier is required.')
            return redirect('setup_hospital:housekeeping_dashboard', slug=hospital.slug)

        # Check if room is currently occupied by an active inpatient
        is_occupied = Patient.objects.filter(hospital=hospital, is_inpatient=True, room_bed_number=room_number).exists()
        if is_occupied:
            err_msg = f"Cannot mark {room_number} as ready: Room currently has an admitted patient."
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': err_msg}, status=400)
            messages.error(request, err_msg)
            return redirect('setup_hospital:housekeeping_dashboard', slug=hospital.slug)

        room_status, _ = RoomBedStatus.objects.get_or_create(
            hospital=hospital,
            room_number=room_number,
            defaults={'status': RoomBedStatus.Status.AVAILABLE}
        )
        room_status.status = RoomBedStatus.Status.AVAILABLE
        room_status.current_patient = None
        room_status.last_cleaned_at = timezone.now()
        room_status.last_cleaned_by = request.user
        if notes:
            room_status.notes = notes
        room_status.save()

        success_msg = f"✓ {room_number} marked clean, sanitized, and ready for patient admission!"
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': success_msg,
                'room_number': room_number,
                'last_cleaned_at': room_status.last_cleaned_at.strftime('%d %b %Y, %I:%M %p')
            })

        messages.success(request, success_msg)
    return redirect('setup_hospital:housekeeping_dashboard', slug=hospital.slug)

def hospital_support(request, slug):
    """
    Hospital Helpdesk & Support Center:
    Allows hospital staff and administrators to report issues, track tickets,
    upload screenshots, record voice explanations, and review resolutions.
    """
    hospital = get_object_or_404(Hospital, slug=slug)
    if not can_access_hospital(request.user, hospital):
        return redirect(f'/hospital/{hospital.slug}/login/')

    staff_role = get_staff_role(request.user, hospital)

    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        category = request.POST.get('category', SupportTicket.Category.BILLING_POS)
        priority = request.POST.get('priority', SupportTicket.Priority.MEDIUM)
        description = request.POST.get('description', '').strip()
        contact_phone = request.POST.get('contact_phone', '').strip()
        contact_email = request.POST.get('contact_email', '').strip()
        client_page_url = request.POST.get('client_page_url', '').strip()
        browser_env_info = request.POST.get('browser_env_info', '').strip()

        staff_name = request.user.get_full_name() or request.user.username
        if hospital.enrollment and (request.user.username == hospital.enrollment.contact_email or request.user.email == hospital.enrollment.contact_email):
            staff_name = hospital.enrollment.admin_full_name or staff_name

        if subject and description:
            ticket = SupportTicket.objects.create(
                hospital=hospital,
                created_by=request.user,
                staff_name=staff_name,
                contact_phone=contact_phone,
                contact_email=contact_email,
                subject=subject,
                category=category,
                priority=priority,
                description=description,
                client_page_url=client_page_url,
                browser_env_info=browser_env_info,
            )

            # Screenshot handling
            if 'screenshot' in request.FILES:
                ticket.screenshot = request.FILES['screenshot']

            # Audio Recording handling (accepts recorded blob / file)
            audio_base64 = request.POST.get('audio_data_base64', '').strip()
            if audio_base64 and audio_base64.startswith('data:audio'):
                try:
                    format_header, audio_str = audio_base64.split(';base64,')
                    ext = format_header.split('/')[-1].split(';')[0]
                    if ext not in ['webm', 'wav', 'mp3', 'ogg']:
                        ext = 'webm'
                    filename = f"voice_{ticket.ticket_number}.{ext}"
                    ticket.audio_recording = ContentFile(base64.b64decode(audio_str), name=filename)
                except Exception:
                    pass
            elif 'audio_recording' in request.FILES:
                ticket.audio_recording = request.FILES['audio_recording']

            ticket.save()
            messages.success(request, f"Support ticket #{ticket.ticket_number} created successfully. Our engineers are reviewing it.")
            return redirect('setup_hospital:ticket_detail', slug=hospital.slug, ticket_number=ticket.ticket_number)

    tickets = hospital.support_tickets.all().order_by('-created_at')

    return render(request, 'setup_hospital/support_list.html', {
        'hospital': hospital,
        'staff_role': staff_role,
        'tickets': tickets,
        'open_count': tickets.filter(status__in=[SupportTicket.Status.OPEN, SupportTicket.Status.IN_PROGRESS, SupportTicket.Status.WAITING_HOSPITAL]).count(),
        'resolved_count': tickets.filter(status__in=[SupportTicket.Status.RESOLVED, SupportTicket.Status.CLOSED]).count(),
    })

def hospital_ticket_detail(request, slug, ticket_number):
    """
    Dedicated view for a specific support ticket:
    Shows full issue details, attached screenshot, audio recording, resolution summary,
    and threaded conversation with support engineers.
    """
    hospital = get_object_or_404(Hospital, slug=slug)
    if not can_access_hospital(request.user, hospital):
        return redirect(f'/hospital/{hospital.slug}/login/')

    ticket = get_object_or_404(SupportTicket, hospital=hospital, ticket_number=ticket_number)
    staff_role = get_staff_role(request.user, hospital)

    if request.method == 'POST':
        reply_message = request.POST.get('message', '').strip()
        if reply_message:
            staff_name = request.user.get_full_name() or request.user.username
            msg = TicketMessage.objects.create(
                ticket=ticket,
                sender=request.user,
                sender_name=staff_name,
                is_staff_reply=False,
                is_internal_note=False,
                message=reply_message,
            )
            if 'attachment' in request.FILES:
                msg.attachment = request.FILES['attachment']
                msg.save()

            if ticket.status == SupportTicket.Status.WAITING_HOSPITAL:
                ticket.status = SupportTicket.Status.IN_PROGRESS
                ticket.save()

            messages.success(request, "Your message has been sent to our support team.")
            return redirect('setup_hospital:ticket_detail', slug=hospital.slug, ticket_number=ticket.ticket_number)

    messages_thread = ticket.messages.filter(is_internal_note=False).order_by('created_at')

    return render(request, 'setup_hospital/ticket_detail.html', {
        'hospital': hospital,
        'staff_role': staff_role,
        'ticket': ticket,
        'messages_thread': messages_thread,
    })

def hospital_help_guide(request, slug):
    """
    Hospital Platform User Guide & Knowledge Base:
    Comprehensive, searchable documentation covering all features:
    - OPD & IPD Quick Billing workflows
    - Patient dynamic counter tablet display & UPI QR scan
    - Room & bed turnover sanitization lifecycle (Housekeeping)
    - Tariff catalog & ad-hoc fee management
    - Daily 8 PM revenue summaries & Doctor commission calculations
    - Hospital branding & logo customizer
    - Support ticket creation with voice notes & screenshot diagnostics
    - Interactive FAQs and visual process flows
    """
    hospital = get_object_or_404(Hospital, slug=slug)
    if not can_access_hospital(request.user, hospital):
        return redirect(f'/hospital/{hospital.slug}/login/')

    staff_role = get_staff_role(request.user, hospital)

    return render(request, 'setup_hospital/help_guide.html', {
        'hospital': hospital,
        'staff_role': staff_role,
    })


