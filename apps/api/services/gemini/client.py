import google.generativeai as genai
from typing import Optional, Dict, List, Any
import asyncio
import logging
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from core.config import settings
from core.redis import redis_client
import hashlib
import json

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        self.generation_config = {
            'temperature': 0.1,
            'top_p': 0.95,
            'max_output_tokens': 8192,
        }

    def _generate_cache_key(self, prompt: str, config: Dict) -> str:
        """Generate cache key for prompt and config"""
        content = f"{prompt}:{json.dumps(config, sort_keys=True)}"
        return f"gemini:cache:{hashlib.sha256(content.encode()).hexdigest()}"

    async def _get_cached_response(self, cache_key: str) -> Optional[str]:
        """Get cached response if available"""
        try:
            cached = await redis_client.get(cache_key)
            if cached:
                logger.info(f"Cache hit for key: {cache_key[:16]}...")
                return cached
        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")
        return None

    async def _cache_response(self, cache_key: str, response: str, ttl: int = 86400):
        """Cache response with TTL"""
        try:
            await redis_client.set(cache_key, response, ttl)
            logger.info(f"Cached response for key: {cache_key[:16]}...")
        except Exception as e:
            logger.warning(f"Cache storage error: {e}")

    @retry(
        retry=retry_if_exception_type((TimeoutError, ConnectionError)),
        stop=stop_after_attempt(settings.GEMINI_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_content_async(
        self,
        prompt: str,
        generation_config: Optional[Dict] = None,
        use_cache: bool = True,
        cache_ttl: int = 86400
    ) -> str:
        """Generate content with Gemini API (async with retry)"""

        # Merge configs
        config = {**self.generation_config, **(generation_config or {})}

        # Check cache
        if use_cache:
            cache_key = self._generate_cache_key(prompt, config)
            cached_response = await self._get_cached_response(cache_key)
            if cached_response:
                return cached_response

        # Generate content
        try:
            logger.info(f"Generating content with Gemini (prompt length: {len(prompt)})")

            # Run in thread pool since genai is sync
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(
                    prompt,
                    generation_config=config
                )
            )

            result = response.text

            # Cache response
            if use_cache:
                await self._cache_response(cache_key, result, cache_ttl)

            logger.info(f"Generated content length: {len(result)}")
            return result

        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            raise

    async def generate_json_async(
        self,
        prompt: str,
        generation_config: Optional[Dict] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Generate JSON content with Gemini"""

        config = {
            **(generation_config or {}),
            'response_mime_type': 'application/json'
        }

        response_text = await self.generate_content_async(
            prompt,
            generation_config=config,
            use_cache=use_cache
        )

        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response_text[:500]}...")
            raise

    async def generate_batch_async(
        self,
        prompts: List[str],
        generation_config: Optional[Dict] = None,
        max_concurrent: int = 5
    ) -> List[str]:
        """Generate multiple contents concurrently"""

        semaphore = asyncio.Semaphore(max_concurrent)

        async def generate_with_semaphore(prompt):
            async with semaphore:
                return await self.generate_content_async(
                    prompt,
                    generation_config=generation_config
                )

        tasks = [generate_with_semaphore(prompt) for prompt in prompts]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        # Gemini uses ~4 chars per token on average
        return len(text) // 4

# Global client instance
gemini_client = GeminiClient()
