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
from pages.models import Project, RowHeader, ColumnHeader, Task
from pages.forms import ProjectForm, RowHeaderForm, ColumnHeaderForm, QuickTaskForm, TaskForm
import logging

# Set up logging
logger = logging.getLogger(__name__)


@login_required
def project_list_view(request):
    projects = Project.objects.filter(user=request.user)
    return render(request, 'pages/grid/overview/project_list.html', {'projects': projects})


@login_required
def project_create_view(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.user = request.user
            project.save()
            
            # Create default headers for the new project
            category_col = ColumnHeader.objects.create(
                project=project, 
                name='Time / Category', 
                order=0, 
                is_category_column=True
            )
            ColumnHeader.objects.create(project=project, name='Column 1 (Rename)', order=1)
            ColumnHeader.objects.create(project=project, name='Column 2 (Rename)', order=2)
            ColumnHeader.objects.create(project=project, name='Column 3 (Rename)', order=3)

            RowHeader.objects.create(project=project, name='Row 1 (Rename)', order=0)
            RowHeader.objects.create(project=project, name='Row 2 (Rename)', order=1)
            RowHeader.objects.create(project=project, name='Row 3 (Rename)', order=2)
            RowHeader.objects.create(project=project, name='Row 4 (Rename)', order=3)
            
            logger.info(f'User {request.user.username} created project: {project.name}')
            messages.success(request, f'Project "{project.name}" created successfully!')
            return redirect('pages:project_grid', pk=project.pk)
        else:
            logger.warning(f'User {request.user.username} failed to create project - form errors: {form.errors}')
    else:
        form = ProjectForm()
    
    return render(request, 'pages/grid/actions_new_page/project_form.html', {'form': form, 'title': 'Create Project'})


def project_edit_view(request, pk):
    project = get_object_or_404(Project, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, f'Project "{project.name}" updated successfully!')
            return redirect('pages:project_grid', pk=project.pk)
    else:
        form = ProjectForm(instance=project)
    
    return render(request, 'pages/grid/actions_new_page/project_form.html', {
        'form': form, 
        'project': project, 
        'title': 'Edit Project'
    })


def project_delete_view(request, pk):
    project = get_object_or_404(Project, pk=pk, user=request.user)
    if request.method == 'POST':
        project_name = project.name
        project.delete()
        messages.success(request, f'Project "{project_name}" deleted successfully!')
        return redirect('pages:project_list')
    
    return render(request, 'pages/grid/actions_new_page/project_confirm_delete.html', {'project': project})


@login_required
def project_grid_view(request, pk):
    project = get_object_or_404(Project, pk=pk, user=request.user)
    row_headers = project.row_headers.all().order_by('order')
    column_headers = list(project.column_headers.filter(is_category_column=True)) + \
                     list(project.column_headers.filter(is_category_column=False).order_by('order'))
    
    # Create a more efficient tasks lookup
    tasks_by_cell = {}
    all_tasks = project.tasks.all().select_related('row_header', 'column_header')
    
    for task in all_tasks:
        cell_key = f"{task.row_header_id}_{task.column_header_id}"
        if cell_key not in tasks_by_cell:
            tasks_by_cell[cell_key] = []
        tasks_by_cell[cell_key].append(task)

    # Initialize forms for modals
    row_form = RowHeaderForm()
    column_form = ColumnHeaderForm()

    context = {
        'project': project,
        'row_headers': row_headers,
        'column_headers': column_headers,
        'tasks_by_cell': tasks_by_cell,
        'projects': Project.objects.filter(user=request.user),
        'quick_task_form': QuickTaskForm(),
        'row_form': row_form,
        'column_form': column_form,
    }
    return render(request, 'pages/grid/project_grid.html', context)

# Task CRUD Views

@login_required
def task_create_view(request, project_pk, row_pk, col_pk):
    project = get_object_or_404(Project, pk=project_pk, user=request.user)
    row_header = get_object_or_404(RowHeader, pk=row_pk, project=project)
    column_header = get_object_or_404(ColumnHeader, pk=col_pk, project=project)

    if request.method == 'POST':
        form = QuickTaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.row_header = row_header
            task.column_header = column_header
            task.save()
            
            if request.headers.get('HX-Request'):
                # Return just the new task HTML for HTMX to insert
                return render(request, 'pages/grid/actions_in_page/task_item.html', {
                    'task': task,
                })
            
            messages.success(request, f'Task "{task.text}" added successfully!')
            return redirect('pages:project_grid', pk=project.pk)
        else:
            logger.warning(f'User {request.user.username} failed to create task - form errors: {form.errors}')
            if request.headers.get('HX-Request'):
                errors = form.errors.get('text', ['An error occurred'])
                return HttpResponse(
                    f'<div class="text-[var(--delete-button-bg)] text-sm bg-red-50 border border-red-200 rounded-md px-3 py-2 flex items-center"><i class="fas fa-exclamation-triangle mr-2"></i>{errors[0]}</div>',
                    status=422
                )
            messages.error(request, 'Please correct the errors below.')
            return redirect('pages:project_grid', pk=project.pk)
    
    return redirect('pages:project_grid', pk=project.pk)


def task_edit_view(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk, project__user=request.user)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            if request.headers.get('HX-Request'):
                return JsonResponse({
                    'success': True,
                    'message': 'Task updated successfully!'
                })
            messages.success(request, 'Task updated successfully!')
            return redirect('pages:project_grid', pk=task.project.pk)
        else:
            if request.headers.get('HX-Request'):
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                }, status=422)
            messages.error(request, 'Please correct the errors below.')
            return redirect('pages:project_grid', pk=task.project.pk)
    else:
        form = TaskForm(instance=task)
    
    if request.headers.get('HX-Request'):
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
    task = get_object_or_404(Task, pk=task_pk, project__user=request.user)
    
    if request.method == 'POST':
        task.completed = not task.completed
        task.save()
        
        if request.headers.get('HX-Request'):
            return JsonResponse({
                'success': True,
                'completed': task.completed,
                'message': f'Task {"completed" if task.completed else "reopened"} successfully!'
            })
        
        messages.success(request, f'Task {"completed" if task.completed else "reopened"} successfully!')
        return redirect('pages:project_grid', pk=task.project.pk)
    
    return redirect('pages:project_grid', pk=task.project.pk)


