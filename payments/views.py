import decimal
from decimal import Decimal
import urllib.parse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.http import HttpResponse, HttpResponseForbidden
from setup_hospital.models import Hospital, RoomBedStatus, ServiceItem
from setup_hospital.views import can_access_hospital
from billing.models import Bill
from payments.models import PaymentTransaction

def checkout(request, slug, bill_number):
    hospital = get_object_or_404(Hospital, slug=slug)
    if not can_access_hospital(request.user, hospital):
        return redirect(f'/hospital/{hospital.slug}/login/')

    bill = get_object_or_404(Bill, hospital=hospital, bill_number=bill_number)
    
    # Generate standard India UPI URI string
    upi_id = hospital.upi_id or 'cliniqpay@upi'
    pa = urllib.parse.quote(upi_id)
    pn = urllib.parse.quote(hospital.name)
    am = f"{bill.total_amount:.2f}"
    tr = bill.bill_number
    tn = urllib.parse.quote(f"Bill {bill.bill_number}")
    upi_uri = f"upi://pay?pa={pa}&pn={pn}&am={am}&tr={tr}&tn={tn}&cu=INR"

    # If hospital uses YouPI-PG gateway, create YouPI session
    youpi_session = None
    if hospital.upi_gateway_provider == Hospital.UpiGatewayProvider.YOUPI:
        gateway = YoupiPaymentGateway(hospital)
        youpi_session = gateway.create_checkout_session(bill)
        if youpi_session.get('upi_uri'):
            upi_uri = youpi_session['upi_uri']
        if youpi_session.get('qr_code_url'):
            qr_code_url = youpi_session['qr_code_url']
    else:
        encoded_uri = urllib.parse.quote_plus(upi_uri)
        qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=240x240&data={encoded_uri}"

    # Public patient live display URL
    patient_display_url = request.build_absolute_uri(f"/payments/{hospital.slug}/{bill.bill_number}/live/")

    return render(request, 'payments/checkout.html', {
        'hospital': hospital,
        'bill': bill,
        'upi_uri': upi_uri,
        'qr_code_url': qr_code_url,
        'patient_display_url': patient_display_url,
        'youpi_session': youpi_session,
    })

def cashier_screen_live(request, slug):
    """
    Patient-Facing Counter Screen for the Hospital with Token-Based Security.
    Secured by cryptographically random `token` query param to prevent guessing.
    Only authorized when accessed via the hospital's private display token or
    by authenticated clinic staff.
    """
    hospital = get_object_or_404(Hospital, slug=slug)
    token = request.GET.get('token')

    # Security check: Token must match or user must be logged-in staff
    is_staff = can_access_hospital(request.user, hospital)
    is_valid_token = token and hospital.display_token and (token == hospital.display_token)

    if not (is_staff or is_valid_token):
        return HttpResponseForbidden("Access Denied: Invalid or missing counter display security token.")

    # Counter scope filter:
    # If ?counter=pharmacy, filter specifically for pharmacy department bills
    # If ?counter=opd, filter for non-pharmacy bills
    counter_type = request.GET.get('counter', '').strip().lower()

    unpaid_bills = hospital.bills.filter(status=Bill.Status.UNPAID)
    if counter_type == 'pharmacy':
        unpaid_bills = unpaid_bills.filter(items__service__department=ServiceItem.Department.PHARMACY).distinct()
    elif counter_type == 'opd':
        unpaid_bills = unpaid_bills.exclude(items__service__department=ServiceItem.Department.PHARMACY)

    active_bill = unpaid_bills.order_by('-created_at').first()

    # Optional: check if the latest bill was paid within the last 8 seconds to show a brief celebration, then revert to standby
    recent_paid_bill = None
    if not active_bill:
        paid_bills = hospital.bills.order_by('-created_at')
        if counter_type == 'pharmacy':
            paid_bills = paid_bills.filter(items__service__department=ServiceItem.Department.PHARMACY).distinct()
        elif counter_type == 'opd':
            paid_bills = paid_bills.exclude(items__service__department=ServiceItem.Department.PHARMACY)

        latest_bill = paid_bills.first()
        if latest_bill and latest_bill.status == Bill.Status.PAID:
            # Check transaction time via OneToOneField related_name='payment'
            try:
                latest_tx = latest_bill.payment
                if latest_tx and latest_tx.status == PaymentTransaction.Status.SUCCESS and latest_tx.completed_at:
                    if (timezone.now() - latest_tx.completed_at).total_seconds() < 8:
                        recent_paid_bill = latest_bill
            except PaymentTransaction.DoesNotExist:
                pass

    upi_uri = None
    qr_code_url = None

    if active_bill:
        upi_id = hospital.upi_id or 'cliniqpay@upi'
        pa = urllib.parse.quote(upi_id)
        pn = urllib.parse.quote(hospital.name)
        am = f"{active_bill.total_amount:.2f}"
        tr = active_bill.bill_number
        tn = urllib.parse.quote(f"Bill {active_bill.bill_number}")
        upi_uri = f"upi://pay?pa={pa}&pn={pn}&am={am}&tr={tr}&tn={tn}&cu=INR"
        encoded_uri = urllib.parse.quote_plus(upi_uri)
        qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=320x320&data={encoded_uri}"

    return render(request, 'payments/counter_display.html', {
        'hospital': hospital,
        'active_bill': active_bill,
        'recent_paid_bill': recent_paid_bill,
        'upi_uri': upi_uri,
        'qr_code_url': qr_code_url,
        'display_token': hospital.display_token,
        'counter_type': counter_type,
    })

