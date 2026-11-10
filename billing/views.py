import json
from decimal import Decimal
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from setup_hospital.models import Hospital, Doctor, ServiceItem, HospitalStaff, RoomBedStatus
from setup_hospital.views import can_access_hospital, get_staff_role
from billing.models import Patient, Bill, BillItem, MedicineBatch

def search_patients_api(request, slug):
    """API for instant real-time patient search by Name, Phone, or Patient ID."""
    hospital = get_object_or_404(Hospital, slug=slug)
    if not can_access_hospital(request.user, hospital):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    query = request.GET.get('q', '').strip()
    if not query or len(query) < 2:
        return JsonResponse({'patients': []})

    patients = Patient.objects.filter(
        hospital=hospital
    ).filter(
        Q(name__icontains=query) |
        Q(phone__icontains=query) |
        Q(patient_id__icontains=query)
    ).order_by('-created_at')[:8]

    data = []
    for p in patients:
        last_bill = p.bills.filter(hospital=hospital).order_by('-created_at').first()
        data.append({
            'id': p.id,
            'patient_id': p.patient_id or '',
            'name': p.name,
            'phone': p.phone,
            'age': p.age or '',
            'gender': p.gender or 'M',
            'is_inpatient': p.is_inpatient,
            'room_bed_number': p.room_bed_number or '',
            'admission_date': p.admission_date.strftime('%d %b %Y, %I:%M %p') if p.admission_date else '',
            'last_bill_amount': str(last_bill.total_amount) if last_bill else '',
            'last_bill_number': last_bill.bill_number if last_bill else '',
            'last_bill_time': last_bill.created_at.strftime('%d %b, %I:%M %p') if last_bill else '',
        })
    return JsonResponse({'patients': data})

def save_patient_ajax(request, slug):
    """Saves or updates a patient without requiring billing items."""
    hospital = get_object_or_404(Hospital, slug=slug)
    if not can_access_hospital(request.user, hospital):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    if request.method == 'POST':
        patient_name = request.POST.get('patient_name', '').strip()
        patient_phone = request.POST.get('patient_phone', '').strip()
        patient_age = request.POST.get('patient_age') or None
        patient_gender = request.POST.get('patient_gender', 'M')
        is_inpatient = request.POST.get('is_inpatient') == '1'
        room_bed = request.POST.get('room_bed_number', '').strip()

        if not patient_name or not patient_phone:
            return JsonResponse({'error': 'Patient name and 10-digit mobile number are required.'}, status=400)

        with transaction.atomic():
            patient, created = Patient.objects.get_or_create(
                hospital=hospital,
                phone=patient_phone,
                defaults={
                    'name': patient_name,
                    'age': int(patient_age) if patient_age else None,
                    'gender': patient_gender,
                }
            )

            if not created:
                patient.name = patient_name
                if patient_age:
                    patient.age = int(patient_age)
                patient.gender = patient_gender

            if hospital.plan_tier != Hospital.PlanTier.STARTER:
                old_room = patient.room_bed_number
                if is_inpatient:
                    patient.is_inpatient = True
                    if not patient.admission_date:
                        patient.admission_date = timezone.now()
                    if room_bed:
                        if old_room and old_room != room_bed:
                            # Old room goes to CLEANING
                            RoomBedStatus.objects.update_or_create(
                                hospital=hospital,
                                room_number=old_room,
                                defaults={
                                    'status': RoomBedStatus.Status.CLEANING,
                                    'current_patient': None,
                                    'notes': f"Marked for sanitization after transfer of {patient.name} to {room_bed}",
                                }
                            )
                        patient.room_bed_number = room_bed
                        # New room goes to OCCUPIED
                        RoomBedStatus.objects.update_or_create(
                            hospital=hospital,
                            room_number=room_bed,
                            defaults={
                                'status': RoomBedStatus.Status.OCCUPIED,
                                'current_patient': patient,
                            }
                        )
                elif request.POST.get('inpatient_action') == 'discharge':
                    patient.is_inpatient = False
                    patient.discharge_date = timezone.now()
                    if old_room:
                        RoomBedStatus.objects.update_or_create(
                            hospital=hospital,
                            room_number=old_room,
                            defaults={
                                'status': RoomBedStatus.Status.CLEANING,
                                'current_patient': None,
                                'notes': f"Marked for sanitization after discharge of {patient.name}",
                            }
                        )

            patient.save()

        return JsonResponse({
            'success': True,
            'created': created,
            'patient': {
                'id': patient.id,
                'patient_id': patient.patient_id or '',
                'name': patient.name,
                'phone': patient.phone,
                'age': patient.age or '',
                'gender': patient.gender,
                'is_inpatient': patient.is_inpatient,
                'room_bed_number': patient.room_bed_number or '',
                'admission_date': patient.admission_date.strftime('%d %b %Y, %I:%M %p') if patient.admission_date else '',
            }
        })

    return JsonResponse({'error': 'Method not allowed'}, status=405)

