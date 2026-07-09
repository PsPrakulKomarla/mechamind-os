from typing import List, Dict, Any, Optional
import httpx
import asyncio
from abc import ABC, abstractmethod
import structlog

from app.config import settings

logger = structlog.get_logger()


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], temperature: float = 0.1) -> str:
        pass
    
    @abstractmethod
    async def stream_chat(self, messages: List[Dict[str, str]], temperature: float = 0.1):
        pass
    
    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.embedding_model = settings.OPENAI_EMBEDDING_MODEL
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def chat(self, messages: List[Dict[str, str]], temperature: float = 0.1) -> str:
        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json={
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 4000,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    
    async def stream_chat(self, messages: List[Dict[str, str]], temperature: float = 0.1):
        async with self.client.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json={
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 4000,
                "stream": True,
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    import json
                    try:
                        chunk = json.loads(data)
                        content = chunk["choices"][0]["delta"].get("content")
                        if content:
                            yield content
                    except:
                        pass
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        response = await self.client.post(
            f"{self.base_url}/embeddings",
            headers=self.headers,
            json={
                "model": self.embedding_model,
                "input": texts,
            },
        )
        response.raise_for_status()
        data = response.json()
        return [item["embedding"] for item in data["data"]]


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""
    
    def __init__(self):
        self.api_key = settings.ANTHROPIC_API_KEY
        self.model = settings.ANTHROPIC_MODEL
        self.base_url = "https://api.anthropic.com/v1"
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def chat(self, messages: List[Dict[str, str]], temperature: float = 0.1) -> str:
        # Convert to Anthropic format
        system = ""
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                user_messages.append(msg)
        
        response = await self.client.post(
            f"{self.base_url}/messages",
            headers=self.headers,
            json={
                "model": self.model,
                "system": system,
                "messages": user_messages,
                "temperature": temperature,
                "max_tokens": 4000,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["content"][0]["text"]
    
    async def stream_chat(self, messages: List[Dict[str, str]], temperature: float = 0.1):
        system = ""
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                user_messages.append(msg)
        
        async with self.client.stream(
            "POST",
            f"{self.base_url}/messages",
            headers=self.headers,
            json={
                "model": self.model,
                "system": system,
                "messages": user_messages,
                "temperature": temperature,
                "max_tokens": 4000,
                "stream": True,
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    import json
                    try:
                        chunk = json.loads(data)
                        if chunk.get("type") == "content_block_delta":
                            text = chunk.get("delta", {}).get("text", "")
                            if text:
                                yield text
                    except:
                        pass
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        # Anthropic doesn't have embeddings API, use OpenAI or fallback
        raise NotImplementedError("Anthropic doesn't provide embeddings. Use OpenAI or Ollama.")


class OllamaProvider(LLMProvider):
    """Local Ollama provider."""
    
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.embedding_model = settings.OLLAMA_EMBEDDING_MODEL
        self.client = httpx.AsyncClient(timeout=120.0)
    
    async def chat(self, messages: List[Dict[str, str]], temperature: float = 0.1) -> str:
        response = await self.client.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": temperature},
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]
    
    async def stream_chat(self, messages: List[Dict[str, str]], temperature: float = 0.1):
        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": True,
                "options": {"temperature": temperature},
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    import json
                    try:
                        chunk = json.loads(line)
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            yield content
                        if chunk.get("done"):
                            break
                    except:
                        pass
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            response = await self.client.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.embedding_model,
                    "prompt": text,
                },
            )
            response.raise_for_status()
            data = response.json()
            embeddings.append(data["embedding"])
        return embeddings


class LLMProviderFactory:
    """Factory for creating LLM providers."""
    
    _providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "ollama": OllamaProvider,
    }
    
    @classmethod
    def get_provider(cls, provider_name: Optional[str] = None) -> LLMProvider:
        provider_name = provider_name or settings.DEFAULT_LLM_PROVIDER
        provider_class = cls._providers.get(provider_name)
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider_name}")
        return provider_class()
    
    @classmethod
    def get_embedding_provider(cls, provider_name: Optional[str] = None) -> LLMProvider:
        # For embeddings, prefer OpenAI or Ollama
        provider_name = provider_name or "openai"
        if provider_name == "anthropic":
            provider_name = "openai"  # Fallback
        return cls.get_provider(provider_name)


class EmbeddingService:
    """Service for generating embeddings."""
    
    def __init__(self, provider_name: Optional[str] = None):
        self.provider = LLMProviderFactory.get_embedding_provider(provider_name)
    
    async def get_embedding(self, text: str) -> List[float]:
        embeddings = await self.provider.embed([text])
        return embeddings[0]
    
    async def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = await self.provider.embed(batch)
            all_embeddings.extend(embeddings)
        return all_embeddings


# Global instances
embedding_service = EmbeddingService()