def record_cash(request, slug, bill_number):
    hospital = get_object_or_404(Hospital, slug=slug)
    if not can_access_hospital(request.user, hospital):
        return redirect(f'/hospital/{hospital.slug}/login/')

    bill = get_object_or_404(Bill, hospital=hospital, bill_number=bill_number)
    if bill.status == Bill.Status.PAID:
        messages.info(request, f'Bill {bill.bill_number} is already marked as paid.')
        return redirect('payments:success', slug=hospital.slug, bill_number=bill.bill_number)

    if request.method == 'POST':
        try:
            cash_tendered = Decimal(str(request.POST.get('cash_tendered', bill.total_amount)).strip() or bill.total_amount)
        except (ValueError, TypeError, decimal.InvalidOperation):
            cash_tendered = bill.total_amount

        if cash_tendered < bill.total_amount:
            messages.error(request, f'Insufficient cash tendered. Tendered ₹{cash_tendered:.2f} is less than bill total ₹{bill.total_amount:.2f}.')
            return redirect('payments:checkout', slug=hospital.slug, bill_number=bill.bill_number)

        cash_change = max(Decimal('0.00'), cash_tendered - bill.total_amount)

        with transaction.atomic():
            bill.status = Bill.Status.PAID
            bill.save()

            PaymentTransaction.objects.update_or_create(
                bill=bill,
                defaults={
                    'hospital': hospital,
                    'amount': bill.total_amount,
                    'method': PaymentTransaction.Method.CASH,
                    'status': PaymentTransaction.Status.SUCCESS,
                    'cash_tendered': cash_tendered,
                    'cash_change': cash_change,
                    'recorded_by': request.user.username,
                    'completed_at': timezone.now(),
                }
            )

            # Discharge safeguard: only discharge if this is marked as a discharge bill
            # AND there are no remaining unpaid bills for this patient
            if getattr(bill, 'is_discharge_bill', False) and bill.patient and bill.patient.is_inpatient:
                patient = bill.patient
                other_unpaid = patient.bills.filter(hospital=hospital, status=Bill.Status.UNPAID).exclude(id=bill.id).exists()
                if not other_unpaid:
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
                                'notes': f"Discharged on payment of Final Bill {bill.bill_number}",
                            }
                        )
                else:
                    messages.warning(request, f'Payment recorded, but patient remains admitted because other unpaid stay charges exist.')

        return redirect('payments:success', slug=hospital.slug, bill_number=bill.bill_number)

    return redirect('payments:checkout', slug=hospital.slug, bill_number=bill.bill_number)

