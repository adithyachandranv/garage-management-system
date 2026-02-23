from django.urls import path
from jobs import views as job_views

urlpatterns = [
    # Mechanic portal
    path('mechanic/jobs/', job_views.mechanic_jobs, name='mechanic_jobs'),
    path('mechanic/jobs/<int:pk>/', job_views.mechanic_job_detail, name='mechanic_job_detail'),
    path('mechanic/jobs/<int:pk>/repair/', job_views.mechanic_add_repair, name='mechanic_add_repair'),
    path('mechanic/jobs/<int:pk>/status/', job_views.mechanic_update_status, name='mechanic_update_status'),
    path('mechanic/jobs/<int:pk>/estimate/', job_views.mechanic_update_estimate, name='mechanic_update_estimate'),
    path('mechanic/jobs/<int:pk>/request-money/', job_views.mechanic_request_money, name='mechanic_request_money'),
]
