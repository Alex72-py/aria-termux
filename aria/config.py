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
        "provider": "",
        "api_key": "",
        "api_keys": {},
        "model": "",
        "temperature": 0.7,
        "max_tokens": 8192,
        "stream": False,
        "watch_mode": False,
        "guardian_mode": True,
        "auto_apply": False,
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
        self._migrate_config()
        self._load_from_env()
        
        return self.config

    def _migrate_config(self) -> None:
        """Backfill fields introduced in newer versions."""
        merged = self.DEFAULT_CONFIG.copy()
        merged.update(self.config or {})
        if not isinstance(merged.get("api_keys"), dict):
            merged["api_keys"] = {}
        if merged.get("api_key") and merged.get("provider"):
            merged["api_keys"].setdefault(merged["provider"], merged["api_key"])
        self.config = merged
    
    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        env_key = os.getenv("ARIA_API_KEY")
        if env_key:
            self.config["api_key"] = env_key
            logger.info("API key loaded from environment variable")

        env_provider = os.getenv("ARIA_PROVIDER")
        if env_provider:
            self.config["provider"] = env_provider.strip().lower()
            logger.info(f"Provider loaded from environment: {self.config['provider']}")

        env_model = os.getenv("ARIA_MODEL")
        if env_model:
            self.config["model"] = env_model
            logger.info(f"Model loaded from environment: {env_model}")

        # Provider-specific environment overrides
        env_map = {
            "google": os.getenv("GOOGLE_API_KEY"),
            "openrouter": os.getenv("OPENROUTER_API_KEY"),
            "nvidia_nim": os.getenv("NVIDIA_NIM_API_KEY"),
        }
        self.config.setdefault("api_keys", {})
        for provider, key in env_map.items():
            if key:
                self.config["api_keys"][provider] = key
                if provider == self.config.get("provider"):
                    self.config["api_key"] = key
    
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
        provider = self.config.get("provider") or ""
        key = self.config.get("api_key") or self.config.get("api_keys", {}).get(provider)
        if not key:
            logger.error("API key is not configured")
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
        lines = ["ARIA Configuration:\n"]
        for key, value in self.config.items():
            if key == "api_key":
                # Mask API key for security
                display_value = value[:10] + "..." if value else "(not set)"
            else:
                display_value = value
            lines.append(f"  {key}: {display_value}")
        
        return "\n".join(lines)
