import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.db.models import Count
from django.db.models.functions import Coalesce
from django.db.models.functions import Greatest
from django.views.decorators.cache import cache_control, never_cache
from django.views.decorators.vary import vary_on_headers
from django.views.decorators.csrf import csrf_exempt
from pages.models import Project, RowHeader, ColumnHeader, Task
from pages.forms import ProjectForm, RowHeaderForm, ColumnHeaderForm, QuickTaskForm, TaskForm
from pages.specific_views_functions.project_views_functions import (
    get_user_project_optimized,
    get_user_task_optimized, 
    get_user_row_optimized,
    get_user_column_optimized,
    process_grid_data_optimized,
    get_projects_for_dropdown,
    handle_htmx_response,
    create_htmx_trigger_response,
    create_json_response,
    handle_form_submission,
    handle_htmx_form_errors,
    render_task_item,
    render_modal_content,
    create_default_project_structure,
    create_project_from_template_config,
    get_template_configurations,
    bulk_delete_completed_tasks,
    log_user_action,
    get_next_order,
    get_next_column_order
)
import logging
from collections import defaultdict

# Set up logging
logger = logging.getLogger(__name__)


@login_required
@cache_control(max_age=60)
def project_list_view(request):
    # Optimize by only loading needed fields and adding task counts
    projects = Project.objects.filter(user=request.user).annotate(
        task_count=Count('tasks'),
        completed_task_count=Count('tasks', filter=Q(tasks__completed=True))
    ).only('id', 'name', 'created_at').order_by('-created_at')
    
    return render(request, 'pages/grid/overview/project_list.html', {'projects': projects})


@login_required
def project_create_view(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.user = request.user
            project.save()
            
            # Use optimized bulk creation
            create_default_project_structure(project)
            
            log_user_action(request.user, 'created project', project.name)
            messages.success(request, f'Grid "{project.name}" created successfully!')
            return redirect('pages:project_grid', pk=project.pk)
        else:
            logger.warning(f'User {request.user.username} failed to create project - form errors: {form.errors}')
    else:
        form = ProjectForm()
    
    return render(request, 'pages/grid/actions_new_page/project_form.html', {'form': form, 'title': 'Create Project'})


def project_edit_view(request, pk):
    project = get_user_project_optimized(pk, request.user, only_fields=['id', 'name', 'user'])
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, f'Grid "{project.name}" updated successfully!')
            return redirect('pages:project_grid', pk=project.pk)
    else:
        form = ProjectForm(instance=project)
    
    return render(request, 'pages/grid/actions_new_page/project_form.html', {
        'form': form, 
        'project': project, 
        'title': 'Edit Project'
    })


def project_delete_view(request, pk):
    project = get_user_project_optimized(pk, request.user, only_fields=['id', 'name', 'user'])
    
    if request.method == 'POST':
        project_name = project.name
        project.delete()
        messages.success(request, f'Grid "{project_name}" deleted successfully!')
        return redirect('pages:project_list')
    
    return render(request, 'pages/grid/actions_new_page/project_confirm_delete.html', {'project': project})


def is_mobile_device(request):
    """
    Detect if the request is from a mobile device
    """
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    mobile_agents = [
        'mobile', 'android', 'iphone', 'ipad', 'ipod', 'blackberry', 
        'windows phone', 'opera mini', 'palm', 'symbian'
    ]
    return any(agent in user_agent for agent in mobile_agents)

