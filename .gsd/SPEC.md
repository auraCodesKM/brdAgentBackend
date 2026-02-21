# SPEC.md — Backend Advanced RAG Engine

> **Status**: `FINALIZED`

## Vision
Build the most sophisticated BRD Generation Agent backend ever built for a hackathon. Utilize cutting-edge 2025-2026 AI research to achieve unparalleled retrieval precision, zero hallucination, and lightning-fast streaming inference on a local RTX 4090.

## Goals
1. Implement 9 research-backed advanced RAG techniques.
2. Build an asynchronous FastAPI + WebSockets streaming architecture.
3. Process multimodel inputs (Emails, Transcripts, Slack) into a highly structured Document.

## Advanced Techniques to Implement
1. **Prompt Repetition**: `<PROMPT><PROMPT>` transformation for zero-latency benchmark wins.
2. **HyDE**: Qwen 7B hypothetical document embeddings at query time.
3. **HyPE (Index-time)**: Qwen 7B generation of 3 hypothetical questions per chunk during ingestion.
4. **RAPTOR**: Recursive Abstractive Tree (3 levels) stored in FAISS.
5. **CRAG**: Corrective RAG using cross-encoder relevance scoring (Discard < 0.6, Re-retrieve < 0.5).
6. **A-RAG**: Agentic Hierarchical Retrieval combining BM25 (Redis), BGE-M3 (FAISS), and LightRAG.
7. **Speculative Decoding**: vLLM with Qwen 2.5 72B (Verifier) and 7B (Draft) for fast generation.
8. **Redis Semantic Cache**: 0.88 cosine similarity threshold for instant cache hits.
9. **Parallel Section Generation**: `asyncio.gather` across all 8 BRD sections simultaneously.

## Tech Stack
- **Framework**: FastAPI + WebSockets
- **Parsing**: MinerU 2.7.6, faster-whisper large-v3
- **Graph & Vector Storage**: RAG-Anything + LightRAG, FAISS
- **Cache & Sparse**: Redis, redisvl, rank-bm25
- **Embeddings/Reranking**: BGE-M3, BGE-reranker-large (FlagEmbedding)
- **Inference**: vLLM (Qwen 2.5 72B AWQ + 7B)

## Dependencies
- Local RTX 4090 / 128GB RAM remote server environment.
- Local Redis Docker container running.
- All models loaded at startup via FastAPI `startup_event`.
