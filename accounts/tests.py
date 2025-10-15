from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .forms import EmailAuthenticationForm, CustomUserCreationForm

User = get_user_model()

class LoginViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('accounts:login')
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def test_login_page_loads(self):
        """Test that login page loads correctly"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')
        self.assertIsInstance(response.context['form'], EmailAuthenticationForm)

    def test_successful_login(self):
        """Test successful login with correct credentials"""
        response = self.client.post(self.login_url, {
            'username': 'test@example.com',
            'password': 'testpass123'
        })
        self.assertRedirects(response, reverse('pages:project_list'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        # Check for success message
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Welcome back, Test!')

    def test_failed_login(self):
        """Test login with incorrect credentials"""
        response = self.client.post(self.login_url, {
            'username': 'test@example.com',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        # Check for error message
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Please correct the errors below.')

    def test_authenticated_user_redirect(self):
        """Test that authenticated users are redirected from login page"""
        self.client.force_login(self.user)
        response = self.client.get(self.login_url)
        self.assertRedirects(response, reverse('pages:project_list'))

class RegisterViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('accounts:register_choices')

    def test_register_page_loads(self):
        """Test that register page loads correctly"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')
        self.assertIsInstance(response.context['form'], CustomUserCreationForm)

    def test_successful_registration(self):
        """Test successful user registration"""
        response = self.client.post(self.register_url, {
            'email': 'newuser@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'first_name': 'New',
            'last_name': 'User'
        })
        self.assertRedirects(response, reverse('pages:project_list'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())
        # Check for success message
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Welcome to Toad, New! Your account has been created.')

    def test_failed_registration(self):
        """Test registration with invalid data"""
        response = self.client.post(self.register_url, {
            'email': 'invalid-email',
            'password1': 'testpass123',
            'password2': 'differentpass',
            'first_name': 'New',
            'last_name': 'User'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        # Check for error message
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Please correct the errors below.')

    def test_authenticated_user_redirect(self):
        """Test that authenticated users are redirected from register page"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_login(user)
        response = self.client.get(self.register_url)
        self.assertRedirects(response, reverse('pages:project_list'))
