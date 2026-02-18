from django.urls import path
from . import views

urlpatterns = [
    path('setup/<int:job_id>/', views.create_invoice, name='create_invoice'),
    path('invoice/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoice/<int:pk>/pay/', views.process_payment, name='process_payment'),
]
