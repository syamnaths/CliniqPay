import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from setup_hospital.models import Hospital
from setup_hospital.views import can_access_hospital
from billing.models import Bill
from receipts.models import WhatsAppReceiptLog

def view_receipt(request, slug, bill_number):
    hospital = get_object_or_404(Hospital, slug=slug)
    bill = get_object_or_404(Bill, hospital=hospital, bill_number=bill_number)
    receipt_log = WhatsAppReceiptLog.objects.filter(bill=bill).order_by('-sent_at').first()
    return render(request, 'receipts/invoice_receipt.html', {
        'hospital': hospital,
        'bill': bill,
        'receipt_log': receipt_log,
    })

def generate_whatsapp_receipt_text(bill, hospital, receipt_url):
    """
    Builds the official WhatsApp notification message text
    following standard Meta WhatsApp template structure.
    """
    token_str = f"\n🎟 *Queue Token:* #{bill.token_number}" if bill.token_number else ""
    bed_str = f"\n🛏 *Room / Bed:* {bill.room_bed_number}" if bill.bill_type == Bill.BillType.IPD and bill.room_bed_number else ""
    doc_str = f"\n🩺 *Consultant:* {bill.doctor.full_name}" if bill.doctor else ""

    return (
        f"🏥 *{hospital.name} — Tax Invoice & Receipt*\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"Dear *{bill.patient.name}*,\n"
        f"Thank you for visiting {hospital.name}. Your payment has been received and confirmed.\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📄 *Bill Number:* {bill.bill_number}\n"
        f"📅 *Date & Time:* {bill.created_at.strftime('%d %b %Y, %I:%M %p')}\n"
        f"💵 *Amount Paid:* ₹{bill.total_amount:.2f}\n"
        f"💳 *Mode:* {bill.payment.get_method_display() if hasattr(bill, 'payment') else 'Digital UPI'}"
        f"{token_str}{bed_str}{doc_str}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📥 *Download Official Tax Receipt PDF:*\n"
        f"{receipt_url}\n\n"
        f"For billing queries, reach us at {hospital.city}, {hospital.state}.\n"
        f"_CliniqPay Healthcare Fintech OS · ABDM M1 & M2 Certified_"
    )

def dispatch_whatsapp(request, slug, bill_number):
    hospital = get_object_or_404(Hospital, slug=slug)
    if not can_access_hospital(request.user, hospital):
        return HttpResponseForbidden("Access Denied")

    bill = get_object_or_404(Bill, hospital=hospital, bill_number=bill_number)
    phone = request.POST.get('phone', bill.patient.phone).strip()

    # Digits-only phone sanitization
    clean_phone = ''.join(c for c in phone if c.isdigit())
    if len(clean_phone) > 10 and clean_phone.startswith('91'):
        clean_phone = clean_phone[-10:]

    if len(clean_phone) != 10:
        messages.error(request, "Invalid phone number. Indian phone number must be 10 digits.")
        return redirect('payments:success', slug=hospital.slug, bill_number=bill.bill_number)

    # Absolute URL to the receipt
    receipt_absolute_url = request.build_absolute_uri(f"/receipts/{hospital.slug}/{bill.bill_number}/view/")
    message_text = generate_whatsapp_receipt_text(bill, hospital, receipt_absolute_url)

    # Simulated WhatsApp Dispatch Record
    log = WhatsAppReceiptLog.objects.create(
        hospital=hospital,
        bill=bill,
        recipient_phone=clean_phone,
        provider=hospital.whatsapp_api_provider or 'meta_cloud',
        message_id=f"wamid.{uuid.uuid4().hex[:16]}",
        status=WhatsAppReceiptLog.Status.SENT,
        pdf_url=receipt_absolute_url,
    )

    messages.success(request, f"Tax Receipt PDF dispatched to WhatsApp +91 {clean_phone} successfully!")
    return redirect('payments:success', slug=hospital.slug, bill_number=bill.bill_number)

def receipt_status(request, slug, bill_number):
    hospital = get_object_or_404(Hospital, slug=slug)
    bill = get_object_or_404(Bill, hospital=hospital, bill_number=bill_number)
    log = WhatsAppReceiptLog.objects.filter(bill=bill).order_by('-sent_at').first()
    if log:
        return JsonResponse({
            'status': log.status,
            'recipient': log.recipient_phone,
            'sent_at': log.sent_at.isoformat(),
            'message_id': log.message_id,
        })
    return JsonResponse({'status': 'none'})
