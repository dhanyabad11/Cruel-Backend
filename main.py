from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.routes import auth_router as auth_routes
from app.routes import deadline_routes, notification_routes, whatsapp_routes, portal_routes, task_routes
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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )