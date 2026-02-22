import os
import asyncio
from lightrag import LightRAG, QueryParam
from lightrag.llm.ollama import ollama_model_complete
from lightrag.utils import EmbeddingFunc
from models.embeddings import bge_m3
from models.reranker import bge_reranker

# We use the LightRAG instance as the core storage engine for graph relationships
# Note: In a production hackathon setting, the storage dir persists across reboots.

WORKING_DIR = "./lightrag_workspace"

if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)

async def local_bge_m3_embed(texts: list[str]):
    loop = asyncio.get_event_loop()
    embeddings = await loop.run_in_executor(None, bge_m3.embed_dense, texts)
    return embeddings

async def local_bge_rerank(query: str, documents: list[str], top_n: int = None):
    if not documents:
        return []
    loop = asyncio.get_event_loop()
    pairs = [[query, doc] for doc in documents]
    
    def _run():
        scores = bge_reranker.model.compute_score(pairs)
        if isinstance(scores, float):
            scores = [scores]
        import math
        def sigmoid(x):
            try:
                return 1 / (1 + math.exp(-x))
            except OverflowError:
                return 0.0 if x < 0 else 1.0
        return [sigmoid(s) for s in scores]
        
    scores = await loop.run_in_executor(None, _run)
    results = [{"index": i, "relevance_score": s} for i, s in enumerate(scores)]
    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    if top_n is not None:
        return results[:top_n]
    return results

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
        ),
        rerank_model_func=local_bge_rerank
    )
    await rag.initialize_storages()
    return rag

rag_instance = None
