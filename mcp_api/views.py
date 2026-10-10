from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .auth import mcp_token_required, parse_json_body
from .services import (
    GET_DECISION_FIELDS,
    LIST_DECISIONS_FIELDS,
    ApiError,
    _reject_unknown_fields,
    add_column_for_user,
    add_row_for_user,
    add_task_for_user,
    create_grid_for_user,
    delete_column_for_user,
    delete_row_for_user,
    delete_task_for_user,
    get_decision_for_user,
    get_grid_for_user,
    list_decisions_for_user,
    list_grids_for_user,
    log_decision_for_user,
    log_request_for_user,
    rename_column_for_user,
    rename_row_for_user,
    reorder_columns_for_user,
    reorder_rows_for_user,
    update_grid_for_user,
    update_task_for_user,
)


def _json_error(message, status=400):
    return JsonResponse({'error': message}, status=status)


def _agent(request):
    token = getattr(request, 'mcp_token', None)
    return token.name if token else None


def _call(func, *args, **kwargs):
    try:
        result = func(*args, **kwargs)
    except ApiError as exc:
        return _json_error(exc.message, status=exc.status)
    status = 201 if kwargs.get('_created') else 200
    return JsonResponse(result, status=status)


@mcp_token_required
@require_http_methods(['GET', 'POST'])
def whoami(request):
    return JsonResponse({
        'id': request.user.id,
        'email': request.user.email,
        'name': request.user.get_full_name(),
        'agent': _agent(request),
    })


@mcp_token_required
@require_http_methods(['POST'])
def list_grids(request):
    return _call(list_grids_for_user, request.user)


@mcp_token_required
@require_http_methods(['POST'])
def create_grid(request):
    try:
        data = parse_json_body(request)
    except ValueError as exc:
        return _json_error(str(exc))
    try:
        result = create_grid_for_user(
            request.user,
            data.get('name'),
            brief=data.get('brief'),
            rows=data.get('rows'),
            columns=data.get('columns'),
            agent=_agent(request),
        )
    except ApiError as exc:
        return _json_error(exc.message, status=exc.status)
    return JsonResponse(result, status=201)


@mcp_token_required
@require_http_methods(['POST'])
def get_grid(request):
    try:
        data = parse_json_body(request)
    except ValueError as exc:
        return _json_error(str(exc))
    return _call(get_grid_for_user, request.user, data.get('grid_id'))


@mcp_token_required
@require_http_methods(['POST'])
def update_grid(request):
    try:
        data = parse_json_body(request)
    except ValueError as exc:
        return _json_error(str(exc))
    return _call(
        update_grid_for_user,
        request.user,
        data.get('grid_id'),
        brief=data.get('brief'),
        agent=_agent(request),
    )


@mcp_token_required
@require_http_methods(['POST'])
def add_task(request):
    try:
        data = parse_json_body(request)
    except ValueError as exc:
        return _json_error(str(exc))
    try:
        result = add_task_for_user(
            request.user,
            data.get('grid_id'),
            data.get('row_id'),
            data.get('column_id'),
            data.get('text'),
            note=data.get('note'),
            owner=data.get('owner'),
            needs_review=data.get('needs_review'),
            agent=_agent(request),
        )
    except ApiError as exc:
        return _json_error(exc.message, status=exc.status)
    return JsonResponse(result, status=201)


@mcp_token_required
@require_http_methods(['POST'])
def update_task(request):
    try:
        data = parse_json_body(request)
    except ValueError as exc:
        return _json_error(str(exc))
    return _call(
        update_task_for_user,
        request.user,
        data.get('task_id'),
        data=data,
        agent=_agent(request),
    )


@mcp_token_required
@require_http_methods(['POST'])
def delete_task(request):
    try:
        data = parse_json_body(request)
    except ValueError as exc:
        return _json_error(str(exc))
    return _call(delete_task_for_user, request.user, data.get('task_id'), agent=_agent(request))


@mcp_token_required
@require_http_methods(['POST'])
def add_row(request):
    try:
        data = parse_json_body(request)
    except ValueError as exc:
        return _json_error(str(exc))
    try:
        result = add_row_for_user(
            request.user,
            data.get('grid_id'),
            data.get('name'),
            after_row_id=data.get('after_row_id'),
            agent=_agent(request),
        )
    except ApiError as exc:
        return _json_error(exc.message, status=exc.status)
    return JsonResponse(result, status=201)


