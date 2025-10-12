from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.template.loader import render_to_string
from django.db.models import Count, Q
from pages.models import Project, RowHeader, ColumnHeader, Task
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

# Permission and Query Helpers

def get_user_project_optimized(project_pk, user, select_related=None, prefetch_related=None, only_fields=None):
    """Get project with optimized queries and permission check"""
    # Include projects where user is owner OR part of team_toad_user
    queryset = Project.objects.filter(Q(user=user) | Q(team_toad_user=user))
    
    if select_related:
        queryset = queryset.select_related(*select_related)
    if prefetch_related:
        queryset = queryset.prefetch_related(*prefetch_related)
    if only_fields:
        queryset = queryset.only(*only_fields)
    
    return get_object_or_404(queryset, pk=project_pk)

def get_user_task_optimized(task_pk, user, select_related=None, only_fields=None):
    """Get task with optimized queries and permission check"""
    # Include tasks from projects where user is owner OR part of team_toad_user
    queryset = Task.objects.filter(Q(project__user=user) | Q(project__team_toad_user=user))
    
    if select_related:
        queryset = queryset.select_related(*select_related)
    if only_fields:
        queryset = queryset.only(*only_fields)
    
    return get_object_or_404(queryset, pk=task_pk)

def get_user_row_optimized(row_pk, project, select_related=None, only_fields=None):
    """Get row header with optimized queries and permission check"""
    queryset = RowHeader.objects.filter(project=project)
    
    if select_related:
        queryset = queryset.select_related(*select_related)
    if only_fields:
        queryset = queryset.only(*only_fields)
    
    return get_object_or_404(queryset, pk=row_pk)

def get_user_column_optimized(col_pk, project, select_related=None, only_fields=None):
    """Get column header with optimized queries and permission check"""
    queryset = ColumnHeader.objects.filter(project=project)
    
    if select_related:
        queryset = queryset.select_related(*select_related)
    if only_fields:
        queryset = queryset.only(*only_fields)
    
    return get_object_or_404(queryset, pk=col_pk)

# Data Processing Helpers

def process_grid_data_optimized(project):
    """
    Optimized grid data processing with single-pass algorithms
    Returns: (row_headers, category_column, data_column_headers, tasks_by_cell, row_min_heights)
    """
    # Access prefetched data - no additional queries
    row_headers = list(project.row_headers.all())
    all_column_headers = list(project.column_headers.all())
    all_tasks = list(project.tasks.all())
    
    # Separate category and data columns in single pass
    category_column = None
    data_column_headers = []
    
    for col in all_column_headers:
        if col.is_category_column:
            category_column = col
        else:
            data_column_headers.append(col)
    
    # Optimized task grouping with defaultdict (more efficient than manual dict handling)
    tasks_by_cell = defaultdict(list)
    tasks_by_row = defaultdict(list)
    
    for task in all_tasks:
        cell_key = f"{task.row_header_id}_{task.column_header_id}"
        tasks_by_cell[cell_key].append(task)
        tasks_by_row[task.row_header_id].append(task)
    
    # Sort tasks by order field within each cell to respect database ordering
    for cell_key in tasks_by_cell:
        tasks_by_cell[cell_key].sort(key=lambda task: task.order)
    
    # Optimized row height calculation with vectorized operations
    row_min_heights = {}
    for row_header in row_headers:
        row_id = row_header.pk
        row_tasks = tasks_by_row.get(row_id, [])
        
        if row_tasks:
            # Vectorized height calculation
            max_content_height = max(
                max(len(task.text.split('\n')), len(task.text) // 60) * 25
                for task in row_tasks
            )
            row_min_heights[row_id] = max(200, max_content_height + 120)
        else:
            row_min_heights[row_id] = 200
    
    return row_headers, category_column, data_column_headers, dict(tasks_by_cell), row_min_heights

def get_projects_for_dropdown(user):
    """Get optimized project list for dropdown"""
    # Include projects where user is owner OR part of team_toad_user
    return Project.objects.filter(
        Q(user=user) | Q(team_toad_user=user)
    ).distinct().only('id', 'name').order_by('name')

# HTMX Response Helpers

def handle_htmx_response(request, success_response, error_response=None, success_message=None):
    """Handle HTMX response patterns"""
    if request.headers.get('HX-Request'):
        return success_response
    
    if success_message:
        messages.success(request, success_message)
    
    return error_response if error_response else success_response

def create_htmx_trigger_response(trigger_name, status=204):
    """Create HTMX trigger response"""
    response = HttpResponse(status=status)
    response['HX-Trigger'] = trigger_name
    return response

def create_json_response(success, message=None, **kwargs):
    """Create standardized JSON response"""
    response_data = {'success': success}
    if message:
        response_data['message'] = message
    response_data.update(kwargs)
    return JsonResponse(response_data)

# Form Handling Helpers

def handle_form_submission(request, form, success_callback=None, htmx_response=None, success_message_callback=None):
    """Handle common form submission patterns"""
    if form.is_valid():
        instance = form.save(commit=False)
        if success_callback:
            success_callback(instance)
        instance.save()
        
        # Handle success message for non-HTMX requests
        if success_message_callback and not request.headers.get('HX-Request'):
            success_message = success_message_callback(instance)
            messages.success(request, success_message)
        
        # Return HTMX response if needed, otherwise return success status
        if request.headers.get('HX-Request') and htmx_response:
            return True, htmx_response(instance)
        
        return True, instance
    
    return False, form

def handle_htmx_form_errors(request, form):
    """Handle form errors for HTMX requests"""
    if request.headers.get('HX-Request'):
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=422)
    
    messages.error(request, 'Please correct the errors below.')
    return None

