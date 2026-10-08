"""Remote MCP server for Grok Bot.

Talks to Toad's token-authenticated API. Run next to Django:

    pip install -r mcp_server/requirements.txt
    TOAD_API_BASE_URL=http://127.0.0.1:8000 python mcp_server/server.py

Grok Bot connects with this server's public URL (path /mcp) plus the user's
personal access token from Toad settings.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

SERVER_DIR = Path(__file__).resolve().parent
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from toad_client import toad_post

MCP_HOST = os.environ.get('MCP_HOST', '0.0.0.0')
MCP_PORT = int(os.environ.get('MCP_PORT', '3001'))
MCP_PATH = os.environ.get('MCP_PATH', '/mcp')

mcp = FastMCP(
    name='Toad',
    instructions=(
        'Read and edit the signed-in user\'s Toad grids. '
        'Call list_grids to find grid IDs, then get_grid before adding or changing tasks. '
        'get_grid returns the grid brief, task owner, needs_review, and recent activity. '
        'Put lasting context in the brief with update_grid. '
        'Tasks you add are owned by the agent unless you set owner to you. '
        'Set needs_review true when handing drafted work back. '
        'Add, rename, reorder or delete rows and columns with add_row, rename_row, '
        'reorder_rows, delete_row, add_column, rename_column, reorder_columns and delete_column. '
        'Deleting a row or column also deletes the tasks in it. The category column cannot be deleted. '
        'Call log_request after helping someone, with who asked, what they asked, '
        'and whether a follow-up is needed. Do not store tool output in log_request.'
    ),
)


def current_token() -> str:
    headers = get_http_headers()
    auth = headers.get('authorization') or ''
    if auth.lower().startswith('bearer '):
        return auth[7:].strip()
    return auth.strip()


class RequireBearerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.method == 'OPTIONS' or request.url.path in {'/health', '/'}:
            return await call_next(request)
        if not request.headers.get('authorization', '').strip():
            return JSONResponse(
                {
                    'error': (
                        'Missing personal access token. '
                        'Connect with Authorization: Bearer <token> from Toad settings.'
                    )
                },
                status_code=401,
                headers={'WWW-Authenticate': 'Bearer'},
            )
        return await call_next(request)


@mcp.custom_route('/health', methods=['GET'])
async def health_check(request):
    return JSONResponse({'status': 'ok', 'service': 'toad-mcp'})


@mcp.tool
async def list_grids() -> dict:
    """Return the user's Toad grids with their IDs and names."""
    return await toad_post('list_grids', current_token())


@mcp.tool
async def get_grid(grid_id: int) -> dict:
    """Return a grid's brief, rows, columns and tasks, plus recent activity.

    Each task is tagged with its row, column, ticked state, note, owner
    (you or agent) and needs_review.
    """
    return await toad_post('get_grid', current_token(), {'grid_id': grid_id})


@mcp.tool
async def update_grid(grid_id: int, brief: str) -> dict:
    """Set the grid brief. Standing context other agents should see on get_grid."""
    return await toad_post('update_grid', current_token(), {'grid_id': grid_id, 'brief': brief})


@mcp.tool
async def add_task(
    grid_id: int,
    row_id: int,
    column_id: int,
    text: str,
    note: str | None = None,
    owner: str | None = None,
    needs_review: bool | None = None,
) -> dict:
    """Add a task to a grid cell (row and column). An optional note can be included.

    Defaults to owner=agent. Set needs_review true to hand it back for review.
    """
    payload = {
        'grid_id': grid_id,
        'row_id': row_id,
        'column_id': column_id,
        'text': text,
    }
    if note:
        payload['note'] = note
    if owner:
        payload['owner'] = owner
    if needs_review is not None:
        payload['needs_review'] = needs_review
    return await toad_post('add_task', current_token(), payload)


