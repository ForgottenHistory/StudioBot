"""Radio Server Core

Main server class that orchestrates all radio functionality.
"""

import os
import time
import logging
import threading
from pathlib import Path
from datetime import datetime

from src.content.content_manager import ContentManager
from src.content.content_generator import DynamicContentGenerator
from src.content.scheduler import RadioScheduler
from src.voice.voice_manager import VoiceManager
from src.config.config_manager import ConfigManager


class RadioServer:
    def __init__(self, config_file=None):
        print("[RADIO SERVER] Initializing Enhanced Radio Server...")

        # Load configuration first
        self.config = ConfigManager(config_file) if config_file else ConfigManager()

        # Setup logging first
        self._setup_logging()

        # Initialize core components using config
        paths_config = self.config.get_paths_config()
        self.content_manager = ContentManager(paths_config.get('content_dir', 'content'))
        self.voice_manager = VoiceManager(
            self.content_manager,
            paths_config.get('temp_audio_dir', 'temp_audio')
        )

        # Get OpenRouter API key from config
        self.openrouter_api_key = self.config.get_openrouter_api_key()
        if not self.openrouter_api_key:
            print("[ERROR] OPENROUTER_API_KEY not found in config or environment!")
        else:
            print("[RADIO SERVER] OpenRouter API key loaded")

        # Initialize content generator and scheduler
        self.content_generator = DynamicContentGenerator(
            self.openrouter_api_key,
            self.content_manager,
            self.config
        )

        scheduler_config = self.config.get_scheduler_config()
        self.scheduler = RadioScheduler(self.content_generator, self, scheduler_config)

        # Create directories with absolute paths from config
        self.generated_dir = Path(paths_config.get('generated_content_dir', 'generated_content'))
        if not self.generated_dir.is_absolute():
            self.generated_dir = Path.cwd() / self.generated_dir
        self.generated_dir.mkdir(exist_ok=True)

        print("[RADIO SERVER] Enhanced initialization complete")

    def _setup_logging(self):
        """Setup comprehensive logging for server activity"""
        paths_config = self.config.get_paths_config()
        logs_dir = Path(paths_config.get('logs_dir', 'logs'))
        if not logs_dir.is_absolute():
            logs_dir = Path.cwd() / logs_dir
        logs_dir.mkdir(exist_ok=True)

        # Setup main server logger
        self.logger = logging.getLogger('radio_server')
        self.logger.setLevel(logging.INFO)

        # Create file handler with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"radio_server_{timestamp}.log"
        file_handler = logging.FileHandler(log_file)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Also log to console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        self.logger.info("Enhanced Radio Server logging initialized")
        self.logger.info(f"Log file: {log_file}")

    def log_generation(self, generation_type, content, **metadata):
        """Log all content generation with metadata"""
        # Log to main logger
        self.logger.info(f"GENERATION - {generation_type.upper()}: {content[:50]}...")

        # Save detailed log to generated_content
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{generation_type}_{timestamp}.txt"
        log_file = self.generated_dir / filename

        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"# {generation_type.title()}\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Type: {generation_type}\n")

            # Write metadata
            for key, value in metadata.items():
                f.write(f"{key.title()}: {value}\n")

            f.write(f"\n--- CONTENT ---\n")
            f.write(f"{content}\n")

        self.logger.info(f"Detailed log saved: {filename}")

    def start_automation(self):
        """Start the automatic content generation"""
        self.scheduler.start_scheduler()

    def stop_automation(self):
        """Stop the automatic content generation"""
        self.scheduler.stop_scheduler()

    def cleanup_old_files(self):
        """Clean up old temp audio files"""
        self.voice_manager.cleanup_old_files()

    def get_status(self):
        """Get server status information"""
        return {
            "status": "running",
            "server": "Enhanced AI Radio Server",
            "time": datetime.now().isoformat(),
            "tts_device": self.voice_manager.device,
            "openrouter_available": bool(self.openrouter_api_key),
            "topics_loaded": len(self.content_manager.topics),
            "personalities_loaded": len(self.content_manager.personalities),
            "scheduler_running": self.scheduler.is_running
        }

    def get_generated_content_list(self):
        """List recently generated content"""
        generated_files = []
        for file_path in self.generated_dir.glob("*.txt"):
            stat = file_path.stat()
            generated_files.append({
                "filename": file_path.name,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })

        # Sort by modification time (newest first)
        generated_files.sort(key=lambda x: x["modified"], reverse=True)

        return {
            "generated_content": generated_files,
            "total_files": len(generated_files)
        }

    def print_startup_info(self):
        """Print server startup information"""
        print("\n[RADIO SERVER] Starting Enhanced Radio Server...")
        print("[RADIO SERVER] Available endpoints:")
        print("  GET  / - Server status")
        print("  GET  /topics - List available topics")
        print("  GET  /personalities - List available personalities")
        print("  GET  /generate/dynamic_ad?topic=food&personality=crazy_larry")
        print("  GET  /generate/dynamic_conversation?host=chuck&guest=larry&topic=tech")
        print("  POST /generate/custom_tts - Generate TTS for custom text with personality voice")
        print("  POST /scheduler/start - Start automatic content generation")
        print("  POST /scheduler/stop - Stop automatic content generation")
        print("  GET  /scheduler/status - Check scheduler status")
        print("  GET  /generated_content - List auto-generated content")
        print("")
        print("Dynamic Features:")
        print(f"  - {len(self.content_manager.topics)} topics loaded")
        print(f"  - {len(self.content_manager.personalities)} personalities loaded")
        print(f"  - {len(self.voice_manager.voice_mapping)} voice mappings configured")
        print("  - Automatic content generation with timer")
        print("  - Personality-driven conversations with role-based voices")
        print("")

        # Voice configuration info
        voice_info = self.voice_manager.get_voice_info()
        print("Voice Configuration:")
        print("  Role-based mappings:")
        for role, info in voice_info["role_mappings"].items():
            exists = "[OK]" if info["exists"] else "[MISSING]"
            print(f"    {exists} {role}: {info['file']}")

        print("  Personality-specific settings:")
        for name, info in voice_info["personality_settings"].items():
            if info["custom"]:
                exists = "[OK]" if info["exists"] else "[MISSING]"
                print(f"    {exists} {name}: {info['file']} (custom settings)")
            else:
                print(f"    - {name}: using role defaults")

        print("")
        print("Example:")
        print("  curl 'http://localhost:5000/generate/dynamic_ad?topic=food_and_restaurants&personality=crazy_larry'")


def start_background_cleanup(radio_server):
    """Background task to clean up old files"""
    while True:
        time.sleep(1800)  # Run every 30 minutes
        radio_server.cleanup_old_files()