import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# 👇 Call this first to initialize Django apps
django_asgi_app = get_asgi_application()

# 👇 Now import things that rely on Django being set up
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django_channels_jwt_auth_middleware.auth import JWTAuthMiddlewareStack
import chat.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        JWTAuthMiddlewareStack(
            URLRouter(chat.routing.websocket_urlpatterns)
        )
    ),
})