@mcp_token_required
@require_http_methods(['POST'])
def add_column(request):
    try:
        data = parse_json_body(request)
    except ValueError as exc:
        return _json_error(str(exc))
    try:
        result = add_column_for_user(
            request.user,
            data.get('grid_id'),
            data.get('name'),
            after_column_id=data.get('after_column_id'),
            agent=_agent(request),
        )
    except ApiError as exc:
        return _json_error(exc.message, status=exc.status)
    return JsonResponse(result, status=201)


@mcp_token_required
@require_http_methods(['POST'])
def reorder_rows(request):
    try:
        data = parse_json_body(request)
    except ValueError as exc:
        return _json_error(str(exc))
    return _call(
        reorder_rows_for_user,
        request.user,
        data.get('grid_id'),
        data.get('row_ids'),
        agent=_agent(request),
    )


@mcp_token_required
@require_http_methods(['POST'])
def reorder_columns(request):
    try:
        data = parse_json_body(request)
    except ValueError as exc:
        return _json_error(str(exc))
    return _call(
        reorder_columns_for_user,
        request.user,
        data.get('grid_id'),
        data.get('column_ids'),
        agent=_agent(request),
    )


@mcp_token_required
@require_http_methods(['POST'])
def rename_row(request):
    try:
        data = parse_json_body(request)
    except ValueError as exc:
        return _json_error(str(exc))
    return _call(
        rename_row_for_user,
        request.user,
        data.get('row_id'),
        data.get('name'),
        agent=_agent(request),
    )


@mcp_token_required
@require_http_methods(['POST'])
def rename_column(request):
    try:
        data = parse_json_body(request)
    except ValueError as exc:
        return _json_error(str(exc))
    return _call(
        rename_column_for_user,
        request.user,
        data.get('column_id'),
        data.get('name'),
        agent=_agent(request),
    )


@mcp_token_required
@require_http_methods(['POST'])
def delete_row(request):
    try:
        data = parse_json_body(request)
    except ValueError as exc:
        return _json_error(str(exc))
    return _call(delete_row_for_user, request.user, data.get('row_id'), agent=_agent(request))


@mcp_token_required
@require_http_methods(['POST'])
def delete_column(request):
    try:
        data = parse_json_body(request)
    except ValueError as exc:
        return _json_error(str(exc))
    return _call(
        delete_column_for_user, request.user, data.get('column_id'), agent=_agent(request)
    )


@mcp_token_required
@require_http_methods(['POST'])
def log_request(request):
    try:
        data = parse_json_body(request)
    except ValueError as exc:
        return _json_error(str(exc))
    return _call(
        log_request_for_user,
        request.user,
        data.get('what') or data.get('request'),
        asked_by=data.get('asked_by'),
        follow_up_needed=data.get('follow_up_needed', False),
    )


@mcp_token_required
@require_http_methods(['POST'])
def log_decision(request):
    try:
        data = parse_json_body(request)
    except ValueError as exc:
        return _json_error(str(exc))
    try:
        result = log_decision_for_user(
            request.user,
            data,
            agent=_agent(request),
            token=getattr(request, 'mcp_token', None),
        )
    except ApiError as exc:
        return _json_error(exc.message, status=exc.status)
    return JsonResponse(result, status=201)


@mcp_token_required
@require_http_methods(['POST'])
def list_decisions(request):
    try:
        data = parse_json_body(request)
    except ValueError as exc:
        return _json_error(str(exc))
    try:
        _reject_unknown_fields(data, LIST_DECISIONS_FIELDS)
        result = list_decisions_for_user(
            request.user,
            grid_id=data.get('grid_id'),
            task_id=data.get('task_id'),
            status=data.get('status'),
            agent_name=data.get('agent_name'),
            since=data.get('since'),
            limit=data.get('limit'),
        )
    except ApiError as exc:
        return _json_error(exc.message, status=exc.status)
    return JsonResponse(result)


@mcp_token_required
@require_http_methods(['POST'])
def get_decision(request):
    try:
        data = parse_json_body(request)
    except ValueError as exc:
        return _json_error(str(exc))
    try:
        _reject_unknown_fields(data, GET_DECISION_FIELDS)
        result = get_decision_for_user(request.user, data.get('decision_id'))
    except ApiError as exc:
        return _json_error(exc.message, status=exc.status)
    return JsonResponse(result)
