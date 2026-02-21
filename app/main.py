from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="BRD Agent GenAI Engine",
    description="Backend API powering the BRD Generation Platform for HackFest 2026",
    version="1.0.0"
)

# CORS configuration to allow Next.js frontend to talk to us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Simple health check endpoint to verify backend is running."""
    return {"status": "healthy", "service": "BRD Agent LLM Engine"}

from app.api.routes import ingest, generate

# We will include routers here later
app.include_router(ingest.router, prefix="/api/v1/ingest", tags=["Ingestion"])
app.include_router(generate.router, prefix="/api/v1/generate", tags=["Generation"])

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting BRD Agent Backend Server...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
