# ROADMAP.md — Backend Execution

> **Current Phase**: Phase 6
> **Milestone**: v1.0

## Must-Haves (from SPEC)
- [ ] Implement all 9 advanced RAG techniques.
- [ ] Build the Folder Structure and API.

## Phases

### Phase 1: Environment & Models
**Status**: ✅ Completed
**Objective**: Build `requirements.txt`, `.env`, and model loaders (`llm.py`, `embeddings.py`, `reranker.py`, `whisper_engine.py`).

### Phase 2: Caching & State
**Status**: ✅ Completed
**Objective**: Build Redis semantic cache and BM25 sparse index (`redis_cache.py`, `redis_bm25.py`).

### Phase 3: Ingestion Pipeline (HyPE + RAPTOR)
**Status**: ✅ Completed
**Objective**: Build `.pipeline/ingestion.py` enforcing MinerU parsing, semantic chunking, HyPE question generation, and RAPTOR tree building.

### Phase 4: Retrieval Pipeline (A-RAG + HyDE + CRAG)
**Status**: ✅ Completed
**Objective**: Build `.pipeline/retrieval.py` for multi-tool parallel search, HyDE transformations, and CRAG relevance scoring/re-retrieval.

### Phase 5: Generation Pipeline (Parallel + Repetition)
**Status**: ✅ Completed
**Objective**: Build `.pipeline/generator.py` for parallel section orchestration, Prompt Repetition formatting, and vLLM async streaming.

### Phase 6: FastAPI Main & Endpoints
**Status**: ✅ Completed
**Objective**: Wire up `main.py` with the lifecycle startups, CORS for `localhost:3000`, and WebSocket streaming sockets.
