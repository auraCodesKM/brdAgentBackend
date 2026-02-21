import os
import asyncio
from lightrag import LightRAG, QueryParam
from lightrag.llm.ollama import ollama_model_complete
from lightrag.utils import EmbeddingFunc
from models.embeddings import bge_m3

# We use the LightRAG instance as the core storage engine for graph relationships
# Note: In a production hackathon setting, the storage dir persists across reboots.

WORKING_DIR = "./lightrag_workspace"

if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)

async def local_bge_m3_embed(texts: list[str]):
    loop = asyncio.get_event_loop()
    embeddings = await loop.run_in_executor(None, bge_m3.embed_dense, texts)
    return embeddings

async def initialize_lightrag():
    print("Initialize LightRAG Knowledge Graph...")
    
    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=ollama_model_complete,
        llm_model_name="qwen2.5:32b",
        llm_model_kwargs={
            "host": "http://localhost:11434",
            "options": {"num_ctx": 16384}
        },
        embedding_func=EmbeddingFunc(
            embedding_dim=1024,
            max_token_size=8192,
            func=local_bge_m3_embed
        )
    )
    await rag.initialize_storages()
    return rag

rag_instance = None
