"""
Tests for API client module.
"""

import pytest
from aria.api_client import APIClient, APIConfig


def test_api_config_creation():
    """Test API config creation."""
    config = APIConfig(
        api_key="test-key",
        model="gemma-4-26b-a4b-it",
        temperature=0.7,
        max_tokens=2048,
    )
    
    assert config.api_key == "test-key"
    assert config.model == "gemma-4-26b-a4b-it"
    assert config.temperature == 0.7
    assert config.max_tokens == 2048


def test_api_client_initialization():
    """Test API client initialization."""
    config = APIConfig(api_key="test-key")
    client = APIClient(config)
    
    assert client.config.api_key == "test-key"
    assert client.available_models == []
    assert client.last_error is None


def test_api_client_fallback_response():
    """Test fallback response generation."""
    config = APIConfig(api_key="test-key")
    client = APIClient(config)
    client.last_error = "Test error"
    
    response = client._get_fallback_response()
    
    assert "API Error" in response
    assert "offline mode" in response.lower()
    assert "Test error" in response
