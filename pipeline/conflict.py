from pipeline.retrieval import enhanced_retrieve
from models.llm import vllm_engine
import json

async def detect_brd_conflicts(query: str):
    """
    Detects logical inconsistencies between ingested datasets (e.g. Enron vs Slack).
    Utilizes Prompt Repetition for accurate extraction.
    """
    # 1. Fetch cross-functional context
    context_chunks = await enhanced_retrieve(query, section_name="conflict_detection")
    if not isinstance(context_chunks, list):
         return {"conflicts": []} # Fallback if cached string returned
         
    context = "\n\n---\n\n".join(context_chunks)

    # 2. Extract conflicts using structured Prompt Repetition
    prompt = f"Analyze this context and return a JSON list of conflicts between different stakeholders or documents. Context: {context}\n\nAnalyze this context and return a JSON list of conflicts between different stakeholders or documents. Context: {context}"
    
    analysis = await vllm_engine.generate(prompt)
    
    # Simple parse mock
    try:
        # Assuming Qwen formatted the output as JSON within markdown ticks
        if "```json" in analysis:
            raw = analysis.split("```json")[1].split("```")[0].strip()
            return json.loads(raw)
        return json.loads(analysis)
    except Exception as e:
        print(f"Failed to parse JSON conflicts: {e}")
        return {"conflicts": []}