def patient_inpatient_summary_api(request, slug, patient_id):
    """API returning the running IPD summary and all bills for an inpatient."""
    hospital = get_object_or_404(Hospital, slug=slug)
    if not can_access_hospital(request.user, hospital):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    patient = get_object_or_404(Patient, hospital=hospital, id=patient_id)
    bills = patient.bills.filter(hospital=hospital).prefetch_related('items').order_by('-created_at')

    total_billed = bills.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    total_paid = bills.filter(status=Bill.Status.PAID).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    outstanding = total_billed - total_paid

    bills_data = [
        {
            'bill_number': b.bill_number,
            'created_at': b.created_at.strftime('%d %b %Y, %I:%M %p'),
            'date_iso': b.created_at.strftime('%Y-%m-%d'),
            'date_formatted': b.created_at.strftime('%d %b %Y'),
            'month_year': b.created_at.strftime('%B %Y'),
            'total_amount': str(b.total_amount),
            'status': b.status,
            'bill_type': b.bill_type,
            'room_bed_number': b.room_bed_number or '',
            'doctor_name': b.doctor.full_name if b.doctor else '',
            'receipt_url': f'/receipts/{hospital.slug}/receipt/{b.bill_number}/',
            'items_count': b.items.count(),
            'items': [
                {
                    'name': it.item_name,
                    'quantity': it.quantity,
                    'price': str(it.unit_price),
                    'total': str(it.total_price),
                }
                for it in b.items.all()
            ]
        }
        for b in bills
    ]

    return JsonResponse({
        'patient': {
            'id': patient.id,
            'name': patient.name,
            'phone': patient.phone,
            'patient_id': patient.patient_id or '',
            'is_inpatient': patient.is_inpatient,
            'room_bed_number': patient.room_bed_number or '',
            'admission_date': patient.admission_date.strftime('%d %b %Y, %I:%M %p') if patient.admission_date else '',
        },
        'summary': {
            'total_billed': str(total_billed),
            'total_paid': str(total_paid),
            'outstanding': str(outstanding),
        },
        'bills': bills_data,
    })

