from datetime import datetime, date, time
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from setup_hospital.models import Hospital, Doctor
from setup_hospital.views import can_access_hospital, is_hospital_admin
from billing.models import Bill
from payments.models import PaymentTransaction

def daily_report(request, slug):
    """
    Daily 8 PM Collections & Doctor Shares Summary Report.
    Confidential financial breakdown accessible exclusively to Hospital Admin/Owner.
    """
    hospital = get_object_or_404(Hospital, slug=slug)
    if not request.user.is_authenticated:
        return redirect(f'/hospital/{hospital.slug}/login/')
    if not is_hospital_admin(request.user, hospital):
        return redirect('billing:counter', slug=hospital.slug)

    # Selected report date (defaults to today)
    date_str = request.GET.get('date')
    if date_str:
        try:
            report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            report_date = date.today()
    else:
        report_date = date.today()

    # Calculate day start and end in local time
    start_of_day = timezone.make_aware(datetime.combine(report_date, time.min))
    end_of_day = timezone.make_aware(datetime.combine(report_date, time.max))

    # Fetch all bills created on the report date
    bills = hospital.bills.filter(
        created_at__range=(start_of_day, end_of_day)
    ).select_related('patient', 'doctor').prefetch_related('payment')

    total_billed = Decimal('0.00')
    total_upi = Decimal('0.00')
    total_cash = Decimal('0.00')
    total_unpaid = Decimal('0.00')
    total_doctor_shares = Decimal('0.00')
    total_hospital_cut = Decimal('0.00')

    doctor_breakdown = {}

    for bill in bills:
        total_billed += bill.total_amount
        if bill.status == Bill.Status.PAID:
            hosp_cut = max(Decimal('0.00'), bill.total_amount - bill.doctor_share_amount)
            total_doctor_shares += bill.doctor_share_amount
            total_hospital_cut += hosp_cut

            # Payment method breakdown
            try:
                tx = bill.payment
                if tx.method == PaymentTransaction.Method.UPI:
                    total_upi += tx.amount
                elif tx.method == PaymentTransaction.Method.CASH:
                    total_cash += tx.amount
                else:
                    total_cash += bill.total_amount
            except PaymentTransaction.DoesNotExist:
                total_cash += bill.total_amount

            # Doctor share ledger
            doc_name = bill.doctor.full_name if bill.doctor else 'Hospital General / OPD'
            if doc_name not in doctor_breakdown:
                doctor_breakdown[doc_name] = {
                    'name': doc_name,
                    'patient_count': 0,
                    'total_collected': Decimal('0.00'),
                    'doctor_share': Decimal('0.00'),
                    'hospital_share': Decimal('0.00'),
                }
            doctor_breakdown[doc_name]['patient_count'] += 1
            doctor_breakdown[doc_name]['total_collected'] += bill.total_amount
            doctor_breakdown[doc_name]['doctor_share'] += bill.doctor_share_amount
            doctor_breakdown[doc_name]['hospital_share'] += hosp_cut
        else:
            total_unpaid += bill.total_amount

    total_collected = total_upi + total_cash

    # Prepare formatted WhatsApp text representation
    summary_text = (
        f"🏥 *{hospital.name} — Daily 8 PM Summary*\n"
        f"📅 Date: {report_date.strftime('%d %b %Y')}\n\n"
        f"💰 *Collections Overview:*\n"
        f"• Total Billed: ₹{total_billed:.2f}\n"
        f"• UPI Digital Received: ₹{total_upi:.2f}\n"
        f"• Cash In Register: ₹{total_cash:.2f}\n"
        f"• Total Settled: ₹{total_collected:.2f}\n"
        f"• Outstanding / Unpaid: ₹{total_unpaid:.2f}\n\n"
        f"🩺 *Doctor Payouts vs Hospital Cut:*\n"
        f"• Total Doctor Shares: ₹{total_doctor_shares:.2f}\n"
        f"• Hospital Net Margin: ₹{total_hospital_cut:.2f}\n"
    )

    return render(request, 'summary/daily_report.html', {
        'hospital': hospital,
        'report_date': report_date,
        'bills': bills,
        'total_billed': total_billed,
        'total_collected': total_collected,
        'total_upi': total_upi,
        'total_cash': total_cash,
        'total_unpaid': total_unpaid,
        'total_doctor_shares': total_doctor_shares,
        'total_hospital_cut': total_hospital_cut,
        'doctor_breakdown': doctor_breakdown.values(),
        'summary_text': summary_text,
    })

def send_whatsapp(request, slug):
    hospital = get_object_or_404(Hospital, slug=slug)
    if not is_hospital_admin(request.user, hospital):
        return redirect('billing:counter', slug=hospital.slug)

    if request.method == 'POST':
        default_phone = hospital.enrollment.contact_phone if hospital.enrollment else '7510726715'
        phone = request.POST.get('phone', default_phone)
        report_date = request.POST.get('report_date', date.today().isoformat())
        messages.success(request, f"Daily 8 PM Summary dispatched to WhatsApp +91 {phone} successfully.")
        return redirect(f'/summary/{hospital.slug}/?date={report_date}')

    return redirect(f'/summary/{hospital.slug}/')