@login_required
def project_grid_view(request, pk):
    """
    Optimized project grid view with single database query and efficient data processing.
    Serves different templates for mobile and desktop.
    """
    # Single optimized query to load all required data at once
    project = get_user_project_optimized(
        pk, 
        request.user,
        select_related=['user'],
        prefetch_related=['row_headers', 'column_headers', 'tasks__row_header', 'tasks__column_header'],
    )

    is_mobile = is_mobile_device(request)

    if is_mobile:
        # --- Mobile-specific data processing ---
        rows = list(project.row_headers.all().order_by('order'))
        columns = list(project.column_headers.all().order_by('order'))
        tasks = list(project.tasks.all())

        # Create a proper nested dictionary structure
        tasks_by_row_col = {}
        for row in rows:
            tasks_by_row_col[row.pk] = {}
            for column in columns:
                if not column.is_category_column:
                    tasks_by_row_col[row.pk][column.pk] = []
        
        # Populate with actual tasks
        for task in tasks:
            if task.row_header_id in tasks_by_row_col and task.column_header_id in tasks_by_row_col[task.row_header_id]:
                tasks_by_row_col[task.row_header_id][task.column_header_id].append(task)

        context = {
            'project': project,
            'rows': rows,
            'columns': [c for c in columns if not c.is_category_column],
            'tasks_by_row_col': tasks_by_row_col,
            'quick_task_form': QuickTaskForm(),
        }
        
        template_name = 'pages/grid/project_grid_mobile.html'
        if request.headers.get('HX-Request'):
            template_name = 'pages/grid/partials/mobile_grid_content.html'
    else:
        # --- Desktop-specific data processing ---
        row_headers, category_column, data_column_headers, tasks_by_cell, row_min_heights = process_grid_data_optimized(project)
        
        context = {
            'project': project,
            'row_headers': row_headers,
            'category_column': category_column,
            'data_column_headers': data_column_headers,
            'tasks_by_cell': tasks_by_cell,
            'row_min_heights': row_min_heights,
            'quick_task_form': QuickTaskForm(),
            'total_data_columns': len(data_column_headers),
        }
        template_name = 'pages/grid/project_grid.html'
        if request.headers.get('HX-Request'):
            template_name = 'pages/grid/partials/grid_content.html'

    # Lazy load projects for dropdown only when needed (non-HTMX, full page loads)
    if not request.headers.get('HX-Request'):
        context['projects'] = get_projects_for_dropdown(request.user)
    
    return render(request, template_name, context)

# Task CRUD Views

@login_required
def task_create_view(request, project_pk, row_pk, col_pk):
    # Use optimized queries
    project = get_user_project_optimized(project_pk, request.user, only_fields=['id', 'name', 'user'])
    row_header = get_user_row_optimized(row_pk, project, only_fields=['id', 'name', 'project'])
    column_header = get_user_column_optimized(col_pk, project, only_fields=['id', 'name', 'project'])

    if request.method == 'POST':
        form = QuickTaskForm(request.POST)
        
        def success_callback(task):
            task.project = project
            task.row_header = row_header
            task.column_header = column_header
            # Set the order to be the next order in this cell
            existing_tasks = Task.objects.filter(
                project=project,
                row_header=row_header,
                column_header=column_header
            )
            task.order = get_next_order(existing_tasks)
        
        def htmx_response(task):
            return render(request, 'pages/grid/actions_in_page/task_item.html', {'task': task})
        
        def success_message_callback(task):
            return f'Task "{task.text}" added successfully!'
        
        success, result = handle_form_submission(
            request, 
            form, 
            success_callback=success_callback,
            htmx_response=htmx_response,
            success_message_callback=success_message_callback
        )
        
        if success:
            # For HTMX requests, result is the HTMX response; for regular requests, redirect
            if request.headers.get('HX-Request'):
                return result
            else:
                return redirect('pages:project_grid', pk=project.pk)
        else:
            logger.warning(f'User {request.user.username} failed to create task - form errors: {form.errors}')
            error_response = handle_htmx_form_errors(request, form)
            if error_response:
                return error_response
            return redirect('pages:project_grid', pk=project.pk)
    
    return redirect('pages:project_grid', pk=project.pk)


