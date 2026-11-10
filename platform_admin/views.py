import secrets
import string
from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone
from django.core.mail import send_mail
from platform_admin.models import SupportTicket, TicketMessage
from enrollment.models import EnrollmentRequest
from setup_hospital.models import Hospital
from setup_hospital.views import seed_hospital_services

def generate_random_password(length=10):
    chars = string.ascii_letters + string.digits + "!@#$"
    return ''.join(secrets.choice(chars) for _ in range(length))

def is_platform_admin(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff)

def admin_login(request):
    if request.user.is_authenticated and is_platform_admin(request.user):
        return redirect('platform_admin:dashboard')

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            if is_platform_admin(user):
                auth_login(request, user)
                next_url = request.POST.get('next') or request.GET.get('next') or '/platform/'
                return redirect(next_url)
            else:
                form.add_error(None, 'Access denied. You are not a platform administrator.')

    return render(request, 'platform_admin/login.html', {'form': form, 'next': request.GET.get('next', '')})

def admin_logout(request):
    auth_logout(request)
    return redirect('platform_admin:login')

@user_passes_test(is_platform_admin, login_url='/platform/login/')
def dashboard(request):
    enrollments = EnrollmentRequest.objects.all().order_by('-submitted_at')
    return render(request, 'platform_admin/dashboard.html', {
        'enrollments': enrollments,
        'pending_count': enrollments.filter(status=EnrollmentRequest.Status.PENDING_REVIEW).count(),
        'activated_count': enrollments.filter(status=EnrollmentRequest.Status.ACTIVATED).count(),
    })

@user_passes_test(is_platform_admin, login_url='/platform/login/')
def approve_request(request, pk):
    if request.method == 'POST':
        enrollment = get_object_or_404(EnrollmentRequest, pk=pk)
        enrollment.status = EnrollmentRequest.Status.ACTIVATED
        enrollment.reviewed_at = timezone.now()
        enrollment.reviewed_by = request.user.username

        # Generate temporary credentials if not set
        if not enrollment.temp_password:
            enrollment.temp_password = generate_random_password()
        enrollment.save()

        # Provision Hospital tenant if not already present
        hospital, created = Hospital.objects.get_or_create(
            enrollment=enrollment,
            defaults={
                'name': enrollment.hospital_name,
                'plan_tier': enrollment.plan_tier,
                'bed_count': enrollment.bed_count or 20,
                'city': enrollment.city,
                'state': enrollment.state,
            }
        )
        if not created:
            hospital.plan_tier = enrollment.plan_tier
            hospital.bed_count = enrollment.bed_count or hospital.bed_count
            hospital.save()

        # Seed tier-specific services for newly activated clinic
        seed_hospital_services(hospital, hospital.plan_tier)

        # Create or update Clinic Admin user account
        username = enrollment.contact_email
        if not User.objects.filter(username=username).exists():
            User.objects.create_user(
                username=username,
                email=enrollment.contact_email,
                password=enrollment.temp_password,
                first_name=enrollment.admin_full_name
            )

        # Send Welcome Email with credentials
        login_url = request.build_absolute_uri(f'/hospital/{hospital.slug}/')
        email_body = f"""Hello {enrollment.admin_full_name},

Welcome to CliniqPay! Your 7-day free trial has been approved and activated for {enrollment.hospital_name}.

Your Clinic Workspace Login Details:
- Workspace URL: {login_url}
- Admin Username: {username}
- Temporary Password: {enrollment.temp_password}

You can log in, configure your services and tariffs, and start live UPI cashier billing.

Best regards,
The CliniqPay Team
"""
        send_mail(
            subject=f"Welcome to CliniqPay — Credentials for {enrollment.hospital_name}",
            message=email_body,
            from_email='welcome@cliniqpay.com',
            recipient_list=[enrollment.contact_email],
            fail_silently=True,
        )

    return redirect('platform_admin:dashboard')

