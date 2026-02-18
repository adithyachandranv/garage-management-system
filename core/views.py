from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Sum, F, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from accounts.decorators import admin_required, login_required
from jobs.models import ServiceJob, JobActivityLog, JobPart
from billing.models import Invoice, Approval, Payment
from inventory.models import Inventory, Part, StockMovement
from customers.models import Customer, Vehicle, Warranty
from notifications.utils import create_notification
from repairs.models import RepairLog
from django.contrib.auth import get_user_model

User = get_user_model()

# ─── Admin Dashboard ──────────────────────
@admin_required
def admin_dashboard(request):
    active_jobs_count = ServiceJob.objects.filter(
        status__in=['RECEIVED', 'DIAGNOSING', 'WAITING_APPROVAL', 'IN_PROGRESS']
    ).count()

    current_month = timezone.now().month
    monthly_revenue = Invoice.objects.filter(
        is_paid=True, created_at__month=current_month
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    pending_approvals_count = Approval.objects.filter(status='PENDING').count()

    low_stock_count = Inventory.objects.filter(
        stock_quantity__lte=F('low_stock_threshold')
    ).count()

    recent_activity = JobActivityLog.objects.select_related(
        'job', 'performed_by'
    ).order_by('-timestamp')[:10]

    job_status_data = ServiceJob.objects.values('status').annotate(count=Count('status'))

    thirty_days_ago = timezone.now() - timedelta(days=30)
    revenue_trend = Invoice.objects.filter(
        is_paid=True, created_at__gte=thirty_days_ago
    ).annotate(day=TruncDate('created_at')).values('day').annotate(
        daily_total=Sum('total_amount')
    ).order_by('day')

    total_customers = Customer.objects.count()
    total_mechanics = User.objects.filter(role='MECHANIC').count()
    total_jobs = ServiceJob.objects.count()

    context = {
        'active_jobs_count': active_jobs_count,
        'monthly_revenue': monthly_revenue,
        'pending_approvals_count': pending_approvals_count,
        'low_stock_count': low_stock_count,
        'recent_activity': recent_activity,
        'job_status_data': list(job_status_data),
        'revenue_trend': list(revenue_trend),
        'total_customers': total_customers,
        'total_mechanics': total_mechanics,
        'total_jobs': total_jobs,
    }
    return render(request, 'admin_portal/dashboard.html', context)

# ─── Customer Management ──────────────────
@admin_required
def admin_customers_list(request):
    q = request.GET.get('q', '')
    customers = Customer.objects.select_related('user').filter(is_active=True)
    if q:
        customers = customers.filter(
            Q(user__username__icontains=q) | Q(user__phone__icontains=q) | Q(address__icontains=q)
        )
    return render(request, 'admin_portal/customers_list.html', {'customers': customers, 'q': q})

@admin_required
def admin_customer_create(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        phone = request.POST.get('phone', '')
        address = request.POST.get('address', '')
        email = request.POST.get('email', '')
        user = User.objects.create_user(username=username, password=password, role='CUSTOMER', phone=phone, email=email)
        Customer.objects.create(user=user, address=address)
        messages.success(request, f'Customer "{username}" created successfully.')
        return redirect('admin_customers_list')
    return render(request, 'admin_portal/customer_form.html')

@admin_required
def admin_customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    vehicles = customer.vehicles.filter(is_active=True)
    jobs = ServiceJob.objects.filter(vehicle__customer=customer).order_by('-created_at')
    return render(request, 'admin_portal/customer_detail.html', {
        'customer': customer, 'vehicles': vehicles, 'jobs': jobs
    })

# ─── Vehicle Management ──────────────────
@admin_required
def admin_vehicle_create(request):
    customers = Customer.objects.select_related('user').filter(is_active=True)
    if request.method == 'POST':
        customer = get_object_or_404(Customer, pk=request.POST['customer'])
        reg_number = request.POST['registration_number']
        if Vehicle.objects.filter(registration_number=reg_number).exists():
            messages.error(request, f'Vehicle with registration number {reg_number} already exists.')
            return redirect('admin_customer_detail', pk=customer.pk)

        Vehicle.objects.create(
            customer=customer,
            registration_number=reg_number,
            make=request.POST['make'],
            model=request.POST['model'],
            year=request.POST['year'],
            vin=request.POST.get('vin', ''),
        )
        messages.success(request, 'Vehicle added successfully.')
        return redirect('admin_customer_detail', pk=customer.pk)
    return render(request, 'admin_portal/vehicle_form.html', {'customers': customers})

# ─── Job Management ──────────────────────
@admin_required
def admin_jobs_list(request):
    status_filter = request.GET.get('status', '')
    jobs = ServiceJob.objects.select_related('vehicle__customer__user', 'assigned_mechanic').order_by('-created_at')
    if status_filter:
        jobs = jobs.filter(status=status_filter)
    statuses = ServiceJob.STATUS_CHOICES
    return render(request, 'admin_portal/jobs_list.html', {
        'jobs': jobs, 'statuses': statuses, 'current_status': status_filter
    })

@admin_required
def admin_job_create(request):
    vehicles = Vehicle.objects.select_related('customer__user').filter(is_active=True)
    mechanics = User.objects.filter(role='MECHANIC')
    if request.method == 'POST':
        job = ServiceJob.objects.create(
            vehicle_id=request.POST['vehicle'],
            assigned_mechanic_id=request.POST.get('mechanic') or None,
            problem_description=request.POST['problem_description'],
            priority=request.POST.get('priority', 1),
        )
        JobActivityLog.objects.create(job=job, performed_by=request.user, action='Job Created', new_status='RECEIVED')
        messages.success(request, f'Job #{job.id} created successfully.')
        return redirect('admin_jobs_list')
    return render(request, 'admin_portal/job_form.html', {'vehicles': vehicles, 'mechanics': mechanics})

@admin_required
def admin_job_edit(request, pk):
    job = get_object_or_404(ServiceJob, pk=pk)
    mechanics = User.objects.filter(role='MECHANIC')
    if request.method == 'POST':
        job.problem_description = request.POST['problem_description']
        job.priority = request.POST.get('priority', 1)
        
        # Handle mechanic change
        new_mechanic_id = request.POST.get('mechanic')
        if new_mechanic_id:
             if job.assigned_mechanic_id != int(new_mechanic_id):
                 job.assigned_mechanic_id = new_mechanic_id
                 # Notify if changed could be added here
        else:
            job.assigned_mechanic = None

        job.save()
        messages.success(request, 'Job updated successfully.')
        return redirect('admin_job_detail', pk=pk)
    
    return render(request, 'admin_portal/job_form_edit.html', {'job': job, 'mechanics': mechanics})

@admin_required
def admin_job_delete(request, pk):
    job = get_object_or_404(ServiceJob, pk=pk)
    if request.method == 'POST':
        job.delete()
        messages.success(request, 'Job deleted successfully.')
        return redirect('admin_jobs_list')
    return render(request, 'admin_portal/job_confirm_delete.html', {'job': job})

@admin_required
def admin_job_detail(request, pk):
    job = get_object_or_404(ServiceJob.objects.select_related('vehicle__customer__user', 'assigned_mechanic'), pk=pk)
    activity = job.activity_logs.select_related('performed_by').order_by('-timestamp')
    repairs = job.repairs.select_related('mechanic').order_by('-created_at')
    approvals = job.approvals.order_by('-created_at')
    parts = JobPart.objects.filter(job=job).select_related('part')
    mechanics = User.objects.filter(role='MECHANIC')
    
    try:
        invoice = job.invoice
    except Exception:
        invoice = None

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'change_status':
            new_status = request.POST['new_status']
            try:
                job.change_status(new_status, request.user)
                messages.success(request, f'Status changed to {new_status}.')
            except Exception as e:
                messages.error(request, str(e))
        elif action == 'assign_mechanic':
            job.assigned_mechanic_id = request.POST['mechanic']
            job.save()
            
            # Notify mechanic
            try:
                mechanic = User.objects.get(pk=request.POST['mechanic'])
                create_notification(
                    recipient=mechanic,
                    title=f"New Job Assigned: {job.vehicle.registration_number}",
                    message=f"You have been assigned to job #{job.pk} for {job.vehicle.make} {job.vehicle.model}.",
                    notification_type="job_assignment",
                    related_job=job,
                    link=f"/mechanic/jobs/{job.pk}/" 
                )
            except User.DoesNotExist:
                pass

            messages.success(request, 'Mechanic assigned.')
        return redirect('admin_job_detail', pk=pk)

    return render(request, 'admin_portal/job_detail.html', {
        'job': job, 'activity': activity, 'repairs': repairs,
        'approvals': approvals, 'parts': parts, 'mechanics': mechanics,
        'invoice': invoice
    })

# ─── Mechanic Management ────────────────
@admin_required
def admin_mechanics_list(request):
    mechanics = User.objects.filter(role='MECHANIC')
    for m in mechanics:
        m.active_jobs = ServiceJob.objects.filter(assigned_mechanic=m, status__in=['DIAGNOSING', 'IN_PROGRESS']).count()
    return render(request, 'admin_portal/mechanics_list.html', {'mechanics': mechanics})

@admin_required
def admin_mechanic_create(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        phone = request.POST.get('phone', '')
        email = request.POST.get('email', '')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        User.objects.create_user(
            username=username, password=password, role='MECHANIC',
            phone=phone, email=email, first_name=first_name, last_name=last_name
        )
        messages.success(request, f'Mechanic "{username}" created.')
        return redirect('admin_mechanics_list')
    return render(request, 'admin_portal/mechanic_form.html')

# ─── Inventory Management ────────────────
@admin_required
def admin_inventory_list(request):
    inventory = Inventory.objects.select_related('part').order_by('part__name')
    low_stock = inventory.filter(stock_quantity__lte=F('low_stock_threshold'))
    return render(request, 'admin_portal/inventory_list.html', {
        'inventory': inventory, 'low_stock': low_stock,
    })

@admin_required
def admin_part_create(request):
    if request.method == 'POST':
        part = Part.objects.create(
            name=request.POST['name'],
            sku=request.POST['sku'],
            price=request.POST['price'],
            description=request.POST.get('description', ''),
        )
        Inventory.objects.create(
            part=part,
            stock_quantity=int(request.POST.get('stock_quantity', 0)),
            low_stock_threshold=int(request.POST.get('low_stock_threshold', 5)),
        )
        messages.success(request, f'Part "{part.name}" added.')
        return redirect('admin_inventory_list')
    return render(request, 'admin_portal/part_form.html')

@admin_required
def admin_stock_update(request, pk):
    inv = get_object_or_404(Inventory, pk=pk)
    if request.method == 'POST':
        qty = int(request.POST['quantity'])
        move_type = request.POST['movement_type']
        StockMovement.objects.create(
            part=inv.part, quantity=qty, movement_type=move_type, performed_by=request.user
        )
        if move_type == 'IN':
            inv.stock_quantity += qty
        else:
            inv.stock_quantity -= qty
        inv.save()
        messages.success(request, f'Stock updated: {move_type} {qty} x {inv.part.name}')
        return redirect('admin_inventory_list')
    return render(request, 'admin_portal/stock_update.html', {'inventory': inv})

# ─── Billing & Invoices ─────────────────
@admin_required
def admin_billing_list(request):
    invoices = Invoice.objects.select_related('job__vehicle__customer__user').order_by('-created_at')
    return render(request, 'admin_portal/billing_list.html', {'invoices': invoices})

@admin_required
def admin_invoice_create(request):
    completed_jobs = ServiceJob.objects.filter(status='COMPLETED').exclude(invoice__isnull=False)
    if request.method == 'POST':
        job = get_object_or_404(ServiceJob, pk=request.POST['job'])
        parts_cost = sum(jp.quantity * jp.unit_price_snapshot for jp in JobPart.objects.filter(job=job))
        labor_cost = float(request.POST['labor_cost'])
        tax = float(request.POST.get('tax', 0))
        discount = float(request.POST.get('discount', 0))
        total = labor_cost + float(parts_cost) + tax - discount
        Invoice.objects.create(
            job=job, labor_cost=labor_cost, parts_cost=parts_cost,
            tax=tax, discount=discount, total_amount=total
        )
        messages.success(request, f'Invoice for Job #{job.id} created.')
        return redirect('admin_billing_list')
    return render(request, 'admin_portal/invoice_form.html', {'completed_jobs': completed_jobs})

@admin_required
def admin_invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice.objects.select_related('job__vehicle__customer__user'), pk=pk)
    payments = invoice.payments.all().order_by('-created_at')
    parts = JobPart.objects.filter(job=invoice.job).select_related('part')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_payment':
            Payment.objects.create(
                invoice=invoice,
                amount_paid=request.POST['amount_paid'],
                payment_method=request.POST['payment_method'],
                transaction_reference=request.POST.get('transaction_reference', ''),
            )
            total_paid = invoice.payments.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
            if total_paid >= invoice.total_amount:
                invoice.is_paid = True
                invoice.save()
            messages.success(request, 'Payment recorded.')
        elif action == 'mark_paid':
            invoice.is_paid = True
            invoice.save()
            messages.success(request, 'Invoice marked as paid.')
        return redirect('admin_invoice_detail', pk=pk)

    return render(request, 'admin_portal/invoice_detail.html', {
        'invoice': invoice, 'payments': payments, 'parts': parts,
    })

# ─── Approvals ───────────────────────────
@admin_required
def admin_approvals_list(request):
    approvals = Approval.objects.select_related('job__vehicle__customer__user', 'approved_by').order_by('-created_at')
    if request.method == 'POST':
        approval = get_object_or_404(Approval, pk=request.POST['approval_id'])
        approval.status = request.POST['decision']
        approval.approved_by = request.user
        approval.save()
        if approval.status == 'APPROVED':
            try:
                approval.job.change_status('IN_PROGRESS', request.user)
            except Exception:
                pass
        messages.success(request, f'Approval {approval.status.lower()}.')
        return redirect('admin_approvals_list')
    return render(request, 'admin_portal/approvals_list.html', {'approvals': approvals})

# ─── Analytics ───────────────────────────
@admin_required
def admin_analytics(request):
    thirty_days_ago = timezone.now() - timedelta(days=30)

    revenue_trend = Invoice.objects.filter(
        is_paid=True, created_at__gte=thirty_days_ago
    ).annotate(day=TruncDate('created_at')).values('day').annotate(
        daily_total=Sum('total_amount')
    ).order_by('day')

    total_revenue = Invoice.objects.filter(is_paid=True).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    monthly_revenue = Invoice.objects.filter(
        is_paid=True, created_at__month=timezone.now().month
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    jobs_by_status = ServiceJob.objects.values('status').annotate(count=Count('id'))
    mechanic_workload = User.objects.filter(role='MECHANIC').annotate(
        active_jobs=Count('servicejob', filter=Q(servicejob__status__in=['DIAGNOSING', 'IN_PROGRESS']))
    ).order_by('-active_jobs')

    low_stock_items = Inventory.objects.filter(
        stock_quantity__lte=F('low_stock_threshold')
    ).select_related('part')

    return render(request, 'admin_portal/analytics.html', {
        'revenue_trend': list(revenue_trend),
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue,
        'jobs_by_status': list(jobs_by_status),
        'mechanic_workload': mechanic_workload,
        'low_stock_items': low_stock_items,
    })
