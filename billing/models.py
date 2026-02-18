from django.db import models
from core.models import TimeStampedModel
from django.conf import settings

class Approval(TimeStampedModel):
    job = models.ForeignKey('jobs.ServiceJob', on_delete=models.CASCADE, related_name="approvals")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    repairs = models.ManyToManyField('repairs.RepairLog', related_name='approvals')
    estimated_cost_snapshot = models.DecimalField(max_digits=10, decimal_places=2)

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

class Invoice(TimeStampedModel):
    job = models.OneToOneField('jobs.ServiceJob', on_delete=models.CASCADE)
    labor_cost = models.DecimalField(max_digits=10, decimal_places=2)
    parts_cost = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)

class Payment(TimeStampedModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="payments")
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    transaction_reference = models.CharField(max_length=100, blank=True)

