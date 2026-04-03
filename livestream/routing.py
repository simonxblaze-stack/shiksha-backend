from django.urls import re_path
from .consumers import LiveSessionConsumer

websocket_urlpatterns = [
    re_path(
        r"ws/live-session/(?P<session_id>[^/]+)/$", LiveSessionConsumer.as_asgi()),
]