@user_passes_test(is_platform_admin, login_url='/platform/login/')
def edit_enrollment(request, pk):
    enrollment = get_object_or_404(EnrollmentRequest, pk=pk)
    if request.method == 'POST':
        hospital_name = request.POST.get('hospital_name', '').strip()
        plan_tier = request.POST.get('plan_tier', enrollment.plan_tier).strip()
        bed_count = request.POST.get('bed_count', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        contact_phone = request.POST.get('contact_phone', '').strip()
        contact_email = request.POST.get('contact_email', '').strip()
        admin_full_name = request.POST.get('admin_full_name', '').strip()

        if hospital_name:
            enrollment.hospital_name = hospital_name
        if bed_count:
            try:
                enrollment.bed_count = int(bed_count)
            except ValueError:
                pass

        if plan_tier in EnrollmentRequest.PlanTier.values:
            enrollment.plan_tier = plan_tier
        elif enrollment.bed_count is not None:
            # Auto-infer plan tier from bed capacity if not explicitly provided
            if enrollment.bed_count <= 5:
                enrollment.plan_tier = EnrollmentRequest.PlanTier.STARTER
            elif enrollment.bed_count <= 30:
                enrollment.plan_tier = EnrollmentRequest.PlanTier.STANDARD
            else:
                enrollment.plan_tier = EnrollmentRequest.PlanTier.ENTERPRISE
        if city:
            enrollment.city = city
        if state:
            enrollment.state = state
        if contact_phone:
            enrollment.contact_phone = contact_phone
        if contact_email:
            enrollment.contact_email = contact_email
        if admin_full_name:
            enrollment.admin_full_name = admin_full_name

        enrollment.save()

        # If already activated hospital exists, sync changes and update services for new plan
        if hasattr(enrollment, 'hospital') and enrollment.hospital:
            hosp = enrollment.hospital
            old_plan = hosp.plan_tier
            hosp.name = enrollment.hospital_name
            hosp.plan_tier = enrollment.plan_tier
            hosp.bed_count = enrollment.bed_count
            hosp.city = enrollment.city
            hosp.state = enrollment.state
            hosp.save()

            # If plan tier changed/upgraded, seed new tier catalog items non-destructively
            if old_plan != hosp.plan_tier:
                seed_hospital_services(hosp, hosp.plan_tier)

    return redirect('platform_admin:dashboard')

@user_passes_test(is_platform_admin, login_url='/platform/login/')
def reset_hospital_password(request, pk):
    if request.method == 'POST':
        enrollment = get_object_or_404(EnrollmentRequest, pk=pk)
        new_password = request.POST.get('new_password', '').strip()
        if not new_password:
            new_password = generate_random_password()

        enrollment.temp_password = new_password
        enrollment.save()

        # Update User in Django auth
        user = User.objects.filter(username=enrollment.contact_email).first()
        if user:
            user.set_password(new_password)
            user.save()

    return redirect('platform_admin:dashboard')

@user_passes_test(is_platform_admin, login_url='/platform/login/')
def reject_request(request, pk):
    if request.method == 'POST':
        enrollment = get_object_or_404(EnrollmentRequest, pk=pk)
        enrollment.status = EnrollmentRequest.Status.REJECTED
        enrollment.reviewed_at = timezone.now()
        enrollment.reviewed_by = request.user.username
        enrollment.save()
    return redirect('platform_admin:dashboard')

@user_passes_test(is_platform_admin, login_url='/platform/login/')
def support_dashboard(request):
    """
    Master Support Center & Ticket Tracking System:
    Enables platform admins to track, filter, triage, and manage hospital issue tickets
    from submission to final resolution.
    """
    tickets = SupportTicket.objects.select_related('hospital', 'assigned_to', 'created_by').all().order_by('-created_at')

    # Status / Priority filtering
    status_filter = request.GET.get('status', 'all')
    priority_filter = request.GET.get('priority', 'all')
    category_filter = request.GET.get('category', 'all')
    hospital_filter = request.GET.get('hospital', 'all')
    search_q = request.GET.get('q', '').strip().lower()

    if status_filter != 'all':
        tickets = tickets.filter(status=status_filter)
    if priority_filter != 'all':
        tickets = tickets.filter(priority=priority_filter)
    if category_filter != 'all':
        tickets = tickets.filter(category=category_filter)
    if hospital_filter != 'all':
        tickets = tickets.filter(hospital__slug=hospital_filter)
    if search_q:
        tickets = [t for t in tickets if search_q in t.ticket_number.lower() or search_q in t.subject.lower() or search_q in t.hospital.name.lower() or search_q in t.staff_name.lower() or search_q in t.contact_phone]

    all_tickets_qs = SupportTicket.objects.all()
    open_count = all_tickets_qs.filter(status__in=[SupportTicket.Status.OPEN, SupportTicket.Status.IN_PROGRESS]).count()
    urgent_count = all_tickets_qs.filter(priority=SupportTicket.Priority.URGENT, status__in=[SupportTicket.Status.OPEN, SupportTicket.Status.IN_PROGRESS]).count()
    waiting_count = all_tickets_qs.filter(status=SupportTicket.Status.WAITING_HOSPITAL).count()
    resolved_count = all_tickets_qs.filter(status__in=[SupportTicket.Status.RESOLVED, SupportTicket.Status.CLOSED]).count()

    hospitals_list = Hospital.objects.all().order_by('name')

    return render(request, 'platform_admin/support_dashboard.html', {
        'tickets': tickets,
        'open_count': open_count,
        'urgent_count': urgent_count,
        'waiting_count': waiting_count,
        'resolved_count': resolved_count,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'category_filter': category_filter,
        'hospital_filter': hospital_filter,
        'search_q': search_q,
        'hospitals_list': hospitals_list,
        'category_choices': SupportTicket.Category.choices,
        'status_choices': SupportTicket.Status.choices,
        'priority_choices': SupportTicket.Priority.choices,
    })

@user_passes_test(is_platform_admin, login_url='/platform/login/')
def support_ticket_resolve(request, ticket_number):
    """
    Dedicated Ticket Resolution & Diagnostics Workspace:
    Inspect full technical environment, view attached screenshot, listen to audio recording,
    update resolution status, change priority, add internal diagnostic notes,
    and post replies directly to the hospital staff.
    """
    ticket = get_object_or_404(SupportTicket, ticket_number=ticket_number)

    if request.method == 'POST':
        action = request.POST.get('action') or request.POST.get('action_type')

        if action in ['update_status', 'update_ticket']:
            new_status = request.POST.get('status')
            new_priority = request.POST.get('priority')
            assigned_user_id = request.POST.get('assigned_to')
            resolution_notes = request.POST.get('resolution_notes', '').strip()

            if new_status in SupportTicket.Status.values:
                ticket.status = new_status
                if new_status in [SupportTicket.Status.RESOLVED, SupportTicket.Status.CLOSED] and not ticket.resolved_at:
                    ticket.resolved_at = timezone.now()
                elif new_status not in [SupportTicket.Status.RESOLVED, SupportTicket.Status.CLOSED]:
                    ticket.resolved_at = None

            if new_priority in SupportTicket.Priority.values:
                ticket.priority = new_priority

            ticket.resolution_notes = resolution_notes

            if assigned_user_id:
                # check if ID or username
                user = User.objects.filter(id=assigned_user_id).first() if assigned_user_id.isdigit() else User.objects.filter(username=assigned_user_id).first()
                ticket.assigned_to = user
            else:
                ticket.assigned_to = None

            ticket.save()
            messages.success(request, f"Ticket #{ticket.ticket_number} status updated to {ticket.get_status_display()}.")

        elif action in ['post_reply', 'add_reply']:
            message_text = (request.POST.get('message') or request.POST.get('reply_message') or '').strip()
            reply_type = request.POST.get('reply_type')
            is_internal = (request.POST.get('is_internal_note') == '1') or (reply_type == 'internal')

            if message_text:
                msg = TicketMessage.objects.create(
                    ticket=ticket,
                    sender=request.user,
                    sender_name=request.user.get_full_name() or request.user.username,
                    is_staff_reply=True,
                    is_internal_note=is_internal,
                    message=message_text,
                )
                if 'attachment' in request.FILES:
                    msg.attachment = request.FILES['attachment']
                    msg.save()

                if not is_internal and ticket.status == SupportTicket.Status.OPEN:
                    ticket.status = SupportTicket.Status.WAITING_HOSPITAL
                    ticket.save()

                messages.success(request, "Internal note logged." if is_internal else "Reply posted to hospital.")

        return redirect('platform_admin:support_ticket_resolve', ticket_number=ticket.ticket_number)

    messages_thread = ticket.messages.all().order_by('created_at')
    admin_users = User.objects.filter(models.Q(is_staff=True) | models.Q(is_superuser=True)).distinct()

    return render(request, 'platform_admin/ticket_resolve.html', {
        'ticket': ticket,
        'messages_thread': messages_thread,
        'admin_users': admin_users,
        'status_choices': SupportTicket.Status.choices,
        'priority_choices': SupportTicket.Priority.choices,
    })
