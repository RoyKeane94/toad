# Import all views from specific modules
from .specific_views.error_views import (
    handler404, handler500, handler403,
    test_404, test_500, test_403
)

from .specific_views.general_views import (
    home,
    first_grid_tutorial_view,
    templates_overview_view,
    student_jobs_template_view,
    student_revision_template_view,
    course_planner_template_view,
    revision_guide_template_view,
    professionals_jobs_template_view,
    faq_view,
    contact_us_view,
    privacy_policy_view
)

from .specific_views.project_views import (
    project_list_view,
    project_create_view,
    project_edit_view,
    project_delete_view,
    project_grid_view,
    task_create_view,
    task_edit_view,
    task_toggle_complete_view,
    task_delete_view,
    row_create_view,
    row_edit_view,
    row_delete_view,
    column_create_view,
    column_edit_view,
    column_delete_view,
    delete_completed_tasks_view,
    create_from_template_view
)



