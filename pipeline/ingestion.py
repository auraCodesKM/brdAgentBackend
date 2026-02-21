import asyncio
from typing import Dict, Any, List
from cache.redis_bm25 import redis_bm25
from models.llm import vllm_engine
from models.embeddings import bge_m3

class Chunk:
    def __init__(self, text: str):
        self.text = text
        self.hypothetical_questions = []
        self.hypothetical_embeddings = []
        self.raw_embedding = []

class RaptorTree:
    def __init__(self):
        self.all_nodes = []

def mineru_parse(content: bytes) -> str:
    """MinerU 2.7.6 Integration (Fallback to raw UTF-8 if magic_pdf not installed)"""
    try:
        from magic_pdf.data.data_reader_writer import FileBasedDataWriter
        from magic_pdf.pipe.UNIPipe import UNIPipe
        from magic_pdf.rw.MemReaderWriter import MemReaderWriter
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(content)
            temp_pdf_path = temp_pdf.name
            
        try:
            image_writer = MemReaderWriter()
            pipe = UNIPipe(temp_pdf_path, jso_useful_key={"_pdf_type": "", "model_list": []}, image_writer=image_writer, is_draw_boxes=False)
            pipe.pipe_classify()
            pipe.pipe_parse()
            md_content = pipe.pipe_mk_markdown("/tmp", drop_mode="none")
            
            if isinstance(md_content, list):
                 return "\n".join([item.get('content', '') for item in md_content])
            return str(md_content)
        finally:
            os.remove(temp_pdf_path)
    except ImportError:
        print("MinerU (magic-pdf) not installed. Falling back to raw text extraction.")
        return content.decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"MinerU extraction failed: {e}. Falling back to raw text extraction.")
        return content.decode("utf-8", errors="ignore")

def semantic_chunker(text: str, max_tokens=512, overlap=64) -> List[Chunk]:
    """Basic pseudo-semantic sliding window chunker."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_tokens - overlap):
        chunk_text = " ".join(words[i:i + max_tokens])
        if chunk_text:
            chunks.append(Chunk(chunk_text))
    return chunks

async def generate_hypothetical_questions(chunk: Chunk, n: int = 3) -> List[str]:
    """
    HyPE: Hypothetical Prompt Embeddings generated at index time.
    Calls Qwen 7B to predict questions this chunk could answer.
    """
    prompt = f"Given this text, generate {n} hypothetical questions a user might ask that this text uniquely answers. Reply with just the questions separated by newlines.\n\n{chunk.text}"
    response = await vllm_engine.generate(prompt)
    return [q.strip() for q in response.split("\n") if q.strip()]

def build_raptor_tree(chunks: List[Chunk], levels: int = 3) -> RaptorTree:
    """
    Builds a 3-level abstractive routing tree for deeper retrieval.
    Level 1: Leaves (Raw chunks) -> Level 2: Section Summaries -> Level 3: Doc Summary
    """
    # Placeholder for actual RAPTOR clustering + summarization logic.
    # In a full run, we cluster dense embeddings, generate a summary via vLLM, and cluster again.
    tree = RaptorTree()
    tree.all_nodes = [c.text for c in chunks]  # In mock, just returns chunk texts to pass to LightRAG
    return tree

async def ingest_document(content: bytes, source_metadata: Dict[str, Any]):
    """
    Main advanced ingestion pipeline bridging MinerU -> Semantic Chunker -> HyPE -> RAPTOR -> Caches.
    """
    # Step 1: Parse with MinerU
    content_text = mineru_parse(content)

    # Step 2: Semantic chunking
    chunks = semantic_chunker(content_text, max_tokens=512, overlap=64)

    # Step 3: HyPE - generate hypothetical questions per chunk
    for chunk in chunks:
        # Prompt vLLM Qwen 7B for hypothetical questions
        questions = await generate_hypothetical_questions(chunk, n=3)
        chunk.hypothetical_questions = questions
        
        # Embed those questions alongside the raw chunk text
        chunk.hypothetical_embeddings = bge_m3.embed_dense(questions)
        chunk.raw_embedding = bge_m3.embed_dense([chunk.text])

    # Step 4: RAPTOR tree building
    raptor_tree = build_raptor_tree(chunks, levels=3)

    # Step 5: Insert everything into LightRAG Knowledge Graph
    from pipeline.rag_engine import rag_instance
    if rag_instance:
        await rag_instance.insert_content_list(
            raptor_tree.all_nodes,
            file_path=source_metadata.get('filename', 'unknown.doc')
        )

    # Step 6: Update BM25 index in Redis (Sparse Retrieval Map)
    raw_texts = [c.text for c in chunks]
    redis_bm25.add_documents(raw_texts)
    
    return {"status": "success", "chunks_indexed": len(chunks), "raptor_nodes": len(raptor_tree.all_nodes)}
