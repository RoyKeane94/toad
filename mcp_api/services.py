from django.db import transaction
from django.db.models import Prefetch, Q
from django.http import Http404

from pages.models import ColumnHeader, Project, RowHeader, Task, TaskNote
from pages.specific_views_functions.project_views_functions import (
    get_next_order,
    get_user_project_optimized,
    get_user_task_optimized,
)

from .models import MCPRequestLog, TaskActivity


class ApiError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


def _accessible_grids(user):
    return Project.objects.filter(
        Q(user=user) | Q(team_toad_user=user),
        is_archived=False,
    ).distinct()


def log_activity(user, agent, action, task=None, project=None, task_text=''):
    if not agent:
        return
    TaskActivity.objects.create(
        user=user,
        agent=agent,
        action=action,
        task=task,
        project=project or (task.project if task is not None else None),
        task_text=task_text or (task.text if task is not None else ''),
    )


def serialize_task(task):
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
        'owner': task.owner,
        'needs_review': task.needs_review,
    }


def serialize_activity(activity):
    return {
        'agent': activity.agent,
        'action': activity.action,
        'task': activity.task_text,
        'task_id': activity.task_id,
        'created_at': activity.created_at.isoformat(),
    }


def serialize_row(row):
    return {'id': row.id, 'name': row.name, 'order': row.order}


def serialize_column(column):
    return {
        'id': column.id,
        'name': column.name,
        'order': column.order,
        'is_category_column': column.is_category_column,
    }


def _require_grid(user, grid_id):
    if grid_id is None:
        raise ApiError('grid_id is required')
    try:
        return get_user_project_optimized(grid_id, user)
    except Http404:
        raise ApiError('Grid not found', status=404)


def _require_name(name):
    name = (name or '').strip()
    if not name:
        raise ApiError('name is required')
    if len(name) > 100:
        raise ApiError('name must be 100 characters or fewer')
    return name


def _as_id_list(value, field):
    if not isinstance(value, list) or not value:
        raise ApiError(f'{field} must be a non-empty list of IDs')
    ids = []
    for item in value:
        try:
            ids.append(int(item))
        except (TypeError, ValueError):
            raise ApiError(f'{field} must be a list of integers')
    if len(ids) != len(set(ids)):
        raise ApiError(f'{field} must not contain duplicates')
    return ids


def _ordered_rows(project):
    return list(project.row_headers.order_by('order', 'id'))


def _ordered_columns(project):
    return list(project.column_headers.order_by('order', 'id'))


def _apply_row_order(project, row_ids):
    rows = _ordered_rows(project)
    by_id = {row.id: row for row in rows}
    if set(row_ids) != set(by_id):
        raise ApiError('row_ids must include every row in the grid exactly once')
    for index, row_id in enumerate(row_ids):
        row = by_id[row_id]
        if row.order != index:
            row.order = index
            row.save(update_fields=['order', 'updated_at'])
    return [serialize_row(by_id[row_id]) for row_id in row_ids]


def _apply_column_order(project, column_ids):
    columns = _ordered_columns(project)
    category = [column for column in columns if column.is_category_column]
    data = [column for column in columns if not column.is_category_column]
    by_id = {column.id: column for column in data}
    category_ids = {column.id for column in category}
    if any(column_id in category_ids for column_id in column_ids):
        raise ApiError('Do not include the category column; it stays first')
    if set(column_ids) != set(by_id):
        raise ApiError('column_ids must include every data column in the grid exactly once')
    for column in category:
        if column.order != 0:
            column.order = 0
            column.save(update_fields=['order', 'updated_at'])
    for index, column_id in enumerate(column_ids, start=1):
        column = by_id[column_id]
        if column.order != index:
            column.order = index
            column.save(update_fields=['order', 'updated_at'])
    return [serialize_column(column) for column in _ordered_columns(project)]


