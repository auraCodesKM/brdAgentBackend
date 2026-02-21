import os
from lightrag import LightRAG, QueryParam
from lightrag.llm import openai_complete_if_cache

# We use the LightRAG instance as the core storage engine for graph relationships
# Note: In a production hackathon setting, the storage dir persists across reboots.

WORKING_DIR = "./lightrag_workspace"

if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)

async def initialize_lightrag():
    print("Initialize LightRAG Knowledge Graph...")
    
    # We mount LightRAG with dummy openai configs because we override all logic with 
    # our local vLLM endpoint acting exactly like an OpenAI streaming format.
    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_name="qwen2.5-7b",
        llm_model_max_async=4,
        llm_model_max_token_size=32768,
        # Point LightRAG's internal model calls to our local vLLM draft model
        llm_model_func=lambda prompt: openai_complete_if_cache(
            "qwen2.5-7b-instruct", 
            prompt, 
            api_key="empty", 
            base_url="http://localhost:8001/v1"
        )
    )
    return rag

rag_instance = None
