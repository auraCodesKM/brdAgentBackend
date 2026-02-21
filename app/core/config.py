from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    # LLM config
    LLM_PROVIDER: str = "ollama"  # or 'groq', 'openai'
    OLLAMA_MODEL: str = "llama3"
    GROQ_API_KEY: Optional[str] = None
    
    # Vector DB
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    FAISS_INDEX_PATH: str = "./vector_store"
    
    class Config:
        env_file = ".env"

settings = Settings()
