from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def push_ws_notification(user_id, data):
    """
    Push real-time notification to a user via WebSocket.
    Safe to call from anywhere — never breaks if WS fails.
    
    Usage:
        push_ws_notification(user.id, {
            'type': 'assignment',
            'title': 'New assignment posted',
            'id': str(assignment.id),
        })
    """
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        async_to_sync(channel_layer.group_send)(
            f'notifications_{user_id}',
            {
                'type': 'send_notification',
                'data': data
            }
        )
    except Exception:
        pass  # never break system if WebSocket fails