"""Configuration Management System

Handles loading and managing radio server configuration from JSON files.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigManager:
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        if not self.config_file.is_absolute():
            self.config_file = Path.cwd() / self.config_file

        self.config = self._load_config()
        self._validate_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        if not self.config_file.exists():
            print(f"[CONFIG] Config file not found: {self.config_file}")
            print("[CONFIG] Using default configuration")
            return self._get_default_config()

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print(f"[CONFIG] Loaded configuration from {self.config_file}")
                return config
        except Exception as e:
            print(f"[CONFIG] Error loading config file: {e}")
            print("[CONFIG] Using default configuration")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if file is missing"""
        return {
            "server": {
                "host": "0.0.0.0",
                "port": 5000,
                "debug": True
            },
            "content": {
                "max_tokens": 2500,
                "temperature": 0.7,
                "model": "moonshotai/kimi-k2-0905"
            },
            "scheduler": {
                "ad_interval": 120,
                "conversation_interval": 300,
                "auto_start": False
            },
            "voice": {
                "tts_device": "auto",
                "default_voice": "host",
                "radio_effect_strength": 0.8
            },
            "paths": {
                "content_dir": "content",
                "temp_audio_dir": "temp_audio",
                "generated_content_dir": "generated_content",
                "logs_dir": "logs",
                "voices_dir": "voices"
            },
            "audio": {
                "sample_rate": 24000,
                "cleanup_interval": 1800,
                "max_file_age": 3600
            },
            "logging": {
                "level": "INFO",
                "console": True,
                "file": True,
                "max_log_files": 10
            },
            "gui": {
                "window_title": "Enhanced Radio Server Control",
                "window_size": [800, 600],
                "theme": "default",
                "auto_refresh_interval": 2000
            },
            "youtube_music": {
                "api_base_url": "http://localhost:9863",
                "auth_id": "default",
                "check_interval": 1.0
            },
            "radio_server": {
                "host": "localhost",
                "port": 5000
            },
            "ad_generation": {
                "generation_timeout": 45
            },
            "ad_break": {
                "enabled": True,
                "play_audio": True
            }
        }

    def _validate_config(self):
        """Validate configuration values"""
        # Check required environment variables
        if not self.get('content.openrouter_api_key'):
            api_key = os.getenv('OPENROUTER_API_KEY')
            if api_key:
                self.config.setdefault('content', {})['openrouter_api_key'] = api_key

        # Validate paths exist or can be created
        for path_key in ['content_dir', 'temp_audio_dir', 'generated_content_dir', 'logs_dir', 'voices_dir']:
            path_value = self.get(f'paths.{path_key}')
            if path_value:
                path = Path(path_value)
                if not path.is_absolute():
                    path = Path.cwd() / path
                path.mkdir(parents=True, exist_ok=True)

        # Validate voice device
        device = self.get('voice.tts_device')
        if device == 'auto':
            import torch
            actual_device = "cuda" if torch.cuda.is_available() else "cpu"
            self.config['voice']['tts_device'] = actual_device
            print(f"[CONFIG] Auto-detected TTS device: {actual_device}")

    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'server.port')"""
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any):
        """Set configuration value using dot notation"""
        keys = key_path.split('.')
        config = self.config

        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        config[keys[-1]] = value

    def save(self):
        """Save current configuration to file"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
            print(f"[CONFIG] Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"[CONFIG] Error saving configuration: {e}")

    def get_server_config(self) -> Dict[str, Any]:
        """Get server-specific configuration"""
        return self.get('server', {})

    def get_voice_config(self) -> Dict[str, Any]:
        """Get voice-specific configuration"""
        return self.get('voice', {})

    def get_scheduler_config(self) -> Dict[str, Any]:
        """Get scheduler-specific configuration"""
        return self.get('scheduler', {})

    def get_paths_config(self) -> Dict[str, Any]:
        """Get paths configuration"""
        return self.get('paths', {})

    def get_gui_config(self) -> Dict[str, Any]:
        """Get GUI configuration"""
        return self.get('gui', {})

    def get_openrouter_api_key(self) -> Optional[str]:
        """Get OpenRouter API key"""
        return self.get('content.openrouter_api_key') or os.getenv('OPENROUTER_API_KEY')

    def __repr__(self):
        return f"ConfigManager(config_file='{self.config_file}')"