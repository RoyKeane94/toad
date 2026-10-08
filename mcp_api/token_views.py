from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from .models import PersonalAccessToken


@login_required
@require_POST
def generate_mcp_token_view(request):
    raw_token = PersonalAccessToken.issue_for_user(request.user)
    request.session['new_mcp_token'] = raw_token
    messages.success(
        request,
        'Your Grok Bot access token is ready. Copy it now — it will not be shown again.',
    )
    return redirect('accounts:account_settings')


@login_required
@require_POST
def revoke_mcp_token_view(request):
    deleted, _ = PersonalAccessToken.objects.filter(user=request.user).delete()
    request.session.pop('new_mcp_token', None)
    if deleted:
        messages.success(request, 'Your Grok Bot access token has been revoked.')
    else:
        messages.info(request, 'You do not have a Grok Bot access token.')
    return redirect('accounts:account_settings')
