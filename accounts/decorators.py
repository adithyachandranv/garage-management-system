from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from functools import wraps

def role_required(*roles):
    """Decorator that checks if user has one of the specified roles."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            # Allow access if user has role OR is superuser (for admin views)
            if request.user.role in roles or (request.user.is_superuser and 'ADMIN' in roles):
                return view_func(request, *args, **kwargs)
            # Redirect to the correct portal if wrong role
            if request.user.role == 'ADMIN' or request.user.role == 'MANAGER':
                return redirect('admin_dashboard')
            elif request.user.role == 'MECHANIC':
                return redirect('mechanic_jobs')
            elif request.user.role == 'CUSTOMER':
                return redirect('customer_dashboard')
            return redirect('login')
        return _wrapped
    return decorator

def admin_required(view_func):
    return role_required('ADMIN', 'MANAGER')(view_func)

def mechanic_required(view_func):
    return role_required('MECHANIC')(view_func)

def customer_required(view_func):
    return role_required('CUSTOMER')(view_func)