@login_required
def task_edit_view(request, task_pk):
    # For JSON requests, load the full task to ensure proper saving
    if request.method == 'POST' and request.headers.get('Content-Type') == 'application/json':
        task = get_user_task_optimized(
            task_pk, 
            request.user, 
            select_related=['project', 'project__user']
            # Don't restrict fields for JSON updates to ensure proper saving
        )
    else:
        # For regular form requests, use optimized loading
        task = get_user_task_optimized(
            task_pk, 
            request.user, 
            select_related=['project', 'project__user'],
            only_fields=['id', 'text', 'completed', 'project__id', 'project__user', 'project__name']
        )
    
    if request.method == 'POST':
        # Check if this is a JSON request for inline editing
        if request.headers.get('Content-Type') == 'application/json':
            try:
                import json
                data = json.loads(request.body)
                new_text = data.get('text', '').strip()
                
                if not new_text:
                    return JsonResponse({'success': False, 'error': 'Task text cannot be empty'}, status=400)
                
                # Update the task
                old_text = task.text
                task.text = new_text
                
                # Try to save and log the result
                try:
                    # Force a database save
                    task.save(update_fields=['text', 'updated_at'])
                    
                    # Verify the save worked by refreshing from database
                    task.refresh_from_db()
                    
                    return JsonResponse({
                        'success': True, 
                        'message': 'Task updated successfully!',
                        'task_id': task.pk,
                        'text': task.text
                    })
                    
                except Exception as save_error:
                    logger.error(f"Error saving task {task_pk}: {save_error}")
                    return JsonResponse({'success': False, 'error': f'Save failed: {str(save_error)}'}, status=500)
                
            except json.JSONDecodeError as json_error:
                logger.error(f"JSON decode error for task {task_pk}: {json_error}")
                return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
            except Exception as e:
                logger.error(f"Error updating task {task_pk}: {e}")
                return JsonResponse({'success': False, 'error': 'Failed to update task'}, status=500)
        
        # Handle regular form submission
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            updated_task = form.save()
            if request.headers.get('HX-Request'):
                return create_json_response(
                    True,
                    'Task updated successfully!',
                    task_id=updated_task.pk,
                    task_html=render_task_item(updated_task, request)
                )
            messages.success(request, 'Task updated successfully!')
            return redirect('pages:project_grid', pk=task.project.pk)
        else:
            error_response = handle_htmx_form_errors(request, form)
            if error_response:
                return error_response
            return redirect('pages:project_grid', pk=task.project.pk)
    else:
        form = TaskForm(instance=task)
    
    modal_content = render_modal_content(request, 'pages/grid/modals/task_form_content.html', {
        'form': form,
        'task': task,
        'title': 'Edit Task'
    })
    
    if modal_content:
        return render(request, 'pages/grid/modals/task_form_content.html', {
            'form': form,
            'task': task,
            'title': 'Edit Task'
        })
    
    return render(request, 'pages/grid/task_form.html', {
        'form': form, 
        'task': task, 
        'title': 'Edit Task'
    })


@login_required
def task_toggle_complete_view(request, task_pk):
    task = get_user_task_optimized(
        task_pk, 
        request.user,
        select_related=['project'],
        only_fields=['id', 'completed', 'project__id', 'project__user']
    )
    
    if request.method == 'POST':
        task.completed = not task.completed
        task.save()
        
        if request.headers.get('HX-Request'):
            return create_json_response(
                True,
                f'Task {"completed" if task.completed else "reopened"} successfully!',
                completed=task.completed
            )
        
        messages.success(request, f'Task {"completed" if task.completed else "reopened"} successfully!')
        return redirect('pages:project_grid', pk=task.project.pk)
    
    return redirect('pages:project_grid', pk=task.project.pk)


@login_required
def task_delete_view(request, task_pk):
    task = get_user_task_optimized(
        task_pk,
        request.user,
        select_related=['project'],
        only_fields=['id', 'text', 'project__id', 'project__user', 'project__name']
    )
    project_pk = task.project.pk
    task_text = task.text
    
    if request.method == 'POST':
        log_user_action(request.user, 'deleted task', task_text, task.project.name)
        task.delete()
        
        if request.headers.get('HX-Request'):
            return create_json_response(True, 'Task deleted successfully!')
        
        messages.success(request, 'Task deleted successfully!')
    
    return redirect('pages:project_grid', pk=project_pk)

# Row CRUD Views

