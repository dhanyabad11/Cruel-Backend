from .auth_routes import router as auth_router
from .deadline_routes import router as deadline_router
from .portal_routes import router as portal_router
from .notification_routes import router as notification_router

__all__ = [
    "auth_router",
    "deadline_router", 
    "portal_router",
    "notification_router"
]