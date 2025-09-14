from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth_routes, deadline_routes, portal_routes
from app.config import settings
import uvicorn

# Create FastAPI instance
app = FastAPI(
    title="AI Cruel - Deadline Manager",
    description="A production-level deadline management system with portal scraping and smart notifications",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_routes.router, prefix="/api/auth", tags=["authentication"])
app.include_router(deadline_routes.router, prefix="/api/deadlines", tags=["deadlines"])
app.include_router(portal_routes.router, prefix="/api/portals", tags=["portals"])

@app.get("/")
async def root():
    return {"message": "AI Cruel - Deadline Manager API", "version": "1.0.0"}

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