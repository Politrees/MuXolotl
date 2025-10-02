"""Configuration management for MuXolotl
"""

import json
import os
from pathlib import Path


class Config:
    """Application configuration manager"""

    DEFAULT_CONFIG = {
        "theme": "dark",
        "last_output_dir": str(Path.home() / "Downloads"),
        "audio": {
            "default_format": "mp3",
            "default_codec": "auto",
            "default_bitrate": "192k",
            "default_sample_rate": "44100",
            "default_channels": "2",
        },
        "video": {
            "default_format": "mp4",
            "default_video_codec": "libx264",
            "default_audio_codec": "aac",
            "default_preset": "medium",
            "default_crf": "23",
            "default_video_bitrate": "auto",
            "default_audio_bitrate": "192k",
        },
        "advanced": {
            "hardware_acceleration": "auto",
            "thread_count": "auto",
            "overwrite_files": True,
            "preserve_metadata": True,
        },
    }

    def __init__(self, config_path="config.json"):
        """Initialize configuration"""
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, encoding="utf-8") as f:
                    loaded = json.load(f)
                    # Merge with defaults
                    return self._merge_configs(self.DEFAULT_CONFIG.copy(), loaded)
            except Exception:
                pass
        return self.DEFAULT_CONFIG.copy()

    def _merge_configs(self, base, overlay):
        """Recursively merge configurations"""
        for key, value in overlay.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                base[key] = self._merge_configs(base[key], value)
            else:
                base[key] = value
        return base

    def save(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save config: {e}")

    def get(self, key_path, default=None):
        """Get configuration value by path
        
        Args:
            key_path: Dot-separated path (e.g., "audio.default_format")
            default: Default value if not found
            
        Returns:
            Configuration value

        """
        keys = key_path.split(".")
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set(self, key_path, value):
        """Set configuration value by path
        
        Args:
            key_path: Dot-separated path
            value: Value to set

        """
        keys = key_path.split(".")
        config = self.config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value
