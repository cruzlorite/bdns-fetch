# -*- coding: utf-8 -*-
"""
Configuration management for BDNS API client.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import json


class BDNSConfig:
    """Configuration manager for BDNS API client."""

    def __init__(self):
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file and environment variables."""
        config = {}

        # Load from config file
        config_file = self._find_config_file()
        if config_file and config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                config.update(json.load(f))

        # Override with environment variables
        env_config = self._load_from_env()
        config.update(env_config)

        return config

    def _find_config_file(self) -> Optional[Path]:
        """Find configuration file in standard locations."""
        search_paths = [
            Path.cwd() / "bdns-api.json",
            Path.cwd() / ".bdns-api.json",
            Path.home() / ".config" / "bdns-api" / "config.json",
            Path.home() / ".bdns-api.json",
        ]

        for path in search_paths:
            if path.exists():
                return path

        return None

    def _load_from_env(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        env_config = {}

        # API settings
        if base_url := os.getenv("BDNS_API_BASE_URL"):
            env_config["base_url"] = base_url

        if timeout := os.getenv("BDNS_API_TIMEOUT"):
            env_config["timeout"] = int(timeout)

        if rate_limit := os.getenv("BDNS_API_RATE_LIMIT"):
            env_config["rate_limit"] = int(rate_limit)

        # Output settings
        if default_format := os.getenv("BDNS_DEFAULT_FORMAT"):
            env_config["default_format"] = default_format

        if default_compression := os.getenv("BDNS_DEFAULT_COMPRESSION"):
            env_config["default_compression"] = default_compression

        return env_config

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self.config[key] = value

    def save_config(self, path: Optional[Path] = None) -> None:
        """Save current configuration to file."""
        if path is None:
            path = Path.cwd() / ".bdns-api.json"

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)


# Global config instance
config = BDNSConfig()
