import asyncio
from typing import List, AsyncGenerator
from pipeline.retrieval import enhanced_retrieve
from models.llm import vllm_engine
from cache.redis_cache import redis_cache

generation_semaphore = asyncio.Semaphore(2)

# The 8 classic sections of our BRD
SECTION_PROMPTS = {
    "executive_summary": "Write the Executive Summary of the Business Requirements Document based on the context.",
    "business_objectives": "Extract and write the Business Objectives covering KPIs and OKRs based on the context.",
    "stakeholder_analysis": "Identify key stakeholders, sponsors, and their roles from the context.",
    "functional_requirements": "List the explicit functional system requirements requested in the context in bullet points.",
    "non_functional_requirements": "List the non-functional requirements (security, latency, hardware) in the context.",
    "assumptions": "Detail any assumptions, constraints, and dependencies highlighted in the context.",
    "success_metrics": "Outline the quantifiable success metrics defined.",
    "timeline": "Extract phase timelines, milestones, or deadlines mentioned."
}

def format_context(context_chunks: List[str]) -> str:
    """Format the CRAG-filtered chunks into a single readable block."""
    if not context_chunks:
        return "No relevant context found."
    return "\n\n---\n\n".join(context_chunks)

async def generate_brd_section(section_name: str, query: str) -> AsyncGenerator[str, None]:
    """
    Generates a single BRD section.
    Applies DeepMind Prompt Repetition for 0-latency attention boosting.
    Streams tokens back to the WebSocket caller.
    """
    # 1. Autonomous Retrieval
    context_chunks = await enhanced_retrieve(query, section_name)
    
    # Check if the cache hit directly returned the final answer string
    if len(context_chunks) == 2 and context_chunks[0] == "__CACHE_HIT__":
         # It's a cache hit string
         yield context_chunks[1]
         return

    section_prompt = SECTION_PROMPTS.get(section_name, "Write this BRD section.")
    context = format_context(context_chunks)

    # 2. PROMPT REPETITION (arXiv:2512.14982)
    # <PROMPT><PROMPT> technique wins 47/70 benchmarks
    full_prompt = f"System: {section_prompt}\n\nContext:\n{context}\n\nSystem: {section_prompt}\n\nContext:\n{context}\n\nAnswer:"

    # 3. Stream Generation
    completed_section = ""
    async for token in vllm_engine.generate_stream(full_prompt):
        completed_section += token
        yield token  # Yield to WebSocket

    # 4. Cache the finalized result for next time
    redis_cache.store(query, section_name, completed_section)

async def generate_full_brd(base_query: str) -> dict:
    """
    Parallel orchestration of all 8 BRD sections simultaneously.
    This limits total duration to the slowest section (vs sequential sum).
    Note: Websockets usually stream one by one, so this function is useful for batch/API generation.
    """
    sections = [
        "executive_summary", "business_objectives", "stakeholder_analysis",
        "functional_requirements", "non_functional_requirements", "assumptions",
        "success_metrics", "timeline"
    ]
    
    # Wrap generator in a collector to await all parallel
    async def collect_section(sec_name):
        full_text = ""
        async for t in generate_brd_section(sec_name, base_query):
            full_text += t
        return sec_name, full_text

    tasks = [collect_section(sec) for sec in sections]
    results = await asyncio.gather(*tasks)
    
    return {sec: txt for sec, txt in results}
