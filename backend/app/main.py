"""FastAPI main application."""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers import upload, chat, session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Insurance Document Assistant API",
    description="Multi-modal RAG-based insurance document Q&A system",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router)
app.include_router(chat.router)
app.include_router(session.router)


@app.get("/")
async def root():
    return {
        "message": "Insurance Document Assistant API",
        "docs": "/docs",
        "health": "/api/health",
    }


@app.on_event("startup")
async def startup_event():
    logger.info("Insurance Document Assistant API starting up...")
    logger.info(f"CORS allowed origins: {settings.frontend_url}")
    logger.info(f"ChromaDB persist dir: {settings.chroma_persist_dir}")
