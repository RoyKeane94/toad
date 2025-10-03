from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from ..models import ContactSubmission
from ..specific_views_functions.general_views_functions import (
    process_contact_form_submission,
    render_simple_template,
    get_contact_form_context
)
from ..signals import (
    create_course_planner_grid, create_revision_guide_grid, create_shooting_grid, 
    create_product_development_tracker_grid, create_solopreneur_grid, create_weekly_planner_grid, 
    create_sell_side_project_grid, create_origination_director_grid, create_habit_development_tracker_grid,
    create_weekly_fitness_tracker_grid, create_course_planner_grid_structure_only, 
    create_revision_guide_grid_structure_only, create_essay_planner_grid_structure_only, 
    create_job_application_tracker_grid_structure_only, create_weekly_planner_grid_structure_only, 
    create_line_manager_grid_structure_only, create_sell_side_project_grid_structure_only, 
    create_origination_director_grid_structure_only, create_product_development_tracker_grid_structure_only, 
    create_solopreneur_grid_structure_only, create_habit_development_tracker_grid_structure_only, 
    create_weekly_fitness_tracker_grid_structure_only, create_alternative_weekly_planner_grid, 
    create_alternative_weekly_planner_grid_structure_only, create_coffee_shop_tracker_grid,
    create_coffee_shop_tracker_grid_structure_only, create_content_creator_tracker_grid,
    create_content_creator_tracker_grid_structure_only, create_interior_designer_tracker_grid,
    create_interior_designer_tracker_grid_structure_only
)
from ..specific_views_functions.template_functions import create_essay_planner_grid, create_course_planner_template_grid, create_exam_revision_planner_grid, create_job_application_tracker_grid, create_line_manager_grid
import logging

# Set up logging
logger = logging.getLogger(__name__)

@require_http_methods(["GET", "POST"])
def home(request):
    """Handle the home page"""
    return render(request, 'pages/general/home.html')

@login_required
def upgrade_required_view(request):
    """Display the upgrade required page for free tier users"""
    return render(request, 'pages/general/upgrade_required.html')

@login_required
def first_grid_tutorial_view(request):
    """Display the first grid tutorial page for new users"""
    return render_simple_template(request, 'pages/user/first_grid.html')

# Template Views

def templates_overview_view(request):
    """Display the templates overview page - redirect to students templates"""
    from django.shortcuts import redirect
    return redirect('pages:students_templates')

def students_templates_view(request):
    """Display the students templates overview page"""
    return render_simple_template(request, 'pages/general/specific_templates/students/students_overview.html')

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
        # Check if user wants structure only or pre-populated tasks
        structure_only = request.GET.get('structure_only') == 'true'
        
        if structure_only:
            # Create the exam revision planner grid structure only
            project = create_revision_guide_grid_structure_only(request.user)
        else:
            # Create the exam revision planner grid with pre-populated tasks
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
        # Check if user wants structure only or pre-populated tasks
        structure_only = request.GET.get('structure_only') == 'true'
        
        if structure_only:
            # Create the essay planner grid structure only
            project = create_essay_planner_grid_structure_only(request.user)
        else:
            # Create the essay planner grid with pre-populated tasks
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
        # Check if user wants structure only or pre-populated tasks
        structure_only = request.GET.get('structure_only') == 'true'
        
        if structure_only:
            # Create the course planner grid structure only
            project = create_course_planner_grid_structure_only(request.user)
        else:
            # Create the course planner template grid with pre-populated tasks
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
        # Check if user wants structure only or pre-populated tasks
        structure_only = request.GET.get('structure_only') == 'true'
        
        if structure_only:
            # Create the job application tracker grid structure only
            project = create_job_application_tracker_grid_structure_only(request.user)
        else:
            # Create the job application tracker grid with pre-populated tasks
            project = create_job_application_tracker_grid(request.user)
        
        # Redirect to the newly created grid
        return redirect('pages:project_grid', pk=project.pk)
        
    except Exception as e:
        logger.error(f"Error creating job application tracker grid: {e}")
        messages.error(request, "There was an error creating your Job Application Tracker. Please try again.")
        return redirect('pages:templates_overview')

@login_required
def line_manager_template_view(request):
    """Create a Line Manager grid for the current user and redirect to it"""
    try:
        # Check if user wants structure only or pre-populated tasks
        structure_only = request.GET.get('structure_only') == 'true'
        
        if structure_only:
            # Create the line manager grid structure only
            project = create_line_manager_grid_structure_only(request.user)
        else:
            # Create the line manager grid with pre-populated tasks
            project = create_line_manager_grid(request.user)
        
        # Redirect to the newly created grid
        return redirect('pages:project_grid', pk=project.pk)
        
    except Exception as e:
        logger.error(f"Error creating line manager grid: {e}")
        messages.error(request, "There was an error creating your Team Management Grid. Please try again.")
        return redirect('pages:templates_overview')

