from django.db import models
from core.models import TimeStampedModel, SoftDeleteModel
from django.conf import settings

class Customer(TimeStampedModel, SoftDeleteModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    address = models.TextField()

    def __str__(self):
        return self.user.username

class Vehicle(TimeStampedModel, SoftDeleteModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="vehicles")
    registration_number = models.CharField(max_length=50, unique=True, db_index=True)
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.IntegerField()
    vin = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.registration_number

class Warranty(TimeStampedModel):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="warranties")
    warranty_type = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    coverage_details = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.warranty_type} - {self.vehicle.registration_number}"

class Feedback(TimeStampedModel):
    job = models.OneToOneField('jobs.ServiceJob', on_delete=models.CASCADE, related_name='feedback')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='feedbacks')
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comments = models.TextField(blank=True)

    def __str__(self):
        return f"Feedback for Job #{self.job.id} - {self.rating}★"

class ServiceReminder(TimeStampedModel):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='reminders')
    service_type = models.CharField(max_length=100)
    reminder_date = models.DateField()
    notes = models.TextField(blank=True)
    is_dismissed = models.BooleanField(default=False)

    def __str__(self):
        return f"Reminder: {self.vehicle.registration_number} - {self.service_type}"

