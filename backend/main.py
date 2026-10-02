import os
import sys
from pathlib import Path

# Ensure root directory containing 'backend' is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database import init_db, close_db
import backend.database as db_module
from backend.rag.embeddings import get_model

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Starting up backend service...")
    try:
        # Initialize Database connection
        await init_db()
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise e
        
    try:
        # Warm embedding model
        logger.info("Warming up embedding model...")
        get_model()
        logger.info("Embedding model warmed up.")
    except Exception as e:
        logger.error(f"Failed to warm up embedding model: {e}")
        
    yield
    
    # Shutdown actions
    logger.info("Shutting down backend service...")
    await close_db()

app = FastAPI(
    title="CollabAI API",
    description="Backend API for CollabAI Collaborative Workspace",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.routers import auth, workspaces, messages, websocket, documents, search, copilot, tasks

# Base API Router
api_router = APIRouter(prefix="/api")

@api_router.get("/health")
async def health_check():
    try:
        if db_module.db is not None:
            await db_module.db.command("ping")
            return {"status": "ok", "db": "connected"}
        else:
            return {"status": "error", "db": "disconnected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "error", "db": "failed", "detail": str(e)}

# Include routers
api_router.include_router(auth.router)
api_router.include_router(workspaces.router)
api_router.include_router(messages.router)
api_router.include_router(documents.router)
api_router.include_router(search.router)
api_router.include_router(copilot.router)
api_router.include_router(tasks.router)

app.include_router(api_router)
app.include_router(websocket.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