@mcp.tool
async def update_task(
    task_id: int,
    ticked: bool | None = None,
    text: str | None = None,
    row_id: int | None = None,
    column_id: int | None = None,
    owner: str | None = None,
    needs_review: bool | None = None,
) -> dict:
    """Tick, untick, rename, or move a task. Can also set owner and needs_review."""
    payload = {'task_id': task_id}
    if ticked is not None:
        payload['ticked'] = ticked
    if text is not None:
        payload['text'] = text
    if row_id is not None:
        payload['row_id'] = row_id
    if column_id is not None:
        payload['column_id'] = column_id
    if owner is not None:
        payload['owner'] = owner
    if needs_review is not None:
        payload['needs_review'] = needs_review
    return await toad_post('update_task', current_token(), payload)


@mcp.tool
async def delete_task(task_id: int) -> dict:
    """Remove a task from a grid."""
    return await toad_post('delete_task', current_token(), {'task_id': task_id})


@mcp.tool
async def add_row(grid_id: int, name: str, after_row_id: int | None = None) -> dict:
    """Add a row to a grid. Omit after_row_id to append at the bottom."""
    payload = {'grid_id': grid_id, 'name': name}
    if after_row_id is not None:
        payload['after_row_id'] = after_row_id
    return await toad_post('add_row', current_token(), payload)


@mcp.tool
async def add_column(grid_id: int, name: str, after_column_id: int | None = None) -> dict:
    """Add a data column. Omit after_column_id to append on the right. Category stays first."""
    payload = {'grid_id': grid_id, 'name': name}
    if after_column_id is not None:
        payload['after_column_id'] = after_column_id
    return await toad_post('add_column', current_token(), payload)


@mcp.tool
async def reorder_rows(grid_id: int, row_ids: list[int]) -> dict:
    """Set the top-to-bottom order of rows. Pass every row_id from get_grid exactly once."""
    return await toad_post('reorder_rows', current_token(), {'grid_id': grid_id, 'row_ids': row_ids})


@mcp.tool
async def reorder_columns(grid_id: int, column_ids: list[int]) -> dict:
    """Set data column order. Pass every data column_id; do not include the category column."""
    return await toad_post(
        'reorder_columns', current_token(), {'grid_id': grid_id, 'column_ids': column_ids}
    )


@mcp.tool
async def rename_row(row_id: int, name: str) -> dict:
    """Rename a row."""
    return await toad_post('rename_row', current_token(), {'row_id': row_id, 'name': name})


@mcp.tool
async def rename_column(column_id: int, name: str) -> dict:
    """Rename a column, including the category column."""
    return await toad_post(
        'rename_column', current_token(), {'column_id': column_id, 'name': name}
    )


@mcp.tool
async def delete_row(row_id: int) -> dict:
    """Delete a row and every task in it."""
    return await toad_post('delete_row', current_token(), {'row_id': row_id})


@mcp.tool
async def delete_column(column_id: int) -> dict:
    """Delete a data column and every task in it. The category column cannot be deleted."""
    return await toad_post('delete_column', current_token(), {'column_id': column_id})


@mcp.tool
async def log_request(
    what: str,
    asked_by: str | None = None,
    follow_up_needed: bool = False,
) -> dict:
    """Record who asked, what they asked, when, and whether a follow-up is needed.

    Do not include tool output or grid contents. Call this after helping someone.
    """
    payload = {'what': what, 'follow_up_needed': follow_up_needed}
    if asked_by:
        payload['asked_by'] = asked_by
    return await toad_post('log_request', current_token(), payload)


app = mcp.http_app(
    path=MCP_PATH,
    stateless_http=True,
    middleware=[Middleware(RequireBearerMiddleware)],
)


if __name__ == '__main__':
    import uvicorn

    print(f'Toad MCP server listening on http://{MCP_HOST}:{MCP_PORT}{MCP_PATH}')
    uvicorn.run(app, host=MCP_HOST, port=MCP_PORT)
