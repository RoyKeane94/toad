from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Project, RowHeader, ColumnHeader, Task
# You would also create forms in a forms.py file

def home(request):
    return render(request, 'pages/general/home.html')

@login_required
def project_list_view(request):
    projects = Project.objects.filter(user=request.user)
    # Basic project creation form handling (can be moved to a CreateView)
    if request.method == 'POST' and 'create_project' in request.POST:
        project_name = request.POST.get('project_name', '').strip()
        if project_name:
            project = Project.objects.create(user=request.user, name=project_name)
            # Create default headers for the new project
            category_col = ColumnHeader.objects.create(project=project, name='Time / Category', order=0, is_category_column=True)
            ColumnHeader.objects.create(project=project, name='To Do', order=1)
            # Add more default columns as needed

            RowHeader.objects.create(project=project, name='Less than 30 minutes', order=0)
            # Add more default rows as needed
            return redirect('project_grid', pk=project.pk)
            
    return render(request, 'toad_app/project_list.html', {'projects': projects})

@login_required
def project_grid_view(request, pk):
    project = get_object_or_404(Project, pk=pk, user=request.user)
    row_headers = project.row_headers.all().order_by('order')
    # Ensure category column is first, then others by order
    column_headers = list(project.column_headers.filter(is_category_column=True)) + \
                     list(project.column_headers.filter(is_category_column=False).order_by('order'))
    
    tasks_by_cell = {} # {(row.id, col.id): [task1, task2]}
    all_tasks = project.tasks.all()
    for task in all_tasks:
        cell_key = (task.row_header_id, task.column_header_id)
        if cell_key not in tasks_by_cell:
            tasks_by_cell[cell_key] = []
        tasks_by_cell[cell_key].append(task)

    context = {
        'project': project,
        'row_headers': row_headers,
        'column_headers': column_headers,
        'tasks_by_cell': tasks_by_cell,
        'projects': Project.objects.filter(user=request.user) # For the dropdown
    }
    return render(request, 'toad_app/project_grid.html', context)

# --- CRUD Views for Tasks (Conceptual - Forms and full logic needed) ---
@login_required
def task_create_view(request, project_pk, row_pk, col_pk):
    project = get_object_or_404(Project, pk=project_pk, user=request.user)
    row_header = get_object_or_404(RowHeader, pk=row_pk, project=project)
    column_header = get_object_or_404(ColumnHeader, pk=col_pk, project=project)

    if request.method == 'POST':
        task_text = request.POST.get('task_text', '').strip()
        if task_text:
            Task.objects.create(
                project=project,
                row_header=row_header,
                column_header=column_header,
                text=task_text
            )
        return redirect('project_grid', pk=project.pk)
    # Typically, you wouldn't have a GET request for this if it's just inline form submission
    return redirect('project_grid', pk=project.pk)


@login_required
def task_toggle_complete_view(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk, project__user=request.user)
    task.completed = not task.completed
    task.save()
    return redirect('project_grid', pk=task.project.pk)

@login_required
def task_delete_view(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk, project__user=request.user)
    project_pk = task.project.pk
    if request.method == 'POST': # Confirm deletion
        task.delete()
        return redirect('project_grid', pk=project_pk)
    # You'd typically render a confirmation page on GET, or handle via modal + POST
    return redirect('project_grid', pk=project_pk) # Simplified

# --- Stubs for Column/Row CRUD (would use Class-Based Views or more function views with forms) ---
# @login_required
# def column_add_view(request, project_pk): ...
# @login_required
# def column_edit_view(request, project_pk, col_pk): ...
# @login_required
# def column_delete_view(request, project_pk, col_pk): ...
# Similarly for RowHeader CRUD views

# You would use Django's generic Class-Based Views (CreateView, UpdateView, DeleteView)
# for Project, RowHeader, ColumnHeader for easier CRUD.
# Example:
# class ProjectCreateView(LoginRequiredMixin, CreateView):
#     model = Project
#     form_class = ProjectForm # You'd define ProjectForm in forms.py
#     template_name = 'toad_app/project_form.html'
#     success_url = reverse_lazy('project_list') # Or redirect to the new project's grid
#
#     def form_valid(self, form):
#         form.instance.user = self.request.user
#         # Add default rows/columns here after project is saved
#         return super().form_valid(form)