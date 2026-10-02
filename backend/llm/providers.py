import time
import logging
import asyncio
from typing import List, Dict, Any, Tuple
from groq import AsyncGroq, RateLimitError as GroqRateLimitError, APIStatusError as GroqAPIStatusError
from mistralai import Mistral, SDKError as MistralException
import httpx

from backend.config import settings

logger = logging.getLogger(__name__)

class LLMProvider:
    async def call(self, messages: List[Dict[str, str]], model: str, json_mode: bool, temperature: float) -> Tuple[str, int, int, int]:
        """
        Returns (response_text, input_tokens, output_tokens, latency_ms)
        """
        raise NotImplementedError()

class GroqProvider(LLMProvider):
    def __init__(self):
        # Initialize client if API key looks plausible
        key = settings.GROQ_API_KEY
        if not key or "your_groq_api_key" in key:
            self.client = None
            logger.warning("Groq API key not set or placeholder. Groq calls will fail.")
        else:
            self.client = AsyncGroq(api_key=key)

    async def call(self, messages: List[Dict[str, str]], model: str, json_mode: bool, temperature: float) -> Tuple[str, int, int, int]:
        if not self.client:
            raise ValueError("Groq client not initialized (missing API key)")
            
        kwargs = {
            "messages": messages,
            "model": model,
            "temperature": temperature,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
            
        start_time = time.perf_counter()
        try:
            # Groq async completion call
            completion = await self.client.chat.completions.create(**kwargs)
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            
            text = completion.choices[0].message.content or ""
            usage = completion.usage
            tokens_in = usage.prompt_tokens if usage else 0
            tokens_out = usage.completion_tokens if usage else 0
            
            return text, tokens_in, tokens_out, latency_ms
        except (GroqRateLimitError, GroqAPIStatusError) as e:
            # Propagate or check for quota / timeout / rate limit status codes
            status_code = getattr(e, "status_code", 500)
            if status_code in (429, 503, 504, 408):
                logger.warning(f"Groq API returned rate-limit/timeout: {e}")
            raise e
        except Exception as e:
            logger.error(f"Groq provider exception: {e}")
            raise e

class MistralProvider(LLMProvider):
    def __init__(self):
        key = settings.MISTRAL_API_KEY
        if not key or "your_mistral_api_key" in key:
            self.client = None
            logger.warning("Mistral API key not set or placeholder. Mistral calls will fail.")
        else:
            self.client = Mistral(api_key=key)

    async def call(self, messages: List[Dict[str, str]], model: str, json_mode: bool, temperature: float) -> Tuple[str, int, int, int]:
        if not self.client:
            raise ValueError("Mistral client not initialized (missing API key)")
            
        kwargs = {
            "messages": messages,
            "model": model,
            "temperature": temperature,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
            
        start_time = time.perf_counter()
        try:
            # Mistral async chat completion
            # In SDK version 1.2.*, complete_async is used
            completion = await self.client.chat.complete_async(**kwargs)
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            
            text = completion.choices[0].message.content or ""
            usage = completion.usage
            tokens_in = usage.prompt_tokens if usage else 0
            tokens_out = usage.completion_tokens if usage else 0
            
            return text, tokens_in, tokens_out, latency_ms
        except Exception as e:
            logger.error(f"Mistral provider exception: {e}")
            raise e
