import logging
import asyncio
from dataclasses import dataclass
from typing import List, Dict, Any

from backend.config import settings
from backend.llm.providers import GroqProvider, MistralProvider

logger = logging.getLogger(__name__)

MODELS = {
    ("groq",    "small"):   "openai/gpt-oss-20b",
    ("groq",    "default"): "openai/gpt-oss-120b",
    ("mistral", "small"):   "mistral-small-latest",
    ("mistral", "default"): "mistral-large-latest",
}

@dataclass
class LLMResponse:
    text: str
    provider: str
    model: str
    tokens_in: int
    tokens_out: int
    latency_ms: int

class AllProvidersExhausted(Exception):
    pass

# Sticky primary provider initialized from config
_primary_provider = settings.PRIMARY_PROVIDER.lower()

# Instantiated providers
_providers = {
    "groq": GroqProvider(),
    "mistral": MistralProvider()
}

def get_other_provider(current: str) -> str:
    return "mistral" if current == "groq" else "groq"

def is_failover_exception(exc: Exception) -> bool:
    """
    Returns True if the exception should trigger a failover to the fallback provider.
    Fails over on rate limits (429), timeouts, service unavailable (503), or auth errors.
    Does NOT fail over on standard API structure errors (like 400 Bad Request).
    """
    exc_str = str(exc).lower()
    
    # Check rate limits / quota
    if "429" in exc_str or "rate limit" in exc_str or "quota" in exc_str:
        return True
    # Check timeouts
    if "timeout" in exc_str or "504" in exc_str or "408" in exc_str:
        return True
    # Check server availability
    if "503" in exc_str or "502" in exc_str:
        return True
    # Check connection issues or client configuration errors (auth failure is sticky failover)
    if "not initialized" in exc_str or "api key" in exc_str or "401" in exc_str or "403" in exc_str:
        return True
        
    return False

async def complete(
    messages: List[Dict[str, str]],
    tier: str = "default",
    json_mode: bool = False,
    temperature: float = 0.3,
) -> LLMResponse:
    global _primary_provider
    
    order = [_primary_provider, get_other_provider(_primary_provider)]
    errors = []
    
    for provider_name in order:
        provider = _providers[provider_name]
        model = MODELS.get((provider_name, tier))
        if not model:
            logger.error(f"Unknown tier/model combo: {provider_name}, {tier}")
            continue
            
        # Retry logic: Try each provider up to 2 times (1 retry)
        for attempt in range(2):
            try:
                logger.info(f"Attempting LLM completion using {provider_name} ({model}), attempt {attempt+1}")
                text, tokens_in, tokens_out, latency = await provider.call(
                    messages=messages,
                    model=model,
                    json_mode=json_mode,
                    temperature=temperature
                )
                
                # Successful call!
                return LLMResponse(
                    text=text,
                    provider=provider_name,
                    model=model,
                    tokens_in=tokens_in,
                    tokens_out=tokens_out,
                    latency_ms=latency
                )
            except Exception as e:
                logger.warning(f"Error calling {provider_name} on attempt {attempt+1}: {e}")
                errors.append(f"{provider_name} (attempt {attempt+1}): {str(e)}")
                
                # If this is the last attempt for this provider, check if we should failover
                if attempt == 1:
                    # Determine if it's a quota/rate-limit/timeout/key error
                    if is_failover_exception(e):
                        # sticky flip the primary provider
                        old_primary = _primary_provider
                        _primary_provider = get_other_provider(_primary_provider)
                        logger.warning(f"Failing over: sticky primary flipped from {old_primary} to {_primary_provider}")
                        # Move to the next provider in the loop
                        break
                    else:
                        # Non-quota error, raise immediately instead of failing over
                        raise e
                else:
                    # Wait 2 seconds before retry
                    await asyncio.sleep(2.0)
                    
    # If we reached here, both providers failed
    logger.error(f"All LLM providers exhausted. Errors: {errors}")
    raise AllProvidersExhausted(f"All providers exhausted: {'; '.join(errors)}")
