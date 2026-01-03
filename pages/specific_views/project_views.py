import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.db.models import Q, Prefetch
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
from pages.models import Project, RowHeader, ColumnHeader, Task, PersonalTemplate, TemplateRowHeader, TemplateColumnHeader, TemplateTask, ProjectGroup
from accounts.models import User, SubscriptionGroup
from pages.forms import ProjectForm, RowHeaderForm, ColumnHeaderForm, QuickTaskForm, TaskForm, ProjectGroupForm, ProjectGroupAssignmentForm
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
def project_list_view(request):
    # Get all active (non-archived) projects with their groups and task counts
    # Include projects where user is owner OR part of team_toad_user
    # Optimized query with minimal fields and efficient prefetching
    projects = Project.objects.filter(
        Q(user=request.user) | Q(team_toad_user=request.user),
        is_archived=False
    ).select_related(
        'project_group'
    ).prefetch_related(
        Prefetch('team_toad_user', queryset=User.objects.only('id', 'first_name', 'last_name'))
    ).annotate(
        task_count=Count('tasks', distinct=True),
        completed_task_count=Count('tasks', filter=Q(tasks__completed=True), distinct=True)
    ).distinct().order_by('project_group', 'order', '-created_at')
    
    # Manually group projects by their project_group
    grouped_projects = {}
    ungrouped_projects = []
    
    for project in projects:
        if project.project_group:
            group_id = project.project_group.id
            if group_id not in grouped_projects:
                grouped_projects[group_id] = {
                    'group': project.project_group,
                    'projects': []
                }
            grouped_projects[group_id]['projects'].append(project)
        else:
            ungrouped_projects.append(project)
    
    # Convert to list format for template and sort groups by creation date
    grouped_projects_list = sorted(list(grouped_projects.values()), key=lambda x: x['group'].created_at)
    
    # Get user's personal templates (only needed fields)
    personal_templates = PersonalTemplate.objects.filter(
        user=request.user
    ).only('id', 'name', 'created_at').order_by('name')
    
    # Get archived projects (owner OR team member)
    archived_projects = Project.objects.filter(
        Q(user=request.user) | Q(team_toad_user=request.user),
        is_archived=True
    ).select_related(
        'project_group'
    ).prefetch_related(
        Prefetch('team_toad_user', queryset=User.objects.only('id', 'first_name', 'last_name'))
    ).annotate(
        task_count=Count('tasks', distinct=True),
        completed_task_count=Count('tasks', filter=Q(tasks__completed=True), distinct=True)
    ).distinct().order_by('-created_at')
    
    context = {
        'projects': projects,  # Keep for backward compatibility
        'grouped_projects': grouped_projects_list,
        'ungrouped_projects': ungrouped_projects,
        'personal_templates': personal_templates,
        'archived_projects': archived_projects,
        'user_tier': getattr(request.user, 'tier', 'free'),
    }
    
    return render(request, 'pages/grid/overview/project_list.html', context)


