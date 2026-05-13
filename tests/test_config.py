"""
Tests for configuration manager module.
"""

import pytest
import tempfile
from pathlib import Path
from aria.config import ConfigManager


def test_config_manager_initialization():
    """Test config manager initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config.json"
        cm = ConfigManager(config_file=config_file)
        
        assert cm.config_file == config_file


def test_config_load_and_save():
    """Test loading and saving configuration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config.json"
        cm = ConfigManager(config_file=config_file)
        
        # Load (should create default)
        config = cm.load()
        assert config is not None
        
        # Modify and save
        cm.set("api_key", "test-key")
        assert cm.save()
        
        # Load again
        cm2 = ConfigManager(config_file=config_file)
        config2 = cm2.load()
        assert config2["api_key"] == "test-key"


def test_config_get_set():
    """Test get and set operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config.json"
        cm = ConfigManager(config_file=config_file)
        cm.load()
        
        cm.set("test_key", "test_value")
        assert cm.get("test_key") == "test_value"
        assert cm.get("nonexistent", "default") == "default"


def test_config_validation():
    """Test configuration validation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config.json"
        cm = ConfigManager(config_file=config_file)
        cm.load()
        
        # Invalid without API key
        assert not cm.validate()
        
        # Valid with API key
        cm.set("api_key", "test-key")
        assert cm.validate()


def test_config_reset():
    """Test configuration reset."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config.json"
        cm = ConfigManager(config_file=config_file)
        cm.load()
        
        cm.set("api_key", "test-key")
        cm.reset()
        
        assert cm.get("api_key") == ""
