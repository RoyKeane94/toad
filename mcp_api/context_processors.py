from .models import user_has_agent_access


def agent_access(request):
    user = getattr(request, 'user', None)
    return {
        'user_has_agent_access': bool(
            user is not None
            and getattr(user, 'is_authenticated', False)
            and user_has_agent_access(user)
        )
    }
