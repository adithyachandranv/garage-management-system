from django.db import models
from core.models import TimeStampedModel
from django.conf import settings

class RepairLog(TimeStampedModel):
    job = models.ForeignKey('jobs.ServiceJob', on_delete=models.CASCADE, related_name="repairs")
    mechanic = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    diagnosis = models.TextField()
    work_done = models.TextField(blank=True)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2)
    is_approved = models.BooleanField(default=False)
    image = models.ImageField(upload_to='repair_images/', blank=True, null=True)