def discharge_patient(request, slug, patient_id):
    """
    Handles inpatient discharge:
    1. Checks if the patient has any unpaid bills or stay ledger charges.
    2. If there are unpaid bills, redirects to payment checkout for the pending bill.
    3. If there is no bill yet or new final discharge items are added, generates the final discharge invoice and redirects to checkout.
    4. Only confirms and completes the discharge (setting room to CLEANING and is_inpatient=False) once payment is collected.
    """
    hospital = get_object_or_404(Hospital, slug=slug)
    if not can_access_hospital(request.user, hospital):
        return redirect(f'/hospital/{hospital.slug}/login/')

    if request.method == 'POST':
        patient = get_object_or_404(Patient, hospital=hospital, id=patient_id)
        if not patient.is_inpatient:
            return redirect(f'/billing/{hospital.slug}/')

        # Check for existing unpaid bills for this inpatient
        unpaid_bill = patient.bills.filter(hospital=hospital, status=Bill.Status.UNPAID).order_by('-created_at').first()
        if unpaid_bill:
            # Mark bill as discharge bill so upon payment completion the patient is discharged
            if not unpaid_bill.is_discharge_bill:
                unpaid_bill.is_discharge_bill = True
                unpaid_bill.save()
            return redirect('payments:checkout', slug=hospital.slug, bill_number=unpaid_bill.bill_number)

        # If all previous bills are paid and total amount due is 0, discharge directly
        # Or if no bill exists, create final discharge bill
        total_billed = patient.bills.filter(hospital=hospital).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        total_paid = patient.bills.filter(hospital=hospital, status=Bill.Status.PAID).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        outstanding = total_billed - total_paid

        if outstanding <= Decimal('0.00') and patient.bills.filter(hospital=hospital).exists():
            # Already fully settled; confirm discharge immediately
            old_room = patient.room_bed_number
            patient.is_inpatient = False
            patient.discharge_date = timezone.now()
            patient.save()

            if old_room:
                RoomBedStatus.objects.update_or_create(
                    hospital=hospital,
                    room_number=old_room,
                    defaults={
                        'status': RoomBedStatus.Status.CLEANING,
                        'current_patient': None,
                        'notes': f"Marked for sanitization after discharge of {patient.name} on {timezone.now().strftime('%d %b %Y, %I:%M %p')}",
                    }
                )
            return redirect(f'/billing/{hospital.slug}/')
        else:
            # Need to generate a bill or collect outstanding amount
            # Create a final discharge bill for stay
            while Bill.objects.filter(hospital=hospital, bill_number=f"{hospital.bill_prefix}-{hospital.next_bill_number}").exists():
                hospital.next_bill_number += 1
            bill_serial = f"{hospital.bill_prefix}-{hospital.next_bill_number}"
            hospital.next_bill_number += 1
            hospital.save()

            billed_user_repr = request.user.get_full_name() or request.user.username
            bill = Bill.objects.create(
                hospital=hospital,
                patient=patient,
                doctor=patient.bills.filter(hospital=hospital, doctor__isnull=False).values_list('doctor', flat=True).first() and Doctor.objects.filter(id=patient.bills.filter(hospital=hospital, doctor__isnull=False).values_list('doctor', flat=True).first()).first(),
                bill_type=Bill.BillType.IPD,
                room_bed_number=patient.room_bed_number,
                bill_number=bill_serial,
                billed_by=billed_user_repr,
                is_discharge_bill=True,
            )

            # Look for bed service or IPD stay service to attach
            stay_service = hospital.services.filter(department='ipd', is_active=True).first() or hospital.services.filter(is_active=True).first()
            if stay_service:
                BillItem.objects.create(
                    bill=bill,
                    service=stay_service,
                    item_name=f"Inpatient Final Discharge & Stay Settlement ({patient.room_bed_number or 'Ward Bed'})",
                    billing_unit=stay_service.billing_unit,
                    quantity=1,
                    unit_price=stay_service.price,
                    tax_percent=stay_service.tax_percent,
                    total_price=stay_service.price,
                )
                bill.subtotal = stay_service.price
                bill.tax_amount = (stay_service.price * stay_service.tax_percent) / Decimal('100.00')
                bill.total_amount = bill.subtotal + bill.tax_amount
                bill.save()

            return redirect('payments:checkout', slug=hospital.slug, bill_number=bill.bill_number)

    return HttpResponse('Method not allowed', status=405)

