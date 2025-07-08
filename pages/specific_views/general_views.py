from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from ..models import FAQ, ContactSubmission
from ..specific_views_functions.general_views_functions import (
    get_active_faqs,
    process_contact_form_submission,
    render_simple_template,
    get_contact_form_context
)
import logging

# Set up logging
logger = logging.getLogger(__name__)

def home(request):
    return render_simple_template(request, 'pages/general/home.html')

@login_required
def first_grid_tutorial_view(request):
    """Display the first grid tutorial page for new users"""
    return render_simple_template(request, 'pages/user/first_grid.html')

# Template Views

def templates_overview_view(request):
    """Display the templates overview page"""
    return render_simple_template(request, 'pages/general/general_templates_overview.html')

def student_jobs_template_view(request):
    """Display the student job application template"""
    return render_simple_template(request, 'pages/general/specific_templates/students/student_jobs.html')

def student_revision_template_view(request):
    """Display the student revision template"""
    return render_simple_template(request, 'pages/general/specific_templates/students/student_revision.html')

def professionals_jobs_template_view(request):
    """Display the professional job application template"""
    return render_simple_template(request, 'pages/general/specific_templates/professionals/professionals_jobs.html')

# Support Pages

def faq_view(request):
    """Display the FAQ page with all active questions"""
    faqs = get_active_faqs()
    context = {
        'faqs': faqs,
    }
    return render(request, 'pages/general/bumf/FAQ.html', context)

@require_http_methods(["GET", "POST"])
def contact_us_view(request):
    """Handle the contact form - both display and submission"""
    if request.method == 'POST':
        return process_contact_form_submission(request)
    
    # GET request - display the form with default context
    context = get_contact_form_context()
    return render(request, 'pages/general/bumf/contact_us.html', context)

def privacy_policy_view(request):
    """Display the privacy policy page"""
    return render_simple_template(request, 'pages/general/bumf/privacy_policy.html')