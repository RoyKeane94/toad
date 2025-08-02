from django.shortcuts import render, redirect
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
from ..signals import create_course_planner_grid, create_revision_guide_grid
from ..specific_views_functions.template_functions import create_essay_planner_grid, create_course_planner_template_grid, create_exam_revision_planner_grid, create_job_application_tracker_grid
import logging

# Set up logging
logger = logging.getLogger(__name__)

@require_http_methods(["GET", "POST"])
def home(request):
    """Handle the home page"""
    return render(request, 'pages/general/home.html')

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

@login_required
def revision_guide_template_view(request):
    """Create an Exam Revision Planner grid for the current user and redirect to it"""
    try:
        # Create the exam revision planner grid
        project = create_exam_revision_planner_grid(request.user)
        
        # Redirect to the newly created grid
        return redirect('pages:project_grid', pk=project.pk)
        
    except Exception as e:
        logger.error(f"Error creating exam revision planner grid: {e}")
        messages.error(request, "There was an error creating your Exam Revision Planner. Please try again.")
        return redirect('pages:templates_overview')

@login_required
def essay_planner_template_view(request):
    """Create an Essay Planner grid for the current user and redirect to it"""
    try:
        # Create the essay planner grid
        project = create_essay_planner_grid(request.user)
        
        # Redirect to the newly created grid
        return redirect('pages:project_grid', pk=project.pk)
        
    except Exception as e:
        logger.error(f"Error creating essay planner grid: {e}")
        messages.error(request, "There was an error creating your Essay Planner. Please try again.")
        return redirect('pages:templates_overview')

@login_required
def course_planner_template_view(request):
    """Create a Course Planner template grid for the current user and redirect to it"""
    try:
        # Create the course planner template grid
        project = create_course_planner_template_grid(request.user)
        
        # Redirect to the newly created grid
        return redirect('pages:project_grid', pk=project.pk)
        
    except Exception as e:
        logger.error(f"Error creating course planner template grid: {e}")
        messages.error(request, "There was an error creating your Course Planner. Please try again.")
        return redirect('pages:templates_overview')

@login_required
def job_application_tracker_template_view(request):
    """Create a Job Application Tracker grid for the current user and redirect to it"""
    try:
        # Create the job application tracker grid
        project = create_job_application_tracker_grid(request.user)
        
        # Redirect to the newly created grid
        return redirect('pages:project_grid', pk=project.pk)
        
    except Exception as e:
        logger.error(f"Error creating job application tracker grid: {e}")
        messages.error(request, "There was an error creating your Job Application Tracker. Please try again.")
        return redirect('pages:templates_overview')

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