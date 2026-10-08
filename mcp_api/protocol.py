import json

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .auth import extract_bearer_token
from .models import PersonalAccessToken
from .services import ApiError, call_tool

MCP_INSTRUCTIONS = (
    "Read and edit the signed-in user's Toad grids. "
    "Call list_grids to find grid IDs, then get_grid before adding or changing tasks. "
    "get_grid returns the grid brief (standing context), task owner (you or agent), "
    "needs_review, and recent activity. Put lasting context in the brief with update_grid. "
    "Tasks you add are owned by the agent unless you set owner to you. "
    "Set needs_review true when handing drafted work back. "
    "Add, rename, reorder or delete rows and columns with add_row, rename_row, "
    "reorder_rows, delete_row, add_column, rename_column, reorder_columns and delete_column. "
    "Deleting a row or column also deletes the tasks in it. The category column cannot be deleted. "
    "Call log_request after helping someone, with who asked, what they asked, "
    "and whether a follow-up is needed. Do not store tool output in log_request."
)

TOOL_DEFINITIONS = [
    {
        'name': 'list_grids',
        'description': "Return the user's Toad grids with their IDs and names.",
        'inputSchema': {'type': 'object', 'properties': {}},
    },
    {
        'name': 'get_grid',
        'description': (
            "Return a grid's brief, rows, columns and tasks, plus recent activity. "
            "Each task is tagged with its row, column, ticked state, note, owner "
            "(you or agent) and needs_review."
        ),
        'inputSchema': {
            'type': 'object',
            'properties': {'grid_id': {'type': 'integer'}},
            'required': ['grid_id'],
        },
    },
    {
        'name': 'update_grid',
        'description': (
            "Set the grid brief. This is standing context other agents should see "
            "on get_grid (specs, positioning, constraints)."
        ),
        'inputSchema': {
            'type': 'object',
            'properties': {
                'grid_id': {'type': 'integer'},
                'brief': {'type': 'string'},
            },
            'required': ['grid_id', 'brief'],
        },
    },
    {
        'name': 'add_task',
        'description': (
            'Add a task to a grid cell (row and column). An optional note can be included. '
            'Defaults to owner=agent. Set needs_review true to hand it back for review.'
        ),
        'inputSchema': {
            'type': 'object',
            'properties': {
                'grid_id': {'type': 'integer'},
                'row_id': {'type': 'integer'},
                'column_id': {'type': 'integer'},
                'text': {'type': 'string'},
                'note': {'type': 'string'},
                'owner': {'type': 'string', 'enum': ['you', 'agent']},
                'needs_review': {'type': 'boolean'},
            },
            'required': ['grid_id', 'row_id', 'column_id', 'text'],
        },
    },
    {
        'name': 'update_task',
        'description': (
            'Tick, untick, rename, or move a task to another row or column. '
            'Can also set owner (you or agent) and needs_review.'
        ),
        'inputSchema': {
            'type': 'object',
            'properties': {
                'task_id': {'type': 'integer'},
                'ticked': {'type': 'boolean'},
                'text': {'type': 'string'},
                'row_id': {'type': 'integer'},
                'column_id': {'type': 'integer'},
                'owner': {'type': 'string', 'enum': ['you', 'agent']},
                'needs_review': {'type': 'boolean'},
            },
            'required': ['task_id'],
        },
    },
    {
        'name': 'delete_task',
        'description': 'Remove a task from a grid.',
        'inputSchema': {
            'type': 'object',
            'properties': {'task_id': {'type': 'integer'}},
            'required': ['task_id'],
        },
    },
    {
        'name': 'add_row',
        'description': (
            'Add a row to a grid. Omit after_row_id to append at the bottom. '
            'Pass after_row_id to insert below that row.'
        ),
        'inputSchema': {
            'type': 'object',
            'properties': {
                'grid_id': {'type': 'integer'},
                'name': {'type': 'string'},
                'after_row_id': {'type': 'integer'},
            },
            'required': ['grid_id', 'name'],
        },
    },
    {
        'name': 'add_column',
        'description': (
            'Add a data column to a grid. Omit after_column_id to append on the right. '
            'Pass after_column_id to insert to the right of that column. '
            'The category column stays first.'
        ),
        'inputSchema': {
            'type': 'object',
            'properties': {
                'grid_id': {'type': 'integer'},
                'name': {'type': 'string'},
                'after_column_id': {'type': 'integer'},
            },
            'required': ['grid_id', 'name'],
        },
    },
    {
        'name': 'reorder_rows',
        'description': (
            'Set the top-to-bottom order of rows. Pass every row_id from get_grid exactly once.'
        ),
        'inputSchema': {
            'type': 'object',
            'properties': {
                'grid_id': {'type': 'integer'},
                'row_ids': {'type': 'array', 'items': {'type': 'integer'}},
            },
            'required': ['grid_id', 'row_ids'],
        },
    },
    {
        'name': 'reorder_columns',
        'description': (
            'Set the left-to-right order of data columns. Pass every data column_id from get_grid '
            'exactly once. Do not include the category column; it stays first.'
        ),
        'inputSchema': {
            'type': 'object',
            'properties': {
                'grid_id': {'type': 'integer'},
                'column_ids': {'type': 'array', 'items': {'type': 'integer'}},
            },
            'required': ['grid_id', 'column_ids'],
        },
    },
    {
        'name': 'rename_row',
        'description': 'Rename a row.',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'row_id': {'type': 'integer'},
                'name': {'type': 'string'},
            },
            'required': ['row_id', 'name'],
        },
    },
    {
        'name': 'rename_column',
        'description': 'Rename a column, including the category column.',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'column_id': {'type': 'integer'},
                'name': {'type': 'string'},
            },
            'required': ['column_id', 'name'],
        },
    },
    {
        'name': 'delete_row',
        'description': 'Delete a row and every task in it.',
        'inputSchema': {
            'type': 'object',
            'properties': {'row_id': {'type': 'integer'}},
            'required': ['row_id'],
        },
    },
    {
        'name': 'delete_column',
        'description': (
            'Delete a data column and every task in it. The category column cannot be deleted.'
        ),
        'inputSchema': {
            'type': 'object',
            'properties': {'column_id': {'type': 'integer'}},
            'required': ['column_id'],
        },
    },
    {
        'name': 'log_request',
        'description': (
            'Record who asked, what they asked, when, and whether a follow-up is needed. '
            'Do not include tool output or grid contents. Call this after helping someone.'
        ),
        'inputSchema': {
            'type': 'object',
            'properties': {
                'what': {'type': 'string'},
                'asked_by': {'type': 'string'},
                'follow_up_needed': {'type': 'boolean', 'default': False},
            },
            'required': ['what'],
        },
    },
]