@login_required
def task_delete_view(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk, project__user=request.user)
    project_pk = task.project.pk
    task_text = task.text  # Store before deletion
    
    if request.method == 'POST':
        logger.info(f'User {request.user.username} deleted task: "{task_text}" from project: {task.project.name}')
        task.delete()
        if request.headers.get('HX-Request'):
            return HttpResponse('', status=200)
        messages.success(request, 'Task deleted successfully!')
    
    return redirect('pages:project_grid', pk=project_pk)

# Row CRUD Views

def row_create_view(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk, user=request.user)
    
    if request.method == 'POST':
        form = RowHeaderForm(request.POST)
        if form.is_valid():
            row = form.save(commit=False)
            row.project = project
            row.order = project.row_headers.count()
            row.save()
            messages.success(request, f'Row "{row.name}" added successfully!')
            return redirect('pages:project_grid', pk=project.pk)
    else:
        form = RowHeaderForm()
    
    return render(request, 'pages/grid/actions_new_page/grid_item_form.html', {
        'form': form, 
        'project': project, 
        'title': 'Add Row',
        'item_type': 'row'
    })


def row_edit_view(request, project_pk, row_pk):
    project = get_object_or_404(Project, pk=project_pk, user=request.user)
    row = get_object_or_404(RowHeader, pk=row_pk, project=project)
    
    if request.method == 'POST':
        form = RowHeaderForm(request.POST, instance=row)
        if form.is_valid():
            form.save()
            if request.headers.get('HX-Request'):
                return JsonResponse({
                    'success': True,
                    'message': f'Row "{row.name}" updated successfully!'
                })
            messages.success(request, f'Row "{row.name}" updated successfully!')
            return redirect('pages:project_grid', pk=project.pk)
        else:
            if request.headers.get('HX-Request'):
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                }, status=422)
            messages.error(request, 'Please correct the errors below.')
            return redirect('pages:project_grid', pk=project.pk)
    else:
        form = RowHeaderForm(instance=row)
    
    if request.headers.get('HX-Request'):
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
    project = get_object_or_404(Project, pk=project_pk, user=request.user)
    row = get_object_or_404(RowHeader, pk=row_pk, project=project)
    
    if request.method == 'POST':
        row_name = row.name
        row.delete()
        if request.headers.get('HX-Request'):
            return JsonResponse({
                'success': True,
                'message': f'Row "{row_name}" deleted successfully!'
            })
        messages.success(request, f'Row "{row_name}" deleted successfully!')
        return redirect('pages:project_grid', pk=project.pk)
    
    if request.headers.get('HX-Request'):
        return render(request, 'pages/grid/modals/row_delete_content.html', {
            'project': project,
            'row': row
        })
    
