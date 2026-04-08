from accounts.routing import websocket_urlpatterns as accounts_ws
from forum.routing import websocket_urlpatterns as forum_ws
import sessions_app.routing
import livestream.routing
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


django_asgi_app = get_asgi_application()


application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            livestream.routing.websocket_urlpatterns
            + sessions_app.routing.websocket_urlpatterns
            + forum_ws
            + accounts_ws
        )
    ),
})