def row_create_view(request, project_pk):
    project = get_user_project_optimized(project_pk, request.user, only_fields=['id', 'name', 'user'])
    
    if request.method == 'POST':
        form = RowHeaderForm(request.POST)
        
        def success_callback(row):
            row.project = project
            row.order = get_next_order(project.row_headers)
        
        def htmx_response(row):
            return create_htmx_trigger_response('refreshGrid')
        
        def success_message_callback(row):
            return f'Row "{row.name}" added successfully!'
        
        success, result = handle_form_submission(
            request,
            form,
            success_callback=success_callback,
            htmx_response=htmx_response,
            success_message_callback=success_message_callback
        )
        
        if success:
            # For HTMX requests, result is the HTMX response; for regular requests, redirect
            if request.headers.get('HX-Request'):
                return result
            else:
                return redirect('pages:project_grid', pk=project.pk)
    else:
        form = RowHeaderForm()
    
    modal_content = render_modal_content(request, 'pages/grid/modals/row_form_content.html', {
        'form': form,
        'project': project,
        'title': 'Add Row'
    })
    
    if modal_content:
        return render(request, 'pages/grid/modals/row_form_content.html', {
            'form': form,
            'project': project,
            'title': 'Add Row'
        })
    
    return render(request, 'pages/grid/actions_new_page/grid_item_form.html', {
        'form': form, 
        'project': project, 
        'title': 'Add Row',
        'item_type': 'row'
    })


def row_edit_view(request, project_pk, row_pk):
    project = get_user_project_optimized(project_pk, request.user, only_fields=['id', 'name', 'user'])
    row = get_user_row_optimized(
        row_pk, 
        project, 
        select_related=['project'],
        only_fields=['id', 'name', 'project__id']
    )
    
    if request.method == 'POST':
        # Check if this is a JSON request for inline editing
        if request.headers.get('Content-Type') == 'application/json':
            try:
                data = json.loads(request.body)
                row_name = data.get('row_name', '').strip()
                if row_name:
                    row.name = row_name
                    row.save()
                    return create_json_response(
                        True,
                        f'Row "{row.name}" updated successfully!',
                        row_name=row.name
                    )
                else:
                    return create_json_response(False, 'Row name cannot be empty')
            except json.JSONDecodeError:
                return create_json_response(False, 'Invalid JSON data')
        
        # Handle regular form submission
        form = RowHeaderForm(request.POST, instance=row)
        if form.is_valid():
            form.save()
            if request.headers.get('HX-Request'):
                return create_json_response(
                    True,
                    f'Row "{row.name}" updated successfully!',
                    row_name=row.name
                )
            messages.success(request, f'Row "{row.name}" updated successfully!')
            return redirect('pages:project_grid', pk=project.pk)
        else:
            error_response = handle_htmx_form_errors(request, form)
            if error_response:
                return error_response
            return redirect('pages:project_grid', pk=project.pk)
    else:
        form = RowHeaderForm(instance=row)
    
    modal_content = render_modal_content(request, 'pages/grid/modals/row_form_content.html', {
        'form': form,
        'project': project,
        'row': row,
        'title': 'Edit Row'
    })
    
    if modal_content:
        return render(request, 'pages/grid/modals/row_form_content.html', {
            'form': form,
            'project': project,
            'row': row,
            'title': 'Edit Row'
        })
    
    return render(request, 'pages/grid/actions_new_page/grid_item_form.html', {
        'form': form,
        'project': project,
        'item': row,
        'item_type': 'row',
        'title': 'Edit Row'
    })


def row_delete_view(request, project_pk, row_pk):
    project = get_user_project_optimized(project_pk, request.user, only_fields=['id', 'name', 'user'])
    row = get_user_row_optimized(row_pk, project, only_fields=['id', 'name', 'project'])
    
    if request.method == 'POST':
        row_name = row.name
        row.delete()
        
        if request.headers.get('HX-Request'):
            return create_json_response(True, f'Row "{row_name}" deleted successfully!')
        
        messages.success(request, f'Row "{row_name}" deleted successfully!')
        return redirect('pages:project_grid', pk=project.pk)
    
    modal_content = render_modal_content(request, 'pages/grid/modals/row_delete_content.html', {
        'project': project,
        'row': row
    })
    
    if modal_content:
        return render(request, 'pages/grid/modals/row_delete_content.html', {
            'project': project,
            'row': row
        })
    
    return render(request, 'pages/grid/actions_new_page/row_confirm_delete.html', {
        'project': project,
        'row': row
    })

# Column CRUD Views

