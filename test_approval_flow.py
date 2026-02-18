
import os
import django
from decimal import Decimal

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.conf import settings
# Mock allowed hosts for test client
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS += ['testserver']

from django.contrib.auth import get_user_model
from django.test import Client
from jobs.models import ServiceJob, JobPart
from customers.models import Customer, Vehicle
from billing.models import Approval
from inventory.models import Part, Inventory
from repairs.models import RepairLog

User = get_user_model()

def test_approval_flow():
    # Setup Data
    print("Setting up test data...")
    password = 'password123'
    
    mechanic, _ = User.objects.get_or_create(username='mech_approval', defaults={'email': 'mech@example.com', 'role': 'MECHANIC'})
    if _: mechanic.set_password(password); mechanic.save()
    
    customer_user, _ = User.objects.get_or_create(username='cust_approval', defaults={'email': 'cust@example.com', 'role': 'CUSTOMER', 'phone': '555-0202'})
    if _: customer_user.set_password(password); customer_user.save()
    
    customer, _ = Customer.objects.get_or_create(user=customer_user, defaults={'address': '456 Test Ave'})
    vehicle, _ = Vehicle.objects.get_or_create(customer=customer, registration_number='APP-99', defaults={'make': 'Honda', 'model': 'Civic', 'year': 2018})
    
    # Create Job
    job = ServiceJob.objects.create(vehicle=vehicle, problem_description="Engine noise", status='DIAGNOSING', assigned_mechanic=mechanic)
    print(f"Job Created: {job.status}")

    # Add Repair Estimate
    RepairLog.objects.create(job=job, diagnosis="Replace Spark Plugs", estimated_cost=Decimal('100.00'))

    # Client for Mechanic
    mc = Client()
    mc.force_login(mechanic)
    
    # 1. Mechanic Requests Approval
    print("\n[1] Mechanic Requesting Approval...")
    response = mc.post(f'/mechanic/jobs/{job.pk}/approval/')
    job.refresh_from_db()
    if job.status != 'WAITING_APPROVAL':
        print(f"FAIL: Job status is {job.status}, expected WAITING_APPROVAL")
        print(f"Response Status: {response.status_code}")
        # Print messages if any
        messages = list(response.context['messages']) if response.context and 'messages' in response.context else []
        for m in messages:
             print(f"Message: {m}")
        if response.status_code != 302:
             print(f"Content: {response.content.decode()}")
        return
    print(f"PASS: Job status transition to {job.status}")
    
    # Client for Customer
    cc = Client()
    cc.force_login(customer_user)
    
    # 2. Customer Approves
    print("\n[2] Customer Approving...")
    approval = job.approvals.filter(status='PENDING').first()
    if not approval:
        print("FAIL: No pending approval found")
        return
        
    response = cc.post(f'/customer/approve/{approval.pk}/', {'decision': 'APPROVED'})
    job.refresh_from_db()
    approval.refresh_from_db()
    
    if job.status != 'IN_PROGRESS':
        print(f"FAIL: Job status is {job.status}, expected IN_PROGRESS")
        return
    if approval.status != 'APPROVED':
        print(f"FAIL: Approval status is {approval.status}")
        return
        
    # Verify repairs are approved
    for repair in approval.repairs.all():
        if not repair.is_approved:
            print(f"FAIL: Repair {repair.pk} not marked as approved")
            return
            
    print(f"PASS: Job status transition to {job.status}")
    print("PASS: Repairs marked as approved")
    
    # 3. Mechanic Adds More Repairs (e.g. found another issue)
    print("\n[3] Mechanic Adding More Repairs...")
    r2 = RepairLog.objects.create(job=job, diagnosis="Replace Coil Pack", estimated_cost=Decimal('50.00'))
    if r2.is_approved:
        print("FAIL: New repair should be unapproved by default")
        return

    # 4. Mechanic Requests Approval AGAIN (IN_PROGRESS -> WAITING_APPROVAL)
    print("\n[4] Mechanic Requesting Approval AGAIN...")
    response = mc.post(f'/mechanic/jobs/{job.pk}/approval/')
    
    job.refresh_from_db()
    if job.status != 'WAITING_APPROVAL':
        print(f"FAIL: Job status is {job.status}, expected WAITING_APPROVAL (Transition from IN_PROGRESS)")
        # Debug why
        try:
            job.change_status('WAITING_APPROVAL', mechanic)
        except Exception as e:
            print(f"Transition Error: {e}")
        return
    print(f"PASS: Job status transition to {job.status} (Re-approval)")
    
    # 5. Customer Approves Again
    print("\n[5] Customer Approving Again...")
    approval_2 = job.approvals.filter(status='PENDING').order_by('-created_at').first()
    if approval_2.pk == approval.pk:
        print("FAIL: Did not create new approval object")
        return
        
    # Verify approval_2 only contains the new repair
    if not approval_2.repairs.filter(pk=r2.pk).exists():
        print("FAIL: Second approval does not contain the new repair")
        return
    if approval_2.repairs.count() != 1:
        print(f"FAIL: Second approval should have 1 repair, has {approval_2.repairs.count()}")
        return

    response = cc.post(f'/customer/approve/{approval_2.pk}/', {'decision': 'APPROVED'})
    job.refresh_from_db()
    r2.refresh_from_db()
    
    if job.status != 'IN_PROGRESS':
        print(f"FAIL: Job status is {job.status}, expected IN_PROGRESS")
        return
        
    if not r2.is_approved:
        print("FAIL: Subsequent repair was not marked as approved")
        return
        
    print(f"PASS: Job status transition to {job.status}")
    print("PASS: Subsequent repair approved successfully")

    print("\nSUCCESS: Multi-approval flow verified.")

if __name__ == '__main__':
    test_approval_flow()
