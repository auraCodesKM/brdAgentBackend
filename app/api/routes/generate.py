from fastapi import APIRouter, HTTPException
from app.models.schemas import GenerateRequest, GenerateResponse
import logging
import asyncio

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=GenerateResponse)
async def generate_brd_section(request: GenerateRequest):
    """
    Endpoint to accept a RAG prompt and generate the BRD markdown text.
    In Phase 2, this will hit FAISS local database and stream the Ollama/Langchain output.
    """
    logger.info(f"Received generation query: {request.query}")
    
    # Mocking latency for LLM inference
    await asyncio.sleep(1.5)
    
    # Placeholder Response
    return GenerateResponse(
        text=f"## Generated Response\n\nThis is a placeholder for the RAG generated content regarding: '{request.query}'.\nThe backend FAISS vector search pipeline is currently being initialized.",
        citations=[
            {
                "id": "doc_123",
                "source": "Enron_Email_12.eml",
                "content": "We need to make sure the platform aggregates fragmented channels.",
                "score": 0.92
            }
        ]
    )