def column_create_view(request, project_pk):
    project = get_user_project_optimized(project_pk, request.user, only_fields=['id', 'name', 'user'])
    
    if request.method == 'POST':
        form = ColumnHeaderForm(request.POST)
        
        def success_callback(column):
            column.project = project
            column.order = get_next_column_order(project)
        
        def htmx_response(column):
            return create_htmx_trigger_response('scrollToEnd')
        
        def success_message_callback(column):
            return f'Column "{column.name}" added successfully!'
        
        success, result = handle_form_submission(
            request,
            form,
            success_callback=success_callback,
            htmx_response=htmx_response,
            success_message_callback=success_message_callback
        )
        
        if success:
            # For HTMX requests, result is the HTMX response; for regular requests, redirect
            if request.headers.get('HX-Request'):
                return result
            else:
                return redirect('pages:project_grid', pk=project.pk)
    else:
        form = ColumnHeaderForm()
    
    modal_content = render_modal_content(request, 'pages/grid/modals/column_form_content.html', {
        'form': form,
        'project': project,
        'title': 'Add Column'
    })
    
    if modal_content:
        return render(request, 'pages/grid/modals/column_form_content.html', {
            'form': form,
            'project': project,
            'title': 'Add Column'
        })
    
    return render(request, 'pages/grid/actions_new_page/grid_item_form.html', {
        'form': form, 
        'project': project, 
        'title': 'Add Column',
        'item_type': 'column'
    })


def column_edit_view(request, project_pk, col_pk):
    project = get_user_project_optimized(project_pk, request.user, only_fields=['id', 'name', 'user'])
    column = get_user_column_optimized(
        col_pk, 
        project, 
        select_related=['project'],
        only_fields=['id', 'name', 'project__id']
    )
    
    if request.method == 'POST':
        # Check if this is a JSON request for inline editing
        if request.headers.get('Content-Type') == 'application/json':
            try:
                data = json.loads(request.body)
                col_name = data.get('col_name', '').strip()
                if col_name:
                    column.name = col_name
                    column.save()
                    return create_json_response(
                        True,
                        f'Column "{column.name}" updated successfully!',
                        col_name=column.name
                    )
                else:
                    return create_json_response(False, 'Column name cannot be empty')
            except json.JSONDecodeError:
                return create_json_response(False, 'Invalid JSON data')
        
        # Handle regular form submission
        form = ColumnHeaderForm(request.POST, instance=column)
        if form.is_valid():
            form.save()
            if request.headers.get('HX-Request'):
                return create_json_response(
                    True,
                    f'Column "{column.name}" updated successfully!',
                    col_name=column.name
                )
            messages.success(request, f'Column "{column.name}" updated successfully!')
            return redirect('pages:project_grid', pk=project.pk)
        else:
            error_response = handle_htmx_form_errors(request, form)
            if error_response:
                return error_response
            return redirect('pages:project_grid', pk=project.pk)
    else:
        form = ColumnHeaderForm(instance=column)
    
    modal_content = render_modal_content(request, 'pages/grid/modals/column_form_content.html', {
        'form': form,
        'project': project,
        'column': column,
        'title': 'Edit Column'
    })
    
    if modal_content:
        return render(request, 'pages/grid/modals/column_form_content.html', {
            'form': form,
            'project': project,
            'column': column,
            'title': 'Edit Column'
        })
    
    return render(request, 'pages/grid/actions_new_page/grid_item_form.html', {
        'form': form,
        'project': project,
        'item': column,
        'item_type': 'column',
        'title': 'Edit Column'
    })


def column_delete_view(request, project_pk, col_pk):
    project = get_user_project_optimized(project_pk, request.user, only_fields=['id', 'name', 'user'])
    column = get_user_column_optimized(col_pk, project, only_fields=['id', 'name', 'project'])
    
    if request.method == 'POST':
        column_name = column.name
        column.delete()
        
        if request.headers.get('HX-Request'):
            return create_htmx_trigger_response('resetGridToInitial')
        
        messages.success(request, f'Column "{column_name}" deleted successfully!')
        return redirect('pages:project_grid', pk=project.pk)
    
    modal_content = render_modal_content(request, 'pages/grid/modals/column_delete_content.html', {
        'project': project,
        'column': column
    })
    
    if modal_content:
        return render(request, 'pages/grid/modals/column_delete_content.html', {
            'project': project,
            'column': column
        })
    
    return render(request, 'pages/grid/actions_new_page/column_confirm_delete.html', {
        'project': project,
        'column': column
    })