@login_required
def alternative_weekly_planner_template_view(request):
    """Create an Alternative Weekly Planner grid for the current user and redirect to it"""
    try:
        # Check if user wants structure only or pre-populated tasks
        structure_only = request.GET.get('structure_only') == 'true'
        
        if structure_only:
            # Create the alternative weekly planner grid structure only
            project = create_alternative_weekly_planner_grid_structure_only(request.user)
        else:
            # Create the alternative weekly planner grid with pre-populated tasks
            project = create_alternative_weekly_planner_grid(request.user)
        
        # Redirect to the newly created grid
        return redirect('pages:project_grid', pk=project.pk)
        
    except Exception as e:
        logger.error(f"Error creating alternative weekly planner grid: {e}")
        messages.error(request, "There was an error creating your Alternative Weekly Planner. Please try again.")
        return redirect('pages:templates_overview')

@login_required
def weekly_planner_template_view(request):
    """Create a Weekly Planner grid for the current user and redirect to it"""
    try:
        # Check if user wants structure only or pre-populated tasks
        structure_only = request.GET.get('structure_only') == 'true'
        
        if structure_only:
            # Create the weekly planner grid structure only
            project = create_weekly_planner_grid_structure_only(request.user)
        else:
            # Create the weekly planner grid with pre-populated tasks
            project = create_weekly_planner_grid(request.user)
        
        # Redirect to the newly created grid
        return redirect('pages:project_grid', pk=project.pk)
        
    except Exception as e:
        logger.error(f"Error creating weekly planner grid: {e}")
        messages.error(request, "There was an error creating your Weekly Planner. Please try again.")
        return redirect('pages:templates_overview')

@login_required
def sell_side_project_template_view(request):
    """Create a Sell Side Project grid for the current user and redirect to it"""
    try:
        # Check if user wants structure only or pre-populated tasks
        structure_only = request.GET.get('structure_only') == 'true'
        
        if structure_only:
            # Create the sell side project grid structure only
            project = create_sell_side_project_grid_structure_only(request.user)
        else:
            # Create the sell side project grid with pre-populated tasks
            project = create_sell_side_project_grid(request.user)
        
        # Redirect to the newly created grid
        return redirect('pages:project_grid', pk=project.pk)
        
    except Exception as e:
        logger.error(f"Error creating sell side project grid: {e}")
        messages.error(request, "There was an error creating your Sell Side Project. Please try again.")
        return redirect('pages:templates_overview')

@login_required
def origination_director_template_view(request):
    """Create an Origination Director grid for the current user and redirect to it"""
    try:
        # Check if user wants structure only or pre-populated tasks
        structure_only = request.GET.get('structure_only') == 'true'
        
        if structure_only:
            # Create the origination director grid structure only
            project = create_origination_director_grid_structure_only(request.user)
        else:
            # Create the origination director grid with pre-populated tasks
            project = create_origination_director_grid(request.user)
        
        # Redirect to the newly created grid
        return redirect('pages:project_grid', pk=project.pk)
        
    except Exception as e:
        logger.error(f"Error creating origination director grid: {e}")
        messages.error(request, "There was an error creating your Origination Director. Please try again.")
        return redirect('pages:templates_overview')

def shooting_template_landing_view(request):
    """Display the shooting template landing page"""
    return render_simple_template(request, 'pages/user_templates/shooting.html')

@login_required
def shooting_template_create_view(request):
    """Create a Shooting grid for the current user and redirect to it"""
    try:
        # Create the shooting grid
        project = create_shooting_grid(request.user)
        
        # Redirect to the newly created grid
        return redirect('pages:project_grid', pk=project.pk)
        
    except Exception as e:
        logger.error(f"Error creating shooting grid: {e}")
        messages.error(request, "There was an error creating your Shooting Schedule. Please try again.")
        return redirect('pages:templates_overview')

@login_required
def product_development_tracker_template_view(request):
    """Create a Product Development Tracker grid for the current user and redirect to it"""
    try:
        # Check if user wants structure only or pre-populated tasks
        structure_only = request.GET.get('structure_only') == 'true'
        
        if structure_only:
            # Create the product development tracker grid structure only
            project = create_product_development_tracker_grid_structure_only(request.user)
        else:
            # Create the product development tracker grid with pre-populated tasks
            project = create_product_development_tracker_grid(request.user)
        
        # Redirect to the newly created grid
        return redirect('pages:project_grid', pk=project.pk)
        
    except Exception as e:
        logger.error(f"Error creating product development tracker grid: {e}")
        messages.error(request, "There was an error creating your Product Development Tracker. Please try again.")
        return redirect('pages:templates_overview')

@login_required
def solopreneur_template_view(request):
    """Create a Solopreneur grid for the current user and redirect to it"""
    try:
        # Check if user wants structure only or pre-populated tasks
        structure_only = request.GET.get('structure_only') == 'true'
        
        if structure_only:
            # Create the solopreneur grid structure only
            project = create_solopreneur_grid_structure_only(request.user)
        else:
            # Create the solopreneur grid with pre-populated tasks
            project = create_solopreneur_grid(request.user)
        
        # Redirect to the newly created grid
        return redirect('pages:project_grid', pk=project.pk)
        
    except Exception as e:
        logger.error(f"Error creating solopreneur grid: {e}")
        messages.error(request, "There was an error creating your Solopreneur grid. Please try again.")
        return redirect('pages:templates_overview')

