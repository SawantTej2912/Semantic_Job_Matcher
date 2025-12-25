"""
Gemini Provider with multi-key rotation and optimized model selection.

This module provides a robust Gemini API client that:
- Rotates through multiple API keys on 429 errors
- Uses gemini-2.5-flash-lite for higher rate limits (30 RPM)
- Implements smart throttling between calls
"""
import os
import time
import logging
from typing import List, Optional
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# Smart throttling configuration
THROTTLE_DELAY = 2  # Seconds between consecutive API calls

# Track last API call time for throttling
_last_api_call_time = 0


class GeminiProvider:
    """
    Gemini API provider with multi-key rotation and smart throttling.
    
    Features:
    - Automatic key rotation on ResourceExhausted errors
    - Uses gemini-2.5-flash-lite (30 RPM free tier)
    - Smart throttling between calls
    """
    
    def __init__(self, api_keys: List[str]):
        """
        Initialize provider with multiple API keys.
        
        Args:
            api_keys: List of Gemini API keys for rotation
        """
        if not api_keys or not api_keys[0]:
            raise ValueError("At least one API key is required")
        
        self.api_keys = api_keys
        self.current_key_index = 0
        self.clients = {}
        
        # Initialize clients for all keys
        for i, key in enumerate(api_keys):
            if key:  # Only create client if key is not empty
                try:
                    self.clients[i] = genai.Client(api_key=key)
                    logger.info(f"✅ Initialized Gemini client for key #{i+1}")
                except Exception as e:
                    logger.warning(f"⚠️  Failed to initialize client for key #{i+1}: {e}")
        
        if not self.clients:
            raise ValueError("Failed to initialize any Gemini clients")
        
        logger.info(f"✅ GeminiProvider initialized with {len(self.clients)} API key(s)")
    
    def _wait_for_throttle(self):
        """Ensure minimum delay between API calls."""
        global _last_api_call_time
        current_time = time.time()
        time_since_last_call = current_time - _last_api_call_time
        
        if time_since_last_call < THROTTLE_DELAY:
            sleep_time = THROTTLE_DELAY - time_since_last_call
            logger.info(f"⏱️  Throttling: waiting {sleep_time:.1f}s before next API call...")
            time.sleep(sleep_time)
        
        _last_api_call_time = time.time()
    
    def _rotate_key(self):
        """Rotate to the next available API key."""
        old_index = self.current_key_index
        
        # Try next keys in rotation
        for _ in range(len(self.clients)):
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            if self.current_key_index in self.clients:
                logger.warning(f"🔄 Rotating from key #{old_index+1} to key #{self.current_key_index+1}")
                return True
        
        logger.error("❌ All API keys exhausted!")
        return False
    
    def _is_rate_limit_error(self, error: Exception) -> bool:
        """Check if error is a rate limit error."""
        error_str = str(error)
        return ("429" in error_str or 
                "RESOURCE_EXHAUSTED" in error_str or 
                "quota" in error_str.lower() or
                "rate limit" in error_str.lower())
    
    def get_current_client(self) -> genai.Client:
        """Get the current active Gemini client."""
        if self.current_key_index not in self.clients:
            # Find first available client
            for i in self.clients:
                self.current_key_index = i
                break
        
        return self.clients[self.current_key_index]
    
    def generate_content(self, prompt: str, max_output_tokens: int = 1500, temperature: float = 0.3) -> str:
        """
        Generate content with automatic key rotation on rate limits.
        
        Uses gemini-2.5-flash-lite for higher rate limits (30 RPM).
        
        Args:
            prompt: The prompt to send to Gemini
            max_output_tokens: Maximum tokens in response
            temperature: Temperature for generation
            
        Returns:
            Generated text response
            
        Raises:
            Exception: If all keys are exhausted or other error occurs
        """
        # Apply throttling
        self._wait_for_throttle()
        
        max_retries = len(self.clients)
        
        for attempt in range(max_retries):
            try:
                client = self.get_current_client()
                
                response = client.models.generate_content(
                    model='models/gemini-2.5-flash-lite',  # Lighter model with 30 RPM
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=temperature,
                        max_output_tokens=max_output_tokens,
                    )
                )
                
                return response.text.strip()
                
            except Exception as e:
                if self._is_rate_limit_error(e):
                    logger.warning(f"⚠️  Rate limit hit on key #{self.current_key_index+1}: {e}")
                    
                    if attempt < max_retries - 1:
                        if self._rotate_key():
                            logger.info(f"🔄 Retrying with next key...")
                            continue
                        else:
                            raise Exception("All API keys exhausted. Please wait 60 seconds.")
                    else:
                        raise Exception("All API keys exhausted. Please wait 60 seconds.")
                else:
                    # Non-rate-limit error, re-raise
                    raise
        
        raise Exception("All API keys exhausted. Please wait 60 seconds.")
    
    def embed_content(self, text: str) -> List[float]:
        """
        Generate embedding with automatic key rotation on rate limits.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            768-dimensional embedding vector
            
        Raises:
            Exception: If all keys are exhausted or other error occurs
        """
        # Apply throttling
        self._wait_for_throttle()
        
        max_retries = len(self.clients)
        
        for attempt in range(max_retries):
            try:
                client = self.get_current_client()
                
                result = client.models.embed_content(
                    model='text-embedding-004',
                    contents=text
                )
                
                return list(result.embeddings[0].values)
                
            except Exception as e:
                if self._is_rate_limit_error(e):
                    logger.warning(f"⚠️  Rate limit hit on embedding with key #{self.current_key_index+1}: {e}")
                    
                    if attempt < max_retries - 1:
                        if self._rotate_key():
                            logger.info(f"🔄 Retrying embedding with next key...")
                            continue
                        else:
                            raise Exception("All API keys exhausted. Please wait 60 seconds.")
                    else:
                        raise Exception("All API keys exhausted. Please wait 60 seconds.")
                else:
                    # Non-rate-limit error, re-raise
                    raise
        
        raise Exception("All API keys exhausted. Please wait 60 seconds.")


# Initialize global provider
def initialize_provider() -> Optional[GeminiProvider]:
    """
    Initialize Gemini provider from environment variables.
    
    Reads GEMINI_API_KEYS (comma-separated) or GEMINI_API_KEY (single key).
    
    Returns:
        GeminiProvider instance or None if no keys available
    """
    # Try to read multiple keys first
    keys_str = os.getenv("GEMINI_API_KEYS", "")
    
    if keys_str:
        # Parse comma-separated keys
        keys = [k.strip() for k in keys_str.split(",") if k.strip()]
    else:
        # Fallback to single key
        single_key = os.getenv("GEMINI_API_KEY", "")
        keys = [single_key] if single_key else []
    
    if not keys:
        logger.warning("⚠️  No Gemini API keys found in environment")
        return None
    
    try:
        provider = GeminiProvider(keys)
        return provider
    except Exception as e:
        logger.error(f"❌ Failed to initialize GeminiProvider: {e}")
        return None


# Global provider instance
gemini_provider = initialize_provider()