def confirm_upi(request, slug, bill_number):
    hospital = get_object_or_404(Hospital, slug=slug)
    if not can_access_hospital(request.user, hospital):
        return redirect(f'/hospital/{hospital.slug}/login/')

    bill = get_object_or_404(Bill, hospital=hospital, bill_number=bill_number)
    if bill.status == Bill.Status.PAID:
        messages.info(request, f'Bill {bill.bill_number} is already marked as paid.')
        return redirect('payments:success', slug=hospital.slug, bill_number=bill.bill_number)

    if request.method == 'POST':
        utr = request.POST.get('utr_number', '').strip() or f"UPI{timezone.now().strftime('%Y%m%d%H%M%S')}"

        with transaction.atomic():
            bill.status = Bill.Status.PAID
            bill.save()

            PaymentTransaction.objects.update_or_create(
                bill=bill,
                defaults={
                    'hospital': hospital,
                    'amount': bill.total_amount,
                    'method': PaymentTransaction.Method.UPI,
                    'status': PaymentTransaction.Status.SUCCESS,
                    'utr_number': utr,
                    'recorded_by': request.user.username,
                    'completed_at': timezone.now(),
                }
            )

            # Discharge safeguard: only discharge if this is marked as a discharge bill
            # AND there are no remaining unpaid bills for this patient
            if getattr(bill, 'is_discharge_bill', False) and bill.patient and bill.patient.is_inpatient:
                patient = bill.patient
                other_unpaid = patient.bills.filter(hospital=hospital, status=Bill.Status.UNPAID).exclude(id=bill.id).exists()
                if not other_unpaid:
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
                                'notes': f"Discharged on payment of Final Bill {bill.bill_number}",
                            }
                        )
                else:
                    messages.warning(request, f'Payment recorded, but patient remains admitted because other unpaid stay charges exist.')

        return redirect('payments:success', slug=hospital.slug, bill_number=bill.bill_number)

    return redirect('payments:checkout', slug=hospital.slug, bill_number=bill.bill_number)

def payment_success(request, slug, bill_number):
    hospital = get_object_or_404(Hospital, slug=slug)
    bill = get_object_or_404(Bill, hospital=hospital, bill_number=bill_number)
    payment = PaymentTransaction.objects.filter(bill=bill).first()
    return render(request, 'payments/success.html', {
        'hospital': hospital,
        'bill': bill,
        'payment': payment,
    })

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from payments.services.youpi import YoupiPaymentGateway

