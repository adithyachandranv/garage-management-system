import os
import django
from decimal import Decimal

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.conf import settings
settings.ALLOWED_HOSTS += ['testserver']

from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory
from jobs.models import ServiceJob, JobPart
from repairs.models import RepairLog
from inventory.models import Part
from billing.models import Invoice, Payment
from billing.views import create_invoice, process_payment
from customers.models import Customer, Vehicle

User = get_user_model()

def run_test():
    # Setup
    print("Setting up test data...")
    password = 'password123'
    admin, _ = User.objects.get_or_create(username='admin_billing', defaults={'email': 'admin@example.com', 'role': 'ADMIN'})
    admin.set_password(password)
    admin.role = 'ADMIN' # Ensure role is correct
    admin.save()
    
    customer_user, _ = User.objects.get_or_create(username='customer_billing', defaults={'email': 'cust@example.com', 'role': 'CUSTOMER', 'phone': '555-0101'})
    if _: customer_user.set_password('password123'); customer_user.save()

    customer, _ = Customer.objects.get_or_create(user=customer_user, defaults={'address': '123 Test Lane'})
    vehicle, _ = Vehicle.objects.get_or_create(customer=customer, registration_number='BILL-01', defaults={'make': 'Toyota', 'model': 'Camry', 'year': 2020})
    
    # Create Job
    job = ServiceJob.objects.create(vehicle=vehicle, problem_description="Brake issue", status='COMPLETED')
    
    # Add Repairs (Labor)
    r1 = RepairLog.objects.create(job=job, diagnosis="Worn pads", estimated_cost=Decimal('50.00'), is_approved=True) # $50 Labor (Approved)
    r2 = RepairLog.objects.create(job=job, diagnosis="Rotors resurface", estimated_cost=Decimal('100.00'), is_approved=True) # $100 Labor (Approved)
    
    # Add an UNAPPROVED repair (Should be ignored in invoice)
    r3 = RepairLog.objects.create(job=job, diagnosis="Optional detailing", estimated_cost=Decimal('200.00'), is_approved=False)
    
    # Total Labor = 150.00 (Only approved)
    
    # Add Parts (Parts are currently billed regardless of approval in this simple model, 
    # but let's assume parts usage implies approval or we only care about labor approval logic for now as per user request)
    part, _ = Part.objects.get_or_create(sku="BP-001", defaults={'name': "Brake Pad", 'price': Decimal('25.00')})
    # Ensure inventory exists
    from inventory.models import Inventory
    Inventory.objects.get_or_create(part=part, defaults={'stock_quantity': 10})
    
    JobPart.objects.create(job=job, part=part, quantity=2, unit_price_snapshot=Decimal('25.00')) # $50 Parts
    # Total Parts = 50.00
    
    # Expected Totals
    # Labor: 150.00 (50 + 100)
    # Parts: 50.00
    # Tax: (150+50) * 0.10 = 20.00
    # Total: 220.00
    
    print("Test 1: Create Invoice")
    factory = RequestFactory()
    request = factory.get(f'/billing/setup/{job.pk}/')
    request.user = admin
    
    # We can't easily call view directly with redirect unless we mock messages/etc, 
    # but create_invoice view is simple. Let's try Client.
    c = Client()
    c.force_login(admin)
    response = c.get(f'/billing/setup/{job.pk}/', follow=True)
    
    # Check if invoice created
    invoice = Invoice.objects.filter(job=job).first()
    if not invoice:
        print(f"FAIL: Invoice not created. Status: {response.status_code}")
        if response.status_code != 302:
            print(f"Content: {response.content.decode()}")
        return
        
    print(f"Invoice Created: #{invoice.pk}")
    print(f"Labor: {invoice.labor_cost} (Expected 150.00)")
    print(f"Parts: {invoice.parts_cost} (Expected 50.00)")
    print(f"Tax: {invoice.tax} (Expected 20.00)")
    print(f"Total: {invoice.total_amount} (Expected 220.00)")
    
    if invoice.total_amount == Decimal('220.00'):
        print("PASS: Invoice totals matching")
    else:
        print("FAIL: Invoice totals mismatch")
        
    print("\nTest 2: Process Payment")
    payment_url = f'/billing/invoice/{invoice.pk}/pay/'
    response = c.post(payment_url, follow=True)
    
    invoice.refresh_from_db()
    if invoice.is_paid:
        print("PASS: Invoice marked as paid")
    else:
        print("FAIL: Invoice not paid")
        
    payment = Payment.objects.filter(invoice=invoice).first()
    if payment and payment.amount_paid == Decimal('220.00'):
        print("PASS: Payment record created")
    else:
        print("FAIL: Payment record missing or incorrect")

if __name__ == '__main__':
    try:
        run_test()
    except Exception as e:
        print(f"Error: {e}")
