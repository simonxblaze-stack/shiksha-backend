import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

django_asgi_app = get_asgi_application()

import livestream.routing
import sessions_app.routing
from forum.routing import websocket_urlpatterns as forum_ws
from accounts.routing import websocket_urlpatterns as accounts_ws

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                livestream.routing.websocket_urlpatterns
                + sessions_app.routing.websocket_urlpatterns
                + forum_ws
                + accounts_ws
            )
        )
    ),
})