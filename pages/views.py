from django.shortcuts import render

# Import all views from specific modules
from .specific_views.error_views import (
    handler404, handler500, handler403,
    test_404, test_500, test_403
)

from .specific_views.general_views import (
    home,
    first_grid_tutorial_view,
    upgrade_required_view,
    templates_overview_view,
    students_templates_view,
    student_jobs_template_view,
    student_revision_template_view,
    course_planner_template_view,
    revision_guide_template_view,
    essay_planner_template_view,
    job_application_tracker_template_view,
    line_manager_template_view,
    weekly_planner_template_view,
    alternative_weekly_planner_template_view,
    sell_side_project_template_view,
    origination_director_template_view,
    professionals_jobs_template_view,
    professionals_templates_view,
    entrepreneurs_templates_view,
    personal_templates_view,
    habit_development_tracker_template_view,
    weekly_fitness_tracker_template_view,
    shooting_template_landing_view,
    shooting_template_create_view,
    product_development_tracker_template_view,
    solopreneur_template_view,
    coffee_shop_tracker_template_view,
    content_creator_tracker_template_view,
    interior_designer_tracker_template_view,
    online_store_tracker_template_view,
    faq_view,
    contact_us_view,
    privacy_policy_view
)

from pages.specific_views.project_views import (
    project_list_view, project_create_view, project_edit_view, project_delete_view,
    project_grid_view, delete_completed_tasks_view, archive_project_confirm_view, archive_project_view, restore_project_view,
    project_group_create_view, project_group_update_view, project_group_edit_view,
    save_as_template_view, use_template_view, template_edit_view, template_delete_view,
    create_from_template_view, task_create_view, task_edit_view, task_toggle_complete_view,
    task_delete_view, task_assign_view, create_task_reminder, task_note_view, task_notes_view, task_reorder_view, row_create_view, row_edit_view, row_delete_view,
    column_create_view, column_edit_view, column_delete_view, share_grid_view, accept_grid_invitation_view
)

# Import analytics functions
from .specific_views_functions.analytics_views_functions import get_dashboard_analytics


def dashboard_view(request):
    """
    Superuser dashboard with analytics
    """
    if not request.user.is_superuser:
        from django.http import Http404
        raise Http404("Dashboard not found")
    
    analytics = get_dashboard_analytics()
    
    context = analytics
    
    return render(request, 'pages/dashboard/dashboard.html', context)