def professionals_jobs_template_view(request):
    """Display the professionals job application template"""
    return render_simple_template(request, 'pages/general/specific_templates/professionals/professionals_jobs.html')

def professionals_templates_view(request):
    """Display the professionals templates overview page"""
    return render_simple_template(request, 'pages/general/specific_templates/professionals/professionals_overview.html')

def entrepreneurs_templates_view(request):
    """Display the entrepreneurs templates overview page"""
    return render(request, 'pages/general/specific_templates/entrepreneurs/entrepreneurs_overview.html')

def personal_templates_view(request):
    """Display the personal templates overview page"""
    return render_simple_template(request, 'pages/general/specific_templates/personal/personal_overview.html')

@login_required
def habit_development_tracker_template_view(request):
    """Create a Habit Development Tracker grid for the current user and redirect to it"""
    try:
        # Check if user wants structure only or pre-populated tasks
        structure_only = request.GET.get('structure_only') == 'true'
        
        if structure_only:
            # Create the habit development tracker grid structure only
            project = create_habit_development_tracker_grid_structure_only(request.user)
        else:
            # Create the habit development tracker grid with pre-populated tasks
            project = create_habit_development_tracker_grid(request.user)
        
        # Redirect to the newly created grid
        return redirect('pages:project_grid', pk=project.pk)
        
    except Exception as e:
        logger.error(f"Error creating habit development tracker grid: {e}")
        messages.error(request, "There was an error creating your Habit Development Tracker. Please try again.")
        return redirect('pages:templates_overview')

@login_required
def weekly_fitness_tracker_template_view(request):
    """Create a Weekly Fitness Tracker grid for the current user and redirect to it"""
    try:
        # Check if user wants structure only or pre-populated tasks
        structure_only = request.GET.get('structure_only') == 'true'
        
        if structure_only:
            # Create the weekly fitness tracker grid structure only
            project = create_weekly_fitness_tracker_grid_structure_only(request.user)
        else:
            # Create the weekly fitness tracker grid with pre-populated tasks
            project = create_weekly_fitness_tracker_grid(request.user)
        
        # Redirect to the newly created grid
        return redirect('pages:project_grid', pk=project.pk)
        
    except Exception as e:
        logger.error(f"Error creating weekly fitness tracker grid: {e}")
        messages.error(request, "There was an error creating your Weekly Fitness Tracker. Please try again.")
        return redirect('pages:templates_overview')

@login_required
def coffee_shop_tracker_template_view(request):
    """Create a Coffee Shop Tracker grid for the current user and redirect to it"""
    try:
        # Check if user wants structure only or pre-populated tasks
        structure_only = request.GET.get('structure_only') == 'true'
        
        if structure_only:
            # Create the coffee shop tracker grid structure only
            project = create_coffee_shop_tracker_grid_structure_only(request.user)
        else:
            # Create the coffee shop tracker grid with pre-populated tasks
            project = create_coffee_shop_tracker_grid(request.user)
        
        # Redirect to the newly created grid
        return redirect('pages:project_grid', pk=project.pk)
        
    except Exception as e:
        logger.error(f"Error creating coffee shop tracker grid: {e}")
        messages.error(request, "There was an error creating your Coffee Shop Tracker. Please try again.")
        return redirect('pages:templates_overview')

@login_required
def content_creator_tracker_template_view(request):
    """Create a Content Creator Tracker grid for the current user and redirect to it"""
    try:
        # Check if user wants structure only or pre-populated tasks
        structure_only = request.GET.get('structure_only') == 'true'
        
        if structure_only:
            # Create the content creator tracker grid structure only
            project = create_content_creator_tracker_grid_structure_only(request.user)
        else:
            # Create the content creator tracker grid with pre-populated tasks
            project = create_content_creator_tracker_grid(request.user)
        
        # Redirect to the newly created grid
        return redirect('pages:project_grid', pk=project.pk)
        
    except Exception as e:
        logger.error(f"Error creating content creator tracker grid: {e}")
        messages.error(request, "There was an error creating your Content Creator Tracker. Please try again.")
        return redirect('pages:templates_overview')

@login_required
def interior_designer_tracker_template_view(request):
    """Create an Interior Designer Tracker grid for the current user and redirect to it"""
    try:
        # Check if user wants structure only or pre-populated tasks
        structure_only = request.GET.get('structure_only') == 'true'
        
        if structure_only:
            # Create the interior designer tracker grid structure only
            project = create_interior_designer_tracker_grid_structure_only(request.user)
        else:
            # Create the interior designer tracker grid with pre-populated tasks
            project = create_interior_designer_tracker_grid(request.user)
        
        # Redirect to the newly created grid
        return redirect('pages:project_grid', pk=project.pk)
        
    except Exception as e:
        logger.error(f"Error creating interior designer tracker grid: {e}")
        messages.error(request, "There was an error creating your Interior Designer Tracker. Please try again.")
        return redirect('pages:templates_overview')

# Support Pages

def faq_view(request):
    """Display the FAQ page with all active questions"""
    context = {}
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