def cashier_counter(request, slug):
    hospital = get_object_or_404(Hospital, slug=slug)
    if not can_access_hospital(request.user, hospital):
        return redirect(f'/hospital/{hospital.slug}/login/?next=/hospital/{hospital.slug}/billing/')

    staff = getattr(request.user, 'hospital_staff', None)
    if staff and staff.role == HospitalStaff.Role.HOUSEKEEPING:
        return redirect('setup_hospital:housekeeping_dashboard', slug=hospital.slug)
    elif staff and staff.role == HospitalStaff.Role.PHARMACIST:
        return redirect('billing:pharmacy_counter', slug=hospital.slug)

    services = hospital.services.filter(is_active=True)
    doctors = hospital.doctors.all()
    recent_bills = hospital.bills.order_by('-created_at')[:10]
    patients_history = hospital.patients.order_by('-created_at')[:15]
    for p in patients_history:
        p.last_bill = p.bills.filter(hospital=hospital).order_by('-created_at').first()
    next_serial = f"{hospital.bill_prefix}-{hospital.next_bill_number}"

    # Determine Biller display name and allowed department scopes
    staff_role = get_staff_role(request.user, hospital)
    biller_name = request.user.get_full_name() or request.user.username
    staff = request.user.hospital_staff if hasattr(request.user, 'hospital_staff') else None
    if hospital.enrollment and (request.user.username == hospital.enrollment.contact_email or request.user.email == hospital.enrollment.contact_email):
        biller_name = hospital.enrollment.admin_full_name or biller_name

    allowed_departments = ['all', 'opd', 'pharmacy', 'lab', 'radiology', 'ipd', 'emergency', 'ot_surgery', 'misc']
    if staff and staff.role in [HospitalStaff.Role.CASHIER, HospitalStaff.Role.FRONT_DESK]:
        allowed_departments = staff.get_scoped_departments_list()
        # Filter services if restricted to specific department counters
        if 'all' not in allowed_departments:
            services = services.filter(department__in=allowed_departments)

    # Distinct departments that actually exist in this hospital's active services
    available_departments = list(services.values_list('department', flat=True).distinct())

    # Build configured ward cadres with bed occupancy & cleaning status map
    ward_cadres = hospital.ward_cadres.select_related('service_item').all()
    occupied_beds = set(
        hospital.patients.filter(is_inpatient=True).exclude(room_bed_number__isnull=True).values_list('room_bed_number', flat=True)
    )
    cleaning_beds = set(
        RoomBedStatus.objects.filter(hospital=hospital, status=RoomBedStatus.Status.CLEANING).values_list('room_number', flat=True)
    )

    cadres_data = []
    for c in ward_cadres:
        beds_list = []
        for bed_num in c.get_bed_numbers():
            is_occ = bed_num in occupied_beds
            is_cln = (bed_num in cleaning_beds) and not is_occ
            beds_list.append({
                'number': bed_num,
                'is_occupied': is_occ,
                'is_cleaning': is_cln,
                'status': 'occupied' if is_occ else ('cleaning' if is_cln else 'available'),
            })
        cadres_data.append({
            'id': c.id,
            'name': c.name,
            'service_id': c.service_item_id or '',
            'service_name': c.service_item.name if c.service_item else '',
            'service_price': str(c.service_item.price) if c.service_item else '',
            'unit_short_label': c.service_item.unit_short_label if c.service_item else 'day',
            'beds': beds_list,
        })

    cadres_json = json.dumps(cadres_data)

    return render(request, 'billing/counter.html', {
        'hospital': hospital,
        'services': services,
        'doctors': doctors,
        'recent_bills': recent_bills,
        'patients_history': patients_history,
        'next_serial': next_serial,
        'biller_name': biller_name,
        'staff_role': staff_role,
        'allowed_departments': allowed_departments,
        'available_departments': available_departments,
        'cadres_data': cadres_data,
        'cadres_json': cadres_json,
        'ward_cadres': ward_cadres,
    })

