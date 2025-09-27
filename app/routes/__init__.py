# SUPABASE-ONLY IMPORTS 🚀
# Only importing working routes that have been converted to Supabase
from .auth_routes_supabase import router as auth_router

# TODO: Convert these routes to Supabase:
# from .deadline_routes import router as deadline_router
# from .portal_routes import router as portal_router  
# from .notification_routes import router as notification_router
# from .task_routes import router as task_router

__all__ = [
    "auth_router",
]