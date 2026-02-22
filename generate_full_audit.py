import asyncio
from pipeline.retrieval import enhanced_retrieve
from pipeline.generator import SECTION_PROMPTS, generate_brd_section, format_context

async def main():
    query = "Generate a comprehensive section for the BRD based directly on the provided unstructured corpus context."
    
    print("Retrieving baseline context...")
    context_chunks = await enhanced_retrieve(query, "executive_summary")
    
    if len(context_chunks) == 2 and context_chunks[0] == "__CACHE_HIT__":
         raw_context = context_chunks[1]
    else:
         raw_context = format_context(context_chunks)
    
    with open("audit_context.md", "w", encoding="utf-8") as f:
        f.write("# Ingested Data (Context)\n\n")
        f.write(raw_context)

    sections = [
        "executive_summary",
        "business_objectives",
        "stakeholder_analysis",
        "functional_requirements",
        "non_functional_requirements",
        "assumptions",
        "success_metrics",
        "timeline"
    ]
    
    with open("audit_brd.md", "w", encoding="utf-8") as f:
        f.write("# Full Generated BRD\n\n")
    
    for sec in sections:
        print(f"Generating {sec}...")
        content = ""
        # The generator yields status messages then the actual content. We just capture it all.
        async for chunk in generate_brd_section(sec, query):
            content += chunk
            print(chunk, end="", flush=True)
            
        with open("audit_brd.md", "a", encoding="utf-8") as f:
            f.write(f"\n\n# {sec}\n")
            f.write(content)
            f.write("\n\n---\n\n")
            
    print("\n\nFinished writing audit files.")

if __name__ == "__main__":
    asyncio.run(main())
