from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from accounts.decorators import customer_required
from .models import Customer, Vehicle, Warranty, Feedback, ServiceReminder
from jobs.models import ServiceJob, JobActivityLog
from billing.models import Invoice, Approval
from repairs.models import RepairLog
from notifications.utils import create_notification

# ─── Customer Dashboard ─────────────────
@customer_required
def customer_dashboard(request):
    customer = get_object_or_404(Customer, user=request.user)
    vehicles = customer.vehicles.filter(is_active=True)
    active_jobs = ServiceJob.objects.filter(
        vehicle__customer=customer
    ).exclude(status__in=['DELIVERED', 'CANCELLED']).select_related(
        'vehicle', 'assigned_mechanic'
    ).order_by('-created_at')[:5]
    recent_jobs = ServiceJob.objects.filter(
        vehicle__customer=customer, status__in=['DELIVERED', 'COMPLETED']
    ).select_related('vehicle').order_by('-completed_at')[:5]
    reminders = ServiceReminder.objects.filter(
        vehicle__customer=customer, is_dismissed=False,
        reminder_date__gte=timezone.now().date()
    ).select_related('vehicle').order_by('reminder_date')[:5]

    pending_approvals = Approval.objects.filter(
        job__vehicle__customer=customer, status='PENDING'
    ).select_related('job__vehicle').count()

    total_spent = Invoice.objects.filter(
        job__vehicle__customer=customer, is_paid=True
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    return render(request, 'customer/dashboard.html', {
        'customer': customer, 'vehicles': vehicles,
        'active_jobs': active_jobs, 'recent_jobs': recent_jobs,
        'reminders': reminders, 'pending_approvals': pending_approvals,
        'total_spent': total_spent,
    })

# ─── My Vehicles ────────────────────────
@customer_required
def customer_vehicles(request):
    customer = get_object_or_404(Customer, user=request.user)
    vehicles = customer.vehicles.filter(is_active=True)
    for v in vehicles:
        v.job_count = v.jobs.count()
        v.active_job_count = v.jobs.exclude(status__in=['DELIVERED', 'CANCELLED']).count()
    return render(request, 'customer/vehicles.html', {'vehicles': vehicles})

# ─── Vehicle Detail ──────────────────────
@customer_required
def customer_vehicle_detail(request, pk):
    customer = get_object_or_404(Customer, user=request.user)
    vehicle = get_object_or_404(Vehicle, pk=pk, customer=customer)
    jobs = vehicle.jobs.order_by('-created_at')
    warranties = vehicle.warranties.filter(is_active=True)
    reminders = vehicle.reminders.filter(is_dismissed=False).order_by('reminder_date')
    return render(request, 'customer/vehicle_detail.html', {
        'vehicle': vehicle, 'jobs': jobs, 'warranties': warranties, 'reminders': reminders,
    })

# ─── Job Detail (Customer View) ─────────
@customer_required
def customer_job_detail(request, pk):
    customer = get_object_or_404(Customer, user=request.user)
    job = get_object_or_404(
        ServiceJob.objects.select_related('assigned_mechanic', 'vehicle'),
        pk=pk, vehicle__customer=customer
    )
    repairs = job.repairs.order_by('-created_at')
    activity = job.activity_logs.select_related('performed_by').order_by('-timestamp')
    approvals = job.approvals.order_by('-created_at')

    # Safe check for OneToOne reverse relation
    try:
        has_feedback = job.feedback is not None
    except Feedback.DoesNotExist:
        has_feedback = False

    total_repair_cost = sum(r.estimated_cost for r in repairs)

    return render(request, 'customer/job_detail.html', {
        'job': job, 'repairs': repairs, 'activity': activity,
        'approvals': approvals, 'has_feedback': has_feedback,
        'total_repair_cost': total_repair_cost,
    })

# ─── Approve/Reject Repair ──────────────
@customer_required
def customer_approve_repair(request, pk):
    customer = get_object_or_404(Customer, user=request.user)
    approval = get_object_or_404(
        Approval.objects.select_related('job__vehicle'),
        pk=pk, job__vehicle__customer=customer, status='PENDING'
    )
    if request.method == 'POST':
        decision = request.POST['decision']
        approval.status = decision
        approval.approved_by = request.user
        approval.save()
        if decision == 'APPROVED':
            # Mark linked repairs as approved
            approval.repairs.update(is_approved=True)

            try:
                approval.job.change_status('IN_PROGRESS', request.user)
            except Exception as e:
                messages.error(request, f"Could not update job status: {e}")
        
        # Notify mechanic
        if approval.job.assigned_mechanic:
            create_notification(
                recipient=approval.job.assigned_mechanic,
                title=f"Repair {decision.title()}: {approval.job.vehicle.registration_number}",
                message=f"Customer has {decision.lower()} the additional repairs.",
                notification_type="approval_response",
                related_job=approval.job,
                link=f"/mechanic/jobs/{approval.job.pk}/"
            )

        messages.success(request, f'Repair {decision.lower()}.')
        return redirect('customer_job_detail', pk=approval.job.pk)
    return render(request, 'customer/approve_repair.html', {'approval': approval})

# ─── Billing ─────────────────────────────
@customer_required
def customer_billing(request):
    customer = get_object_or_404(Customer, user=request.user)
    invoices = Invoice.objects.filter(
        job__vehicle__customer=customer
    ).select_related('job__vehicle').order_by('-created_at')

    total_spent = invoices.filter(is_paid=True).aggregate(
        total=Sum('total_amount'))['total'] or 0
    pending_amount = invoices.filter(is_paid=False).aggregate(
        total=Sum('total_amount'))['total'] or 0

    return render(request, 'customer/billing.html', {
        'invoices': invoices, 'total_spent': total_spent,
        'pending_amount': pending_amount,
    })

# ─── Feedback ────────────────────────────
@customer_required
def customer_feedback(request, pk):
    customer = get_object_or_404(Customer, user=request.user)
    job = get_object_or_404(ServiceJob, pk=pk, vehicle__customer=customer, status__in=['COMPLETED', 'DELIVERED'])
    try:
        if job.feedback:
            messages.info(request, 'Feedback already submitted for this job.')
            return redirect('customer_job_detail', pk=pk)
    except Feedback.DoesNotExist:
        pass
    if request.method == 'POST':
        Feedback.objects.create(
            job=job, customer=customer,
            rating=int(request.POST['rating']),
            comments=request.POST.get('comments', ''),
        )
        messages.success(request, 'Thank you for your feedback!')
        return redirect('customer_job_detail', pk=pk)
    return render(request, 'customer/feedback_form.html', {'job': job})

# ─── Reminders ───────────────────────────
@customer_required
def customer_reminders(request):
    customer = get_object_or_404(Customer, user=request.user)
    reminders = ServiceReminder.objects.filter(
        vehicle__customer=customer, is_dismissed=False
    ).select_related('vehicle').order_by('reminder_date')
    if request.method == 'POST':
        reminder = get_object_or_404(ServiceReminder, pk=request.POST['reminder_id'], vehicle__customer=customer)
        reminder.is_dismissed = True
        reminder.save()
        messages.success(request, 'Reminder dismissed.')
        return redirect('customer_reminders')
        return redirect('customer_reminders')
    
    notifications = request.user.notifications.all()
    return render(request, 'customer/reminders.html', {'reminders': reminders, 'notifications': notifications})