@login_required
def project_create_view(request):
    # Check grid limit based on user tier
    user_tier = getattr(request.user, 'tier', 'free')
    active_project_count = Project.objects.filter(user=request.user, is_archived=False).count()
    
    if user_tier == 'free':
        if active_project_count >= 2:
            messages.error(request, 'Free users can have a maximum of 2 active grids. Please upgrade to Personal to create more grids.')
            from django.urls import reverse
            return redirect(f"{reverse('pages:upgrade_required')}?reason=grid_limit")
    elif user_tier in ['personal', 'personal_trial']:
        if active_project_count >= 10:
            messages.error(request, 'Personal users can have a maximum of 10 active grids. Please archive some grids to create new ones.')
            from django.urls import reverse
            return redirect(f"{reverse('pages:upgrade_required')}?reason=grid_limit&tier=personal")
    
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.user = request.user
            project.save()
            
            # Use optimized bulk creation
            create_default_project_structure(project)
            
            # Update second grid tracking
            if not request.user.second_grid_created:
                active_project_count = Project.objects.filter(user=request.user, is_archived=False).count()
                if active_project_count >= 2:
                    request.user.second_grid_created = True
                    request.user.save(update_fields=['second_grid_created'])
            
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
        # Check if this is a JSON request for inline editing
        if request.headers.get('Content-Type') == 'application/json':
            try:
                data = json.loads(request.body)
                new_name = data.get('name', '').strip()
                
                if not new_name:
                    return JsonResponse({
                        'success': False,
                        'error': 'Project name cannot be empty'
                    })
                
                # Update the project name
                project.name = new_name
                project.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Project name updated successfully',
                    'new_name': new_name
                })
                
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid JSON data'
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                })
        
        # Regular form submission
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, f'Grid "{project.name}" updated successfully!')
            return redirect('pages:project_grid', pk=project.pk)
    else:
        form = ProjectForm(instance=project)
    
    # Check if this is an HTMX request (modal) or regular page request
    if request.headers.get('HX-Request'):
        template_name = 'pages/grid/actions_new_page/project_form_modal.html'
    else:
        template_name = 'pages/grid/actions_new_page/project_form.html'
    
    return render(request, template_name, {
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
    
    # Check if this is an HTMX request (modal) or regular page request
    if request.headers.get('HX-Request'):
        template_name = 'pages/grid/actions_new_page/project_confirm_delete_modal.html'
    else:
        template_name = 'pages/grid/actions_new_page/project_confirm_delete.html'
    
    return render(request, template_name, {'project': project})


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
            'user_tier': getattr(request.user, 'tier', 'free'),
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
            'user_tier': getattr(request.user, 'tier', 'free'),
        }
        template_name = 'pages/grid/project_grid.html'
        if request.headers.get('HX-Request'):
            template_name = 'pages/grid/partials/grid_content.html'

    # Lazy load projects for dropdown only when needed (non-HTMX, full page loads)
    if not request.headers.get('HX-Request'):
        context['projects'] = get_projects_for_dropdown(request.user)
        
        # Add grouped projects data for the grid tabs (including archived projects)
        # Include projects where user is owner OR part of team_toad_user
        # Optimized with Prefetch for team members
        all_projects = Project.objects.filter(
            Q(user=request.user) | Q(team_toad_user=request.user)
        ).select_related(
            'project_group'
        ).prefetch_related(
            Prefetch('team_toad_user', queryset=User.objects.only('id', 'first_name', 'last_name'))
        ).distinct().order_by('project_group', 'order', '-created_at')
        
        # Manually group projects by their project_group
        grouped_projects = {}
        ungrouped_projects = []
        archived_projects = []
        
        for proj in all_projects:
            if proj.is_archived:
                archived_projects.append(proj)
            elif proj.project_group:
                group_id = proj.project_group.id
                if group_id not in grouped_projects:
                    grouped_projects[group_id] = {
                        'group': proj.project_group,
                        'projects': []
                    }
                grouped_projects[group_id]['projects'].append(proj)
            else:
                ungrouped_projects.append(proj)
        
        # Convert to list format for template and sort groups by creation date
        grouped_projects_list = sorted(list(grouped_projects.values()), key=lambda x: x['group'].created_at)
        
        # Convert to list format for template
        context['grouped_projects'] = grouped_projects_list
        context['ungrouped_projects'] = ungrouped_projects
        context['archived_projects'] = archived_projects
    
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
            return render(request, 'pages/grid/actions_in_page/task_item.html', {'task': task, 'project': project})
        
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


@login_required
def task_assign_view(request, task_pk):
    """Assign a task to a team member"""
    from accounts.models import User
    
    task = get_user_task_optimized(
        task_pk,
        request.user,
        select_related=['project', 'assigned_to'],
        only_fields=['id', 'text', 'project__id', 'project__user', 'project__is_team_toad', 'assigned_to__id']
    )
    
    # Verify this is a team toad project
    if not task.project.is_team_toad:
        return JsonResponse({
            'success': False,
            'error': 'This is not a team project'
        }, status=400)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            
            if user_id is None:
                # Unassign the task
                task.assigned_to = None
                task.save()
                
                log_user_action(
                    request.user, 
                    'unassigned task', 
                    f'"{task.text}"', 
                    task.project
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Task unassigned successfully'
                })
            
            # Get the user to assign to
            try:
                assign_to_user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'User not found'
                }, status=404)
            
            # Verify the user is in the team_toad_user list
            if not task.project.team_toad_user.filter(pk=user_id).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'User is not a team member'
                }, status=403)
            
            # Assign the task
            task.assigned_to = assign_to_user
            task.save()
            
            log_user_action(
                request.user, 
                'assigned task', 
                f'"{task.text}" to {assign_to_user.first_name} {assign_to_user.last_name}', 
                task.project.name
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Task assigned to {assign_to_user.first_name} {assign_to_user.last_name}',
                'assigned_to': {
                    'id': assign_to_user.pk,
                    'name': f'{assign_to_user.first_name} {assign_to_user.last_name}',
                    'initials': f'{assign_to_user.first_name[0]}{assign_to_user.last_name[0]}' if assign_to_user.first_name and assign_to_user.last_name else assign_to_user.email[0]
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f'Error assigning task: {e}')
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    }, status=405)


