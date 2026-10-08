import json
from functools import wraps

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import PersonalAccessToken


def extract_bearer_token(request):
    auth = request.headers.get('Authorization') or request.META.get('HTTP_AUTHORIZATION', '')
    if auth.lower().startswith('bearer '):
        return auth[7:].strip()
    return auth.strip()


def parse_json_body(request):
    if not request.body:
        return {}
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError as exc:
        raise ValueError('Invalid JSON body') from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError('JSON body must be an object')
    return data


def mcp_token_required(view_func):
    """Authenticate API requests with a personal access token. CSRF-exempt."""

    @csrf_exempt
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if request.method == 'OPTIONS':
            return JsonResponse({'ok': True})
        raw_token = extract_bearer_token(request)
        if not raw_token:
            return JsonResponse({'error': 'Missing personal access token'}, status=401)
        token = PersonalAccessToken.authenticate_token(raw_token)
        if not token:
            return JsonResponse({'error': 'Invalid personal access token'}, status=401)
        request.user = token.user
        request.mcp_token = token
        return view_func(request, *args, **kwargs)

    return wrapped
