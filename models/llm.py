import os
import httpx
import json
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
PRIMARY_MODEL = os.getenv("OLLAMA_MODEL_NAME", "qwen2.5:32b")
DRAFT_MODEL = os.getenv("DRAFT_LLM", "qwen2.5:32b")

class OllamaClient:
    def __init__(self):
        self.base_url = OLLAMA_URL
        self.model = PRIMARY_MODEL
        self.draft_model = DRAFT_MODEL

    async def generate_stream(self, prompt: str, model_override: str = None):
        """Asynchronously stream tokens from the Ollama server."""
        model_to_use = model_override or self.model
        
        async with httpx.AsyncClient() as client:
            req_data = {
                "model": model_to_use,
                "prompt": prompt,
                "max_tokens": 2048,
                "temperature": 0.2,
                "stream": True
            }
            
            async with client.stream("POST", f"{self.base_url}/completions", json=req_data, timeout=120.0) as response:
                response.raise_for_status()
                async for chunk in response.aiter_lines():
                    if chunk.startswith("data: "):
                        data_str = chunk[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            data_json = json.loads(data_str)
                            text = data_json["choices"][0]["text"]
                            if text:
                                yield text
                        except json.JSONDecodeError:
                            continue

    async def generate(self, prompt: str, model_override: str = None, max_tokens: int = 512) -> str:
        """Standard async generation (used for HyDE/HyPE with 7B)."""
        model_to_use = model_override or self.draft_model
        
        async with httpx.AsyncClient() as client:
            req_data = {
                "model": model_to_use,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": 0.7,
                "stream": False
            }
            response = await client.post(f"{self.base_url}/completions", json=req_data, timeout=180.0)
            response.raise_for_status()
            return response.json()["choices"][0]["text"]

vllm_engine = OllamaClient()