@login_required
def delete_completed_tasks_view(request, pk):
    project = get_user_project_optimized(pk, request.user, only_fields=['id', 'name', 'user'])
    
    if request.method == 'POST':
        count = bulk_delete_completed_tasks(project)
        if count > 0:
            messages.success(request, f'Successfully deleted {count} completed tasks!')
        else:
            messages.info(request, 'No completed tasks to delete.')
        return redirect('pages:project_grid', pk=project.pk)
    
    return render(request, 'pages/grid/actions_in_page/clear_completed_tasks.html', {
        'project': project
    })

@login_required
def create_from_template_view(request, template_type):
    """Create a new project from a template"""
    if request.method == 'POST':
        templates = get_template_configurations()
        
        if template_type not in templates:
            messages.error(request, 'Invalid template type.')
            return redirect('pages:templates_overview')
        
        template_config = templates[template_type]
        project = create_project_from_template_config(request.user, template_config)
        
        log_user_action(request.user, f'created project from template: {template_type}', project.name)
        messages.success(request, f'Grid "{project.name}" created from template successfully!')
        return redirect('pages:project_grid', pk=project.pk)
    
    return redirect('pages:templates_overview')

@login_required
def task_reorder_view(request, project_pk):
    """Handle task reordering via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            task_order = data.get('task_order', [])

            if not task_order:
                return JsonResponse({'success': False, 'error': 'No task order provided'}, status=400)

            # Verify project exists and user has access
            project = get_user_project_optimized(project_pk, request.user, only_fields=['id', 'name', 'user'])
            if not project:
                return JsonResponse({'success': False, 'error': 'Project not found'}, status=404)

            # Group tasks by their new container (row, col) to handle order properly
            container_tasks = {}
            for index, task_data in enumerate(task_order):
                task_id = task_data.get('id')
                new_row = task_data.get('row')
                new_col = task_data.get('col')
                
                if not task_id or not new_row or not new_col:
                    continue
                
                container_key = f"{new_row}_{new_col}"
                if container_key not in container_tasks:
                    container_tasks[container_key] = []
                container_tasks[container_key].append((task_id, index))

            # Update tasks in each container with proper ordering
            for container_key, tasks_in_container in container_tasks.items():
                # Sort by the original index to maintain the order within this container
                tasks_in_container.sort(key=lambda x: x[1])
                
                for container_order, (task_id, _) in enumerate(tasks_in_container):
                    try:
                        task = Task.objects.get(id=task_id, project=project)
                        
                        # Update order within the container
                        task.order = container_order
                        
                        # Update row and column if they've changed (cross-container move)
                        new_row, new_col = container_key.split('_')
                        
                        if new_row != str(task.row_header.pk):
                            try:
                                new_row_header = RowHeader.objects.get(id=new_row, project=project)
                                task.row_header = new_row_header
                            except RowHeader.DoesNotExist:
                                logger.warning(f"Row header {new_row} not found for project {project_pk}")
                                continue
                        
                        if new_col != str(task.column_header.pk):
                            try:
                                new_column_header = ColumnHeader.objects.get(id=new_col, project=project)
                                task.column_header = new_column_header
                            except ColumnHeader.DoesNotExist:
                                logger.warning(f"Column header {new_col} not found for project {project_pk}")
                                continue
                        
                        # Save all changes
                        task.save()
                        
                    except Task.DoesNotExist:
                        logger.warning(f"Task {task_id} not found for project {project_pk}")
                        continue

            log_user_action(request.user, 'reordered tasks', f'in project {project.name}')
            return JsonResponse({'success': True, 'message': 'Task order and position updated successfully'})
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            logger.error(f"Error reordering tasks for project {project_pk}: {e}")
            return JsonResponse({'success': False, 'error': 'Failed to reorder tasks'}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)