def create_bill(request, slug):
    hospital = get_object_or_404(Hospital, slug=slug)
    if not can_access_hospital(request.user, hospital):
        return redirect(f'/hospital/{hospital.slug}/login/')

    if request.method == 'POST':
        patient_name = (request.POST.get('patient_name') or request.POST.get('name') or '').strip()
        patient_phone = (request.POST.get('patient_phone') or request.POST.get('phone') or '').strip()
        patient_age = request.POST.get('patient_age') or request.POST.get('age') or None
        patient_gender = request.POST.get('patient_gender') or request.POST.get('gender') or 'M'
        doctor_id = request.POST.get('doctor_id')
        service_ids = request.POST.getlist('services') or request.POST.getlist('service_ids')

        # Check for custom/ad-hoc miscellaneous item
        custom_item_name = request.POST.get('custom_item_name', '').strip()
        custom_item_price_raw = request.POST.get('custom_item_price', '').strip()
        custom_item_qty_raw = request.POST.get('custom_item_qty', '1').strip()
        custom_item_tax_raw = request.POST.get('custom_item_tax', '').strip()
        has_custom_item = bool(custom_item_name and custom_item_price_raw)

        if not patient_name or not patient_phone or (not service_ids and not has_custom_item):
            messages.error(request, 'Missing patient name, phone, or service selection. Please select at least one service or medication.')
            referrer = request.META.get('HTTP_REFERER')
            if referrer and 'pharmacy' in referrer:
                return redirect('billing:pharmacy_counter', slug=hospital.slug)
            return redirect('billing:counter', slug=hospital.slug)

        is_inpatient_checkbox = request.POST.get('is_inpatient') == '1'
        room_bed_val = request.POST.get('room_bed_number', '').strip()

        with transaction.atomic():
            # Patient record
            patient, _ = Patient.objects.get_or_create(
                hospital=hospital,
                phone=patient_phone,
                defaults={
                    'name': patient_name,
                    'age': int(patient_age) if patient_age else None,
                    'gender': patient_gender,
                }
            )

            # Update Inpatient Enrollment if hospital is Standard or Enterprise
            bill_type_val = Bill.BillType.OPD
            if hospital.plan_tier != Hospital.PlanTier.STARTER:
                old_room = patient.room_bed_number
                if is_inpatient_checkbox:
                    patient.is_inpatient = True
                    if not patient.admission_date:
                        patient.admission_date = timezone.now()
                    if room_bed_val:
                        if old_room and old_room != room_bed_val:
                            # Old room goes to CLEANING
                            RoomBedStatus.objects.update_or_create(
                                hospital=hospital,
                                room_number=old_room,
                                defaults={
                                    'status': RoomBedStatus.Status.CLEANING,
                                    'current_patient': None,
                                    'notes': f"Marked for sanitization after transfer of {patient.name} to {room_bed_val}",
                                }
                            )
                        patient.room_bed_number = room_bed_val
                        # New room goes to OCCUPIED
                        RoomBedStatus.objects.update_or_create(
                            hospital=hospital,
                            room_number=room_bed_val,
                            defaults={
                                'status': RoomBedStatus.Status.OCCUPIED,
                                'current_patient': patient,
                            }
                        )
                    patient.save()
                    bill_type_val = Bill.BillType.IPD
                elif patient.is_inpatient:
                    # Patient is already an active admitted inpatient
                    bill_type_val = Bill.BillType.IPD

            # Doctor & OPD Consultation Token Generation
            doctor = None
            token_num = None
            est_wait_min = 0

            if doctor_id:
                doctor = Doctor.objects.filter(hospital=hospital, id=doctor_id).first()

            # If this is an OPD bill with a consulting doctor, compute today's sequential queue token & wait time
            if bill_type_val == Bill.BillType.OPD and doctor:
                today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
                today_doctor_bills = Bill.objects.filter(
                    hospital=hospital,
                    doctor=doctor,
                    bill_type=Bill.BillType.OPD,
                    created_at__gte=today_start
                )
                existing_tokens_count = today_doctor_bills.count()
                token_num = existing_tokens_count + 1

                # Calculate estimated wait time: 10 mins per waiting patient ahead
                waiting_ahead_count = today_doctor_bills.filter(queue_status=Bill.QueueStatus.WAITING).count()
                est_wait_min = waiting_ahead_count * 10

            # Generate Next Auto Serial Number securely per hospital
            while Bill.objects.filter(hospital=hospital, bill_number=f"{hospital.bill_prefix}-{hospital.next_bill_number}").exists():
                hospital.next_bill_number += 1
            bill_serial = f"{hospital.bill_prefix}-{hospital.next_bill_number}"
            hospital.next_bill_number += 1
            hospital.save()

            is_discharge_bill_req = request.POST.get('is_discharge_bill') in ['true', '1', True]
            if is_discharge_bill_req and patient.is_inpatient:
                bill_type_val = Bill.BillType.IPD

            # Create Bill with cashier / admin identity
            billed_user_repr = request.user.get_full_name() or request.user.username
            bill = Bill.objects.create(
                hospital=hospital,
                patient=patient,
                doctor=doctor,
                bill_type=bill_type_val,
                room_bed_number=patient.room_bed_number if bill_type_val == Bill.BillType.IPD else None,
                bill_number=bill_serial,
                token_number=token_num,
                queue_status=Bill.QueueStatus.WAITING,
                estimated_wait_minutes=est_wait_min,
                billed_by=billed_user_repr,
                is_discharge_bill=is_discharge_bill_req,
            )

            subtotal = Decimal('0.00')
            tax_total = Decimal('0.00')
            consultation_fee = Decimal('0.00')

            for s_id in service_ids:
                service = ServiceItem.objects.filter(hospital=hospital, id=s_id).first()
                if service:
                    # Retrieve quantity or default to 1 (e.g. for hourly observation or units)
                    qty_param = request.POST.get(f'qty_{s_id}', '1').strip()
                    try:
                        quantity = max(1, int(qty_param))
                    except (ValueError, TypeError):
                        quantity = 1

                    line_subtotal = service.price * quantity
                    item_tax = (line_subtotal * service.tax_percent) / Decimal('100.00')
                    line_total = line_subtotal + item_tax

                    batch_val = request.POST.get(f'batch_{s_id}', '').strip()
                    expiry_val = request.POST.get(f'expiry_{s_id}', '').strip()

                    BillItem.objects.create(
                        bill=bill,
                        service=service,
                        item_name=service.name,
                        billing_unit=service.billing_unit,
                        quantity=quantity,
                        unit_price=service.price,
                        tax_percent=service.tax_percent,
                        total_price=line_total,
                        batch_number=batch_val if batch_val else None,
                        expiry_date=expiry_val if expiry_val else None,
                    )
                    subtotal += line_subtotal
                    tax_total += item_tax
                    if 'consultation' in service.name.lower():
                        consultation_fee += line_subtotal

            # Process custom / ad-hoc miscellaneous charge if entered
            if has_custom_item:
                try:
                    custom_price = Decimal(custom_item_price_raw)
                except Exception:
                    custom_price = Decimal('0.00')

                try:
                    custom_qty = max(1, int(custom_item_qty_raw))
                except Exception:
                    custom_qty = 1

                try:
                    custom_tax_pct = Decimal(custom_item_tax_raw) if custom_item_tax_raw else hospital.default_tax_percent
                except Exception:
                    custom_tax_pct = Decimal('0.00')

                custom_line_subtotal = custom_price * custom_qty
                custom_item_tax = (custom_line_subtotal * custom_tax_pct) / Decimal('100.00')
                custom_line_total = custom_line_subtotal + custom_item_tax

                custom_batch = request.POST.get('custom_batch_number', '').strip()
                custom_expiry = request.POST.get('custom_expiry_date', '').strip()

                BillItem.objects.create(
                    bill=bill,
                    service=None,
                    item_name=custom_item_name,
                    billing_unit='count',
                    quantity=custom_qty,
                    unit_price=custom_price,
                    tax_percent=custom_tax_pct,
                    total_price=custom_line_total,
                    batch_number=custom_batch if custom_batch else None,
                    expiry_date=custom_expiry if custom_expiry else None,
                )
                subtotal += custom_line_subtotal
                tax_total += custom_item_tax
                if 'consultation' in custom_item_name.lower():
                    consultation_fee += custom_line_subtotal

            bill.subtotal = subtotal
            bill.tax_amount = tax_total
            bill.total_amount = subtotal + tax_total

            # Calculate Doctor Share Cut
            if doctor and consultation_fee > Decimal('0.00'):
                if doctor.cut_type == Doctor.CutType.PERCENTAGE:
                    bill.doctor_share_amount = (consultation_fee * doctor.cut_value) / Decimal('100.00')
                else:
                    bill.doctor_share_amount = min(doctor.cut_value, consultation_fee)

            bill.save()

        return redirect('billing:detail', slug=hospital.slug, bill_number=bill.bill_number)

    return redirect('billing:counter', slug=hospital.slug)

