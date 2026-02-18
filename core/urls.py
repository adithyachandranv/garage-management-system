from django.urls import path
from . import views

urlpatterns = [
    path('admin-panel/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    # Keep old dashboard URL for backward compat
    path('dashboard/', views.admin_dashboard, name='dashboard'),

    # Customers
    path('admin-panel/customers/', views.admin_customers_list, name='admin_customers_list'),
    path('admin-panel/customers/create/', views.admin_customer_create, name='admin_customer_create'),
    path('admin-panel/customers/<int:pk>/', views.admin_customer_detail, name='admin_customer_detail'),

    # Vehicles
    path('admin-panel/vehicles/create/', views.admin_vehicle_create, name='admin_vehicle_create'),

    # Jobs
    path('admin-panel/jobs/', views.admin_jobs_list, name='admin_jobs_list'),
    path('admin-panel/jobs/create/', views.admin_job_create, name='admin_job_create'),
    path('admin-panel/jobs/<int:pk>/', views.admin_job_detail, name='admin_job_detail'),
    path('admin-panel/jobs/<int:pk>/edit/', views.admin_job_edit, name='admin_job_edit'),
    path('admin-panel/jobs/<int:pk>/delete/', views.admin_job_delete, name='admin_job_delete'),

    # Mechanics
    path('admin-panel/mechanics/', views.admin_mechanics_list, name='admin_mechanics_list'),
    path('admin-panel/mechanics/create/', views.admin_mechanic_create, name='admin_mechanic_create'),

    # Inventory
    path('admin-panel/inventory/', views.admin_inventory_list, name='admin_inventory_list'),
    path('admin-panel/inventory/parts/create/', views.admin_part_create, name='admin_part_create'),
    path('admin-panel/inventory/<int:pk>/stock/', views.admin_stock_update, name='admin_stock_update'),

    # Billing
    path('admin-panel/billing/', views.admin_billing_list, name='admin_billing_list'),
    path('admin-panel/billing/create/', views.admin_invoice_create, name='admin_invoice_create'),
    path('admin-panel/billing/<int:pk>/', views.admin_invoice_detail, name='admin_invoice_detail'),

    # Approvals
    path('admin-panel/approvals/', views.admin_approvals_list, name='admin_approvals_list'),

    # Analytics
    path('admin-panel/analytics/', views.admin_analytics, name='admin_analytics'),
]
