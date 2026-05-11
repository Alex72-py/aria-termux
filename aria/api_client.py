"""
API Client for Google AI Studio with self-healing capabilities.

This module handles all interactions with the Google Generative AI API,
including automatic model detection, retry logic, and fallback mechanisms.
"""

import time
import logging
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
import google.generativeai as genai

logger = logging.getLogger(__name__)


@dataclass
class APIConfig:
    """Configuration for API client."""
    api_key: str
    model: str = "gemma-4-26b-a4b-it"
    temperature: float = 0.7
    max_tokens: int = 2048


class APIClient:
    """
    Google AI Studio API client with self-healing capabilities.
    
    Features:
    - Automatic model detection and switching
    - Exponential backoff retry logic
    - Graceful fallback to offline mode
    - Rate limit handling
    """
    
    def __init__(self, config: APIConfig):
        """Initialize API client with configuration."""
        self.config = config
        self.available_models: List[str] = []
        self.last_error: Optional[str] = None
        
        try:
            genai.configure(api_key=config.api_key)
            logger.info(f"API configured with model: {config.model}")
        except Exception as e:
            logger.error(f"Failed to configure API: {e}")
            self.last_error = str(e)
    
    def fetch_available_models(self) -> List[str]:
        """
        Fetch list of available models from API.
        
        Returns:
            List of available model names
        """
        try:
            models = genai.list_models()
            self.available_models = [m.name.replace("models/", "") for m in models]
            logger.info(f"Fetched {len(self.available_models)} available models")
            return self.available_models
        except Exception as e:
            logger.error(f"Failed to fetch available models: {e}")
            self.last_error = str(e)
            return self.available_models or ["gemma-4-26b-a4b-it"]
    
    def validate_model(self, model: str) -> bool:
        """
        Validate if model is available.
        
        Args:
            model: Model name to validate
            
        Returns:
            True if model is available, False otherwise
        """
        if not self.available_models:
            self.fetch_available_models()
        
        return model in self.available_models
    
    def generate_content(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        max_retries: int = 3,
    ) -> str:
        """
        Generate content using the API with self-healing.
        
        Args:
            prompt: User prompt
            system_instruction: System instruction for the model
            max_retries: Maximum number of retries
            
        Returns:
            Generated content or error message
        """
        for attempt in range(max_retries):
            try:
                # Validate model before attempting request
                if not self.validate_model(self.config.model):
                    logger.warning(f"Model {self.config.model} not available, fetching alternatives")
                    available = self.fetch_available_models()
                    if available:
                        self.config.model = available[0]
                        logger.info(f"Switched to model: {self.config.model}")
                
                # Create model instance
                model = genai.GenerativeModel(
                    model_name=self.config.model,
                    system_instruction=system_instruction,
                    generation_config=genai.types.GenerationConfig(
                        temperature=self.config.temperature,
                        max_output_tokens=self.config.max_tokens,
                    ),
                )
                
                # Generate response
                response = model.generate_content(prompt)
                self.last_error = None
                logger.info("Content generated successfully")
                return response.text
                
            except Exception as e:
                self.last_error = str(e)
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                
                if attempt < max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {max_retries} attempts failed")
        
        return self._get_fallback_response()
    
    def _get_fallback_response(self) -> str:
        """
        Get fallback response when API is unavailable.
        
        Returns:
            Fallback message with offline mode suggestion
        """
        return (
            f"❌ API Error: {self.last_error}\n\n"
            "Offline mode activated. Use `/kb <query>` to search the knowledge base.\n"
            "Try `/models` to check available models or `/config` to update settings."
        )
    
    def is_available(self) -> bool:
        """
        Check if API is available.
        
        Returns:
            True if API is available, False otherwise
        """
        try:
            genai.list_models()
            return True
        except Exception as e:
            logger.error(f"API availability check failed: {e}")
            return False