@csrf_exempt
def youpi_webhook(request, slug):
    """
    Cryptographically authenticated webhook receiver for YouPI-PG.
    Validates HMAC-SHA256 signature, deduplicates via X-Gateway-Delivery-Id,
    and updates Bill status to PAID with verified UTR upon OBSERVED_SUCCESS or RECONCILED.
    """
    hospital = get_object_or_404(Hospital, slug=slug)

    if request.method != 'POST':
        return HttpResponseForbidden("Method not allowed")

    raw_body = request.body
    signature = request.headers.get('X-Gateway-Signature') or request.META.get('HTTP_X_GATEWAY_SIGNATURE', '')
    event_type = request.headers.get('X-Gateway-Event') or request.META.get('HTTP_X_GATEWAY_EVENT', '')
    delivery_id = request.headers.get('X-Gateway-Delivery-Id') or request.META.get('HTTP_X_GATEWAY_DELIVERY_ID', '')

    gateway = YoupiPaymentGateway(hospital)

    # 1. Cryptographic HMAC validation (in production or when webhook_secret configured)
    if hospital.youpi_webhook_secret and not gateway.verify_webhook_signature(raw_body, signature):
        return JsonResponse({'error': 'Invalid webhook signature'}, status=401)

    try:
        data = json.loads(raw_body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'Malformed JSON payload'}, status=400)

    order_id = data.get('order_id') or data.get('bill_number')
    if not order_id:
        return JsonResponse({'error': 'Missing order_id'}, status=400)

    bill = Bill.objects.filter(hospital=hospital, bill_number=order_id).first()
    if not bill:
        return JsonResponse({'error': 'Bill not found'}, status=404)

    # 2. Idempotency Check: Ignore duplicate webhook deliveries
    if delivery_id and PaymentTransaction.objects.filter(hospital=hospital, webhook_delivery_id=delivery_id).exists():
        return JsonResponse({'received': True, 'note': 'Duplicate delivery ignored', 'delivery_id': delivery_id})

    # If already paid, acknowledge receipt safely
    if bill.status == Bill.Status.PAID:
        return JsonResponse({'received': True, 'status': 'already_settled'})

    event = event_type or data.get('event')
    # Successful payment events from YouPI
    if event in ('OBSERVED_SUCCESS', 'RECONCILED', 'SUCCESS', 'PAYMENT_RECEIVED'):
        utr = data.get('utr') or data.get('bank_rrn') or f"YOUPI{timezone.now().strftime('%Y%m%d%H%M%S')}"
        youpi_pay_id = data.get('payment_id') or data.get('id')

        with transaction.atomic():
            bill.status = Bill.Status.PAID
            bill.save()

            PaymentTransaction.objects.update_or_create(
                bill=bill,
                defaults={
                    'hospital': hospital,
                    'amount': bill.total_amount,
                    'method': PaymentTransaction.Method.UPI,
                    'status': PaymentTransaction.Status.SUCCESS,
                    'utr_number': utr,
                    'gateway_provider': 'youpi',
                    'youpi_payment_id': youpi_pay_id,
                    'webhook_delivery_id': delivery_id,
                    'is_verified_webhook': True,
                    'recorded_by': 'youpi_webhook_relay',
                    'completed_at': timezone.now(),
                }
            )

            # Inpatient discharge safeguard
            if getattr(bill, 'is_discharge_bill', False) and bill.patient and bill.patient.is_inpatient:
                patient = bill.patient
                other_unpaid = patient.bills.filter(hospital=hospital, status=Bill.Status.UNPAID).exclude(id=bill.id).exists()
                if not other_unpaid:
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
                                'notes': f"Discharged on YouPI webhook settlement of Final Bill {bill.bill_number}",
                            }
                        )

        return JsonResponse({
            'received': True,
            'status': 'settled',
            'bill_number': bill.bill_number,
            'utr': utr,
            'delivery_id': delivery_id
        })

    return JsonResponse({'received': True, 'event': event, 'status': 'acknowledged'})

def test_youpi_sandbox_webhook(request, slug, bill_number):
    """
    Developer / Tester action: Simulates an incoming YouPI-PG bank observer credit alert.
    Sends a signed HMAC-SHA256 mock webhook internally to test instant reconciliation.
    """
    hospital = get_object_or_404(Hospital, slug=slug)
    if not can_access_hospital(request.user, hospital):
        return HttpResponseForbidden("Access Denied")

    bill = get_object_or_404(Bill, hospital=hospital, bill_number=bill_number)
    gateway = YoupiPaymentGateway(hospital)
    test_packet = gateway.generate_test_webhook_payload(bill, event='OBSERVED_SUCCESS')

    # Send payload directly to youpi_webhook logic
    from django.test import RequestFactory
    factory = RequestFactory()
    mock_req = factory.post(
        f'/payments/{hospital.slug}/youpi/webhook/',
        data=test_packet['raw_bytes'],
        content_type='application/json',
        HTTP_X_GATEWAY_SIGNATURE=test_packet['headers']['X-Gateway-Signature'],
        HTTP_X_GATEWAY_EVENT=test_packet['headers']['X-Gateway-Event'],
        HTTP_X_GATEWAY_DELIVERY_ID=test_packet['headers']['X-Gateway-Delivery-Id'],
    )

    response = youpi_webhook(mock_req, slug=hospital.slug)
    if response.status_code == 200:
        messages.success(request, f"YouPI Sandbox Webhook verified! Bill {bill.bill_number} marked as PAID via simulated UPI Observer.")
        return redirect('payments:success', slug=hospital.slug, bill_number=bill.bill_number)
    else:
        messages.error(request, f"Webhook simulation failed with status {response.status_code}.")
        return redirect('payments:checkout', slug=hospital.slug, bill_number=bill.bill_number)
