import os

import httpx

TOAD_API_BASE_URL = os.environ.get('TOAD_API_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')


def _authorization_token(raw_token: str) -> str:
    token = (raw_token or '').strip()
    if token.lower().startswith('bearer '):
        return token[7:].strip()
    return token


async def toad_post(path: str, raw_token: str, payload: dict | None = None) -> dict:
    token = _authorization_token(raw_token)
    if not token:
        return {
            'error': 'Missing personal access token. Add it in Grok Bot when you connect this server.'
        }

    url = f'{TOAD_API_BASE_URL}/api/mcp/{path.lstrip("/")}'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload or {}, headers=headers)
    except httpx.RequestError as exc:
        return {'error': f'Could not reach Toad at {TOAD_API_BASE_URL}: {exc}'}

    try:
        data = response.json()
    except ValueError:
        return {'error': f'Toad returned a non-JSON response ({response.status_code})'}

    if response.is_error:
        if isinstance(data, dict) and data.get('error'):
            return {'error': data['error']}
        return {'error': f'Toad returned {response.status_code}'}
    return data
