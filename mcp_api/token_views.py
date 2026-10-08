from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from .models import PersonalAccessToken


@login_required
@require_POST
def generate_mcp_token_view(request):
    name = (request.POST.get('name') or '').strip() or 'Grok Bot'
    raw_token = PersonalAccessToken.issue_for_user(request.user, name=name)
    request.session['new_mcp_token'] = raw_token
    request.session['new_mcp_token_name'] = name
    messages.success(
        request,
        f'Token for {name} is ready. Copy it now — it will not be shown again.',
    )
    return redirect('accounts:account_settings')


@login_required
@require_POST
def revoke_mcp_token_view(request, token_id):
    token = get_object_or_404(PersonalAccessToken, pk=token_id, user=request.user)
    name = token.name
    token.delete()
    if request.session.get('new_mcp_token_name') == name:
        request.session.pop('new_mcp_token', None)
        request.session.pop('new_mcp_token_name', None)
    messages.success(request, f'The {name} token has been revoked.')
    return redirect('accounts:account_settings')