# Template Rendering Helpers

def render_task_item(task, request=None):
    """Render task item HTML"""
    return render_to_string('pages/grid/actions_in_page/task_item.html', {
        'task': task
    }, request=request)

def render_modal_content(request, template_name, context):
    """Render modal content for HTMX requests"""
    if request.headers.get('HX-Request'):
        return render_to_string(template_name, context, request=request)
    return None

# Project Creation Helpers

def create_default_project_structure(project):
    """Create minimal grid structure for new project"""
    # Create category column
    ColumnHeader.objects.create(
        project=project, 
        name='Time / Category', 
        order=0, 
        is_category_column=True
    )
    
    # Create single data column with project name
    data_column = ColumnHeader.objects.create(
        project=project, 
        name=project.name, 
        order=1
    )
    
    # Create single row
    row = RowHeader.objects.create(
        project=project, 
        name='Quick Actions', 
        order=0
    )
    
    # Create single task
    Task.objects.create(
        project=project,
        row_header=row,
        column_header=data_column,
        text='Begin by decluttering your mind'
    )

def create_project_from_template_config(user, template_config):
    """Create project from template configuration"""
    # Create the project
    project = Project.objects.create(
        user=user,
        name=template_config['name']
    )
    
    # Create the category column
    ColumnHeader.objects.create(
        project=project,
        name='Time / Category',
        order=0,
        is_category_column=True
    )
    
    # Bulk create columns
    columns = [
        ColumnHeader(project=project, name=col_name, order=i + 1)
        for i, col_name in enumerate(template_config['columns'])
    ]
    ColumnHeader.objects.bulk_create(columns)
    
    # Bulk create rows
    rows = [
        RowHeader(project=project, name=row_name, order=i)
        for i, row_name in enumerate(template_config['rows'])
    ]
    RowHeader.objects.bulk_create(rows)
    
    return project

# Template Configurations

def get_template_configurations():
    """Get all template configurations"""
    return {
        'student_jobs': {
            'name': 'Student Job Applications',
            'rows': [
                'Quick Apply (< 30 min)',
                'Standard Apply (30 min - 1 hr)', 
                'Detailed Apply (1-3 hrs)',
                'Major Investment (3+ hrs)'
            ],
            'columns': [
                'Research',
                'Applied', 
                'Interview',
                'Final Result'
            ]
        },
        'student_revision': {
            'name': 'Student Revision Planner',
            'rows': [
                'High Priority (< 1 hour)',
                'Medium Priority (1-3 hours)',
                'Study Sessions (3-5 hours)',
                'Deep Dive (5+ hours)'
            ],
            'columns': [
                'Not Started',
                'In Progress',
                'Review Needed',
                'Exam Ready'
            ]
        },
        'professionals_jobs': {
            'name': 'Professional Career Tracker',
            'rows': [
                'Quick Connections (< 30 min)',
                'Strategic Outreach (1-2 hrs)',
                'Major Opportunity (3+ hrs)'
            ],
            'columns': [
                'Networking',
                'Applications',
                'Interviews', 
                'Negotiations'
            ]
        }
    }

# Deletion Helpers

def bulk_delete_completed_tasks(project):
    """Efficiently delete completed tasks"""
    completed_tasks = project.tasks.filter(completed=True)
    count = completed_tasks.count()
    if count > 0:
        completed_tasks.delete()
        return count
    return 0

# Logging Helpers

def log_user_action(user, action, item_name, project_name=None):
    """Log user actions consistently"""
    if project_name:
        logger.info(f'User {user.username} {action}: "{item_name}" from project: {project_name}')
    else:
        logger.info(f'User {user.username} {action}: {item_name}')

# Ordering Helpers

def get_next_order(queryset, field_name='order'):
    """Get next order value for ordered items"""
    return queryset.count()

def get_next_column_order(project):
    """Get next column order (excluding category column)"""
    return project.column_headers.filter(is_category_column=False).count() + 1
