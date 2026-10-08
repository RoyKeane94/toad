from django.conf import settings


def mcp_server_public_url(request):
    """URL shown in settings and used to connect Grok Bot.

    Prefer MCP_SERVER_PUBLIC_URL. Otherwise use localhost in development
    and the current public host in production.
    """
    configured = (getattr(settings, 'MCP_SERVER_PUBLIC_URL', '') or '').strip()
    if configured:
        return configured.rstrip('/')
    if settings.DEBUG:
        return 'http://localhost:3001/mcp'
    return f'https://{request.get_host()}/mcp'
