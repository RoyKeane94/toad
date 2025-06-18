from django.shortcuts import render
import logging

# Set up logging
logger = logging.getLogger(__name__)

def home(request):
    return render(request, 'pages/general/home.html')

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