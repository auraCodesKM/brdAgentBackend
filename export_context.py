import asyncio
from pipeline.retrieval import enhanced_retrieve
from pipeline.generator import format_context
import pipeline.rag_engine as rag_mod

async def main():
    rag_mod.rag_instance = await rag_mod.initialize_lightrag()
    query = "Generate a comprehensive section for the BRD based directly on the provided unstructured corpus context."
    chunks = await enhanced_retrieve(query, "executive_summary")
    raw_context = chunks[1] if len(chunks) == 2 and chunks[0] == "__CACHE_HIT__" else format_context(chunks)
    
    with open("raw_ingested_data.md", "w", encoding="utf-8") as f:
        f.write("# Raw Ingested Graph Data\n\n")
        f.write(raw_context)
    print("Exported raw context.")

if __name__ == "__main__":
    asyncio.run(main())
