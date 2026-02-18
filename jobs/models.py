from django.db import models
from core.models import TimeStampedModel, SoftDeleteModel
from django.conf import settings
from django.core.exceptions import ValidationError


class ServiceJob(TimeStampedModel, SoftDeleteModel):

    STATUS_CHOICES = [
        ('RECEIVED', 'Received'),
        ('DIAGNOSING', 'Diagnosing'),
        ('WAITING_APPROVAL', 'Waiting Approval'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]

    vehicle = models.ForeignKey('customers.Vehicle', on_delete=models.CASCADE, related_name="jobs")
    assigned_mechanic = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'role': 'MECHANIC'}
    )

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='RECEIVED')
    problem_description = models.TextField()
    estimated_completion = models.DateTimeField(null=True, blank=True)
    priority = models.IntegerField(default=1)

    completed_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Job #{self.id} - {self.vehicle.registration_number}"

    VALID_TRANSITIONS = {
        'RECEIVED': ['DIAGNOSING', 'CANCELLED'],
    'DIAGNOSING': ['WAITING_APPROVAL', 'CANCELLED'],
    'WAITING_APPROVAL': ['IN_PROGRESS', 'CANCELLED'],
    'IN_PROGRESS': ['COMPLETED', 'CANCELLED', 'WAITING_APPROVAL'],
    'COMPLETED': ['DELIVERED'],
    'DELIVERED': [],
    'CANCELLED': [],   
}

    def change_status(self, new_status, user):
        from django.core.exceptions import ValidationError
        from django.utils import timezone
        from jobs.models import JobActivityLog

        if new_status not in self.VALID_TRANSITIONS[self.status]:
            raise ValidationError(
                f"Invalid transition from {self.status} to {new_status}"
            )

        old_status = self.status

        if new_status == 'COMPLETED':
            self.completed_at = timezone.now()

        if new_status == 'DELIVERED':
            self.delivered_at = timezone.now()

        self.status = new_status
        self.save()

        JobActivityLog.objects.create(
            job=self,
            performed_by=user,
            action="Status Changed",
            old_status=old_status,
            new_status=new_status,
        )

class JobActivityLog(models.Model):
    job = models.ForeignKey(ServiceJob, on_delete=models.CASCADE, related_name="activity_logs")
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.TextField()
    old_status = models.CharField(max_length=30, blank=True)
    new_status = models.CharField(max_length=30, blank=True)
    remarks = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

class JobPart(models.Model):
    job = models.ForeignKey(ServiceJob, on_delete=models.CASCADE)
    part = models.ForeignKey('inventory.Part', on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    unit_price_snapshot = models.DecimalField(max_digits=10, decimal_places=2)
