from django.urls import path
from . import views

urlpatterns = [
    path('customer/dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('customer/vehicles/', views.customer_vehicles, name='customer_vehicles'),
    path('customer/vehicles/<int:pk>/', views.customer_vehicle_detail, name='customer_vehicle_detail'),
    path('customer/jobs/<int:pk>/', views.customer_job_detail, name='customer_job_detail'),
    path('customer/approve/<int:pk>/', views.customer_approve_repair, name='customer_approve_repair'),
    path('customer/billing/', views.customer_billing, name='customer_billing'),
    path('customer/jobs/<int:pk>/feedback/', views.customer_feedback, name='customer_feedback'),
    path('customer/reminders/', views.customer_reminders, name='customer_reminders'),
]
