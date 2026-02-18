import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client, RequestFactory
from django.contrib.auth import get_user_model
from jobs.models import ServiceJob
from notifications.models import Notification
from customers.models import Customer, Vehicle
from billing.models import Approval

User = get_user_model()

def test_notifications():
    print("Setting up test data...")
    # Create Users
    admin_user, _ = User.objects.get_or_create(username='admin_notif', defaults={'role': 'ADMIN', 'is_superuser': True})
    if hasattr(admin_user, 'set_password'): admin_user.set_password('pass'); admin_user.save()
    
    mechanic_user, _ = User.objects.get_or_create(username='mech_notif', defaults={'role': 'MECHANIC'})
    if hasattr(mechanic_user, 'set_password'): mechanic_user.set_password('pass'); mechanic_user.save()
    
    cust_user, _ = User.objects.get_or_create(username='cust_notif', defaults={'role': 'CUSTOMER'})
    if hasattr(cust_user, 'set_password'): cust_user.set_password('pass'); cust_user.save()
    
    customer, _ = Customer.objects.get_or_create(user=cust_user, defaults={'address': 'Address'})
    
    # Create Vehicle
    vehicle, _ = Vehicle.objects.get_or_create(
        customer=customer, registration_number='NOTIF001', 
        defaults={'make': 'Test', 'model': 'Car', 'year': 2022}
    )
    
    # Create Job
    job, _ = ServiceJob.objects.get_or_create(
        vehicle=vehicle, status='RECEIVED', 
        defaults={'problem_description': 'Test Issue'}
    )
    
    c = Client()
    
    print("\n--- Test 1: Job Assignment Notification (Core) ---")
    c.force_login(admin_user)
    initial_count = Notification.objects.filter(recipient=mechanic_user).count()
    resp = c.post(f'/admin-panel/jobs/{job.pk}/', {
        'action': 'assign_mechanic',
        'mechanic': mechanic_user.pk
    }, follow=True)
    
    new_count = Notification.objects.filter(recipient=mechanic_user).count()
    if new_count > initial_count:
        print("PASS: Notification created for mechanic.")
        n = Notification.objects.filter(recipient=mechanic_user).first()
        print(f"  Title: {n.title}")
    else:
        print(f"FAIL: Notification not created. Resp code: {resp.status_code}")
        
    print("\n--- Test 2: Status Update Notification (Mechanic) ---")
    c.force_login(mechanic_user)
    # Refresh job
    job.refresh_from_db()
    
    initial_count = Notification.objects.filter(recipient=cust_user).count()
    resp = c.post(f'/mechanic/jobs/{job.pk}/update-status/', {
        'new_status': 'DIAGNOSING'
    }, follow=True)
    
    new_count = Notification.objects.filter(recipient=cust_user).count()
    if new_count > initial_count:
        print("PASS: Notification created for customer (Status Update).")
        n = Notification.objects.filter(recipient=cust_user, notification_type='job_update').first()
        print(f"  Title: {n.title}")
    else:
        print(f"FAIL: Notification not created. Resp code: {resp.status_code}")

    print("\n--- Test 3: Approval Request Notification (Mechanic) ---")
    initial_count = Notification.objects.filter(recipient=cust_user).count()
    # Ensure job is in a state allowing approval request? The view might not check strict state for this test?
    resp = c.post(f'/mechanic/jobs/{job.pk}/request-approval/', {}, follow=True)
    
    new_count = Notification.objects.filter(recipient=cust_user).count()
    if new_count > initial_count: # Wait, logic creates approval if not exists?
        # Check specific type
        n = Notification.objects.filter(recipient=cust_user, notification_type='approval_request').first()
        if n:
            print("PASS: Notification created for customer (Approval Request).")
            print(f"  Title: {n.title}")
        else:
             print("FAIL: Notification created but not approval_request?")
    else:
        print(f"FAIL: Notification not created. Resp code: {resp.status_code}")

    print("\n--- Test 4: Approval Response Notification (Customer) ---")
    c.force_login(cust_user)
    # Need an approval object
    approval = Approval.objects.filter(job=job).first()
    if not approval:
        print("SKIPPING: No approval object found to approve.")
    else:
        initial_count = Notification.objects.filter(recipient=mechanic_user).count()
        resp = c.post(f'/customer/approve-repair/{approval.pk}/', {
            'decision': 'APPROVED'
        }, follow=True)
        
        new_count = Notification.objects.filter(recipient=mechanic_user).count()
        if new_count > initial_count:
             print("PASS: Notification created for mechanic (Approval Response).")
             n = Notification.objects.filter(recipient=mechanic_user, notification_type='approval_response').first()
             print(f"  Title: {n.title}")
        else:
             print(f"FAIL: Notification not created. Resp code: {resp.status_code}")
             
    # Cleanup
    print("\nCleaning up...")
    # Notification.objects.all().delete()
    # User.objects.filter(username__in=['admin_notif', 'mech_notif', 'cust_notif']).delete()
    
if __name__ == '__main__':
    test_notifications()