# If HTMX request fails, render the normal page

    return render(request, 'pages/grid/actions_new_page/row_confirm_delete.html', {
        'project': project,
        'row': row
    })

# Column CRUD Views

def column_create_view(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk, user=request.user)
    
    if request.method == 'POST':
        form = ColumnHeaderForm(request.POST)
        if form.is_valid():
            column = form.save(commit=False)
            column.project = project
            column.order = project.column_headers.filter(is_category_column=False).count() + 1
            column.save()
            messages.success(request, f'Column "{column.name}" added successfully!')
            return redirect('pages:project_grid', pk=project.pk)
    else:
        form = ColumnHeaderForm()
    
    return render(request, 'pages/grid/actions_new_page/grid_item_form.html', {
        'form': form, 
        'project': project, 
        'title': 'Add Column',
        'item_type': 'column'
    })


def column_edit_view(request, project_pk, col_pk):
    project = get_object_or_404(Project, pk=project_pk, user=request.user)
    column = get_object_or_404(ColumnHeader, pk=col_pk, project=project)
    
    if request.method == 'POST':
        form = ColumnHeaderForm(request.POST, instance=column)
        if form.is_valid():
            form.save()
            if request.headers.get('HX-Request'):
                return JsonResponse({
                    'success': True,
                    'message': f'Column "{column.name}" updated successfully!'
                })
            messages.success(request, f'Column "{column.name}" updated successfully!')
            return redirect('pages:project_grid', pk=project.pk)
        else:
            if request.headers.get('HX-Request'):
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                }, status=422)
            messages.error(request, 'Please correct the errors below.')
            return redirect('pages:project_grid', pk=project.pk)
    else:
        form = ColumnHeaderForm(instance=column)
    
    if request.headers.get('HX-Request'):
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
    project = get_object_or_404(Project, pk=project_pk, user=request.user)
    column = get_object_or_404(ColumnHeader, pk=col_pk, project=project)
    
    if request.method == 'POST':
        column_name = column.name
        column.delete()
        if request.headers.get('HX-Request'):
            return JsonResponse({
                'success': True,
                'message': f'Column "{column_name}" deleted successfully!'
            })
        messages.success(request, f'Column "{column_name}" deleted successfully!')
        return redirect('pages:project_grid', pk=project.pk)
    
    if request.headers.get('HX-Request'):
        return render(request, 'pages/grid/modals/column_delete_content.html', {
            'project': project,
            'column': column
        })

# If HTMX request fails, render the normal page

    return render(request, 'pages/grid/actions_new_page/column_confirm_delete.html', {
        'project': project,
        'column': column
    })

@login_required
def delete_completed_tasks_view(request, pk):
    project = get_object_or_404(Project, pk=pk, user=request.user)
    
    if request.method == 'POST':
        completed_tasks = project.tasks.filter(completed=True)
        count = completed_tasks.count()
        completed_tasks.delete()
        messages.success(request, f'Successfully deleted {count} completed tasks!')
        return redirect('pages:project_grid', pk=project.pk)
    
    return render(request, 'pages/grid/actions_in_page/clear_completed_tasks.html', {
        'project': project
    })

@login_required
def create_from_template_view(request, template_type):
    """Create a new project from a template"""
    if request.method == 'POST':
        # Template configurations
        templates = {
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
        
        if template_type not in templates:
            messages.error(request, 'Invalid template type.')
            return redirect('pages:templates_overview')
        
        template_config = templates[template_type]
        
        # Create the project
        project = Project.objects.create(
            user=request.user,
            name=template_config['name']
        )
        
        # Create the category column
        category_col = ColumnHeader.objects.create(
            project=project,
            name='Time / Category',
            order=0,
            is_category_column=True
        )
        
        # Create columns
        for i, col_name in enumerate(template_config['columns']):
            ColumnHeader.objects.create(
                project=project,
                name=col_name,
                order=i + 1
            )
        
        # Create rows
        for i, row_name in enumerate(template_config['rows']):
            RowHeader.objects.create(
                project=project,
                name=row_name,
                order=i
            )
        
        logger.info(f'User {request.user.username} created project from template: {template_type}')
        messages.success(request, f'Project "{project.name}" created from template successfully!')
        return redirect('pages:project_grid', pk=project.pk)
    
    return redirect('pages:templates_overview')