@login_required
def create_task_reminder(request, task_pk):
    """Create a calendar reminder for a task by generating and emailing an ICS file"""
    task = get_user_task_optimized(
        task_pk,
        request.user,
        select_related=['project'],
        only_fields=['id', 'text', 'project__id', 'project__user', 'project__name']
    )
    
    if request.method == 'POST':
        try:
            reminder_date = request.POST.get('reminder_date')
            reminder_note = request.POST.get('reminder_note', '').strip()
            
            if not reminder_date:
                return JsonResponse({'success': False, 'error': 'Reminder date is required'}, status=400)
            
            # Parse the date
            from datetime import datetime, date
            try:
                reminder_date_obj = datetime.strptime(reminder_date, '%Y-%m-%d').date()
                
                # Check if date is not in the past
                if reminder_date_obj < date.today():
                    return JsonResponse({'success': False, 'error': 'Reminder date cannot be in the past'}, status=400)
                
                # Save reminder date to task model (use timezone-aware datetime)
                from django.utils import timezone as tz
                # Combine date with min time and make it timezone-aware
                reminder_datetime = tz.make_aware(datetime.combine(reminder_date_obj, datetime.min.time()))
                task.reminder = reminder_datetime
                task.save(update_fields=['reminder'])
                    
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Invalid date format'}, status=400)
            
            # Generate ICS calendar file
            from icalendar import Calendar, Event
            import uuid
            from django.core.mail import EmailMessage
            from django.conf import settings
            
            # Create calendar
            cal = Calendar()
            cal.add('prodid', '-//Toad App//Task Reminder//EN')
            cal.add('version', '2.0')
            cal.add('calscale', 'GREGORIAN')
            cal.add('method', 'REQUEST')
            
            # Create event
            event = Event()
            event.add('uid', str(uuid.uuid4()))
            # Create all-day event by setting both start and end dates
            # For all-day events, we need to set both DTSTART and DTEND with VALUE=DATE
            event.add('dtstart', reminder_date_obj)
            event['dtstart'].params['VALUE'] = 'DATE'
            
            # For all-day events, DTEND should be the next day
            from datetime import timedelta
            end_date = reminder_date_obj + timedelta(days=1)
            event.add('dtend', end_date)
            event['dtend'].params['VALUE'] = 'DATE'
            
            # Set creation timestamp (use timezone-aware datetime)
            from django.utils import timezone
            # Get current time in UTC (timezone.now() returns timezone-aware datetime)
            dtstamp = timezone.now()
            event.add('dtstamp', dtstamp)
            
            event.add('summary', f'Task Reminder: {task.text}')
            
            # Build description
            description_parts = [
                f'Task: {task.text}',
                f'From Grid: {task.project.name}',
            ]
            if reminder_note:
                description_parts.append(f'Note: {reminder_note}')
            
            event.add('description', '\n\n'.join(description_parts))
            event.add('categories', 'TASK_REMINDER')
            event.add('status', 'CONFIRMED')
            event.add('sequence', 0)  # Required for proper Outlook handling
            event.add('transp', 'TRANSPARENT')  # Don't block time
            
            # Add organizer (required for Outlook to show Accept/Decline buttons)
            from django.utils.encoding import force_str
            event.add('organizer', f'MAILTO:{request.user.email}', parameters={'CN': force_str(request.user.get_full_name() or request.user.email)})
            
            # Add attendee with RSVP
            event.add('attendee', f'MAILTO:{request.user.email}', parameters={
                'CN': force_str(request.user.get_full_name() or request.user.email),
                'RSVP': 'FALSE',  # Set to FALSE so no response is expected
                'ROLE': 'REQ-PARTICIPANT',
                'PARTSTAT': 'ACCEPTED'
            })
            
            cal.add_component(event)
            
            # Generate ICS content
            ics_content = cal.to_ical()
            
            # Send email with ICS attachment as Outlook invite
            subject = f'Task Reminder: {task.text}'
            
            # Format the date nicely
            formatted_date = reminder_date_obj.strftime('%B %d, %Y')
            
            # Create HTML message
            html_message = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .task-info {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0; }}
        .task-info strong {{ color: #2563eb; }}
        .note {{ background: #fef3c7; padding: 10px; border-left: 3px solid #f59e0b; margin: 15px 0; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <p>Hi {request.user.first_name},</p>
        
        <p>You've set a reminder for your task:</p>
        
        <div class="task-info">
            <strong>Task:</strong> {task.text}<br>
            <strong>Grid:</strong> {task.project.name}<br>
            <strong>Reminder Date:</strong> {formatted_date}
        </div>"""
            
            if reminder_note:
                html_message += f"""
        <div class="note">
            <strong>Note:</strong> {reminder_note}
        </div>"""
            
            html_message += """
        <p>This email contains a calendar invitation. Click <strong>"Accept"</strong> or <strong>"Add to Calendar"</strong> to add this reminder to your calendar.</p>
        
        <div class="footer">
            Best regards,<br>
            The Toad Team
        </div>
    </div>
</body>
</html>"""
            
            # Validate email address
            if not request.user.email:
                return JsonResponse({'success': False, 'error': 'User email address is required'}, status=400)
            
            email = EmailMessage(
                subject=subject,
                body=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[request.user.email],
            )
            email.content_subtype = "html"
            
            # Attach ICS file with proper content type for Outlook invites
            # Note: Some email clients prefer this without the method=REQUEST in the content type
            email.attach('task_reminder.ics', ics_content, 'text/calendar')
            email.send()
            
            return JsonResponse({
                'success': True, 
                'message': f'Calendar reminder sent to {request.user.email}!'
            })
            
        except Exception as e:
            logger.error(f"Error creating task reminder for task {task_pk}: {e}")
            return JsonResponse({'success': False, 'error': 'Failed to create reminder'}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)


@login_required
def task_note_view(request, task_pk):
    """Handle task notes - GET to retrieve, POST to create/update, DELETE to remove"""
    from pages.models import TaskNote
    from pages.forms import TaskNoteForm
    
    task = get_user_task_optimized(
        task_pk,
        request.user,
        select_related=['project'],
        only_fields=['id', 'text', 'project__id', 'project__user', 'project__name']
    )
    
    if request.method == 'GET':
        # Return existing note if it exists
        try:
            note = task.notes.first()
            if note:
                return JsonResponse({
                    'success': True,
                    'note': {
                        'note': note.note,
                        'created_at': note.created_at.isoformat(),
                        'updated_at': note.updated_at.isoformat()
                    }
                })
            else:
                return JsonResponse({
                    'success': True,
                    'note': None
                })
        except Exception as e:
            logger.error(f"Error retrieving note for task {task_pk}: {e}")
            return JsonResponse({'success': False, 'error': 'Failed to retrieve note'}, status=500)
    
    elif request.method == 'POST':
        # Create or update note
        try:
            note_text = request.POST.get('note', '').strip()
            
            if not note_text:
                return JsonResponse({'success': False, 'error': 'Note text is required'}, status=400)
            
            # Always create a new note
            note = TaskNote.objects.create(
                task=task,
                created_by=request.user,
                note=note_text
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Note saved successfully!',
                'note': {
                    'note': note.note,
                    'created_at': note.created_at.isoformat(),
                    'updated_at': note.updated_at.isoformat()
                }
            })
            
        except Exception as e:
            logger.error(f"Error saving note for task {task_pk}: {e}")
            return JsonResponse({'success': False, 'error': 'Failed to save note'}, status=500)
    
    elif request.method == 'DELETE':
        # Delete note
        try:
            note_id = request.headers.get('X-Note-ID')
            if note_id:
                # Delete specific note
                try:
                    note = TaskNote.objects.get(id=note_id, task=task)
                    note.delete()
                    has_notes = task.notes.exists()
                    return JsonResponse({
                        'success': True,
                        'message': 'Note deleted successfully!',
                        'has_notes': has_notes
                    })
                except TaskNote.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'Note not found'
                    }, status=404)
            else:
                # Delete first note (legacy behavior)
                note = task.notes.first()
                if note:
                    note.delete()
                    has_notes = task.notes.exists()
                    return JsonResponse({
                        'success': True,
                        'message': 'Note deleted successfully!',
                        'has_notes': has_notes
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'No note found to delete'
                    }, status=404)
                
        except Exception as e:
            logger.error(f"Error deleting note for task {task_pk}: {e}")
            return JsonResponse({'success': False, 'error': 'Failed to delete note'}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

@login_required
def task_notes_view(request, task_pk):
    """Get all notes for a task"""
    from pages.models import TaskNote
    
    task = get_user_task_optimized(
        task_pk,
        request.user,
        select_related=['project'],
        only_fields=['id', 'text', 'project__id', 'project__user', 'project__name']
    )
    
    if request.method == 'GET':
        try:
            notes = task.notes.all()
            notes_data = []
            for note in notes:
                notes_data.append({
                    'id': note.id,
                    'note': note.note,
                    'created_at': note.created_at.isoformat(),
                    'updated_at': note.updated_at.isoformat()
                })
            
            return JsonResponse({
                'success': True,
                'notes': notes_data
            })
        except Exception as e:
            logger.error(f"Error retrieving notes for task {task_pk}: {e}")
            return JsonResponse({'success': False, 'error': 'Failed to retrieve notes'}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

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
            # Return JSON response for AJAX requests
            return create_json_response(True, f'Successfully deleted {count} completed tasks!')
        else:
            messages.info(request, 'No completed tasks to delete.')
            # Return JSON response for AJAX requests
            return create_json_response(True, 'No completed tasks to delete.')
    
    return render(request, 'pages/grid/actions_in_page/clear_completed_tasks.html', {
        'project': project
    })


@login_required
def archive_project_confirm_view(request, pk):
    """Show confirmation page before archiving a project"""
    project = get_user_project_optimized(pk, request.user, only_fields=['id', 'name', 'user'])
    
    # Get project statistics
    total_tasks = Task.objects.filter(project=project).count()
    completed_tasks = Task.objects.filter(project=project, completed=True).count()
    total_rows = RowHeader.objects.filter(project=project).count()
    total_columns = ColumnHeader.objects.filter(project=project).count()
    
    return render(request, 'pages/grid/actions_new_page/archive_project_confirm.html', {
        'project': project,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'total_rows': total_rows,
        'total_columns': total_columns,
    })

@login_required
def archive_project_view(request, pk):
    project = get_user_project_optimized(pk, request.user, only_fields=['id', 'name', 'user'])
    
    if request.method == 'POST':
        # Set the project as archived
        project.is_archived = True
        project.save()
        
        messages.success(request, f'Project "{project.name}" has been archived successfully!')
        return redirect('pages:project_list')
    
    return redirect('pages:project_grid', pk=project.pk)


@login_required
def restore_project_view(request, pk):
    project = get_user_project_optimized(pk, request.user, only_fields=['id', 'name', 'user'])
    
    if request.method == 'POST':
        # Set the project as not archived
        project.is_archived = False
        project.save()
        
        messages.success(request, f'Project "{project.name}" has been restored successfully!')
        return redirect('pages:project_list')
    
    return redirect('pages:project_list')

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
def save_as_template_view(request, pk):
    """Save the current project as a personal template"""
    project = get_user_project_optimized(pk, request.user, only_fields=['id', 'name', 'user'])
    
    if request.method == 'POST':
        template_name = request.POST.get('template_name', '').strip()
        template_style = request.POST.get('template_style', '')
        
        if not template_name:
            messages.error(request, 'Template name is required.')
            return redirect('pages:project_grid', pk=project.pk)
        
        if not template_style:
            messages.error(request, 'Please select a template style.')
            return redirect('pages:project_grid', pk=project.pk)
        
        try:
            # Create the personal template with the user-provided name
            template = PersonalTemplate.objects.create(
                user=request.user,
                name=template_name
            )
            
            # Get all rows and columns from the project (including category column for template)
            rows = project.row_headers.all().order_by('order')
            columns = project.column_headers.all().order_by('order')
            
            # Create template row headers with sequential order
            template_rows = []
            for i, row in enumerate(rows):
                template_row = TemplateRowHeader.objects.create(
                    template=template,
                    name=row.name,
                    order=i  # Use sequential order instead of copying from project
                )
                template_rows.append(template_row)
            
            # Create template column headers with sequential order
            template_columns = []
            for i, column in enumerate(columns):
                template_column = TemplateColumnHeader.objects.create(
                    template=template,
                    name=column.name,
                    order=i  # Use sequential order instead of copying from project
                )
                template_columns.append(template_column)
            
            # Create a mapping for quick lookup using names (more reliable than IDs)
            row_mapping = {row.name: template_row for row, template_row in zip(rows, template_rows)}
            col_mapping = {column.name: template_column for column, template_column in zip(columns, template_columns)}
            
            # If "Save with example tasks" is selected, create template tasks
            if template_style == 'with_tasks':
                # Order tasks by their visual position: row order, column order, then task order within cell
                tasks = project.tasks.all().order_by('row_header__order', 'column_header__order', 'order')
                logger.info(f"Saving template with {tasks.count()} tasks from project {project.name}")
                
                # Debug: Log the order of tasks being saved
                logger.info("=== TASK ORDERING DEBUG ===")
                for idx, task in enumerate(tasks):
                    logger.info(f"Task {idx}: '{task.text[:30]}...' in Row {task.row_header.order} ({task.row_header.name}) x Col {task.column_header.order} ({task.column_header.name}) with order {task.order}")
                logger.info("=== END DEBUG ===")
                
                # Include tasks from all columns (including category column) when saving as template
                
                # Save tasks in the exact order they appear in the grid
                for i, task in enumerate(tasks):
                    # Find the corresponding template row and column using names
                    template_row = row_mapping.get(task.row_header.name)
                    template_column = col_mapping.get(task.column_header.name)
                    
                    if template_row and template_column:
                        TemplateTask.objects.create(
                            template_row_header=template_row,
                            template_column_header=template_column,
                            text=task.text,
                            completed=task.completed,
                            order=i  # Just use the loop index - simple sequential order
                        )
                        logger.info(f"Created template task: {task.text[:50]} in {template_row.name} x {template_column.name} with order {i}")
                    else:
                        # Debug logging for missing mappings
                        logger.warning(f"Task '{task.text[:50]}' could not be mapped - Row: {task.row_header.name} -> {template_row}, Col: {task.column_header.name} -> {template_column}")
                
                # Log summary of template creation
                if template_style == 'with_tasks':
                    created_tasks = TemplateTask.objects.filter(template_row_header__template=template).count()
                    logger.info(f"Template created with {created_tasks} tasks out of {tasks.count()} original tasks")
            
            log_user_action(request.user, f'saved project as template: {template.name}', project.name)
            messages.success(request, f'Template "{template.name}" saved successfully!')
            
        except Exception as e:
            logger.error(f"Error saving template for project {pk}: {e}")
            messages.error(request, 'Failed to save template. Please try again.')
        
        return redirect('pages:project_list')
    
    # For GET requests, render the modal template
    return render(request, 'pages/grid/actions_in_page/save_as_template_modal.html', {
        'project': project
    })


@login_required
def use_template_view(request, pk):
    """Create a new project from a personal template"""
    if request.method == 'POST':
        try:
            # Get the template
            template = PersonalTemplate.objects.get(id=pk, user=request.user)
            
            # Create a new project with just the template name
            project = Project.objects.create(
                user=request.user,
                name=template.name
            )
            
            # Create the category column (always first)
            ColumnHeader.objects.create(
                project=project,
                name='Time / Category',
                order=0,
                is_category_column=True
            )
            
            # Create row headers from template
            template_rows = template.row_headers.all().order_by('order')
            row_objects = []
            for i, template_row in enumerate(template_rows):
                row = RowHeader.objects.create(
                    project=project,
                    name=template_row.name,
                    order=i
                )
                row_objects.append(row)
            
            # Create column headers from template (including category column)
            template_columns = template.column_headers.all().order_by('order')
            col_objects = []
            for i, template_column in enumerate(template_columns):
                # Check if this was originally a category column
                is_category = template_column.name == 'Time / Category'
                column = ColumnHeader.objects.create(
                    project=project,
                    name=template_column.name,
                    order=i,
                    is_category_column=is_category
                )
                col_objects.append(column)
            
            # Create tasks from template if they exist
            template_tasks = TemplateTask.objects.filter(
                template_row_header__template=template
            ).select_related('template_row_header', 'template_column_header').order_by('order')
            
            logger.info(f"Creating project from template with {template_tasks.count()} template tasks")
            
            # Debug: Log the order of template tasks being used
            logger.info("=== TEMPLATE TASK ORDERING DEBUG ===")
            for idx, template_task in enumerate(template_tasks):
                logger.info(f"Template Task {idx}: '{template_task.text[:30]}...' in Row {template_task.template_row_header.order} ({template_task.template_row_header.name}) x Col {template_task.template_column_header.order} ({template_task.template_column_header.name}) with order {template_task.order}")
            logger.info("=== END DEBUG ===")
            
            # Create tasks using the same logic as signals - use list indices
            for template_task in template_tasks:
                # Get the row and column indices from the template
                row_idx = template_task.template_row_header.order
                col_idx = template_task.template_column_header.order
                
                # Use the list indices to get the correct row and column objects
                row = row_objects[row_idx]
                column = col_objects[col_idx]
                
                # Create task with the actual text from the template
                Task.objects.create(
                    project=project,
                    row_header=row,
                    column_header=column,
                    text=template_task.text,  # Use the actual task text from template
                    completed=False,  # Always start as incomplete
                    order=template_task.order  # Use the exact same order from the template
                )
                logger.info(f"Created task: {template_task.text[:50]} in {row.name} x {column.name} with order {template_task.order}")
            
            # Log summary of task creation
            created_tasks = Task.objects.filter(project=project).count()
            logger.info(f"Project created with {created_tasks} tasks out of {template_tasks.count()} template tasks")
            
            log_user_action(request.user, f'created project from template: {template.name}', project.name)
            messages.success(request, f'Grid "{project.name}" created from template successfully!')
            
            return redirect('pages:project_grid', pk=project.pk)
            
        except PersonalTemplate.DoesNotExist:
            messages.error(request, 'Template not found.')
        except Exception as e:
            logger.error(f"Error using template {pk}: {e}")
            messages.error(request, 'Failed to create grid from template. Please try again.')
    
    return redirect('pages:project_list')


@login_required
def template_edit_view(request, pk):
    """Edit a personal template"""
    try:
        template = PersonalTemplate.objects.get(id=pk, user=request.user)
    except PersonalTemplate.DoesNotExist:
        messages.error(request, 'Template not found.')
        return redirect('pages:project_list')
    
    if request.method == 'POST':
        # Check if this is a JSON request for inline editing
        if request.headers.get('Content-Type') == 'application/json':
            try:
                data = json.loads(request.body)
                template_name = data.get('template_name', '').strip()
                
                if not template_name:
                    return JsonResponse({
                        'success': False,
                        'error': 'Template name cannot be empty'
                    })
                
                # Update the template name
                template.name = template_name
                template.save()
                
                log_user_action(request.user, f'edited template: {template_name}', template.name)
                
                return JsonResponse({
                    'success': True,
                    'message': 'Template name updated successfully',
                    'new_name': template_name
                })
                
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid JSON data'
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                })
        
        # Regular form submission
        template_name = request.POST.get('template_name', '').strip()
        if not template_name:
            messages.error(request, 'Template name is required.')
            return redirect('pages:template_edit', pk=pk)
        
        template.name = template_name
        template.save()
        
        log_user_action(request.user, f'edited template: {template_name}', template.name)
        messages.success(request, f'Template "{template_name}" updated successfully!')
        return redirect('pages:project_list')
    
    context = {'template': template}
    return render(request, 'pages/grid/actions_new_page/template_edit_modal.html', context)


@login_required
def template_delete_view(request, pk):
    """Delete a personal template"""
    try:
        template = PersonalTemplate.objects.get(id=pk, user=request.user)
    except PersonalTemplate.DoesNotExist:
        messages.error(request, 'Template not found.')
        return redirect('pages:project_list')
    
    if request.method == 'POST':
        template_name = template.name
        template.delete()
        
        log_user_action(request.user, f'deleted template: {template_name}', 'N/A')
        messages.success(request, f'Template "{template_name}" deleted successfully!')
        return redirect('pages:project_list')
    
    context = {'template': template}
    return render(request, 'pages/grid/actions_new_page/template_confirm_delete_modal.html', context)


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
                task_id = task_data.get('task_id')  # Changed from 'id' to 'task_id'
                new_row = task_data.get('row_header')  # Changed from 'row' to 'row_header'
                new_col = task_data.get('column_header')  # Changed from 'col' to 'column_header'
                
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

            return JsonResponse({'success': True, 'message': 'Task order and position updated successfully'})
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            logger.error(f"Error reordering tasks for project {project_pk}: {e}")
            return JsonResponse({'success': False, 'error': 'Failed to reorder tasks'}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)


@login_required
def project_group_create_view(request):
    """Create a new project group and optionally assign projects to it"""
    if request.method == 'POST':
        form = ProjectGroupForm(request.POST)
        if form.is_valid():
            try:
                group = form.save()
                
                # Handle project assignments if any projects were selected
                selected_projects = request.POST.getlist('projects')
                if selected_projects:
                    projects = Project.objects.filter(id__in=selected_projects, user=request.user)
                    for project in projects:
                        project.project_group = group
                        project.save()
                
                log_user_action(request.user, 'created project group', group.name)
                messages.success(request, f'Group "{group.name}" created successfully!')
                return redirect('pages:project_list')
            except Exception as e:
                messages.error(request, f'Error creating group: {str(e)}')
                logger.error(f'Error creating project group: {str(e)}')
                return redirect('pages:project_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProjectGroupForm()
    
    # Get user's projects for the assignment form
    user_projects = request.user.toad_projects.all()
    
    context = {
        'form': form,
        'projects': user_projects,
    }
    
    return render(request, 'pages/grid/actions_new_page/project_group_form.html', context)


@login_required
def project_group_update_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            project_id = data.get('project_id')
            group_id = data.get('group_id')
            order = data.get('order')
            
            if not project_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Project ID is required'
                })
            
            # Get the project
            try:
                project = Project.objects.get(id=project_id, user=request.user)
            except Project.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Project not found'
                })
            
            # Update the project group
            if group_id is None:
                project.project_group = None
            else:
                try:
                    group = ProjectGroup.objects.get(id=group_id)
                    project.project_group = group
                except ProjectGroup.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'Group not found'
                    })
            
            project.save()
            
            # Update order if provided
            if order is not None:
                try:
                    # Update all projects in the group with their new order
                    for item in order:
                        if item.get('project_id') and item.get('order') is not None:
                            try:
                                project_to_update = Project.objects.get(
                                    id=item['project_id'], 
                                    user=request.user
                                )
                                project_to_update.order = item['order']
                                project_to_update.save()
                            except Project.DoesNotExist:
                                continue  # Skip if project doesn't exist
                except Exception as e:
                    logger.error(f'Error updating project order: {str(e)}')
                    # Don't fail the entire request if order update fails
            
            return JsonResponse({
                'success': True,
                'message': 'Project group and order updated successfully'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })


@login_required
def project_group_edit_view(request, pk):
    try:
        group = ProjectGroup.objects.get(id=pk)
        
        # Check if user has access to this group by checking if they have projects in this group
        user_projects_in_group = Project.objects.filter(user=request.user, project_group=group).exists()
        if not user_projects_in_group:
            return JsonResponse({
                'success': False,
                'error': 'Access denied - you do not have any projects in this group'
            })
        
        if request.method == 'POST':
            # Check if this is a JSON request for inline editing
            if request.headers.get('Content-Type') == 'application/json':
                try:
                    data = json.loads(request.body)
                    new_name = data.get('name', '').strip()
                    
                    if not new_name:
                        return JsonResponse({
                            'success': False,
                            'error': 'Group name cannot be empty'
                        })
                    
                    # Update the group name
                    group.name = new_name
                    group.save()
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Group name updated successfully',
                        'new_name': new_name
                    })
                    
                except json.JSONDecodeError:
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid JSON data'
                    })
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    })
            
            # Regular form submission (fallback)
            form = ProjectGroupForm(request.POST, instance=group)
            if form.is_valid():
                form.save()
                messages.success(request, f'Group "{group.name}" updated successfully!')
                return redirect('pages:project_list')
        else:
            form = ProjectGroupForm(instance=group)
        
        # Check if this is an HTMX request (modal) or regular page request
        if request.headers.get('HX-Request'):
            template_name = 'pages/grid/actions_new_page/project_group_form_modal.html'
        else:
            template_name = 'pages/grid/actions_new_page/project_group_form.html'
        
        return render(request, template_name, {
            'form': form, 
            'group': group, 
            'title': 'Edit Group'
        })
        
    except ProjectGroup.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Group not found'
        })


@login_required
def share_grid_view(request, pk):
    """
    Handle grid sharing via email invitation or shareable link
    """
    try:
        project = get_user_project_optimized(pk, request.user)
        
        if request.method == 'POST':
            data = json.loads(request.body)
            invitation_type = data.get('type')  # 'email' or 'link'
            email = data.get('email', '').strip()
            personal_message = data.get('message', '').strip()
            
            if invitation_type == 'email':
                return _handle_email_invitation(request, project, email, personal_message)
            elif invitation_type == 'link':
                return _handle_shareable_link(request, project)
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid invitation type'
                })
        
        return JsonResponse({
            'success': False,
            'error': 'Invalid request method'
        })
        
    except Exception as e:
        logger.error(f"Error in share_grid_view: {e}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while sharing the grid'
        })


def _handle_email_invitation(request, project, email, personal_message):
    """
    Handle email invitation creation and sending
    """
    from pages.models import GridInvitation
    from accounts.email_utils import send_grid_invitation_email
    from django.utils import timezone
    from datetime import timedelta
    
    # Validate email
    if not email:
        return JsonResponse({
            'success': False,
            'error': 'Email address is required'
        })
    
    # Check if user has valid tier for collaboration
    try:
        invited_user = User.objects.get(email=email)
        valid_tiers = ['pro', 'pro_trial', 'society_pro', 'beta']
        if invited_user.tier not in valid_tiers:
            return JsonResponse({
                'success': False,
                'error': f'The user with email {email} doesn\'t have a Team Toad account. They need to upgrade to Team Toad.'
            })
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': f'No user found with email {email}. User must be registered and have a Team Toad account.'
        })
    
    # Check if user is already part of the project
    if project.team_toad_user.filter(email=email).exists():
        return JsonResponse({
            'success': False,
            'error': f'User with email {email} is already part of this grid'
        })
    
    # Check if there's already a pending invitation for this email and project
    existing_invitation = GridInvitation.objects.filter(
        project=project,
        invited_email=email,
        invitation_type='email',
        status='pending'
    ).first()
    
    if existing_invitation and not existing_invitation.is_expired():
        return JsonResponse({
            'success': False,
            'error': f'A pending invitation already exists for {email}. Please wait for it to be accepted or expired.'
        })
    
    # Create new invitation
    try:
        invitation = GridInvitation.objects.create(
            project=project,
            invited_by=request.user,
            invited_email=email,
            invitation_type='email',
            personal_message=personal_message,
            expires_at=timezone.now() + timedelta(days=7),  # 7 days expiry
        )
        
        # Send email
        email_sent = send_grid_invitation_email(invitation, request)
        
        if email_sent:
            return JsonResponse({
                'success': True,
                'message': f'Invitation sent successfully to {email}',
                'invitation_id': invitation.id
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Failed to send invitation email'
            })
            
    except Exception as e:
        logger.error(f"Error creating email invitation: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to create invitation'
        })


def _handle_shareable_link(request, project):
    """
    Handle shareable link creation - creates a new link each time
    """
    from pages.models import GridInvitation
    from django.utils import timezone
    from datetime import timedelta
    from django.urls import reverse
    
    # Create a new shareable link invitation each time
    try:
        invitation = GridInvitation.objects.create(
            project=project,
            invited_by=request.user,
            invited_email='',  # Empty for shareable links
            invitation_type='link',
            expires_at=timezone.now() + timedelta(days=30),  # 30 days for links
        )
        
        # Build the shareable link
        if request:
            shareable_url = request.build_absolute_uri(
                reverse('pages:accept_grid_invitation', kwargs={'token': invitation.token})
            )
        else:
            shareable_url = f"{settings.SITE_URL}/grids/invite/{invitation.token}/"
        
        return JsonResponse({
            'success': True,
            'message': 'Shareable link created successfully',
            'shareable_url': shareable_url,
            'invitation_id': invitation.id,
            'expires_at': invitation.expires_at.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error creating shareable link: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to create shareable link'
        })


def accept_grid_invitation_view(request, token):
    """
    Handle accepting grid invitations via token
    """
    from pages.models import GridInvitation
    from django.contrib import messages
    
    try:
        invitation = GridInvitation.objects.get(token=token)
        
        # Check if invitation is still valid
        if not invitation.can_be_accepted():
            if invitation.is_expired():
                messages.error(request, 'This invitation has expired.')
            else:
                messages.error(request, 'This invitation is no longer valid.')
            return redirect('pages:home')
        
        # If user is logged in, accept the invitation
        if request.user.is_authenticated:
            # Check if user has valid tier
            valid_tiers = ['pro', 'pro_trial', 'society_pro', 'beta']
            if request.user.tier not in valid_tiers:
                messages.error(request, f'You need a Pro, Pro Trial, Society Pro, or Beta account to collaborate on grids. Your current tier is "{request.user.tier}".')
                return redirect('pages:upgrade_required_pro')
            
            # Accept the invitation
            if invitation.accept(request.user):
                messages.success(request, f'You have successfully joined the grid "{invitation.project.name}"!')
                return redirect('pages:project_grid', pk=invitation.project.pk)
            else:
                messages.error(request, 'Failed to accept the invitation.')
                return redirect('pages:home')
        
        else:
            # User is not logged in, redirect to login with next parameter
            messages.info(request, 'Please log in to accept this grid invitation.')
            return redirect('accounts:login') + f'?next={request.get_full_path()}'
            
    except GridInvitation.DoesNotExist:
        messages.error(request, 'Invalid invitation link.')
        return redirect('pages:home')
    except Exception as e:
        logger.error(f"Error accepting grid invitation: {e}")
        messages.error(request, 'An error occurred while accepting the invitation.')
        return redirect('pages:home')


@login_required
def team_add_member_view(request, project_pk):
    """Add a team member to a Team Toad project"""
    import logging
    logger = logging.getLogger(__name__)
    
    project = get_object_or_404(Project, pk=project_pk)
    
    # Check if user is the project owner
    if project.user != request.user:
        return JsonResponse({
            'success': False,
            'error': 'Only the project owner can add team members'
        }, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip().lower()
            
            if not email:
                return JsonResponse({
                    'success': False,
                    'error': 'Email is required'
                }, status=400)
            
            # Check if user exists
            try:
                user_to_add = User.objects.get(email=email)
            except User.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'No user found with this email address'
                }, status=404)
            
            # Check if user is already a team member
            if project.team_toad_user.filter(pk=user_to_add.pk).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'User is already a team member'
                }, status=400)
            
            # Add user to team and make project a Team Toad project
            project.team_toad_user.add(user_to_add)
            project.is_team_toad = True
            project.save()
            
            logger.info(f"Added {user_to_add.get_full_name} ({email}) to team project {project.name}")
            
            return JsonResponse({
                'success': True,
                'message': f'{user_to_add.get_full_name} has been added to the team'
            })
            
        except Exception as e:
            logger.error(f"Error adding team member: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Failed to add team member'
            }, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)


@login_required
def team_remove_member_view(request, project_pk):
    """Remove a team member from a Team Toad project"""
    import logging
    logger = logging.getLogger(__name__)
    
    project = get_object_or_404(Project, pk=project_pk)
    
    # Check if user is the project owner
    if project.user != request.user:
        return JsonResponse({
            'success': False,
            'error': 'Only the project owner can remove team members'
        }, status=403)
    
    # Check if this is a Team Toad project
    if not project.is_team_toad:
        return JsonResponse({
            'success': False,
            'error': 'This is not a Team Toad project'
        }, status=400)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            member_id = data.get('member_id')
            
            if not member_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Member ID is required'
                }, status=400)
            
            # Get the user to remove
            try:
                user_to_remove = User.objects.get(pk=member_id)
            except User.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'User not found'
                }, status=404)
            
            # Check if user is actually a team member
            if not project.team_toad_user.filter(pk=member_id).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'User is not a team member'
                }, status=400)
            
            # Don't allow removing the project owner
            if user_to_remove == project.user:
                return JsonResponse({
                    'success': False,
                    'error': 'Cannot remove the project owner'
                }, status=400)
            
            # Remove user from team
            project.team_toad_user.remove(user_to_remove)
            
            # Unassign any tasks assigned to this user
            Task.objects.filter(project=project, assigned_to=user_to_remove).update(assigned_to=None)
            
            logger.info(f"Removed {user_to_remove.get_full_name} from team project {project.name}")
            
            return JsonResponse({
                'success': True,
                'message': f'{user_to_remove.get_full_name} has been removed from the team'
            })
            
        except Exception as e:
            logger.error(f"Error removing team member: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Failed to remove team member'
            }, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)


@login_required
def get_shared_team_users_view(request, project_pk):
    """Get users who share team grids with the logged-in user and users from SubscriptionGroups (excluding current grid members)"""
    try:
        project = get_user_project_optimized(project_pk, request.user, only_fields=['id', 'name', 'user'])
        
        # Get all projects where the logged-in user is either owner or team member
        user_projects = Project.objects.filter(
            Q(user=request.user) | Q(team_toad_user=request.user),
            is_team_toad=True
        ).exclude(pk=project_pk).distinct()
        
        # Get all unique users from these projects (excluding the current user and current grid members)
        # Users who are owners or team members of projects that the logged-in user is also on
        shared_users = User.objects.filter(
            Q(toad_projects__in=user_projects) | Q(team_toad_projects__in=user_projects)
        ).exclude(
            pk=request.user.pk
        ).exclude(
            pk__in=project.team_toad_user.values_list('pk', flat=True)
        ).distinct()
        
        # Get users from SubscriptionGroups where the current user is admin or member
        subscription_group_user_ids = set()
        
        # Get groups where user is admin
        admin_groups = SubscriptionGroup.objects.filter(
            admin=request.user,
            is_active=True
        ).prefetch_related('members')
        
        for group in admin_groups:
            # Add all members of this group
            subscription_group_user_ids.update(group.members.values_list('pk', flat=True))
        
        # Get groups where user is a member
        member_groups = request.user.subscription_groups.filter(is_active=True).prefetch_related('members', 'admin')
        
        for group in member_groups:
            # Add all members of this group
            subscription_group_user_ids.update(group.members.values_list('pk', flat=True))
            # Add the admin (they're not automatically a member)
            subscription_group_user_ids.add(group.admin_id)
        
        # Get users from SubscriptionGroups, excluding current user and current grid members
        subscription_users = User.objects.filter(
            pk__in=subscription_group_user_ids
        ).exclude(
            pk=request.user.pk
        ).exclude(
            pk__in=project.team_toad_user.values_list('pk', flat=True)
        ).distinct()
        
        # Combine both sets of users and get unique users
        all_user_ids = set(shared_users.values_list('pk', flat=True))
        all_user_ids.update(subscription_users.values_list('pk', flat=True))
        
        # Get final list of users, ordered by name
        final_users = User.objects.filter(
            pk__in=all_user_ids
        ).order_by('first_name', 'last_name', 'email').values('id', 'first_name', 'last_name', 'email')
        
        # Convert to list and format
        users_list = []
        for user in final_users:
            users_list.append({
                'id': user['id'],
                'name': f"{user['first_name']} {user['last_name']}".strip() or user['email'],
                'email': user['email']
            })
        
        return JsonResponse({
            'success': True,
            'users': users_list
        })
        
    except Exception as e:
        logger.error(f"Error getting shared team users: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to load shared team users'
        }, status=500)


@login_required
def team_add_multiple_members_view(request, project_pk):
    """Add multiple team members to a Team Toad project at once"""
    project = get_object_or_404(Project, pk=project_pk)
    
    # Check if user is the project owner
    if project.user != request.user:
        return JsonResponse({
            'success': False,
            'error': 'Only the project owner can add team members'
        }, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_ids = data.get('user_ids', [])
            
            if not user_ids or not isinstance(user_ids, list):
                return JsonResponse({
                    'success': False,
                    'error': 'User IDs are required'
                }, status=400)
            
            # Get users to add
            users_to_add = User.objects.filter(pk__in=user_ids)
            
            if users_to_add.count() != len(user_ids):
                return JsonResponse({
                    'success': False,
                    'error': 'Some users were not found'
                }, status=404)
            
            # Filter out users who are already team members
            existing_member_ids = set(project.team_toad_user.values_list('pk', flat=True))
            new_users = [u for u in users_to_add if u.pk not in existing_member_ids]
            
            if not new_users:
                return JsonResponse({
                    'success': False,
                    'error': 'All selected users are already team members'
                }, status=400)
            
            # Add users to team and make project a Team Toad project
            project.team_toad_user.add(*new_users)
            project.is_team_toad = True
            project.save()
            
            # Format success message
            if len(new_users) == 1:
                message = f'{new_users[0].get_full_name()} has been added to the team'
            else:
                message = f'{len(new_users)} users have been added to the team'
            
            logger.info(f"Added {len(new_users)} users to team project {project.name}")
            
            return JsonResponse({
                'success': True,
                'message': message,
                'added_count': len(new_users)
            })
            
        except Exception as e:
            logger.error(f"Error adding multiple team members: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Failed to add team members'
            }, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)


