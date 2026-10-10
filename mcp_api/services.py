from datetime import datetime, timezone as dt_timezone

from django.db import transaction
from django.db.models import Prefetch, Q
from django.http import Http404
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_date

from pages.models import ColumnHeader, Project, RowHeader, Task, TaskNote
from pages.specific_views_functions.project_views_functions import (
    get_next_order,
    get_user_project_optimized,
    get_user_task_optimized,
)

from .models import DecisionEntry, DecisionReview, MCPRequestLog, TaskActivity

LOG_DECISION_FIELDS = {
    'grid_id',
    'task_id',
    'request',
    'action_summary',
    'decision',
    'rationale',
    'sources',
    'output_link',
    'requested_by',
    'supersedes',
    'agent',
}
LIST_DECISIONS_FIELDS = {
    'grid_id',
    'task_id',
    'status',
    'agent_name',
    'since',
    'limit',
}
GET_DECISION_FIELDS = {'decision_id'}


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


def _accessible_row(user, row_id):
    if row_id is None:
        raise ApiError('row_id is required')
    row = (
        RowHeader.objects.select_related('project')
        .filter(pk=row_id)
        .filter(Q(project__user=user) | Q(project__team_toad_user=user))
        .distinct()
        .first()
    )
    if not row:
        raise ApiError('Row not found', status=404)
    return row


def _accessible_column(user, column_id):
    if column_id is None:
        raise ApiError('column_id is required')
    column = (
        ColumnHeader.objects.select_related('project')
        .filter(pk=column_id)
        .filter(Q(project__user=user) | Q(project__team_toad_user=user))
        .distinct()
        .first()
    )
    if not column:
        raise ApiError('Column not found', status=404)
    return column


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


def rename_row_for_user(user, row_id, name, agent=None):
    name = _require_name(name)
    row = _accessible_row(user, row_id)
    old_name = row.name
    if name != old_name:
        row.name = name
        row.save(update_fields=['name', 'updated_at'])
        log_activity(
            user, agent, f'renamed row to {name}', project=row.project, task_text=old_name
        )
    return {'ok': True, 'row': serialize_row(row)}


def rename_column_for_user(user, column_id, name, agent=None):
    name = _require_name(name)
    column = _accessible_column(user, column_id)
    old_name = column.name
    if name != old_name:
        column.name = name
        column.save(update_fields=['name', 'updated_at'])
        log_activity(
            user, agent, f'renamed column to {name}', project=column.project, task_text=old_name
        )
    return {'ok': True, 'column': serialize_column(column)}


def delete_row_for_user(user, row_id, agent=None):
    row = _accessible_row(user, row_id)
    project = row.project
    name = row.name
    deleted_id = row.id
    with transaction.atomic():
        row.delete()
        remaining = [item.id for item in _ordered_rows(project)]
        rows_payload = _apply_row_order(project, remaining) if remaining else []
    log_activity(user, agent, f'deleted row {name}', project=project, task_text=name)
    return {'ok': True, 'deleted_row_id': deleted_id, 'rows': rows_payload}


def delete_column_for_user(user, column_id, agent=None):
    column = _accessible_column(user, column_id)
    if column.is_category_column:
        raise ApiError('Cannot delete the category column')
    project = column.project
    name = column.name
    deleted_id = column.id
    with transaction.atomic():
        column.delete()
        data_ids = [
            item.id for item in _ordered_columns(project) if not item.is_category_column
        ]
        columns_payload = _apply_column_order(project, data_ids) if data_ids else [
            serialize_column(item) for item in _ordered_columns(project)
        ]
    log_activity(user, agent, f'deleted column {name}', project=project, task_text=name)
    return {'ok': True, 'deleted_column_id': deleted_id, 'columns': columns_payload}


def _enforce_grid_limit(user):
    tier = getattr(user, 'tier', 'free')
    count = Project.objects.filter(user=user, is_archived=False).count()
    if tier == 'free' and count >= 2:
        raise ApiError('Free users can have a maximum of 2 active grids.', status=403)
    if tier in {'personal', 'personal_trial'} and count >= 10:
        raise ApiError('Personal users can have a maximum of 10 active grids.', status=403)


def _as_name_list(value, field):
    if not isinstance(value, list):
        raise ApiError(f'{field} must be a list of names')
    return [_require_name(item) for item in value]