def bill_detail(request, slug, bill_number):
    hospital = get_object_or_404(Hospital, slug=slug)
    bill = get_object_or_404(Bill, hospital=hospital, bill_number=bill_number)
    return render(request, 'billing/detail.html', {
        'hospital': hospital,
        'bill': bill,
    })

def pharmacy_counter(request, slug):
    """
    Dedicated Pharmacy Dispensing Terminal:
    Tailored specifically for Registered Pharmacists (Standard & Enterprise Plans)
    with medicine search, mandatory/standard Batch Number and Expiry Date tracking,
    referring doctor linkage, and live daily pharmacy dispensing ledger.
    """
    hospital = get_object_or_404(Hospital, slug=slug)
    if not can_access_hospital(request.user, hospital):
        return redirect(f'/hospital/{hospital.slug}/login/?next=/billing/{hospital.slug}/pharmacy/')

    # Check Plan Tier & Role permissions:
    staff_role = get_staff_role(request.user, hospital)
    if staff_role not in [HospitalStaff.Role.PHARMACIST, HospitalStaff.Role.ADMIN]:
        messages.error(request, "Access restricted to Registered Pharmacists and Hospital Administrators.")
        return redirect('billing:counter', slug=hospital.slug)

    if hospital.plan_tier == Hospital.PlanTier.STARTER:
        messages.warning(request, "Dedicated Pharmacy Terminal with Batch & Expiry tracking is available on Standard and Enterprise plans. Using Pharmacy-Lite.")
        return redirect('billing:counter', slug=hospital.slug)

    # Filter medications & pharmacy consumables with active batches and rack locations
    services = ServiceItem.objects.filter(hospital=hospital, department=ServiceItem.Department.PHARMACY).prefetch_related('batches')
    doctors = Doctor.objects.filter(hospital=hospital).order_by('name')
    batches = MedicineBatch.objects.filter(hospital=hospital, is_active=True).select_related('service_item')

    # Recent pharmacy bills (bills that contain pharmacy items or billed by pharmacist)
    recent_pharmacy_bills = Bill.objects.filter(
        hospital=hospital,
        items__service__department=ServiceItem.Department.PHARMACY
    ).distinct().order_by('-created_at')[:15]

    patients_history = Patient.objects.filter(hospital=hospital).order_by('-created_at')[:30]
    next_serial = f"{hospital.bill_prefix}-{hospital.next_bill_number}"
    biller_name = request.user.get_full_name() or request.user.username

    # Active Doctor Prescriptions awaiting pharmacy fulfillment
    from billing.models import Prescription
    import json
    active_prescriptions = Prescription.objects.filter(
        hospital=hospital,
        status=Prescription.Status.ACTIVE
    ).select_related('patient', 'doctor').prefetch_related('medications').order_by('-created_at')[:15]

    active_rx_data = []
    for rx in active_prescriptions:
        med_list = []
        for m in rx.medications.all():
            med_list.append({
                'medicine_name': m.medicine_name,
                'service_id': m.service_item_id or '',
                'quantity': m.quantity,
                'dosage': m.dosage,
                'timing': m.timing,
                'duration': m.duration,
            })
        active_rx_data.append({
            'id': rx.id,
            'rx_number': rx.rx_number,
            'patient_name': rx.patient.name,
            'patient_phone': rx.patient.phone,
            'patient_age': rx.patient.age or '',
            'patient_gender': rx.patient.gender or 'M',
            'doctor_id': rx.doctor_id or '',
            'doctor_name': rx.doctor.name if rx.doctor else '',
            'medications': med_list,
        })

    return render(request, 'billing/pharmacy_counter.html', {
        'hospital': hospital,
        'services': services,
        'batches': batches,
        'doctors': doctors,
        'recent_bills': recent_pharmacy_bills,
        'patients_history': patients_history,
        'active_prescriptions': active_prescriptions,
        'active_rx_json': json.dumps(active_rx_data),
        'next_serial': next_serial,
        'biller_name': biller_name,
        'staff_role': staff_role,
    })

