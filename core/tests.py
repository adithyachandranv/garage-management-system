from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

class DashboardTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password', role='ADMIN')
        self.client.login(username='testuser', password='password')

    def test_dashboard_view_status_code(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_view_context(self):
        response = self.client.get(reverse('dashboard'))
        self.assertIn('active_jobs_count', response.context)
        self.assertIn('monthly_revenue', response.context)
        self.assertIn('pending_approvals_count', response.context)
        self.assertIn('low_stock_count', response.context)
        self.assertIn('revenue_trend', response.context)
        self.assertIn('job_status_data', response.context)
