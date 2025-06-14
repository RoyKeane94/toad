from django.contrib import admin
from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    # Home and project list
    path('', views.home, name='home'),
    path('projects/', views.project_list_view, name='project_list'),
    
    # Project CRUD
    path('projects/create/', views.project_create_view, name='project_create'),
    path('projects/<int:pk>/', views.project_grid_view, name='project_grid'),
    path('projects/<int:pk>/edit/', views.project_edit_view, name='project_edit'),
    path('projects/<int:pk>/delete/', views.project_delete_view, name='project_delete'),
    path('projects/<int:pk>/delete-completed/', views.delete_completed_tasks_view, name='delete_completed_tasks'),
    
    # Task CRUD
    path('projects/<int:project_pk>/tasks/create/<int:row_pk>/<int:col_pk>/', views.task_create_view, name='task_create'),
    path('tasks/<int:task_pk>/toggle/', views.task_toggle_complete_view, name='task_toggle_complete'),
    path('tasks/<int:task_pk>/edit/', views.task_edit_view, name='task_edit'),
    path('tasks/<int:task_pk>/delete/', views.task_delete_view, name='task_delete'),
    
    # Row CRUD
    path('projects/<int:project_pk>/rows/create/', views.row_create_view, name='row_create'),
    path('projects/<int:project_pk>/rows/<int:row_pk>/edit/', views.row_edit_view, name='row_edit'),
    path('projects/<int:project_pk>/rows/<int:row_pk>/delete/', views.row_delete_view, name='row_delete'),
    
    # Column CRUD
    path('projects/<int:project_pk>/columns/create/', views.column_create_view, name='column_create'),
    path('projects/<int:project_pk>/columns/<int:col_pk>/edit/', views.column_edit_view, name='column_edit'),
    path('projects/<int:project_pk>/columns/<int:col_pk>/delete/', views.column_delete_view, name='column_delete'),
]