from config.celery import app
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


@app.task(bind=True, max_retries=3, default_retry_delay=5)
def push_ws_notification_task(self, user_id, data):
    """
    Async Celery task to push WebSocket notification to a user.
    Retries up to 3 times if it fails.
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
    except Exception as exc:
        raise self.retry(exc=exc)
