"""
Configuration Manager
Handles application configuration with JSON persistence.
"""

import os
import json
from typing import List, Optional
from ..common import Config

class ConfigManager:
    """Manages application configuration with JSON persistence"""

    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self._config: Optional[Config] = None

    @property
    def config(self) -> Config:
        """Lazy load configuration"""
        if self._config is None:
            self._config = self.load_config()
        return self._config

    def load_config(self) -> Config:
        """Load configuration from JSON file with validation and defaults"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return Config.from_dict(data)
        except (json.JSONDecodeError, KeyError, TypeError):
            # Return default configuration on any error
            pass

        return Config()

    def save_config(self, config: Optional[Config] = None) -> bool:
        """Save configuration to JSON file with error handling"""
        if config is None:
            config = self.config

        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=4, ensure_ascii=False)
            self._config = config  # Update cached config
            return True
        except (IOError, OSError):
            return False

    def update_config(self, **kwargs) -> bool:
        """Update configuration fields and save"""
        config = self.config
        updated = False

        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
                updated = True

        if updated:
            return self.save_config(config)
        return False

    def reset_to_defaults(self) -> bool:
        """Reset configuration to defaults"""
        return self.save_config(Config())

    def validate_paths(self) -> List[str]:
        """Validate configuration paths and return list of issues"""
        issues = []
        config = self.config

        # Expand paths for validation
        git_dir = os.path.expanduser(config.git_dir)
        work_tree = os.path.expanduser(config.work_tree)

        if not os.path.exists(work_tree):
            issues.append(f"Work tree path does not exist: {work_tree}")

        if not os.path.isdir(work_tree):
            issues.append(f"Work tree path is not a directory: {work_tree}")

        # Check git directory if it exists
        if os.path.exists(git_dir) and not os.path.isdir(git_dir):
            issues.append(f"Git directory path exists but is not a directory: {git_dir}")

        return issues