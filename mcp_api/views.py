from django.db.models import Prefetch, Q
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_http_methods

from pages.models import ColumnHeader, Project, RowHeader, Task, TaskNote
from pages.specific_views_functions.project_views_functions import (
    get_next_order,
    get_user_project_optimized,
    get_user_task_optimized,
)

from .auth import mcp_token_required, parse_json_body
from .models import MCPRequestLog


def _json_error(message, status=400):
    return JsonResponse({'error': message}, status=status)


def _accessible_grids(user):
    return Project.objects.filter(
        Q(user=user) | Q(team_toad_user=user),
        is_archived=False,
    ).distinct()


def _serialize_task(task):
    notes = list(task.notes.all())
    latest_note = notes[0] if notes else None
    return {
        'id': task.id,
        'text': task.text,
        'row_id': task.row_header_id,
        'row': task.row_header.name,
        'column_id': task.column_header_id,
        'column': task.column_header.name,
        'ticked': task.completed,
        'note': latest_note.note if latest_note else None,
    }


@mcp_token_required
@require_http_methods(['GET', 'POST'])
def whoami(request):
    return JsonResponse({
        'id': request.user.id,
        'email': request.user.email,
        'name': request.user.get_full_name(),
    })


@mcp_token_required
@require_http_methods(['POST'])
def list_grids(request):
    grids = _accessible_grids(request.user).only('id', 'name').order_by('name')
    return JsonResponse({
        'grids': [{'id': grid.id, 'name': grid.name} for grid in grids],
    })


@mcp_token_required
@require_http_methods(['POST'])
def get_grid(request):
    try:
        data = parse_json_body(request)
    except ValueError as exc:
        return _json_error(str(exc))

    grid_id = data.get('grid_id')
    if grid_id is None:
        return _json_error('grid_id is required')

    try:
        project = get_user_project_optimized(
            grid_id,
            request.user,
            prefetch_related=[
                'row_headers',
                'column_headers',
                Prefetch(
                    'tasks',
                    queryset=Task.objects.select_related('row_header', 'column_header').prefetch_related(
                        Prefetch('notes', queryset=TaskNote.objects.order_by('-created_at'))
                    ),
                ),
            ],
        )
    except Http404:
        return _json_error('Grid not found', status=404)

    rows = [
        {'id': row.id, 'name': row.name, 'order': row.order}
        for row in project.row_headers.all()
    ]
    columns = [
        {
            'id': column.id,
            'name': column.name,
            'order': column.order,
            'is_category_column': column.is_category_column,
        }
        for column in project.column_headers.all()
    ]
    tasks = [_serialize_task(task) for task in project.tasks.all()]

    return JsonResponse({
        'id': project.id,
        'name': project.name,
        'rows': rows,
        'columns': columns,
        'tasks': tasks,
    })


@mcp_token_required
@require_http_methods(['POST'])
def add_task(request):
    try:
        data = parse_json_body(request)
    except ValueError as exc:
        return _json_error(str(exc))

    grid_id = data.get('grid_id')
    row_id = data.get('row_id')
    column_id = data.get('column_id')
    text = (data.get('text') or '').strip()
    note_text = (data.get('note') or '').strip() or None

    if grid_id is None or row_id is None or column_id is None:
        return _json_error('grid_id, row_id and column_id are required')
    if not text:
        return _json_error('text is required')

    try:
        project = get_user_project_optimized(grid_id, request.user)
    except Http404:
        return _json_error('Grid not found', status=404)
    try:
        row = project.row_headers.get(pk=row_id)
        column = project.column_headers.get(pk=column_id)
    except (RowHeader.DoesNotExist, ColumnHeader.DoesNotExist):
        return _json_error('Row or column does not belong to this grid', status=404)

    if column.is_category_column:
        return _json_error('Cannot add a task to the category column. Use a data column.')

    task = Task(
        project=project,
        row_header=row,
        column_header=column,
        text=text,
        order=get_next_order(Task.objects.filter(
            project=project,
            row_header=row,
            column_header=column,
        )),
    )
    task.full_clean()
    task.save()

    if note_text:
        TaskNote.objects.create(task=task, created_by=request.user, note=note_text)

    task = Task.objects.select_related('row_header', 'column_header').prefetch_related(
        Prefetch('notes', queryset=TaskNote.objects.order_by('-created_at'))
    ).get(pk=task.pk)

    return JsonResponse({'ok': True, 'task': _serialize_task(task)}, status=201)


