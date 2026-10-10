import csv
from datetime import datetime, time, timezone as dt_timezone

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_http_methods, require_POST

from mcp_api.models import DecisionEntry, user_has_agent_access
from mcp_api.services import (
    ApiError,
    _accessible_decision_qs,
    review_decision_for_user,
    verify_decision_chain,
)
from pages.models import Project
from pages.specific_views_functions.project_views_functions import (
    get_user_project_optimized,
    get_user_task_optimized,
)


def _require_agent_access(user):
    if not user_has_agent_access(user):
        raise Http404


def _decision_filters(request, grid_id=None, task_id=None):
    grid_filter = request.GET.get('grid') or grid_id
    agent = (request.GET.get('agent') or '').strip()
    status = (request.GET.get('status') or '').strip()
    date_from = (request.GET.get('date_from') or '').strip()
    date_to = (request.GET.get('date_to') or '').strip()
    return {
        'grid_id': int(grid_filter) if grid_filter else None,
        'task_id': task_id,
        'agent_name': agent or None,
        'status': status or None,
        'date_from': date_from,
        'date_to': date_to,
    }


def _filtered_entries(user, filters):
    qs = (
        _accessible_decision_qs(user)
        .select_related('grid', 'task')
        .prefetch_related('reviews')
        .order_by('-created_at', '-id')
    )
    if filters.get('grid_id'):
        qs = qs.filter(grid_id=filters['grid_id'])
    if filters.get('task_id'):
        qs = qs.filter(Q(task_id=filters['task_id']) | Q(task_id_snapshot=filters['task_id']))
    if filters.get('agent_name'):
        qs = qs.filter(agent_name=filters['agent_name'])
    if filters.get('status'):
        qs = qs.filter(status=filters['status'])
    date_from = parse_date(filters['date_from']) if filters.get('date_from') else None
    date_to = parse_date(filters['date_to']) if filters.get('date_to') else None
    if date_from:
        start = timezone.make_aware(datetime.combine(date_from, time.min), dt_timezone.utc)
        qs = qs.filter(created_at__gte=start)
    if date_to:
        end = timezone.make_aware(datetime.combine(date_to, time.max), dt_timezone.utc)
        qs = qs.filter(created_at__lte=end)
    return qs


def _filter_context(user, filters, project=None, task=None):
    grids = (
        Project.objects.filter(Q(user=user) | Q(team_toad_user=user))
        .distinct()
        .order_by('name')
    )
    agents = (
        _accessible_decision_qs(user)
        .exclude(agent_name='')
        .order_by('agent_name')
        .values_list('agent_name', flat=True)
        .distinct()
    )
    return {
        'project': project,
        'task': task,
        'grids': grids,
        'agents': agents,
        'status_choices': DecisionEntry.STATUS_CHOICES,
        'filters': {
            'grid': str(filters.get('grid_id') or ''),
            'agent': filters.get('agent_name') or '',
            'status': filters.get('status') or '',
            'date_from': filters.get('date_from') or '',
            'date_to': filters.get('date_to') or '',
        },
        'status_pending': DecisionEntry.STATUS_PENDING,
    }


def _list_context(request, grid_id=None, task_id=None, project=None, task=None):
    filters = _decision_filters(request, grid_id=grid_id, task_id=task_id)
    context = _filter_context(request.user, filters, project=project, task=task)
    context['entries'] = _filtered_entries(request.user, filters)
    context['verify_result'] = request.session.pop('decision_chain_result', None)
    return context


@login_required
def decision_log_view(request):
    _require_agent_access(request.user)
    return render(request, 'pages/grid/decision_log.html', _list_context(request))


@login_required
def grid_decision_log_view(request, pk):
    _require_agent_access(request.user)
    project = get_user_project_optimized(pk, request.user)
    return render(
        request,
        'pages/grid/decision_log.html',
        _list_context(request, grid_id=project.pk, project=project),
    )


@login_required
def task_decision_log_view(request, task_pk):
    _require_agent_access(request.user)
    task = get_user_task_optimized(task_pk, request.user, select_related=['project'])
    return render(
        request,
        'pages/grid/decision_log.html',
        _list_context(
            request,
            grid_id=task.project_id,
            task_id=task.pk,
            project=task.project,
            task=task,
        ),
    )


@login_required
@require_POST
def decision_review_view(request, decision_id):
    _require_agent_access(request.user)
    status = (request.POST.get('status') or '').strip()
    comment = (request.POST.get('comment') or '').strip()
    try:
        review_decision_for_user(request.user, decision_id, status, comment=comment)
    except ApiError as exc:
        if exc.status == 404:
            raise Http404
        messages.error(request, exc.message)
    else:
        messages.success(
            request,
            'Decision approved.' if status == DecisionEntry.STATUS_APPROVED else 'Decision rejected.',
        )
    return redirect(request.POST.get('next') or reverse('pages:decision_log'))


@login_required
def decision_log_export_view(request, pk=None, task_pk=None):
    _require_agent_access(request.user)
    project = None
    task = None
    grid_id = pk
    task_id = task_pk
    if pk is not None:
        project = get_user_project_optimized(pk, request.user)
        grid_id = project.pk
    if task_pk is not None:
        task = get_user_task_optimized(task_pk, request.user, select_related=['project'])
        grid_id = task.project_id
        task_id = task.pk
    filters = _decision_filters(request, grid_id=grid_id, task_id=task_id)
    entries = _filtered_entries(request.user, filters)
    response = HttpResponse(content_type='text/csv')
    filename = 'decision-log.csv'
    if task is not None:
        filename = f'decision-log-task-{task.pk}.csv'
    elif project is not None:
        filename = f'decision-log-grid-{project.pk}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow([
        'id',
        'created_at',
        'grid',
        'agent',
        'task',
        'requested_by',
        'request',
        'action_summary',
        'decision',
        'rationale',
        'sources',
        'output_link',
        'status',
        'reviewer',
        'reviewed_at',
        'review_comment',
        'entry_hash',
    ])
    for entry in entries:
        writer.writerow([
            entry.id,
            entry.created_at.isoformat(),
            entry.grid.name if entry.grid_id else '',
            entry.agent_name,
            entry.task_text_snapshot,
            entry.requested_by,
            entry.request,
            entry.action_summary,
            entry.decision,
            entry.rationale,
            ' '.join(entry.sources or []),
            entry.output_link,
            entry.status,
            entry.reviewer,
            entry.reviewed_at.isoformat() if entry.reviewed_at else '',
            entry.review_comment,
            entry.entry_hash,
        ])
    return response


@login_required
@require_http_methods(['GET', 'POST'])
def decision_log_verify_view(request, pk=None):
    _require_agent_access(request.user)
    grid_id = pk
    if pk is not None:
        project = get_user_project_optimized(pk, request.user)
        grid_id = project.pk
    request.session['decision_chain_result'] = verify_decision_chain(
        request.user, grid_id=grid_id
    )
    if pk is not None:
        return redirect('pages:grid_decision_log', pk=pk)
    return redirect('pages:decision_log')
