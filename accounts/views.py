from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView
from django.contrib import messages
from .models import User
from customers.models import Customer


class RoleBasedLoginView(LoginView):
    template_name = 'accounts/login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self._get_role_redirect(request.user))
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return self._get_role_redirect(self.request.user)

    @staticmethod
    def _get_role_redirect(user):
        if user.role in ('ADMIN', 'MANAGER') or user.is_superuser:
            return '/admin-panel/dashboard/'
        elif user.role == 'MECHANIC':
            return '/mechanic/jobs/'
        elif user.role == 'CUSTOMER':
            return '/customer/dashboard/'
        return '/admin-panel/dashboard/'


def landing_view(request):
    """Root URL: redirect authenticated users to their portal, show login otherwise."""
    if request.user.is_authenticated:
        return redirect(RoleBasedLoginView._get_role_redirect(request.user))
    return redirect('login')


def signup_view(request):
    """Handle user registration with role selection (Customer or Mechanic)."""
    if request.user.is_authenticated:
        return redirect(RoleBasedLoginView._get_role_redirect(request.user))

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        role = request.POST.get('role', '')
        address = request.POST.get('address', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()

        # Validation
        errors = []
        if not username:
            errors.append('Username is required.')
        if not password:
            errors.append('Password is required.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if role not in ('CUSTOMER', 'MECHANIC'):
            errors.append('Please select a valid role.')
        if User.objects.filter(username=username).exists():
            errors.append('Username already taken.')
        if email and User.objects.filter(email=email).exists():
            errors.append('Email already in use.')

        if errors:
            for err in errors:
                messages.error(request, err)
            selected_role = request.POST.get('role', 'CUSTOMER')
            return render(request, 'accounts/signup.html', {
                'form_data': request.POST,
                'customer_checked': 'checked' if selected_role == 'CUSTOMER' else '',
                'mechanic_checked': 'checked' if selected_role == 'MECHANIC' else '',
            })

        # Create user
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            phone=phone,
            role=role,
            first_name=first_name,
            last_name=last_name,
        )

        # If customer, also create Customer record
        if role == 'CUSTOMER':
            Customer.objects.create(user=user, address=address or '')

        # Auto-login
        login(request, user)
        messages.success(request, f'Welcome to GaragePro, {user.get_full_name() or user.username}!')
        return redirect(RoleBasedLoginView._get_role_redirect(user))

    return render(request, 'accounts/signup.html', {
        'customer_checked': 'checked',
        'mechanic_checked': '',
    })
