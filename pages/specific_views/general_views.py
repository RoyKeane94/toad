from django.shortcuts import render
from django.contrib.auth.decorators import login_required
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