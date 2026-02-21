import os
from lightrag import LightRAG, QueryParam
from lightrag.llm.ollama import ollama_model_complete, ollama_embed
from lightrag.utils import EmbeddingFunc

# We use the LightRAG instance as the core storage engine for graph relationships
# Note: In a production hackathon setting, the storage dir persists across reboots.

WORKING_DIR = "./lightrag_workspace"

if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)

async def initialize_lightrag():
    print("Initialize LightRAG Knowledge Graph...")
    
    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=ollama_model_complete,
        llm_model_name="qwen2.5:32b",
        llm_model_kwargs={
            "host": "http://localhost:11434",
            "options": {"num_ctx": 16384}
        },
        embedding_func=EmbeddingFunc(
            embedding_dim=1024,
            max_token_size=8192,
            func=lambda texts: ollama_embed(
                texts,
                embed_model="bge-m3",
                host="http://localhost:11434"
            )
        )
    )
    await rag.initialize_storages()
    return rag

rag_instance = None
