"""YouTube Music Integration System - Refactored

Simplified orchestrator that coordinates YouTube Music monitoring and content generation.
"""

import asyncio
import os
import sys
import logging
from typing import Optional, Dict, Any

# Set UTF-8 encoding for Windows console
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from src.config.config_manager import ConfigManager
from src.youtube_music.monitor import YouTubeMusicMonitor
from src.youtube_music.content_generator import ContentGenerator

# Set up logging with UTF-8 support
class UTF8StreamHandler(logging.StreamHandler):
    def __init__(self):
        super().__init__(sys.stdout)

    def emit(self, record):
        try:
            msg = self.format(record)
            # Remove emojis for console output to avoid encoding issues
            msg_clean = ''.join(c for c in msg if ord(c) < 65536)
            self.stream.write(msg_clean + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('radio_integration.log', encoding='utf-8'),
        UTF8StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class YouTubeMusicIntegration:
    def __init__(self, config_file: str = "config.json"):
        self.config = ConfigManager(config_file)
        self.content_generator = ContentGenerator(self.config)
        self.monitor = YouTubeMusicMonitor(
            self.config,
            on_track_change=self.handle_song_switch
        )

        # Connect components
        self.content_generator.youtube_music_monitor = self.monitor
        self.monitor.ad_generator_callback = self.content_generator

    async def handle_song_switch(self, new_track_info: Dict[str, Any], pre_generated_ad: Optional[Dict[str, Any]] = None):
        """Handle immediate song switch detection"""
        logger.info(f"🔥 SONG SWITCH: {new_track_info['artist']} - {new_track_info['title']}")

        if pre_generated_ad:
            content_type = pre_generated_ad.get('content_type', 'ad')
            logger.info(f"✅ Using pre-generated {content_type} for instant playback")
            # Use pre-generated content for immediate playback
            await self.content_generator.handle_song_switch_with_pregenerated_content(new_track_info, pre_generated_ad)
        else:
            logger.info("🚫 No pre-generated content available - skipping break to avoid delay")
            logger.info("   (Content will be pre-generated for the next natural transition)")

    async def start(self):
        """Start the YouTube Music integration"""
        logger.info("🚀 Starting YouTube Music Integration System")
        logger.info("📝 Make sure th-ch YouTube Music is running with API server enabled")
        logger.info("📻 Make sure server.py is running")

        try:
            await self.monitor.start_monitoring()
        finally:
            await self.monitor.close_session()

    def stop(self):
        """Stop the integration"""
        self.monitor.stop_monitoring()


async def main():
    """Main entry point"""
    integration = YouTubeMusicIntegration()

    try:
        await integration.start()
    except KeyboardInterrupt:
        logger.info("👋 Shutting down...")
        integration.stop()
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(main())