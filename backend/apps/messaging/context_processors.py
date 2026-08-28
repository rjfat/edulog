from .models import Message


def unread_message_count(request):
    """Sidebar badge: how many unread messages are waiting for the user."""
    if not request.user.is_authenticated:
        return {'unread_message_count': 0}
    return {
        'unread_message_count': Message.objects.filter(
            receiver=request.user, read=False
        ).count(),
    }