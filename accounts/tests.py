from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

class AuthenticationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')

    def test_login_view(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_login_success(self):
        response = self.client.post(reverse('login'), {'username': 'testuser', 'password': 'password'})
        self.assertRedirects(response, reverse('dashboard'))

    def test_logout_view(self):
        self.client.login(username='testuser', password='password')
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('login'))
