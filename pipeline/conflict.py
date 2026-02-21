from pipeline.retrieval import enhanced_retrieve
from models.llm import vllm_engine
import json
import time

async def detect_brd_conflicts(query: str):
    """
    Detects logical inconsistencies between ingested datasets (e.g. Enron vs Slack).
    Utilizes Prompt Repetition for accurate extraction.
    """
    # 1. Fetch cross-functional context
    start_time = time.time()
    context_chunks = await enhanced_retrieve(query, section_name="conflict_detection")
    retrieval_time = time.time() - start_time
    
    if not isinstance(context_chunks, list):
         return {"conflicts": [], "metrics": {"retrieval_sec": retrieval_time, "inference_sec": 0}}
         
    context = "\n\n---\n\n".join(context_chunks)

    # 2. Extract conflicts using structured Prompt Repetition
    prompt = f"Analyze this context and return a JSON list of conflicts between different stakeholders or documents. Context: {context}\n\nAnalyze this context and return a JSON list of conflicts between different stakeholders or documents. Context: {context}"
    
    start_time = time.time()
    analysis = await vllm_engine.generate(prompt, max_tokens=2048)
    inference_time = time.time() - start_time
    
    metrics = {
        "retrieval_sec": round(retrieval_time, 2),
        "inference_sec": round(inference_time, 2),
        "total_sec": round(retrieval_time + inference_time, 2)
    }
    
    try:
        if "```json" in analysis:
            raw = analysis.split("```json")[1].split("```")[0].strip()
            result = json.loads(raw)
        else:
            result = json.loads(analysis)
            
        result["metrics"] = metrics
        return result
    except Exception as e:
        print(f"Failed to parse JSON conflicts: {e}")
        return {"conflicts": [], "metrics": metrics}