def _cors(response):
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'GET, POST, DELETE, OPTIONS'
    response['Access-Control-Allow-Headers'] = (
        'Authorization, Content-Type, Accept, MCP-Protocol-Version, Mcp-Session-Id'
    )
    response['Access-Control-Expose-Headers'] = 'Mcp-Session-Id, MCP-Protocol-Version'
    return response


def _jsonrpc_result(request_id, result):
    return _cors(JsonResponse({
        'jsonrpc': '2.0',
        'id': request_id,
        'result': result,
    }))


def _jsonrpc_error(request_id, code, message, status=400):
    return _cors(JsonResponse(
        {
            'jsonrpc': '2.0',
            'id': request_id,
            'error': {'code': code, 'message': message},
        },
        status=status,
    ))


def _info_payload():
    return {
        'name': 'Toad',
        'status': 'ok',
        'transport': 'streamable-http',
        'message': (
            'This is the Toad MCP endpoint. Connect Grok Bot with this URL '
            'and a personal access token from Account Settings.'
        ),
        'tools': [tool['name'] for tool in TOOL_DEFINITIONS],
    }


def _html_info():
    tools = ''.join(f'<li><code>{tool["name"]}</code> — {tool["description"]}</li>' for tool in TOOL_DEFINITIONS)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Toad MCP</title>
  <style>
    body {{ font-family: ui-sans-serif, system-ui, sans-serif; background: #f7faf9; color: #1f2933; margin: 0; }}
    main {{ max-width: 40rem; margin: 4rem auto; background: #fff; padding: 2rem; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
    h1 {{ margin: 0 0 .5rem; font-size: 1.5rem; }}
    p, li {{ color: #52606d; line-height: 1.5; }}
    code {{ background: #f0f4f2; padding: .1rem .35rem; border-radius: 4px; }}
  </style>
</head>
<body>
  <main>
    <h1>Toad MCP is running</h1>
    <p>This URL is for Grok Bot, not the Toad website. Add it as a custom MCP server with your personal access token from Account Settings.</p>
    <ul>{tools}</ul>
  </main>
</body>
</html>'''


def _handle_rpc(user, message, agent=None):
    if not isinstance(message, dict):
        return _jsonrpc_error(None, -32600, 'Invalid Request')

    method = message.get('method')
    request_id = message.get('id')
    params = message.get('params') or {}

    if method == 'initialize':
        protocol = (params.get('protocolVersion') or '2025-03-26')
        return _jsonrpc_result(request_id, {
            'protocolVersion': protocol,
            'capabilities': {'tools': {'listChanged': False}},
            'serverInfo': {'name': 'Toad', 'version': '1.0'},
            'instructions': MCP_INSTRUCTIONS,
        })

    if method in {'notifications/initialized', 'notifications/cancelled'}:
        return _cors(HttpResponse(status=202))

    if method == 'ping':
        return _jsonrpc_result(request_id, {})

    if method == 'tools/list':
        return _jsonrpc_result(request_id, {'tools': TOOL_DEFINITIONS})

    if method == 'tools/call':
        if user is None:
            return _jsonrpc_error(request_id, -32001, 'Invalid personal access token', status=401)
        name = params.get('name')
        arguments = params.get('arguments') or {}
        try:
            result = call_tool(user, name, arguments, agent=agent)
            is_error = isinstance(result, dict) and 'error' in result
        except ApiError as exc:
            result = {'error': exc.message}
            is_error = True
        return _jsonrpc_result(request_id, {
            'content': [{'type': 'text', 'text': json.dumps(result)}],
            'structuredContent': result,
            'isError': is_error,
        })

    if request_id is None:
        return _cors(HttpResponse(status=202))
    return _jsonrpc_error(request_id, -32601, f'Method not found: {method}')


@csrf_exempt
@require_http_methods(['GET', 'POST', 'DELETE', 'OPTIONS'])
def mcp_endpoint(request):
    if request.method == 'OPTIONS':
        return _cors(HttpResponse(status=204))

    if request.method == 'DELETE':
        return _cors(HttpResponse(status=204))

    if request.method == 'GET':
        accept = request.headers.get('Accept', '')
        if 'text/html' in accept and 'application/json' not in accept:
            return _cors(HttpResponse(_html_info(), content_type='text/html'))
        return _cors(JsonResponse(_info_payload()))

    raw_token = extract_bearer_token(request)
    token = PersonalAccessToken.authenticate_token(raw_token) if raw_token else None

    try:
        message = json.loads(request.body or b'{}')
    except json.JSONDecodeError:
        return _jsonrpc_error(None, -32700, 'Parse error')

    if token is None:
        request_id = message.get('id') if isinstance(message, dict) else None
        return _jsonrpc_error(
            request_id,
            -32001,
            'Missing or invalid personal access token',
            status=401,
        )

    return _handle_rpc(token.user, message, agent=token.name)
