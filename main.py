import asyncio
import os
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from pipeline.ingestion import ingest_document
from pipeline.generator import generate_brd_section, generate_full_brd
from pipeline.conflict import detect_brd_conflicts
from cache.redis_cache import redis_cache
import pipeline.rag_engine as rag_mod

app = FastAPI(
    title="Advanced BRD Generation Agent - Hackfest 2.0",
    description="Sophisticated RAG Engine featuring HyDE, RAPTOR, CRAG, and DeepMind Prompt Repetition.",
    version="1.0.0"
)

# CORS configuration for the Next.js frontend running on localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """
    On startup, the singleton models (Whisper, BGE-M3, BGE-Reranker) have already 
    been loaded directly through their import files synchronously.
    However, LightRAG requires an async init.
    """
    print("FastAPI Backend Starting...")
    rag_mod.rag_instance = await rag_mod.initialize_lightrag()
    print("All Models & Databases Loaded Successfully.")

@app.post("/api/ingest")
async def upload_document(file: UploadFile = File(...)):
    """
    REST Endpoint: Upload a PDF, CSV, EML, or JSON file.
    Triggers: MinerU -> Semantic Chunking -> HyPE -> RAPTOR -> Caches.
    """
    try:
        content = await file.read()
        metadata = {"filename": file.filename, "content_type": file.content_type}
        
        # Dispatch the heavy advanced RAG pipeline
        result = await ingest_document(content, metadata)
        return {"filename": file.filename, "status": "success", "details": result}
    except Exception as e:
        return {"filename": file.filename, "status": "error", "reason": str(e)}

@app.post("/api/conflicts")
async def retrieve_conflicts(query: str):
    """
    REST Endpoint: Generates an analytics report spotting structural conflicts
    between uploaded datasources using RRF mapping.
    """
    report = await detect_brd_conflicts(query)
    return report

@app.get("/cache/stats")
async def cache_stats():
    """Monitor Upstash Free Tier Budget."""
    info = redis_cache.redis.info()
    return {
        "used_memory_mb": round(info.get("used_memory", 0) / 1024 / 1024, 2),
        "total_keys": redis_cache.redis.dbsize(),
        "budget_used_percent": round(
            info.get("used_memory", 0) / (256 * 1024 * 1024) * 100, 1
        ),
        "region": "Mumbai",
        "ttl_policy": "2hr semantic, 24hr BM25, 1hr session"
    }

@app.websocket("/api/generate/stream/{section_name}")
async def generate_section_stream(websocket: WebSocket, section_name: str):
    """
    WebSocket Endpoint: Stream generated BRD section directly to the UI.
    Utilizes: CRAG, A-RAG, HyDE, Prompt Repetition.
    """
    await websocket.accept()
    query = ""
    try:
        # Client sends the contextual query/guidance first
        query = await websocket.receive_text()
        print(f"WS requested {section_name} with query: {query}")
        
        # Async stream tokens immediately from vLLM as they arrive
        async for token in generate_brd_section(section_name, query):
            await websocket.send_text(token)
            
        # Send termination sequence
        await websocket.send_text("[DONE]")
        
    except WebSocketDisconnect:
        print(f"WebSocket client disconnected for {section_name}")
    except Exception as e:
        await websocket.send_text(f"[ERROR]: {str(e)}")
    finally:
        try:
            await websocket.close()
        except RuntimeError:
            pass  # Already closed

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
