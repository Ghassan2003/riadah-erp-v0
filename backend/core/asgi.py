"""
ASGI config for ERP System project.
Supports both HTTP (Django) and WebSocket (Channels) protocols.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter
from channels.auth import AuthMiddlewareStack
from channels.routing import URLRouter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Initialize Django ASGI application early to ensure AppRegistry is populated
# before importing other modules that may depend on ORM or AppConfig.
django_asgi_app = get_asgi_application()

# Import WebSocket routing after Django is initialized
from notifications.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    # HTTP requests are handled by Django's standard ASGI application.
    "http": django_asgi_app,

    # WebSocket requests are routed through Channels with auth middleware.
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
