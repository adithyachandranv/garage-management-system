from django.contrib.auth.models import AbstractUser
from django.db import models
from core.models import TimeStampedModel

class User(AbstractUser, TimeStampedModel):

    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('MANAGER', 'Manager'),
        ('MECHANIC', 'Mechanic'),
        ('CUSTOMER', 'Customer'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"