def add_row_for_user(user, grid_id, name, after_row_id=None, agent=None):
    name = _require_name(name)
    project = _require_grid(user, grid_id)
    rows = _ordered_rows(project)
    row_ids = [row.id for row in rows]
    if after_row_id is not None:
        if after_row_id not in row_ids:
            raise ApiError('after_row_id does not belong to this grid', status=404)
        insert_at = row_ids.index(after_row_id) + 1
    else:
        insert_at = len(row_ids)

    with transaction.atomic():
        row = RowHeader.objects.create(project=project, name=name, order=insert_at)
        row_ids.insert(insert_at, row.id)
        rows_payload = _apply_row_order(project, row_ids)
    log_activity(user, agent, f'added row {name}', project=project, task_text=name)
    return {'ok': True, 'row': serialize_row(row), 'rows': rows_payload}


def add_column_for_user(user, grid_id, name, after_column_id=None, agent=None):
    name = _require_name(name)
    project = _require_grid(user, grid_id)
    columns = _ordered_columns(project)
    data_ids = [column.id for column in columns if not column.is_category_column]
    if after_column_id is not None:
        after = next((column for column in columns if column.id == after_column_id), None)
        if after is None:
            raise ApiError('after_column_id does not belong to this grid', status=404)
        if after.is_category_column:
            insert_at = 0
        else:
            insert_at = data_ids.index(after_column_id) + 1
    else:
        insert_at = len(data_ids)

    with transaction.atomic():
        column = ColumnHeader.objects.create(
            project=project,
            name=name,
            is_category_column=False,
            order=insert_at + 1,
        )
        data_ids.insert(insert_at, column.id)
        columns_payload = _apply_column_order(project, data_ids)
    log_activity(user, agent, f'added column {name}', project=project, task_text=name)
    return {'ok': True, 'column': serialize_column(column), 'columns': columns_payload}


def reorder_rows_for_user(user, grid_id, row_ids, agent=None):
    row_ids = _as_id_list(row_ids, 'row_ids')
    project = _require_grid(user, grid_id)
    with transaction.atomic():
        rows_payload = _apply_row_order(project, row_ids)
    names = ', '.join(row['name'] for row in rows_payload)
    log_activity(user, agent, 'reordered rows', project=project, task_text=names)
    return {'ok': True, 'rows': rows_payload}


def reorder_columns_for_user(user, grid_id, column_ids, agent=None):
    column_ids = _as_id_list(column_ids, 'column_ids')
    project = _require_grid(user, grid_id)
    with transaction.atomic():
        columns_payload = _apply_column_order(project, column_ids)
    names = ', '.join(
        column['name'] for column in columns_payload if not column['is_category_column']
    )
    log_activity(user, agent, 'reordered columns', project=project, task_text=names)
    return {'ok': True, 'columns': columns_payload}


def list_grids_for_user(user):
    grids = _accessible_grids(user).only('id', 'name').order_by('name')
    return {'grids': [{'id': grid.id, 'name': grid.name} for grid in grids]}