def create_grid_for_user(user, name, brief=None, rows=None, columns=None, agent=None):
    name = _require_name(name)
    _enforce_grid_limit(user)
    if brief is None:
        brief = ''
    else:
        brief = str(brief)
    if rows is None:
        row_names = ['To do']
    elif rows == []:
        row_names = []
    else:
        row_names = _as_name_list(rows, 'rows')
    if columns is None or columns == []:
        column_names = [name]
    else:
        column_names = _as_name_list(columns, 'columns')

    with transaction.atomic():
        project = Project.objects.create(user=user, name=name, brief=brief)
        ColumnHeader.objects.create(
            project=project,
            name='Time / Category',
            order=0,
            is_category_column=True,
        )
        for index, column_name in enumerate(column_names, start=1):
            ColumnHeader.objects.create(
                project=project,
                name=column_name,
                order=index,
                is_category_column=False,
            )
        for index, row_name in enumerate(row_names):
            RowHeader.objects.create(project=project, name=row_name, order=index)
        if not getattr(user, 'second_grid_created', True):
            active = Project.objects.filter(user=user, is_archived=False).count()
            if active >= 2:
                user.second_grid_created = True
                user.save(update_fields=['second_grid_created'])

    log_activity(user, agent, f'created grid {name}', project=project, task_text=name)
    payload = get_grid_for_user(user, project.id)
    payload['ok'] = True
    return payload


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


def _reject_unknown_fields(arguments, allowed):
    unknown = sorted(set(arguments) - allowed)
    if unknown:
        raise ApiError(f'Unknown field(s): {", ".join(unknown)}')


def _text_value(value, field, required=True, max_length=None, one_line=False):
    if value is None:
        text = ''
    else:
        text = str(value)
        if one_line:
            text = text.replace('\n', ' ').replace('\r', ' ')
        text = text.strip()
    if required and not text:
        raise ApiError(f'{field} is required')
    if max_length is not None and len(text) > max_length:
        raise ApiError(f'{field} must be {max_length} characters or fewer')
    return text


def _as_url_list(value):
    if value is None:
        return []
    if not isinstance(value, list):
        raise ApiError('sources must be a list of URLs')
    urls = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ApiError('sources must be a list of URLs')
        urls.append(item.strip())
    return urls


def serialize_decision(entry, include_reviews=False, include_chain=False):
    payload = {
        'id': entry.id,
        'created_at': entry.created_at.isoformat(),
        'grid_id': entry.grid_id,
        'task_id': entry.task_id,
        'task_id_snapshot': entry.task_id_snapshot,
        'task_text_snapshot': entry.task_text_snapshot,
        'agent_name': entry.agent_name,
        'requested_by': entry.requested_by,
        'request': entry.request,
        'action_summary': entry.action_summary,
        'decision': entry.decision,
        'rationale': entry.rationale,
        'sources': entry.sources or [],
        'output_link': entry.output_link or '',
        'status': entry.status,
        'reviewer': entry.reviewer,
        'reviewed_at': entry.reviewed_at.isoformat() if entry.reviewed_at else None,
        'review_comment': entry.review_comment,
        'supersedes': entry.supersedes_id,
        'prev_hash': entry.prev_hash,
        'entry_hash': entry.entry_hash,
    }
    if include_reviews:
        payload['reviews'] = [
            {
                'id': review.id,
                'actor': review.actor,
                'old_status': review.old_status,
                'new_status': review.new_status,
                'comment': review.comment,
                'created_at': review.created_at.isoformat(),
            }
            for review in entry.reviews.all()
        ]
    if include_chain:
        payload['supersede_chain'] = [
            serialize_decision(item) for item in _supersede_chain(entry)
        ]
    return payload


def _supersede_chain(entry):
    current = entry
    seen = {current.id}
    while current.supersedes_id and current.supersedes_id not in seen:
        current = current.supersedes
        seen.add(current.id)
    chain = [current]
    while True:
        nxt = (
            DecisionEntry.objects.filter(supersedes=current)
            .exclude(id__in={item.id for item in chain})
            .order_by('id')
            .first()
        )
        if nxt is None:
            break
        chain.append(nxt)
        current = nxt
    return chain


def _accessible_decision_qs(user):
    return DecisionEntry.objects.filter(
        Q(user=user) | Q(grid__user=user) | Q(grid__team_toad_user=user)
    ).distinct()


def apply_decision_review(entry, new_status, actor, comment='', update_task=True):
    if new_status not in DecisionEntry.REVIEW_STATUSES and new_status != DecisionEntry.STATUS_PENDING:
        raise ApiError('status must be pending_review, approved, rejected or superseded')
    old_status = entry.status
    if old_status == new_status:
        return entry
    comment = (comment or '').strip()
    now = timezone.now()
    DecisionReview.objects.create(
        entry=entry,
        actor=actor,
        old_status=old_status,
        new_status=new_status,
        comment=comment,
        created_at=now,
    )
    entry.status = new_status
    entry.reviewer = actor
    entry.reviewed_at = now
    entry.review_comment = comment
    entry.save(update_fields=['status', 'reviewer', 'reviewed_at', 'review_comment'])
    if update_task and entry.task_id and new_status in {
        DecisionEntry.STATUS_APPROVED,
        DecisionEntry.STATUS_REJECTED,
    }:
        task = entry.task
        task.needs_review = False
        update_fields = ['needs_review', 'updated_at']
        if new_status == DecisionEntry.STATUS_APPROVED:
            task.owner = Task.OWNER_YOU
            update_fields.append('owner')
        task.save(update_fields=update_fields)
    return entry


