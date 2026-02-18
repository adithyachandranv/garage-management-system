from django.urls import path
from django.contrib.auth import views as auth_views
from .views import RoleBasedLoginView, signup_view

urlpatterns = [
    path('login/', RoleBasedLoginView.as_view(), name='login'),
    path('signup/', signup_view, name='signup'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
]
