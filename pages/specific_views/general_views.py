from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from ..models import FAQ, ContactSubmission
import logging

# Set up logging
logger = logging.getLogger(__name__)

def home(request):
    return render(request, 'pages/general/home.html')

@login_required
def first_grid_tutorial_view(request):
    """Display the first grid tutorial page for new users"""
    return render(request, 'pages/user/first_grid.html')

# Template Views

def templates_overview_view(request):
    """Display the templates overview page"""
    return render(request, 'pages/general/general_templates_overview.html')

def student_jobs_template_view(request):
    """Display the student job application template"""
    return render(request, 'pages/general/specific_templates/students/student_jobs.html')

def student_revision_template_view(request):
    """Display the student revision template"""
    return render(request, 'pages/general/specific_templates/students/student_revision.html')

def professionals_jobs_template_view(request):
    """Display the professional job application template"""
    return render(request, 'pages/general/specific_templates/professionals/professionals_jobs.html')

# Support Pages

def faq_view(request):
    """Display the FAQ page with all active questions"""
    faqs = FAQ.objects.filter(is_active=True).order_by('category', 'order', 'question')
    context = {
        'faqs': faqs,
    }
    return render(request, 'pages/general/bumf/FAQ.html', context)

@require_http_methods(["GET", "POST"])
def contact_us_view(request):
    """Handle the contact form - both display and submission"""
    if request.method == 'POST':
        try:
            # Extract form data
            name = request.POST.get('name', '').strip()
            email = request.POST.get('email', '').strip()
            category = request.POST.get('category', 'general')
            subject = request.POST.get('subject', '').strip()
            message = request.POST.get('message', '').strip()
            
            # Basic validation
            if not all([name, email, subject, message]):
                return render(request, 'pages/general/bumf/contact_us.html', {
                    'error': 'Please fill in all required fields.',
                    'form_data': request.POST
                })
            
            # Create the contact submission
            submission = ContactSubmission.objects.create(
                name=name,
                email=email,
                category=category,
                subject=subject,
                message=message,
                user=request.user if request.user.is_authenticated else None
            )
            
            logger.info(f"New contact submission from {email}: {subject}")
            
            # Return success response
            if request.headers.get('HX-Request'):
                # HTMX request - return success message
                return render(request, 'pages/general/bumf/contact_us.html', {
                    'success': True,
                    'message': 'Thank you for your message! We\'ll get back to you within 24 hours.'
                })
            else:
                # Regular form submission
                messages.success(request, 'Thank you for your message! We\'ll get back to you within 24 hours.')
                return render(request, 'pages/general/bumf/contact_us.html', {
                    'success': True
                })
                
        except Exception as e:
            logger.error(f"Error processing contact form: {str(e)}")
            error_message = 'Sorry, there was an error sending your message. Please try again.'
            
            if request.headers.get('HX-Request'):
                return render(request, 'pages/general/bumf/contact_us.html', {
                    'error': error_message,
                    'form_data': request.POST
                })
            else:
                messages.error(request, error_message)
                return render(request, 'pages/general/bumf/contact_us.html', {
                    'error': error_message,
                    'form_data': request.POST
                })
    
    # GET request - just display the form
    return render(request, 'pages/general/bumf/contact_us.html')

def privacy_policy_view(request):
    """Display the privacy policy page"""
    return render(request, 'pages/general/bumf/privacy_policy.html')