def review_decision_for_user(user, decision_id, new_status, comment=''):
    entry = _accessible_decision_qs(user).filter(pk=decision_id).first()
    if entry is None:
        raise ApiError('Decision not found', status=404)
    if new_status not in {DecisionEntry.STATUS_APPROVED, DecisionEntry.STATUS_REJECTED}:
        raise ApiError("status must be 'approved' or 'rejected'")
    if entry.status != DecisionEntry.STATUS_PENDING:
        raise ApiError('Only pending decisions can be approved or rejected')
    actor = user.get_full_name() or user.email
    return serialize_decision(
        apply_decision_review(entry, new_status, actor, comment=comment),
        include_reviews=True,
    )


def log_decision_for_user(user, arguments, agent=None, token=None):
    arguments = arguments or {}
    _reject_unknown_fields(arguments, LOG_DECISION_FIELDS)
    if token is None:
        raise ApiError('A personal access token is required to log a decision', status=401)

    grid_id = arguments.get('grid_id')
    project = _require_grid(user, grid_id)
    task = None
    task_id = arguments.get('task_id')
    if task_id is not None:
        try:
            task = get_user_task_optimized(task_id, user, select_related=['project'])
        except Http404:
            raise ApiError('Task not found', status=404)
        if task.project_id != project.id:
            raise ApiError('task_id does not belong to this grid')

    request_text = _text_value(
        arguments.get('request'), 'request', max_length=500, one_line=True
    )
    action_summary = _text_value(arguments.get('action_summary'), 'action_summary')
    decision = _text_value(arguments.get('decision'), 'decision')
    rationale = _text_value(arguments.get('rationale'), 'rationale', required=False)
    output_link = _text_value(arguments.get('output_link'), 'output_link', required=False)
    requested_by = _text_value(
        arguments.get('requested_by'),
        'requested_by',
        required=False,
        max_length=200,
        one_line=True,
    ) or (user.get_full_name() or user.email)
    agent_name = _text_value(
        arguments.get('agent'), 'agent', required=False, max_length=100, one_line=True
    ) or (agent or (token.name if token else ''))
    if not agent_name:
        raise ApiError('agent is required')
    sources = _as_url_list(arguments.get('sources'))

    supersedes = None
    supersedes_id = arguments.get('supersedes')
    if supersedes_id is not None:
        supersedes = _accessible_decision_qs(user).filter(pk=supersedes_id).first()
        if supersedes is None:
            raise ApiError('supersedes decision not found', status=404)

    with transaction.atomic():
        previous = (
            DecisionEntry.objects.select_for_update()
            .filter(user=user)
            .order_by('-id')
            .first()
        )
        entry = DecisionEntry(
            user=user,
            created_at=timezone.now(),
            grid=project,
            task=task,
            task_id_snapshot=task.id if task is not None else None,
            task_text_snapshot=task.text if task is not None else '',
            agent_name=agent_name,
            token=token,
            requested_by=requested_by,
            request=request_text,
            action_summary=action_summary,
            decision=decision,
            rationale=rationale,
            sources=sources,
            output_link=output_link,
            status=DecisionEntry.STATUS_PENDING,
            supersedes=supersedes,
            prev_hash=previous.entry_hash if previous else '',
        )
        entry.save()
        entry.entry_hash = entry.compute_hash()
        entry.save(update_fields=['entry_hash'])
        if supersedes is not None and supersedes.status != DecisionEntry.STATUS_SUPERSEDED:
            apply_decision_review(
                supersedes,
                DecisionEntry.STATUS_SUPERSEDED,
                actor=agent_name,
                comment=f'Superseded by decision {entry.id}',
                update_task=False,
            )
        if task is not None:
            task.needs_review = True
            task.save(update_fields=['needs_review', 'updated_at'])

    return serialize_decision(entry)


def _parse_since(value):
    if value is None or value == '':
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    parsed = parse_datetime(text)
    if parsed is None:
        day = parse_date(text)
        if day is not None:
            parsed = datetime(day.year, day.month, day.day)
    if parsed is None:
        raise ApiError('since must be an ISO date or datetime')
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, dt_timezone.utc)
    return parsed


