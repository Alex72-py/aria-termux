"""
Configuration management for ARIA.

Handles loading, saving, and validating configuration files.
Supports both JSON and environment variable configuration.
"""

import json
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages ARIA configuration."""
    
    DEFAULT_CONFIG_DIR = Path.home() / ".aria"
    DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"
    
    DEFAULT_CONFIG = {
        "api_key": "",
        "model": "gemma-4-26b-a4b-it",
        "temperature": 0.7,
        "max_tokens": 2048,
        "watch_mode": False,
        "guardian_mode": True,
        "created_at": None,
        "updated_at": None,
    }
    
    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Custom config file path
        """
        self.config_file = config_file or self.DEFAULT_CONFIG_FILE
        self.config: Dict[str, Any] = {}
        self._ensure_config_dir()
    
    def _ensure_config_dir(self) -> None:
        """Ensure configuration directory exists."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Config directory ensured: {self.config_file.parent}")
    
    def load(self) -> Dict[str, Any]:
        """
        Load configuration from file or environment.
        
        Returns:
            Configuration dictionary
        """
        # Try loading from file first
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    self.config = json.load(f)
                logger.info(f"Configuration loaded from {self.config_file}")
            except Exception as e:
                logger.error(f"Failed to load config file: {e}")
                self.config = self.DEFAULT_CONFIG.copy()
        else:
            self.config = self.DEFAULT_CONFIG.copy()
        
        # Override with environment variables
        self._load_from_env()
        
        return self.config
    
    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        env_key = os.getenv("ARIA_API_KEY")
        if env_key:
            self.config["api_key"] = env_key
            logger.info("API key loaded from environment variable")
        
        env_model = os.getenv("ARIA_MODEL")
        if env_model:
            self.config["model"] = env_model
            logger.info(f"Model loaded from environment: {env_model}")
    
    def save(self) -> bool:
        """
        Save configuration to file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.config["updated_at"] = datetime.now().isoformat()
            
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=2)
            
            logger.info(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config[key] = value
        logger.debug(f"Configuration set: {key} = {value}")
    
    def validate(self) -> bool:
        """
        Validate configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        if not self.config.get("api_key"):
            logger.error("API key is not configured")
            return False
        
        if not self.config.get("model"):
            logger.error("Model is not configured")
            return False
        
        return True
    
    def reset(self) -> None:
        """Reset configuration to defaults."""
        self.config = self.DEFAULT_CONFIG.copy()
        self.config["created_at"] = datetime.now().isoformat()
        logger.info("Configuration reset to defaults")
    
    def display(self) -> str:
        """
        Get formatted configuration display.
        
        Returns:
            Formatted configuration string
        """
        lines = ["📋 ARIA Configuration:\n"]
        for key, value in self.config.items():
            if key == "api_key":
                # Mask API key for security
                display_value = value[:10] + "..." if value else "(not set)"
            else:
                display_value = value
            lines.append(f"  {key}: {display_value}")
        
        return "\n".join(lines)
