import asyncio
import os
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
import time
import uvicorn

from pipeline.ingestion import ingest_document
from pipeline.generator import generate_brd_section, generate_full_brd
from pipeline.conflict import detect_brd_conflicts
from pipeline.traceability import generate_traceability_matrix
from cache.redis_cache import redis_cache
import pipeline.rag_engine as rag_mod

app = FastAPI(
    title="Advanced BRD Generation Agent - Hackfest 2.0",
    description="Sophisticated RAG Engine featuring HyDE, RAPTOR, CRAG, and DeepMind Prompt Repetition.",
    version="1.0.0"
)

# CORS configuration for the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://brd-agent-cmka.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    print(f"[{request.method}] {request.url.path} completed in {process_time:.4f} seconds")
    return response

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

@app.get("/conflicts")
async def retrieve_conflicts_get():
    """
    REST Endpoint: Generates an analytics report spotting structural conflicts
    between uploaded datasources using RRF mapping.
    """
    report = await detect_brd_conflicts("Identify any structural conflicts or contradictory requirements in the uploaded documents.")
    return report

@app.get("/traceability")
async def get_traceability():
    """
    REST Endpoint: Generates a traceability matrix mapping requirements to sources.
    """
    matrix = await generate_traceability_matrix()
    return matrix

@app.get("/health")
async def health_check():
    """Verify system is up before demo."""
    return {"status": "healthy", "gpu": "RTX 4090", "vram_used": "Managed by vLLM"}

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
            
        import json
        
        # Send termination completion payload map for UI status toggle
        await websocket.send_text(json.dumps({"type": "complete", "message": "BRD generation complete"}))
        
        # Send original termination sequence
        await websocket.send_text("[DONE]")
        
    except WebSocketDisconnect:
        print(f"WebSocket client disconnected for {section_name}")
    except Exception as e:
        import traceback
        print(f"WebSocket Exception in {section_name}: {e}")
        traceback.print_exc()
        try:
            await websocket.send_text(f"[ERROR]: {str(e)}")
        except RuntimeError:
            pass
    finally:
        try:
            await websocket.close()
        except RuntimeError:
            pass  # Already closed

from pydantic import BaseModel
from fastapi.responses import StreamingResponse

class EmailPayload(BaseModel):
    text: str

@app.post("/ingest/email")
async def ingest_email(payload: EmailPayload):
    content = payload.text.encode("utf-8")
    
    sender = "unknown_sender"
    subject = "unknown_subject"
    for line in payload.text.split('\n'):
        if line.startswith("From:"):
            sender = line.split("From:", 1)[1].strip()
        elif line.startswith("Subject:"):
            subject = line.split("Subject:", 1)[1].strip()
            
    doc_id = f"{sender}_{subject[:30]}".replace(' ', '_').replace('@', '_')
    source_name = f"{sender} — {subject}"
    
    metadata = {"filename": source_name, "content_type": "message/rfc822", "doc_id": doc_id}
    result = await ingest_document(content, metadata)
    return {"status": "success", "details": result}

@app.get("/ingest/status")
async def get_ingest_status():
    return {"status": "completed", "docs_processed": 1}

class EditRequest(BaseModel):
    section: str
    query: str
    current_content: str

@app.post("/api/generate/edit")
async def edit_section_endpoint(request: EditRequest):
    result = await generate_section_edit(
        section=request.section,
        query=request.query,
        current_content=request.current_content
    )
    return {"content": result}

class SectionPayload(BaseModel):
    section: str

@app.post("/generate/section")
async def generate_section(payload: SectionPayload):
    query_text = payload.section.replace("_", " ")
    return StreamingResponse(generate_brd_section(payload.section, query_text), media_type="text/plain")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