def list_decisions_for_user(
    user,
    grid_id=None,
    task_id=None,
    status=None,
    agent_name=None,
    since=None,
    limit=None,
):
    qs = _accessible_decision_qs(user).select_related('grid', 'task')
    if grid_id is not None:
        qs = qs.filter(grid_id=grid_id)
    if task_id is not None:
        qs = qs.filter(Q(task_id=task_id) | Q(task_id_snapshot=task_id))
    if status:
        valid = {choice[0] for choice in DecisionEntry.STATUS_CHOICES}
        if status not in valid:
            raise ApiError(f'status must be one of {", ".join(sorted(valid))}')
        qs = qs.filter(status=status)
    if agent_name:
        qs = qs.filter(agent_name=agent_name)
    since_at = _parse_since(since)
    if since_at is not None:
        qs = qs.filter(created_at__gte=since_at)
    if limit is None:
        limit = 50
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        raise ApiError('limit must be an integer')
    if limit < 1 or limit > 200:
        raise ApiError('limit must be between 1 and 200')
    entries = list(qs.order_by('-created_at', '-id')[:limit])
    return {'decisions': [serialize_decision(entry) for entry in entries]}


def get_decision_for_user(user, decision_id):
    if decision_id is None:
        raise ApiError('decision_id is required')
    entry = (
        _accessible_decision_qs(user)
        .select_related('grid', 'task', 'supersedes')
        .prefetch_related('reviews')
        .filter(pk=decision_id)
        .first()
    )
    if entry is None:
        raise ApiError('Decision not found', status=404)
    return serialize_decision(entry, include_reviews=True, include_chain=True)


def verify_decision_chain(user, grid_id=None):
    if grid_id is not None:
        user_ids = list(
            DecisionEntry.objects.filter(grid_id=grid_id)
            .filter(Q(user=user) | Q(grid__user=user) | Q(grid__team_toad_user=user))
            .values_list('user_id', flat=True)
            .distinct()
        )
        if not user_ids:
            user_ids = [user.id]
        qs = DecisionEntry.objects.filter(user_id__in=user_ids)
    else:
        qs = DecisionEntry.objects.filter(user=user)
    entries = list(qs.order_by('id'))
    broken = []
    previous_by_user = {}
    for entry in entries:
        expected = entry.compute_hash()
        reasons = []
        if entry.entry_hash != expected:
            reasons.append('entry_hash does not match recomputed hash')
        prev = previous_by_user.get(entry.user_id)
        expected_prev = prev.entry_hash if prev else ''
        if entry.prev_hash != expected_prev:
            reasons.append('prev_hash does not match previous entry')
        if reasons:
            broken.append({'id': entry.id, 'reasons': reasons})
        previous_by_user[entry.user_id] = entry
    return {
        'ok': not broken,
        'checked': len(entries),
        'broken': broken,
    }


def call_tool(user, name, arguments, agent=None, token=None):
    arguments = arguments or {}
    if name == 'list_grids':
        return list_grids_for_user(user)
    if name == 'create_grid':
        return create_grid_for_user(
            user,
            arguments.get('name'),
            brief=arguments.get('brief'),
            rows=arguments.get('rows'),
            columns=arguments.get('columns'),
            agent=agent,
        )
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
    if name == 'rename_row':
        return rename_row_for_user(
            user,
            arguments.get('row_id'),
            arguments.get('name'),
            agent=agent,
        )
    if name == 'rename_column':
        return rename_column_for_user(
            user,
            arguments.get('column_id'),
            arguments.get('name'),
            agent=agent,
        )
    if name == 'delete_row':
        return delete_row_for_user(user, arguments.get('row_id'), agent=agent)
    if name == 'delete_column':
        return delete_column_for_user(user, arguments.get('column_id'), agent=agent)
    if name == 'log_request':
        return log_request_for_user(
            user,
            arguments.get('what') or arguments.get('request'),
            asked_by=arguments.get('asked_by'),
            follow_up_needed=arguments.get('follow_up_needed', False),
        )
    if name == 'log_decision':
        return log_decision_for_user(user, arguments, agent=agent, token=token)
    if name == 'list_decisions':
        _reject_unknown_fields(arguments, LIST_DECISIONS_FIELDS)
        return list_decisions_for_user(
            user,
            grid_id=arguments.get('grid_id'),
            task_id=arguments.get('task_id'),
            status=arguments.get('status'),
            agent_name=arguments.get('agent_name'),
            since=arguments.get('since'),
            limit=arguments.get('limit'),
        )
    if name == 'get_decision':
        _reject_unknown_fields(arguments, GET_DECISION_FIELDS)
        return get_decision_for_user(user, arguments.get('decision_id'))
    raise ApiError(f'Unknown tool: {name}', status=404)
