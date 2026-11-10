import re
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.core.mail import send_mail
from enrollment.models import EnrollmentRequest

def landing(request):
    return render(request, 'enrollment/landing.html')

def submit_enrollment(request):
    if request.method != 'POST':
        return HttpResponse('Method not allowed', status=405)

    hospital_name = request.POST.get('hospital_name', '').strip()
    plan_tier = request.POST.get('plan_tier', EnrollmentRequest.PlanTier.STANDARD).strip()
    bed_count = request.POST.get('bed_count', '20').strip()
    city = request.POST.get('city', '').strip()
    state = request.POST.get('state', '').strip()
    contact_phone = request.POST.get('contact_phone', '').strip()
    contact_email = request.POST.get('contact_email', '').strip()
    admin_full_name = request.POST.get('admin_full_name', '').strip()

    if not all([hospital_name, city, state, contact_phone, contact_email, admin_full_name]):
        return HttpResponse('All fields are required', status=400)

    try:
        bed_count = int(bed_count) if bed_count else 20
    except ValueError:
        bed_count = 20

    if plan_tier not in EnrollmentRequest.PlanTier.values:
        plan_tier = EnrollmentRequest.PlanTier.STANDARD

    # Validate phone (10 digits)
    cleaned_phone = re.sub(r'\D', '', contact_phone)
    if len(cleaned_phone) != 10:
        return HttpResponse('Valid 10-digit phone number is required', status=400)

    enrollment = EnrollmentRequest.objects.create(
        hospital_name=hospital_name,
        plan_tier=plan_tier,
        bed_count=bed_count,
        city=city,
        state=state,
        contact_phone=cleaned_phone,
        contact_email=contact_email,
        admin_full_name=admin_full_name,
        status=EnrollmentRequest.Status.PENDING_REVIEW,
    )

    # Send acknowledgment email to the applicant
    tracking_url = request.build_absolute_uri(f'/enrollment/status/{enrollment.reference_token}/')
    email_body = f"""Hello {enrollment.admin_full_name},

Thank you for enrolling {enrollment.hospital_name} with CliniqPay!

We have successfully received your enrollment application. Here are your details:
• Hospital / Clinic: {enrollment.hospital_name}
• Selected Plan: {enrollment.get_plan_tier_display()}
• Declared Bed Capacity: {enrollment.bed_count} beds
• Location: {enrollment.city}, {enrollment.state}
• Application Reference Token: {enrollment.reference_token}

Our platform administration team is reviewing your details. Once activated, your secure clinic workspace login credentials will be delivered to this email address.

You can track your live activation status here:
{tracking_url}

Best regards,
CliniqPay Team
support@cliniqpay.com
"""
    send_mail(
        subject=f"Application Received — CliniqPay Enrollment for {enrollment.hospital_name}",
        message=email_body,
        from_email='welcome@cliniqpay.com',
        recipient_list=[enrollment.contact_email],
        fail_silently=True,
    )

    return render(request, 'enrollment/confirmation.html', {'enrollment': enrollment})

def track_status(request, token):
    enrollment = get_object_or_404(EnrollmentRequest, reference_token=token)
    return render(request, 'enrollment/status.html', {'enrollment': enrollment})

def terms_of_service(request):
    """Statutory Terms of Service & ABDM Compliance Page."""
    return render(request, 'enrollment/legal_terms.html')

def security_whitepaper(request):
    """Enterprise Technical Security & DPDP Compliance Whitepaper."""
    return render(request, 'enrollment/security_whitepaper.html')

def system_status(request):
    """Live Infrastructure Health & Subsystem Status Page."""
    return render(request, 'enrollment/system_status.html')
