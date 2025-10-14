from django.contrib import admin
from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    
    # Superuser Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # User tutorial
    path('first-grid/', views.first_grid_tutorial_view, name='first_grid_tutorial'),
    
    # Upgrade required
    path('upgrade-required/', views.upgrade_required_view, name='upgrade_required'),
    
    # Test error pages (development only)
    path('test-404/', views.test_404, name='test_404'),
    path('test-500/', views.test_500, name='test_500'),
    path('test-403/', views.test_403, name='test_403'),
    
    # Template URLs
    path('templates/', views.templates_overview_view, name='templates_overview'),
    path('templates/students/', views.students_templates_view, name='students_templates'),
    path('templates/course-planner/', views.course_planner_template_view, name='course_planner_template'),
    path('templates/revision-guide/', views.revision_guide_template_view, name='revision_guide_template'),
    path('templates/essay-planner/', views.essay_planner_template_view, name='essay_planner_template'),
    path('templates/job-application-tracker/', views.job_application_tracker_template_view, name='job_application_tracker_template'),
    path('templates/line-manager/', views.line_manager_template_view, name='line_manager_template'),
    path('templates/weekly-planner/', views.weekly_planner_template_view, name='weekly_planner_template'),
    path('templates/alternative-weekly-planner/', views.alternative_weekly_planner_template_view, name='alternative_weekly_planner_template'),
    path('templates/sell-side-project/', views.sell_side_project_template_view, name='sell_side_project_template'),
    path('templates/origination-director/', views.origination_director_template_view, name='origination_director_template'),
    path('templates/shooting/', views.shooting_template_landing_view, name='shooting_template'),
    path('templates/shooting/create/', views.shooting_template_create_view, name='shooting_template_create'),
    path('templates/product-development-tracker/', views.product_development_tracker_template_view, name='product_development_tracker_template'),
    path('templates/solopreneur/', views.solopreneur_template_view, name='solopreneur_template'),
    path('templates/coffee-shop-tracker/', views.coffee_shop_tracker_template_view, name='coffee_shop_tracker_template'),
    path('templates/content-creator-tracker/', views.content_creator_tracker_template_view, name='content_creator_tracker_template'),
    path('templates/interior-designer-tracker/', views.interior_designer_tracker_template_view, name='interior_designer_tracker_template'),
    path('templates/online-store-tracker/', views.online_store_tracker_template_view, name='online_store_tracker_template'),
    path('templates/student-jobs/', views.student_jobs_template_view, name='student_jobs_template'),
    path('templates/student-revision/', views.student_revision_template_view, name='student_revision_template'),
    path('templates/professionals-jobs/', views.professionals_jobs_template_view, name='professionals_jobs_template'),
    path('templates/professionals/', views.professionals_templates_view, name='professionals_templates'),
    path('templates/entrepreneurs/', views.entrepreneurs_templates_view, name='entrepreneurs_templates'),
    path('templates/personal/', views.personal_templates_view, name='personal_templates'),
    path('templates/habit-development-tracker/', views.habit_development_tracker_template_view, name='habit_development_tracker_template'),
    path('templates/weekly-fitness-tracker/', views.weekly_fitness_tracker_template_view, name='weekly_fitness_tracker_template'),
    path('templates/create/<str:template_type>/', views.create_from_template_view, name='create_from_template'),
    
    # Support Pages
    path('faq/', views.faq_view, name='faq'),
    path('contact/', views.contact_us_view, name='contact_us'),
    path('privacy/', views.privacy_policy_view, name='privacy_policy'),
    
    # Grid URLs
    path('grids/', views.project_list_view, name='project_list'),
    path('grids/create/', views.project_create_view, name='project_create'),

    path('grids/<int:pk>/', views.project_grid_view, name='project_grid'),
    path('grids/<int:pk>/edit/', views.project_edit_view, name='project_edit'),
    path('grids/<int:pk>/delete/', views.project_delete_view, name='project_delete'),
    path('grids/<int:pk>/clear-completed/', views.delete_completed_tasks_view, name='delete_completed_tasks'),
    path('grids/<int:pk>/archive/confirm/', views.archive_project_confirm_view, name='archive_project_confirm'),
    path('grids/<int:pk>/archive/', views.archive_project_view, name='archive_project'),
    path('grids/<int:pk>/restore/', views.restore_project_view, name='restore_project'),
    path('grids/<int:pk>/save-template/', views.save_as_template_view, name='save_as_template'),
    path('templates/<int:pk>/use/', views.use_template_view, name='use_template'),
    path('templates/<int:pk>/edit/', views.template_edit_view, name='template_edit'),
    path('templates/<int:pk>/delete/', views.template_delete_view, name='template_delete'),
    
    # Task URLs
    path('grids/<int:project_pk>/tasks/create/<int:row_pk>/<int:col_pk>/', views.task_create_view, name='task_create'),
    path('tasks/<int:task_pk>/edit/', views.task_edit_view, name='task_edit'),
    path('tasks/<int:task_pk>/toggle/', views.task_toggle_complete_view, name='task_toggle_complete'),
    path('tasks/<int:task_pk>/delete/', views.task_delete_view, name='task_delete'),
    path('tasks/<int:task_pk>/assign/', views.task_assign_view, name='task_assign'),
    path('tasks/<int:task_pk>/reminder/', views.create_task_reminder, name='create_task_reminder'),
    path('tasks/<int:task_pk>/assign/', views.task_assign_view, name='task_assign'),
    path('grids/<int:project_pk>/tasks/reorder/', views.task_reorder_view, name='task_reorder'),
    
    # Row URLs
    path('grids/<int:project_pk>/rows/create/', views.row_create_view, name='row_create'),
    path('grids/<int:project_pk>/rows/<int:row_pk>/edit/', views.row_edit_view, name='row_edit'),
    path('grids/<int:project_pk>/rows/<int:row_pk>/delete/', views.row_delete_view, name='row_delete'),
    
    # Column URLs
    path('grids/<int:project_pk>/columns/create/', views.column_create_view, name='column_create'),
    path('grids/<int:project_pk>/columns/<int:col_pk>/edit/', views.column_edit_view, name='column_edit'),
    path('grids/<int:project_pk>/columns/<int:col_pk>/delete/', views.column_delete_view, name='column_delete'),
    
    # Project Group URLs
    path('grids/group/create/', views.project_group_create_view, name='project_group_create'),
    path('grids/project/update-group/', views.project_group_update_view, name='project_group_update'),
    path('grids/group/<int:pk>/edit/', views.project_group_edit_view, name='project_group_edit'),
    
    # Grid Sharing URLs
    path('grids/<int:pk>/share/', views.share_grid_view, name='share_grid'),
    path('grids/invite/<str:token>/', views.accept_grid_invitation_view, name='accept_grid_invitation'),
]