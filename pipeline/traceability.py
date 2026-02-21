import pandas as pd
import json
from pipeline.retrieval import enhanced_retrieve
from models.llm import vllm_engine

class TraceabilityMatrixBuilder:
    def __init__(self):
        self.requirements = []

    def log_requirement(self, req_id: str, desc: str, source_doc: str, chunk_id: str, is_conflict: bool = False, conflict_detail: str = ""):
        self.requirements.append({
            "Requirement ID": req_id,
            "Description": desc,
            "Source Document": source_doc,
            "Chunk Citation": chunk_id,
            "Conflict Flag": is_conflict,
            "Conflict Details": conflict_detail
        })

    def export_csv(self, filename: str = "traceability_matrix.csv"):
        """Exports the precise origin of every generated BRD requirement to a CSV dataset."""
        df = pd.DataFrame(self.requirements)
        df.to_csv(filename, index=False)
        return filename

traceability_builder = TraceabilityMatrixBuilder()

async def generate_traceability_matrix():
    """
    Retrieves all requirements, features, constraints, and systems from the parsed graph
    and constructs a JSON traceability matrix mapping them to sources and stakeholders.
    """
    query = "List all functional requirements, features, system constraints, and technical specifications."
    
    # 1. Fetch cross-functional context
    context_chunks = await enhanced_retrieve(query, section_name="traceability")
    if not isinstance(context_chunks, list):
         return {"status": "error", "matrix": []}
         
    context = "\n\n---\n\n".join(context_chunks)

    # 2. Extract matrix using Prompt Repetition
    instruction = "Analyze this context and extract all project requirements, features, constraints, and system specifications. Return ONLY a valid JSON list of objects. Each object must have exactly these 4 keys: 'req_id' (e.g., REQ-001), 'description' (what the requirement is), 'source' (the source document or sender), and 'owner' (the stakeholder who owns or mentioned it)."
    prompt = f"{instruction}\nContext: {context}\n\n{instruction}\nContext: {context}"
    
    analysis = await vllm_engine.generate(prompt, max_tokens=2048)
    
    try:
        if "```json" in analysis:
            raw = analysis.split("```json")[1].split("```")[0].strip()
            matrix = json.loads(raw)
        else:
            matrix = json.loads(analysis)
        return {"status": "success", "matrix": matrix}
    except Exception as e:
        print(f"Failed to parse JSON traceability: {e}")
        return {"status": "error", "matrix": []}
