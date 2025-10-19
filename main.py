from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.routes import auth_router as auth_routes
from app.routes import deadline_routes, notification_routes, whatsapp_routes, portal_routes, task_routes, notification_settings_routes
from app.config import settings
from app.services.notification_service import initialize_notification_service
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI instance
app = FastAPI(
    title="AI Cruel - Deadline Manager",
    description="A production-level deadline management system with portal scraping and smart notifications",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - Production-level configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Initialize notification service
try:
    notification_service = initialize_notification_service()
    if notification_service.validate_config():
        logger.info("Twilio notification service initialized successfully")
    else:
        logger.warning("Twilio configuration invalid - notifications will not work")
except Exception as e:
    logger.warning(f"Failed to initialize notification service: {e}")

# Include routers
app.include_router(auth_routes, prefix="/api/auth", tags=["authentication"])
app.include_router(deadline_routes.router, prefix="/api/deadlines", tags=["deadlines"])
app.include_router(notification_routes.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(notification_settings_routes.router, tags=["notification-settings"])
app.include_router(whatsapp_routes.router, tags=["whatsapp"])
app.include_router(portal_routes.router, prefix="/api/portals", tags=["portals"])
app.include_router(task_routes.router, prefix="/api", tags=["tasks"])

@app.get("/")
async def root():
    return {"message": "AI Cruel - Deadline Manager API", "version": "1.0.0"}

@app.get("/test")
async def serve_test_page():
    return FileResponse("whatsapp_test.html")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai-cruel-backend"}

@app.get("/debug/config")
async def debug_config():
    """Debug endpoint to check environment variables"""
    import os
    return {
        "redis_url_from_settings": settings.REDIS_URL[:50] + "..." if len(settings.REDIS_URL) > 50 else settings.REDIS_URL,
        "redis_url_from_env": os.getenv("REDIS_URL", "NOT SET")[:50] + "..." if os.getenv("REDIS_URL") else "NOT SET",
        "env_vars_loaded": "REDIS_URL" in os.environ
    }

@app.get("/debug/celery")
async def debug_celery():
    """Test if Celery is working"""
    try:
        from app.celery_app import celery_app
        # Try to inspect Celery
        inspect = celery_app.control.inspect()
        active = inspect.active()
        registered = inspect.registered()
        stats = inspect.stats()
        
        return {
            "celery_configured": True,
            "broker_url": celery_app.conf.broker_url[:50] + "..." if celery_app.conf.broker_url else "NOT SET",
            "workers_active": active is not None,
            "registered_tasks": len(registered.get(list(registered.keys())[0], [])) if registered and registered.keys() else 0,
            "workers_online": list(stats.keys()) if stats else []
        }
    except Exception as e:
        return {
            "celery_configured": False,
            "error": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )