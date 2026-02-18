import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from django.test import Client
from accounts.models import User
from customers.models import Customer

c = Client(SERVER_NAME='localhost')
all_ok = True

def check(name, status, expected, url=None):
    global all_ok
    ok = status == expected
    if not ok:
        all_ok = False
    mark = 'OK' if ok else 'FAIL'
    extra = f' -> {url}' if url else ''
    print(f'  [{mark}] {name}: {status}{extra} (expected {expected})')

# 1. Root URL redirects to login
r = c.get('/', SERVER_NAME='localhost')
check('Root (guest)', r.status_code, 302, getattr(r, 'url', None))

# 2. Login page loads
r = c.get('/accounts/login/', SERVER_NAME='localhost')
check('Login page', r.status_code, 200)

# 3. Signup page loads
r = c.get('/accounts/signup/', SERVER_NAME='localhost')
check('Signup page', r.status_code, 200)

# 4. Signup as Customer
r = c.post('/accounts/signup/', {
    'username': 'test_cust_su', 'password': 'testpass123',
    'confirm_password': 'testpass123', 'role': 'CUSTOMER',
    'email': 'tcsu@ex.com', 'phone': '1111', 'address': '123 St',
    'first_name': 'Test', 'last_name': 'Cust',
}, SERVER_NAME='localhost')
check('Signup Customer', r.status_code, 302, getattr(r, 'url', None))
cu = User.objects.filter(username='test_cust_su').first()
cr = Customer.objects.filter(user=cu).first() if cu else None
print(f'    User: {cu is not None} role={cu.role if cu else "?"}, Customer: {cr is not None}')
c.logout()

# 5. Signup as Mechanic
r = c.post('/accounts/signup/', {
    'username': 'test_mech_su', 'password': 'testpass123',
    'confirm_password': 'testpass123', 'role': 'MECHANIC',
    'email': 'tmsu@ex.com', 'phone': '2222',
    'first_name': 'Test', 'last_name': 'Mech',
}, SERVER_NAME='localhost')
check('Signup Mechanic', r.status_code, 302, getattr(r, 'url', None))
mu = User.objects.filter(username='test_mech_su').first()
print(f'    User: {mu is not None} role={mu.role if mu else "?"}')
c.logout()

# 6. Login as Customer
r = c.post('/accounts/login/', {'username': 'test_cust_su', 'password': 'testpass123'}, SERVER_NAME='localhost')
check('Login Customer', r.status_code, 302, getattr(r, 'url', None))

# 7. Root redirects customer
r = c.get('/', SERVER_NAME='localhost')
check('Root->Customer', r.status_code, 302, getattr(r, 'url', None))
c.logout()

# 8. Login as Mechanic
r = c.post('/accounts/login/', {'username': 'test_mech_su', 'password': 'testpass123'}, SERVER_NAME='localhost')
check('Login Mechanic', r.status_code, 302, getattr(r, 'url', None))

# 9. Root redirects mechanic
r = c.get('/', SERVER_NAME='localhost')
check('Root->Mechanic', r.status_code, 302, getattr(r, 'url', None))
c.logout()

# 10. Admin redirect
admin = User.objects.filter(is_superuser=True).first()
if admin:
    c.force_login(admin)
    r = c.get('/', SERVER_NAME='localhost')
    check('Root->Admin', r.status_code, 302, getattr(r, 'url', None))
    c.logout()

# 11. Validation: duplicate username
r = c.post('/accounts/signup/', {
    'username': 'test_cust_su', 'password': 'p', 'confirm_password': 'p', 'role': 'CUSTOMER',
}, SERVER_NAME='localhost')
check('Dup username', r.status_code, 200)

# 12. Validation: password mismatch
r = c.post('/accounts/signup/', {
    'username': 'xyzunique', 'password': 'a', 'confirm_password': 'b', 'role': 'CUSTOMER',
}, SERVER_NAME='localhost')
check('Pwd mismatch', r.status_code, 200)

# Cleanup
Customer.objects.filter(user__username='test_cust_su').delete()
User.objects.filter(username__in=['test_cust_su', 'test_mech_su']).delete()

print()
print('=== ' + ('ALL PASSED' if all_ok else 'SOME FAILED') + ' ===')