def download_pharmacy_batch_csv_sample(request, slug):
    """Download a dedicated sample CSV template for bulk medicine inward batch inventory (Pharmacist & Admin only)."""
    import csv
    hospital = get_object_or_404(Hospital, slug=slug)
    if not can_access_hospital(request.user, hospital):
        return HttpResponse('Unauthorized', status=403)

    staff_role = get_staff_role(request.user, hospital)
    if staff_role not in [HospitalStaff.Role.PHARMACIST, HospitalStaff.Role.ADMIN]:
        return HttpResponse('Forbidden: Only registered pharmacists and hospital administrators can download the pharmacy batch template.', status=403)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{hospital.slug}_pharmacy_batches_template.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'item_name', 'item_code', 'batch_number', 'expiry_date', 'stock_quantity', 'rack_location', 'unit_price', 'tax_percent', 'billing_unit'
    ])
    
    # Practical sample pharmaceutical rows
    writer.writerow(['Augmentin 625 Duo Tablet', 'AUG-625', 'BT2026A', '11/27', '120', 'Rack A-02 / Shelf 1', '215.00', '12.00', 'strip'])
    writer.writerow(['Azithromycin 500mg Strip', 'AZI-500', 'AZ8901', '08/26', '60', 'Rack A-04 / Shelf 2', '120.00', '12.00', 'strip'])
    writer.writerow(['Pantoprazole 40mg (Pan-40)', 'PAN-40', 'PN7723', '03/28', '200', 'Rack B-01 / Shelf 3', '95.00', '12.00', 'strip'])
    writer.writerow(['Human Actrapid Insulin 100IU', 'INS-ACT', 'IN4402', '05/26', '35', 'Cold Storage Fridge #1 (2-8°C)', '480.00', '5.00', 'count'])
    writer.writerow(['Dolo 650mg Paracetamol', 'DOLO-650', 'DL9910', '10/27', '300', 'Front Shelf / Fast Move', '32.00', '0.00', 'strip'])

    return response

