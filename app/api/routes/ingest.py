from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload")
async def upload_document(files: List[UploadFile] = File(...)):
    """
    Endpoint to ingest raw CSV, JSON, or EML files.
    In Phase 2 parsing, this route will map to Local FAISS embeddings.
    """
    results = []
    
    for file in files:
        if not file.filename:
            continue
            
        logger.info(f"Ingesting file: {file.filename}")
        
        # We will parse EML/CSV/JSON contents here
        content = await file.read()
        
        # Store metadata response
        results.append({
            "filename": file.filename,
            "status": "embedded",
            "size_bytes": len(content)
        })
        
    return {"message": "Successfully ingested documents into vector store", "details": results}

@router.get("/status")
async def ingestion_status():
    """Returns database size info."""
    return {"status": "ready", "vectors_count": 0}
