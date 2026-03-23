from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

import chat.routing
import notification.routing
import presence.routing

application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat.routing.websocket_urlpatterns +
            notification.routing.websocket_urlpatterns +
            presence.routing.websocket_urlpatterns
        )
    ),
})