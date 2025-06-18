from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.http import HttpResponse

User = get_user_model()


class GeneralViewsTestCase(TestCase):
    """Test cases for general views in pages.specific_views.general_views"""
    
    def setUp(self):
        """Set up test client and user for tests"""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
    
    def test_home_view_get(self):
        """Test that home view renders correctly"""
        response = self.client.get(reverse('pages:home'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/general/home.html')
    
    def test_home_view_anonymous_user(self):
        """Test that home view is accessible to anonymous users"""
        response = self.client.get(reverse('pages:home'))
        
        self.assertEqual(response.status_code, 200)
        # Should not redirect to login
        self.assertNotEqual(response.status_code, 302)
    
    def test_home_view_authenticated_user(self):
        """Test that home view works for authenticated users"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('pages:home'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/general/home.html')
    
    def test_templates_overview_view_get(self):
        """Test that templates overview view renders correctly"""
        response = self.client.get(reverse('pages:templates_overview'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/general/general_templates_overview.html')
    
    def test_templates_overview_view_anonymous_user(self):
        """Test that templates overview is accessible to anonymous users"""
        response = self.client.get(reverse('pages:templates_overview'))
        
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.status_code, 302)
    
    def test_student_jobs_template_view_get(self):
        """Test that student jobs template view renders correctly"""
        response = self.client.get(reverse('pages:student_jobs_template'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/general/specific_templates/students/student_jobs.html')
    
    def test_student_jobs_template_view_anonymous_user(self):
        """Test that student jobs template is accessible to anonymous users"""
        response = self.client.get(reverse('pages:student_jobs_template'))
        
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.status_code, 302)
    
    def test_student_revision_template_view_get(self):
        """Test that student revision template view renders correctly"""
        response = self.client.get(reverse('pages:student_revision_template'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/general/specific_templates/students/student_revision.html')
    
    def test_student_revision_template_view_anonymous_user(self):
        """Test that student revision template is accessible to anonymous users"""
        response = self.client.get(reverse('pages:student_revision_template'))
        
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.status_code, 302)
    
    def test_professionals_jobs_template_view_get(self):
        """Test that professionals jobs template view renders correctly"""
        response = self.client.get(reverse('pages:professionals_jobs_template'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/general/specific_templates/professionals/professionals_jobs.html')
    
    def test_professionals_jobs_template_view_anonymous_user(self):
        """Test that professionals jobs template is accessible to anonymous users"""
        response = self.client.get(reverse('pages:professionals_jobs_template'))
        
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.status_code, 302)
    
    def test_all_template_views_return_html_content(self):
        """Test that all template views return HTML content"""
        template_urls = [
            'pages:home',
            'pages:templates_overview',
            'pages:student_jobs_template',
            'pages:student_revision_template',
            'pages:professionals_jobs_template'
        ]
        
        for url_name in template_urls:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 200)
                self.assertIsInstance(response, HttpResponse)
                # Check that response contains HTML
                self.assertIn('text/html', response.get('Content-Type', ''))
    
    def test_template_views_with_post_method(self):
        """Test that template views handle POST requests appropriately"""
        template_urls = [
            'pages:home',
            'pages:templates_overview',
            'pages:student_jobs_template',
            'pages:student_revision_template',
            'pages:professionals_jobs_template'
        ]
        
        for url_name in template_urls:
            with self.subTest(url_name=url_name):
                response = self.client.post(reverse(url_name))
                # These views should still render on POST (they don't handle POST differently)
                self.assertEqual(response.status_code, 200)
    
    def test_template_views_with_authenticated_user(self):
        """Test that all template views work correctly with authenticated users"""
        self.client.login(email='test@example.com', password='testpass123')
        
        template_urls = [
            'pages:home',
            'pages:templates_overview',
            'pages:student_jobs_template',
            'pages:student_revision_template',
            'pages:professionals_jobs_template'
        ]
        
        for url_name in template_urls:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 200)


class GeneralViewsIntegrationTestCase(TestCase):
    """Integration tests for general views"""
    
    def setUp(self):
        """Set up test client"""
        self.client = Client()
    
    def test_navigation_between_template_views(self):
        """Test that users can navigate between different template views"""
        # Start at templates overview
        response = self.client.get(reverse('pages:templates_overview'))
        self.assertEqual(response.status_code, 200)
        
        # Navigate to each specific template
        template_views = [
            'pages:student_jobs_template',
            'pages:student_revision_template', 
            'pages:professionals_jobs_template'
        ]
        
        for view_name in template_views:
            response = self.client.get(reverse(view_name))
            self.assertEqual(response.status_code, 200)
    
    def test_home_to_templates_navigation(self):
        """Test navigation from home to templates overview"""
        # Start at home
        home_response = self.client.get(reverse('pages:home'))
        self.assertEqual(home_response.status_code, 200)
        
        # Navigate to templates
        templates_response = self.client.get(reverse('pages:templates_overview'))
        self.assertEqual(templates_response.status_code, 200)
    
    def test_all_views_have_consistent_response_format(self):
        """Test that all general views return consistent response formats"""
        all_views = [
            'pages:home',
            'pages:templates_overview',
            'pages:student_jobs_template',
            'pages:student_revision_template',
            'pages:professionals_jobs_template'
        ]
        
        for view_name in all_views:
            with self.subTest(view_name=view_name):
                response = self.client.get(reverse(view_name))
                
                # All should return 200 OK
                self.assertEqual(response.status_code, 200)
                
                # All should return HTML content
                self.assertIn('text/html', response.get('Content-Type', ''))
                
                # All should have some content
                self.assertGreater(len(response.content), 0)
