
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.db_connect import AsyncSessionLocal
from api import community
from contextlib import asynccontextmanager
import config # Ensure .env is loaded
from database.db_connect import AsyncSessionLocal

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Starting Choyxona Community Micro-Service...")
    yield
    # Shutdown logic
    logger.info("Shutting down Choyxona Service...")

app = FastAPI(
    title="TalabaHamkor Community Service",
    version="1.0.0",
    docs_url=None, # Disable docs for prod speed if needed, or keep for debugging
    redoc_url=None,
    lifespan=lifespan
)

# CORS (Allow All for now, or match main bot settings)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
# Note: The prefix must match what Nginx forwards or app expects.
# Nginx location /api/v1/community -> proxy_pass http://localhost:8002/api/v1/community
# So we need to mount with prefix.

from api.dependencies import get_current_student # Just to ensure dependencies load
from api import community
from api import subscription  # [NEW] Import subscription router

app.include_router(community.router, prefix="/api/v1/community", tags=["Community"])
app.include_router(subscription.router, prefix="/api/v1/community", tags=["Subscription"]) # [NEW] Include subscription routes

@app.get("/")
async def root():
    return {"status": "active", "service": "TalabaHamkor Community Service", "version": "1.0.0"}

@app.get("/api/v1/community/health")
async def health_check_prefixed():
    return {"status": "ok", "service": "community"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