@mcp_token_required
@require_http_methods(['POST'])
def update_task(request):
    try:
        data = parse_json_body(request)
    except ValueError as exc:
        return _json_error(str(exc))

    task_id = data.get('task_id')
    if task_id is None:
        return _json_error('task_id is required')

    try:
        task = get_user_task_optimized(
            task_id,
            request.user,
            select_related=['project', 'row_header', 'column_header'],
        )
    except Http404:
        return _json_error('Task not found', status=404)

    update_fields = ['updated_at']

    if 'text' in data:
        new_text = (data.get('text') or '').strip()
        if not new_text:
            return _json_error('text cannot be empty')
        task.text = new_text
        update_fields.append('text')

    if 'ticked' in data:
        ticked = data.get('ticked')
        if not isinstance(ticked, bool):
            return _json_error('ticked must be true or false')
        task.completed = ticked
        update_fields.append('completed')

    new_row_id = data.get('row_id', task.row_header_id)
    new_column_id = data.get('column_id', task.column_header_id)
    moving = new_row_id != task.row_header_id or new_column_id != task.column_header_id

    if moving:
        try:
            new_row = task.project.row_headers.get(pk=new_row_id)
            new_column = task.project.column_headers.get(pk=new_column_id)
        except (RowHeader.DoesNotExist, ColumnHeader.DoesNotExist):
            return _json_error('Row or column does not belong to this grid', status=404)
        if new_column.is_category_column:
            return _json_error('Cannot move a task into the category column.')
        task.row_header = new_row
        task.column_header = new_column
        task.order = get_next_order(Task.objects.filter(
            project=task.project,
            row_header=new_row,
            column_header=new_column,
        ).exclude(pk=task.pk))
        update_fields.extend(['row_header', 'column_header', 'order'])

    if len(update_fields) == 1:
        return _json_error('Provide ticked, text, row_id or column_id to update')

    task.save(update_fields=update_fields)

    task = Task.objects.select_related('row_header', 'column_header').prefetch_related(
        Prefetch('notes', queryset=TaskNote.objects.order_by('-created_at'))
    ).get(pk=task.pk)

    return JsonResponse({'ok': True, 'task': _serialize_task(task)})


@mcp_token_required
@require_http_methods(['POST'])
def delete_task(request):
    try:
        data = parse_json_body(request)
    except ValueError as exc:
        return _json_error(str(exc))

    task_id = data.get('task_id')
    if task_id is None:
        return _json_error('task_id is required')

    try:
        task = get_user_task_optimized(task_id, request.user, select_related=['project'])
    except Http404:
        return _json_error('Task not found', status=404)
    task_id = task.id
    task.delete()
    return JsonResponse({'ok': True, 'deleted_task_id': task_id})


@mcp_token_required
@require_http_methods(['POST'])
def log_request(request):
    try:
        data = parse_json_body(request)
    except ValueError as exc:
        return _json_error(str(exc))

    what = (data.get('what') or data.get('request') or '').strip()
    if not what:
        return _json_error('what is required')

    asked_by = (data.get('asked_by') or '').strip() or request.user.get_full_name() or request.user.email
    follow_up_needed = data.get('follow_up_needed', False)
    if not isinstance(follow_up_needed, bool):
        return _json_error('follow_up_needed must be true or false')

    MCPRequestLog.objects.create(
        user=request.user,
        asked_by=asked_by,
        request_text=what,
        follow_up_needed=follow_up_needed,
    )
    return JsonResponse({'ok': True})
