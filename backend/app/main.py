
import sys
import os

# Add project root to Python path for services imports
# This is needed for Docker container to find the services/ directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import routes
from app.routes import search, resume

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Real-Time Job Recommendation & Resume Intelligence System",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routes.router, prefix="/api/v1")
app.include_router(search.router)  # Search endpoints at /api/search
app.include_router(resume.router)  # Resume endpoints at /api/resume

@app.get("/")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok", "service": settings.PROJECT_NAME}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
