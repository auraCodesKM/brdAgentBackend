import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

FAST_MODEL = os.getenv("DRAFT_LLM", "qwen2.5:7b")
QUALITY_MODEL = os.getenv("OLLAMA_MODEL_NAME", "qwen2.5:32b")
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")

fast_client = AsyncOpenAI(
    base_url=OLLAMA_URL,
    api_key="ollama"
)

quality_client = AsyncOpenAI(
    base_url=OLLAMA_URL,
    api_key="ollama"
)

class OllamaClient:
    def __init__(self):
        self.draft_model = FAST_MODEL
        self.model = QUALITY_MODEL

    async def generate_stream(self, prompt: str, model_override: str = None, temperature: float = 0.2, max_tokens: int = 2048):
        """Asynchronously stream tokens using AsyncOpenAI."""
        model_to_use = model_override or self.model
        client = fast_client if model_to_use == self.draft_model else quality_client
        
        response = await client.completions.create(
            model=model_to_use,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True
        )
        async for chunk in response:
            if chunk.choices and len(chunk.choices) > 0:
                text = chunk.choices[0].text
                if text:
                    yield text

    async def generate(self, prompt: str, model_override: str = None, max_tokens: int = 2048, temperature: float = 0.7) -> str:
        """Standard async generation using AsyncOpenAI."""
        model_to_use = model_override or self.draft_model
        client = fast_client if model_to_use == self.draft_model else quality_client
        
        response = await client.completions.create(
            model=model_to_use,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=False
        )
        if response.choices and len(response.choices) > 0:
            return response.choices[0].text
        return ""

vllm_engine = OllamaClient()