def get_grid_for_user(user, grid_id):
    if grid_id is None:
        raise ApiError('grid_id is required')
    try:
        project = get_user_project_optimized(
            grid_id,
            user,
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
        raise ApiError('Grid not found', status=404)

    activities = TaskActivity.objects.filter(project=project).order_by('-created_at')[:20]

    return {
        'id': project.id,
        'name': project.name,
        'brief': project.brief,
        'rows': [
            {'id': row.id, 'name': row.name, 'order': row.order}
            for row in project.row_headers.all()
        ],
        'columns': [
            {
                'id': column.id,
                'name': column.name,
                'order': column.order,
                'is_category_column': column.is_category_column,
            }
            for column in project.column_headers.all()
        ],
        'tasks': [serialize_task(task) for task in project.tasks.all()],
        'activity': [serialize_activity(item) for item in activities],
    }


def update_grid_for_user(user, grid_id, brief=None, agent=None):
    if grid_id is None:
        raise ApiError('grid_id is required')
    if brief is None:
        raise ApiError('brief is required')
    try:
        project = get_user_project_optimized(grid_id, user)
    except Http404:
        raise ApiError('Grid not found', status=404)
    project.brief = brief
    project.save(update_fields=['brief', 'updated_at'])
    log_activity(user, agent, 'updated the brief', project=project, task_text=brief[:200])
    return {'ok': True, 'id': project.id, 'name': project.name, 'brief': project.brief}


def add_task_for_user(
    user,
    grid_id,
    row_id,
    column_id,
    text,
    note=None,
    owner=None,
    needs_review=None,
    agent=None,
):
    text = (text or '').strip()
    note_text = (note or '').strip() or None
    if grid_id is None or row_id is None or column_id is None:
        raise ApiError('grid_id, row_id and column_id are required')
    if not text:
        raise ApiError('text is required')

    try:
        project = get_user_project_optimized(grid_id, user)
    except Http404:
        raise ApiError('Grid not found', status=404)
    try:
        row = project.row_headers.get(pk=row_id)
        column = project.column_headers.get(pk=column_id)
    except (RowHeader.DoesNotExist, ColumnHeader.DoesNotExist):
        raise ApiError('Row or column does not belong to this grid', status=404)

    if column.is_category_column:
        raise ApiError('Cannot add a task to the category column. Use a data column.')

    if owner is None:
        owner = Task.OWNER_AGENT if agent else Task.OWNER_YOU
    if owner not in {Task.OWNER_YOU, Task.OWNER_AGENT}:
        raise ApiError("owner must be 'you' or 'agent'")
    if needs_review is None:
        needs_review = False
    if not isinstance(needs_review, bool):
        raise ApiError('needs_review must be true or false')

    task = Task(
        project=project,
        row_header=row,
        column_header=column,
        text=text,
        owner=owner,
        needs_review=needs_review,
        order=get_next_order(Task.objects.filter(
            project=project,
            row_header=row,
            column_header=column,
        )),
    )
    task.full_clean()
    task.save()

    if note_text:
        TaskNote.objects.create(task=task, created_by=user, note=note_text)

    log_activity(user, agent, 'added', task=task, project=project)

    task = Task.objects.select_related('row_header', 'column_header').prefetch_related(
        Prefetch('notes', queryset=TaskNote.objects.order_by('-created_at'))
    ).get(pk=task.pk)
    return {'ok': True, 'task': serialize_task(task)}


def update_task_for_user(user, task_id, ticked=None, text=None, row_id=None, column_id=None, data=None, agent=None):
    if task_id is None:
        raise ApiError('task_id is required')

    try:
        task = get_user_task_optimized(
            task_id,
            user,
            select_related=['project', 'row_header', 'column_header'],
        )
    except Http404:
        raise ApiError('Task not found', status=404)

    payload = data if data is not None else {}
    update_fields = ['updated_at']
    actions = []

    new_text = payload['text'] if 'text' in payload else text
    if new_text is not None:
        new_text = new_text.strip()
        if not new_text:
            raise ApiError('text cannot be empty')
        if new_text != task.text:
            actions.append('renamed')
        task.text = new_text
        update_fields.append('text')

    new_ticked = payload['ticked'] if 'ticked' in payload else ticked
    if new_ticked is not None:
        if not isinstance(new_ticked, bool):
            raise ApiError('ticked must be true or false')
        if new_ticked != task.completed:
            actions.append('ticked' if new_ticked else 'unticked')
        task.completed = new_ticked
        update_fields.append('completed')

    if 'owner' in payload and payload.get('owner') is not None:
        owner = payload.get('owner')
        if owner not in {Task.OWNER_YOU, Task.OWNER_AGENT}:
            raise ApiError("owner must be 'you' or 'agent'")
        if owner != task.owner:
            actions.append('handed to agent' if owner == Task.OWNER_AGENT else 'handed to you')
        task.owner = owner
        update_fields.append('owner')

    if 'needs_review' in payload and payload.get('needs_review') is not None:
        needs_review = payload.get('needs_review')
        if not isinstance(needs_review, bool):
            raise ApiError('needs_review must be true or false')
        if needs_review != task.needs_review:
            actions.append('marked for review' if needs_review else 'cleared review')
        task.needs_review = needs_review
        update_fields.append('needs_review')

    new_row_id = payload.get('row_id') if payload.get('row_id') is not None else row_id
    if new_row_id is None:
        new_row_id = task.row_header_id
    new_column_id = payload.get('column_id') if payload.get('column_id') is not None else column_id
    if new_column_id is None:
        new_column_id = task.column_header_id
    moving = new_row_id != task.row_header_id or new_column_id != task.column_header_id

    if moving:
        try:
            new_row = task.project.row_headers.get(pk=new_row_id)
            new_column = task.project.column_headers.get(pk=new_column_id)
        except (RowHeader.DoesNotExist, ColumnHeader.DoesNotExist):
            raise ApiError('Row or column does not belong to this grid', status=404)
        if new_column.is_category_column:
            raise ApiError('Cannot move a task into the category column.')
        destination = new_column.name if new_column_id != task.column_header_id else new_row.name
        task.row_header = new_row
        task.column_header = new_column
        task.order = get_next_order(Task.objects.filter(
            project=task.project,
            row_header=new_row,
            column_header=new_column,
        ).exclude(pk=task.pk))
        update_fields.extend(['row_header', 'column_header', 'order'])
        actions.append(f'moved to {destination}')

    if len(update_fields) == 1:
        raise ApiError('Provide ticked, text, row_id, column_id, owner or needs_review to update')

    task.save(update_fields=update_fields)
    for action in actions:
        log_activity(user, agent, action, task=task, project=task.project)

    task = Task.objects.select_related('row_header', 'column_header').prefetch_related(
        Prefetch('notes', queryset=TaskNote.objects.order_by('-created_at'))
    ).get(pk=task.pk)
    return {'ok': True, 'task': serialize_task(task)}


def delete_task_for_user(user, task_id, agent=None):
    if task_id is None:
        raise ApiError('task_id is required')
    try:
        task = get_user_task_optimized(task_id, user, select_related=['project'])
    except Http404:
        raise ApiError('Task not found', status=404)
    deleted_id = task.id
    project = task.project
    task_text = task.text
    log_activity(user, agent, 'deleted', task=None, project=project, task_text=task_text)
    task.delete()
    return {'ok': True, 'deleted_task_id': deleted_id}


def log_request_for_user(user, what, asked_by=None, follow_up_needed=False):
    what = (what or '').strip()
    if not what:
        raise ApiError('what is required')
    asked_by = (asked_by or '').strip() or user.get_full_name() or user.email
    if not isinstance(follow_up_needed, bool):
        raise ApiError('follow_up_needed must be true or false')
    MCPRequestLog.objects.create(
        user=user,
        asked_by=asked_by,
        request_text=what,
        follow_up_needed=follow_up_needed,
    )
    return {'ok': True}


def call_tool(user, name, arguments, agent=None):
    arguments = arguments or {}
    if name == 'list_grids':
        return list_grids_for_user(user)
    if name == 'get_grid':
        return get_grid_for_user(user, arguments.get('grid_id'))
    if name == 'update_grid':
        return update_grid_for_user(
            user,
            arguments.get('grid_id'),
            brief=arguments.get('brief'),
            agent=agent,
        )
    if name == 'add_task':
        return add_task_for_user(
            user,
            arguments.get('grid_id'),
            arguments.get('row_id'),
            arguments.get('column_id'),
            arguments.get('text'),
            note=arguments.get('note'),
            owner=arguments.get('owner'),
            needs_review=arguments.get('needs_review'),
            agent=agent,
        )
    if name == 'update_task':
        return update_task_for_user(
            user,
            arguments.get('task_id'),
            data=arguments,
            agent=agent,
        )
    if name == 'delete_task':
        return delete_task_for_user(user, arguments.get('task_id'), agent=agent)
    if name == 'add_row':
        return add_row_for_user(
            user,
            arguments.get('grid_id'),
            arguments.get('name'),
            after_row_id=arguments.get('after_row_id'),
            agent=agent,
        )
    if name == 'add_column':
        return add_column_for_user(
            user,
            arguments.get('grid_id'),
            arguments.get('name'),
            after_column_id=arguments.get('after_column_id'),
            agent=agent,
        )
    if name == 'reorder_rows':
        return reorder_rows_for_user(
            user,
            arguments.get('grid_id'),
            arguments.get('row_ids'),
            agent=agent,
        )
    if name == 'reorder_columns':
        return reorder_columns_for_user(
            user,
            arguments.get('grid_id'),
            arguments.get('column_ids'),
            agent=agent,
        )
    if name == 'log_request':
        return log_request_for_user(
            user,
            arguments.get('what') or arguments.get('request'),
            asked_by=arguments.get('asked_by'),
            follow_up_needed=arguments.get('follow_up_needed', False),
        )
    raise ApiError(f'Unknown tool: {name}', status=404)
