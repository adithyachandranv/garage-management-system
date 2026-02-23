from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count
from accounts.decorators import mechanic_required
from .models import ServiceJob, JobActivityLog
from repairs.models import RepairLog
from billing.models import Approval
from notifications.utils import create_notification

# ─── Mechanic: My Jobs ──────────────────
@mechanic_required
def mechanic_jobs(request):
    jobs = ServiceJob.objects.filter(
        assigned_mechanic=request.user
    ).exclude(status__in=['DELIVERED', 'CANCELLED']).select_related(
        'vehicle__customer__user'
    ).order_by('-created_at')

    # Annotate each job with repair stats
    for j in jobs:
        j.repair_count = j.repairs.count()
        j.total_repair_cost = j.repairs.aggregate(total=Sum('estimated_cost'))['total'] or 0

    completed_jobs = ServiceJob.objects.filter(
        assigned_mechanic=request.user, status__in=['COMPLETED', 'DELIVERED']
    ).select_related('vehicle').order_by('-completed_at')[:10]

    # Stats for the mechanic
    total_completed = ServiceJob.objects.filter(
        assigned_mechanic=request.user, status__in=['COMPLETED', 'DELIVERED']
    ).count()

    return render(request, 'mechanic/jobs_list.html', {
        'jobs': jobs, 'completed_jobs': completed_jobs,
        'active_count': jobs.count(),
        'total_completed': total_completed,
    })

# ─── Mechanic: Job Detail ───────────────
@mechanic_required
def mechanic_job_detail(request, pk):
    job = get_object_or_404(
        ServiceJob.objects.select_related('vehicle__customer__user'),
        pk=pk, assigned_mechanic=request.user
    )
    repairs = job.repairs.order_by('-created_at')
    activity = job.activity_logs.select_related('performed_by').order_by('-timestamp')
    approvals = job.approvals.order_by('-created_at')
    total_repair_cost = sum(r.estimated_cost for r in repairs)
    return render(request, 'mechanic/job_detail.html', {
        'job': job, 'repairs': repairs, 'activity': activity,
        'approvals': approvals, 'total_repair_cost': total_repair_cost,
    })

# ─── Mechanic: Add Diagnosis / Repair ───
@mechanic_required
def mechanic_add_repair(request, pk):
    job = get_object_or_404(ServiceJob, pk=pk, assigned_mechanic=request.user)
    if request.method == 'POST':
        repair = RepairLog.objects.create(
            job=job,
            mechanic=request.user,
            diagnosis=request.POST['diagnosis'],
            work_done=request.POST.get('work_done', ''),
            estimated_cost=request.POST['estimated_cost'],
            image=request.FILES.get('image'),
        )
        JobActivityLog.objects.create(
            job=job, performed_by=request.user,
            action='Repair Log Added', remarks=f'Diagnosis: {repair.diagnosis[:50]}'
        )
        messages.success(request, 'Repair log added.')
        return redirect('mechanic_job_detail', pk=pk)
    return render(request, 'mechanic/repair_form.html', {'job': job})

# ─── Mechanic: Update Status ────────────
@mechanic_required
def mechanic_update_status(request, pk):
    job = get_object_or_404(ServiceJob, pk=pk, assigned_mechanic=request.user)
    if request.method == 'POST':
        new_status = request.POST['new_status']
        try:
            job.change_status(new_status, request.user)
            
            # Notify customer
            create_notification(
                recipient=job.vehicle.customer.user,
                title=f"Vehicle Status Update: {job.vehicle.registration_number}",
                message=f"Status changed to {new_status.replace('_', ' ').title()}",
                notification_type="job_update",
                related_job=job,
                link=f"/customer/jobs/{job.pk}/"
            )

            messages.success(request, f'Status updated to {new_status}.')
        except Exception as e:
            messages.error(request, str(e))
        return redirect('mechanic_job_detail', pk=pk)

    # Compute valid next transitions
    valid_transitions = ServiceJob.VALID_TRANSITIONS.get(job.status, [])
    return render(request, 'mechanic/update_status.html', {
        'job': job, 'valid_transitions': valid_transitions,
    })

# ─── Mechanic: Update Estimate ──────────
@mechanic_required
def mechanic_update_estimate(request, pk):
    job = get_object_or_404(ServiceJob, pk=pk, assigned_mechanic=request.user)
    if request.method == 'POST':
        est = request.POST.get('estimated_completion')
        if est:
            job.estimated_completion = est
            job.save()
            JobActivityLog.objects.create(
                job=job, performed_by=request.user,
                action='Estimate Updated', remarks=f'ETA: {est}'
            )
            messages.success(request, 'Estimated completion updated.')
        return redirect('mechanic_job_detail', pk=pk)
    return render(request, 'mechanic/update_estimate.html', {'job': job})

# ─── Mechanic: Request Money ────────────
@mechanic_required
def mechanic_request_money(request, pk):
    job = get_object_or_404(ServiceJob, pk=pk, assigned_mechanic=request.user)
    
    # Identify unapproved repairs
    unapproved_repairs = job.repairs.filter(is_approved=False)
    if not unapproved_repairs.exists():
         messages.info(request, "All repairs are already approved. Add a repair log first.")
         return redirect('mechanic_job_detail', pk=pk)

    total_cost = sum(r.estimated_cost for r in unapproved_repairs)

    if request.method == 'POST':
        description = request.POST.get('description', '')
        approval = Approval.objects.create(
            job=job,
            estimated_cost_snapshot=total_cost,
            status='PENDING',
            description=description,
        )
        approval.repairs.set(unapproved_repairs)
        
        try:
            job.change_status('WAITING_APPROVAL', request.user)
        except Exception:
            pass  # Status transition may not be valid from every state, but the money request is still created

        from jobs.models import JobActivityLog
        JobActivityLog.objects.create(
            job=job, performed_by=request.user,
            action='Money Requested',
            remarks=f'₹{total_cost} for {unapproved_repairs.count()} repair(s)'
        )

        messages.success(request, f'Money request of ₹{total_cost} sent to customer.')
        
        # Notify customer
        create_notification(
            recipient=job.vehicle.customer.user,
            title=f"Money Requested: {job.vehicle.registration_number}",
            message=f"Mechanic has requested ₹{total_cost} for repairs. Please review.",
            notification_type="money_request",
            related_job=job,
            link=f"/customer/jobs/{job.pk}/"
        )
        
        return redirect('mechanic_job_detail', pk=pk)
    
    return render(request, 'mechanic/request_money.html', {
        'job': job,
        'unapproved_repairs': unapproved_repairs,
        'total_cost': total_cost,
    })
