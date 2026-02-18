from django.db import models
from core.models import TimeStampedModel
from django.conf import settings

class Part(TimeStampedModel):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, unique=True, db_index=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Inventory(TimeStampedModel):
    part = models.OneToOneField(Part, on_delete=models.CASCADE)
    stock_quantity = models.IntegerField()
    low_stock_threshold = models.IntegerField(default=5)

class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
    ]

    part = models.ForeignKey(Part, on_delete=models.CASCADE)
    job = models.ForeignKey('jobs.ServiceJob', on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField()
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_TYPES)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.movement_type} - {self.part.name} ({self.quantity})"