from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.db.models import Sum
from decimal import Decimal
from django.utils import timezone
from django.contrib import messages
from .models import Invoice, Payment
from jobs.models import ServiceJob

def is_admin(user):
    return user.role == 'ADMIN'

@login_required
@user_passes_test(is_admin)
def create_invoice(request, job_id):
    job = get_object_or_404(ServiceJob, pk=job_id)
    
    # Check if invoice already exists
    if hasattr(job, 'invoice'):
        messages.info(request, "Invoice already exists for this job.")
        return redirect('invoice_detail', pk=job.invoice.pk)

    # Calculate Labor Cost (Sum of all APPROVED repair est costs)
    labor_cost = job.repairs.filter(is_approved=True).aggregate(total=Sum('estimated_cost'))['total'] or Decimal('0.00')
    
    # Calculate Parts Cost
    parts_cost = Decimal('0.00')
    # Use related_name 'jobpart_set' unless defined otherwise
    # Checking jobs/models.py earlier, JobPart has ForeignKey to ServiceJob. Default is jobpart_set.
    for job_part in job.jobpart_set.all():
        parts_cost += job_part.quantity * job_part.unit_price_snapshot
        
    # Calculate Tax (e.g. 10%)
    tax = (labor_cost + parts_cost) * Decimal('0.10')
    
    total_amount = labor_cost + parts_cost + tax
    
    invoice = Invoice.objects.create(
        job=job,
        labor_cost=labor_cost,
        parts_cost=parts_cost,
        tax=tax,
        total_amount=total_amount
    )
    
    messages.success(request, "Invoice generated successfully.")
    return redirect('invoice_detail', pk=invoice.pk)

@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    
    # Access Control
    if request.user.role != 'ADMIN':
        # Check if user is the customer for this job
        if invoice.job.vehicle.customer.user != request.user:
            raise PermissionDenied

    return render(request, 'billing/invoice_detail.html', {'invoice': invoice})

@login_required
def process_payment(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    
    if request.method == 'POST':
        # Simple mock payment
        Payment.objects.create(
            invoice=invoice,
            amount_paid=invoice.total_amount,
            payment_method='Credit Card',
            transaction_reference=f'TXN-{int(timezone.now().timestamp())}'
        )
        
        invoice.is_paid = True
        invoice.save()
        
        messages.success(request, f"Payment of ${invoice.total_amount} successful!")
        return redirect('invoice_detail', pk=pk)
    
    return redirect('invoice_detail', pk=pk)
