from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .models import Project, RowHeader, ColumnHeader, Task
from .forms import ProjectForm, TaskForm, QuickTaskForm, RowHeaderForm, ColumnHeaderForm
from django.http import HttpResponse, JsonResponse

def home(request):
    return render(request, 'pages/general/home.html')


@login_required
def project_list_view(request):
    projects = Project.objects.filter(user=request.user)
    return render(request, 'pages/grid/project_list.html', {'projects': projects})


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
            ColumnHeader.objects.create(project=project, name='To Do', order=1)
            ColumnHeader.objects.create(project=project, name='In Progress', order=2)
            ColumnHeader.objects.create(project=project, name='Done', order=3)

            RowHeader.objects.create(project=project, name='Less than 30 minutes', order=0)
            RowHeader.objects.create(project=project, name='30 minutes to 1 hour', order=1)
            RowHeader.objects.create(project=project, name='1 to 3 hours', order=2)
            RowHeader.objects.create(project=project, name='More than 3 hours', order=3)
            
            messages.success(request, f'Project "{project.name}" created successfully!')
            return redirect('pages:project_grid', pk=project.pk)
    else:
        form = ProjectForm()
    
    return render(request, 'pages/grid/project_form.html', {'form': form, 'title': 'Create Project'})


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
    
    return render(request, 'pages/grid/project_form.html', {
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
    
    return render(request, 'pages/grid/project_confirm_delete.html', {'project': project})


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

    context = {
        'project': project,
        'row_headers': row_headers,
        'column_headers': column_headers,
        'tasks_by_cell': tasks_by_cell,
        'projects': Project.objects.filter(user=request.user),
        'quick_task_form': QuickTaskForm(),
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
                return render(request, 'pages/grid/task_item.html', {
                    'task': task,
                })
            
            messages.success(request, f'Task "{task.text}" added successfully!')
            return redirect('pages:project_grid', pk=project.pk)
        else:
            if request.headers.get('HX-Request'):
                errors = form.errors.get('text', ['An error occurred'])
                return HttpResponse(
                    f'<div class="text-red-600 text-sm">{errors[0]}</div>',
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
            messages.success(request, 'Task updated successfully!')
            return redirect('pages:project_grid', pk=task.project.pk)
    else:
        form = TaskForm(instance=task)
    
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
        status = "completed" if task.completed else "reopened"
        
        if request.headers.get('HX-Request'):
            return JsonResponse({
                'completed': task.completed,
                'message': f'Task {status} successfully!'
            })
        
        messages.success(request, f'Task {status} successfully!')
        return redirect('pages:project_grid', pk=task.project.pk)
    
    return redirect('pages:project_grid', pk=task.project.pk)


@login_required
def task_delete_view(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk, project__user=request.user)
    project_pk = task.project.pk
    
    if request.method == 'POST':
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
    
    return render(request, 'pages/grid/row_form.html', {
        'form': form, 
        'project': project, 
        'title': 'Add Row'
    })


def row_edit_view(request, project_pk, row_pk):
    project = get_object_or_404(Project, pk=project_pk, user=request.user)
    row = get_object_or_404(RowHeader, pk=row_pk, project=project)
    
    if request.method == 'POST':
        form = RowHeaderForm(request.POST, instance=row)
        if form.is_valid():
            form.save()
            messages.success(request, f'Row "{row.name}" updated successfully!')
            return redirect('pages:project_grid', pk=project.pk)
    else:
        form = RowHeaderForm(instance=row)
    
    return render(request, 'pages/grid/row_form.html', {
        'form': form, 
        'project': project, 
        'row': row, 
        'title': 'Edit Row'
    })


def row_delete_view(request, project_pk, row_pk):
    project = get_object_or_404(Project, pk=project_pk, user=request.user)
    row = get_object_or_404(RowHeader, pk=row_pk, project=project)
    
    if request.method == 'POST':
        row_name = row.name
        row.delete()
        messages.success(request, f'Row "{row_name}" deleted successfully!')
        return redirect('pages:project_grid', pk=project.pk)
    
    return render(request, 'pages/grid/row_confirm_delete.html', {
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
    
    return render(request, 'pages/grid/column_form.html', {
        'form': form, 
        'project': project, 
        'title': 'Add Column'
    })


def column_edit_view(request, project_pk, col_pk):
    project = get_object_or_404(Project, pk=project_pk, user=request.user)
    column = get_object_or_404(ColumnHeader, pk=col_pk, project=project)
    
    if request.method == 'POST':
        form = ColumnHeaderForm(request.POST, instance=column)
        if form.is_valid():
            form.save()
            messages.success(request, f'Column "{column.name}" updated successfully!')
            return redirect('pages:project_grid', pk=project.pk)
    else:
        form = ColumnHeaderForm(instance=column)
    
    return render(request, 'pages/grid/column_form.html', {
        'form': form, 
        'project': project, 
        'column': column, 
        'title': 'Edit Column'
    })


def column_delete_view(request, project_pk, col_pk):
    project = get_object_or_404(Project, pk=project_pk, user=request.user)
    column = get_object_or_404(ColumnHeader, pk=col_pk, project=project)
    
    if request.method == 'POST':
        column_name = column.name
        column.delete()
        messages.success(request, f'Column "{column_name}" deleted successfully!')
        return redirect('pages:project_grid', pk=project.pk)
    
    return render(request, 'pages/grid/column_confirm_delete.html', {
        'project': project, 
        'column': column
    })