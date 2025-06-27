from django.contrib import admin
from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    
    # User tutorial
    path('first-grid/', views.first_grid_tutorial_view, name='first_grid_tutorial'),
    
    # Test error pages (development only)
    path('test-404/', views.test_404, name='test_404'),
    path('test-500/', views.test_500, name='test_500'),
    path('test-403/', views.test_403, name='test_403'),
    
    # Template URLs
    path('templates/', views.templates_overview_view, name='templates_overview'),
    path('templates/student-jobs/', views.student_jobs_template_view, name='student_jobs_template'),
    path('templates/student-revision/', views.student_revision_template_view, name='student_revision_template'),
    path('templates/professionals-jobs/', views.professionals_jobs_template_view, name='professionals_jobs_template'),
    path('templates/create/<str:template_type>/', views.create_from_template_view, name='create_from_template'),
    
    # Project URLs
    path('projects/', views.project_list_view, name='project_list'),
    path('projects/create/', views.project_create_view, name='project_create'),
    path('projects/<int:pk>/', views.project_grid_view, name='project_grid'),
    path('projects/<int:pk>/edit/', views.project_edit_view, name='project_edit'),
    path('projects/<int:pk>/delete/', views.project_delete_view, name='project_delete'),
    path('projects/<int:pk>/clear-completed/', views.delete_completed_tasks_view, name='delete_completed_tasks'),
    
    # Task URLs
    path('projects/<int:project_pk>/tasks/create/<int:row_pk>/<int:col_pk>/', views.task_create_view, name='task_create'),
    path('tasks/<int:task_pk>/edit/', views.task_edit_view, name='task_edit'),
    path('tasks/<int:task_pk>/toggle/', views.task_toggle_complete_view, name='task_toggle_complete'),
    path('tasks/<int:task_pk>/delete/', views.task_delete_view, name='task_delete'),
    
    # Row URLs
    path('projects/<int:project_pk>/rows/create/', views.row_create_view, name='row_create'),
    path('projects/<int:project_pk>/rows/<int:row_pk>/edit/', views.row_edit_view, name='row_edit'),
    path('projects/<int:project_pk>/rows/<int:row_pk>/delete/', views.row_delete_view, name='row_delete'),
    
    # Column URLs
    path('projects/<int:project_pk>/columns/create/', views.column_create_view, name='column_create'),
    path('projects/<int:project_pk>/columns/<int:col_pk>/edit/', views.column_edit_view, name='column_edit'),
    path('projects/<int:project_pk>/columns/<int:col_pk>/delete/', views.column_delete_view, name='column_delete'),
]