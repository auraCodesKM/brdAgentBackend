import asyncio
from typing import List, Dict, Any

from cache.redis_cache import redis_cache
from cache.redis_bm25 import redis_bm25
from models.llm import vllm_engine
from models.embeddings import bge_m3
from models.reranker import bge_reranker
import pipeline.rag_engine as rag_mod
from lightrag import QueryParam

# Global setting to prevent infinite re-retrieval loops in CRAG
MAX_RETRIES = 2

async def faiss_semantic_search(embedding: list[float], top_k: int = 10) -> List[Dict[str, Any]]:
    """Mock FAISS Dense Vector Search finding closest RAPTOR nodes."""
    # In full implementation, FAISS index is loaded and IVFPQ searched here.
    return []

async def lightrag_graph_search(query: str, mode: str = "hybrid") -> List[Dict[str, Any]]:
    """Query LightRAG for entities and relational summaries."""
    if not rag_mod.rag_instance:
        return []
        
    try:
        # We use LightRAG's query_with_stream or raw query logic
        result = await rag_mod.rag_instance.aquery(query, param=QueryParam(mode=mode))
        if result:
            return [{"chunk": result, "score": 1.0, "source": "lightrag"}]
        return []
    except Exception as e:
        print(f"LightRAG search err: {e}")
        return []

def deduplicate_rrf(results_lists: List[List[Dict[str, Any]]], k=60) -> List[str]:
    """Reciprocal Rank Fusion to merge BM25, FAISS, and Knowledge Graph results."""
    rrf_scores = {}
    chunk_map = {}
    
    for result_list in results_lists:
        for text_rank, item in enumerate(result_list):
            chunk_txt = item["chunk"]
            chunk_map[chunk_txt] = chunk_txt
            if chunk_txt not in rrf_scores:
                rrf_scores[chunk_txt] = 0.0
            rrf_scores[chunk_txt] += 1.0 / (k + text_rank + 1)
            
    # Sort merged results by RRF score
    sorted_chunks = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
    return sorted_chunks

async def reformulate_query(query: str) -> str:
    """CRAG logic: Reformulate a query if retrieval yields poor relevance."""
    prompt = f"The following query produced poor search results. Reformulate it to be clearer and focus on different semantic keywords:\n{query}"
    new_query = await vllm_engine.generate(prompt)
    return new_query.strip()

async def enhanced_retrieve(query: str, section_name: str, retry_count: int = 0) -> List[str]:
    """
    Advanced Orchestrator combining: Semantic Cache, HyDE, A-RAG, and CRAG.
    """
    print(f"Retrieving for {section_name} (Attempt {retry_count + 1})...")
    
    # Step 1: Check Redis semantic cache first
    cached = redis_cache.check(query, section_name=section_name, threshold=0.88)
    if cached:
        print(f"CACHE HIT for {section_name}")
        return ["__CACHE_HIT__", cached] # We return the final cached answer as the context, bypassing generation entirely if needed (generator will catch this)

    # Step 2: HyDE - generate hypothetical answer using Prompt Repetition
    hyde_prompt = f"Write a brief BRD {section_name} section: {query}\n\nWrite a brief BRD {section_name} section: {query}"
    hyde_doc = await vllm_engine.generate(hyde_prompt)
    hyde_embedding = bge_m3.embed_dense([hyde_doc])[0].tolist()

    # Step 3: A-RAG - parallel retrieval with all 3 tools
    results_lists = await asyncio.gather(
        faiss_semantic_search(hyde_embedding, top_k=10),
        redis_bm25.search(query, top_k=10),
        lightrag_graph_search(query, mode="hybrid")
    )

    # Step 4: Merge and deduplicate
    merged_text_chunks = deduplicate_rrf(results_lists)
    if not merged_text_chunks:
        merged_text_chunks = ["System Error: No documents found in database."]

    # Step 5: CRAG - score relevance using Cross-Encoder Reranker
    scored_results = bge_reranker.rerank_and_score(query, merged_text_chunks)
    
    # Discard non-relevant chunks
    filtered = [item["chunk"] for item in scored_results if item["score"] > 0.3]
    
    # Step 6: If average quality is too low, re-retrieve up to MAX_RETRIES
    if not filtered or (sum(item["score"] for item in scored_results[:len(filtered)]) / max(len(filtered), 1)) < 0.2:
        if retry_count < MAX_RETRIES:
            print("CRAG: Relevance too low. Reformulating query...")
            new_query = await reformulate_query(query)
            return await enhanced_retrieve(new_query, section_name, retry_count=retry_count + 1)
        else:
            print("CRAG: Max retries hit. Proceeding with best available context.")
            filtered = [item["chunk"] for item in scored_results] # Fallback to top ranking even if low score

    # Debug request from user to trace chunk integrity:
    print("\n" + "="*50)
    print(f"DEBUG: Retrieved Chunks for '{query}'")
    print("="*50)
    for idx, item in enumerate(scored_results[:3]):
        print(f"\n[Chunk {idx+1}] Score: {item['score']:.4f}")
        # Note: the actual source logic is lost in deduplicate_rrf returning just text, 
        # but the scores map accurately.
        text_preview = item["chunk"][:300].replace('\n', ' ') + "..."
        print(f"Content: {text_preview}")
    print("="*50 + "\n")

    return filtered[:5]  # return top 5 highest quality chunks