def upload_pharmacy_batch_csv(request, slug):
    """Bulk import medicine stock and inward batches from CSV into Pharmacy inventory (Pharmacist & Admin only)."""
    import csv
    import io
    hospital = get_object_or_404(Hospital, slug=slug)
    if not can_access_hospital(request.user, hospital):
        return redirect(f'/hospital/{hospital.slug}/login/')

    staff_role = get_staff_role(request.user, hospital)
    if staff_role not in [HospitalStaff.Role.PHARMACIST, HospitalStaff.Role.ADMIN]:
        messages.error(request, 'Forbidden: Only registered pharmacists and hospital administrators can perform bulk pharmacy inward uploads.')
        return redirect('billing:counter', slug=hospital.slug)

    if hospital.plan_tier == Hospital.PlanTier.STARTER:
        messages.warning(request, "Dedicated Batch Inventory is available on Standard and Enterprise plans.")
        return redirect('billing:counter', slug=hospital.slug)

    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload a valid CSV file (.csv).')
            return redirect('billing:pharmacy_counter', slug=hospital.slug)

        try:
            decoded_file = csv_file.read().decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(decoded_file))
            items_created = 0
            batches_created = 0
            batches_updated = 0

            unit_map = {u.value: u.value for u in ServiceItem.BillingUnit}

            for row in reader:
                item_name = row.get('item_name', '').strip()
                if not item_name:
                    continue

                item_code = row.get('item_code', '').strip()
                batch_number = row.get('batch_number', '').strip() or 'BATCH-01'
                expiry_date = row.get('expiry_date', '').strip() or '12/28'
                rack_location = row.get('rack_location', '').strip()

                price_raw = row.get('unit_price', '0.00').strip()
                try:
                    unit_price = Decimal(price_raw)
                except Exception:
                    unit_price = Decimal('0.00')

                tax_raw = row.get('tax_percent', '').strip()
                try:
                    tax_percent = Decimal(tax_raw) if tax_raw else Decimal('0.00')
                except Exception:
                    tax_percent = Decimal('0.00')

                stock_raw = row.get('stock_quantity', '0').strip()
                try:
                    stock_quantity = int(stock_raw)
                except Exception:
                    stock_quantity = 0

                unit_raw = row.get('billing_unit', 'strip').strip().lower()
                billing_unit = unit_map.get(unit_raw, ServiceItem.BillingUnit.STRIP)

                # Find or create corresponding ServiceItem in Pharmacy department
                service_item = None
                if item_code:
                    service_item = ServiceItem.objects.filter(hospital=hospital, code=item_code).first()

                if not service_item:
                    service_item = ServiceItem.objects.filter(
                        hospital=hospital,
                        name__iexact=item_name,
                        department=ServiceItem.Department.PHARMACY
                    ).first()

                if not service_item:
                    service_item = ServiceItem.objects.create(
                        hospital=hospital,
                        department=ServiceItem.Department.PHARMACY,
                        name=item_name,
                        code=item_code or f"MED-{hospital.services.filter(department=ServiceItem.Department.PHARMACY).count() + 1:03d}",
                        price=unit_price,
                        tax_percent=tax_percent,
                        billing_unit=billing_unit,
                        storage_location=rack_location,
                        is_pharmacy_lite=False,
                    )
                    items_created += 1
                else:
                    # Update rack location or price if updated in inward batch
                    if rack_location and not service_item.storage_location:
                        service_item.storage_location = rack_location
                    if unit_price and unit_price > 0:
                        service_item.price = unit_price
                    service_item.save()

                # Add / Update MedicineBatch
                batch, created = MedicineBatch.objects.update_or_create(
                    hospital=hospital,
                    service_item=service_item,
                    batch_number=batch_number,
                    defaults={
                        'expiry_date': expiry_date,
                        'stock_quantity': stock_quantity,
                        'rack_location': rack_location or service_item.storage_location,
                        'mrp': unit_price,
                        'is_active': True,
                    }
                )
                if created:
                    batches_created += 1
                else:
                    batches_updated += 1

            messages.success(
                request,
                f"Pharmacy Batch Inventory processed: {batches_created} inward batch(es) recorded, "
                f"{batches_updated} batch(es) updated ({items_created} new catalog item(s) created)."
            )
        except Exception as e:
            messages.error(request, f"Error processing batch CSV: {str(e)}")

    return redirect('billing:pharmacy_counter', slug=hospital.slug)
