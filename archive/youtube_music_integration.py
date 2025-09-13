# YouTube Music integration for AI Radio Show
import asyncio
import json
import os
import sys
import time
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta

# Set UTF-8 encoding for Windows console
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from winsdk.windows.media.control import \
    GlobalSystemMediaTransportControlsSessionManager as SessionManager

class YouTubeMusicMonitor:
    def __init__(self,
                 on_track_change: Optional[Callable[[Dict[str, Any]], None]] = None,
                 on_track_ending: Optional[Callable[[Dict[str, Any], int], None]] = None,
                 pre_generate_seconds: int = 30):
        """
        Initialize YouTube Music monitor

        Args:
            on_track_change: Callback function called when track changes
            on_track_ending: Callback function called when track is about to end
            pre_generate_seconds: How many seconds before track end to trigger pre-generation
        """
        self.on_track_change = on_track_change
        self.on_track_ending = on_track_ending
        self.pre_generate_seconds = pre_generate_seconds
        self.current_track = None
        self.track_start_time = None
        self.estimated_duration = None
        self.pre_generation_triggered = False
        self.is_running = False
        self.track_history = []  # Store timing data for learning

    def format_track_info(self, props, playback_info=None) -> Dict[str, Any]:
        """Format track information into a standard dictionary"""
        data = {
            "title": props.title or "Unknown",
            "artist": props.artist or "Unknown Artist",
            "album": props.album_title or "",
            "timestamp": datetime.now().isoformat(),
        }

        if playback_info:
            status = str(playback_info.playback_status)
            # Clean up the status string
            if "PLAYING" in status:
                data["status"] = "playing"
            elif "PAUSED" in status:
                data["status"] = "paused"
            else:
                data["status"] = "unknown"

        return data

    async def start_monitoring(self):
        """Start monitoring YouTube Music for track changes"""
        self.is_running = True
        manager = await SessionManager.request_async()
        print("🎵 YouTube Music monitor started")

        while self.is_running:
            try:
                for session in manager.get_sessions():
                    # Only monitor YouTube Music sessions
                    if (hasattr(session, 'source_app_user_model_id') and
                        'youtube-music' in session.source_app_user_model_id):

                        try:
                            props = await session.try_get_media_properties_async()
                            if props and props.title:
                                playback_info = session.get_playback_info()
                                track_info = self.format_track_info(props, playback_info)

                                # Check if track changed
                                track_id = f"{track_info['title']}_{track_info['artist']}"
                                if self.current_track != track_id:
                                    self.current_track = track_id
                                    print(f"🎵 Track changed: {track_info['artist']} - {track_info['title']}")

                                    # Call callback if provided
                                    if self.on_track_change:
                                        self.on_track_change(track_info)

                        except Exception as e:
                            # Silently handle errors
                            pass

                await asyncio.sleep(0.5)

            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(1)

    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_running = False
        print("🛑 YouTube Music monitor stopped")

class RadioSystemIntegration:
    """Integration class for the radio system"""

    def __init__(self):
        self.monitor = YouTubeMusicMonitor(on_track_change=self.handle_track_change)
        self.track_history = []

    def handle_track_change(self, track_info: Dict[str, Any]):
        """Handle track changes - integrate with your radio system here"""

        # Store in history
        self.track_history.append(track_info)

        # Keep only last 10 tracks
        if len(self.track_history) > 10:
            self.track_history.pop(0)

        # Here you can integrate with your radio system
        # For example, you could:
        # 1. Generate a comment about the song using OpenRouter
        # 2. Queue it for the next ad break
        # 3. Update the radio show's playlist

        print(f"📻 Radio system notified: New track playing")
        print(f"   🎵 {track_info['artist']} - {track_info['title']}")

        # Example: Generate ad content based on current song
        self.generate_song_commentary(track_info)

    def generate_song_commentary(self, track_info: Dict[str, Any]):
        """Generate commentary about the current song (placeholder)"""
        # This could integrate with your OpenRouter API
        # to generate relevant comments about the song
        print(f"   💬 Could generate commentary about: {track_info['title']}")

    def get_current_track(self) -> Optional[Dict[str, Any]]:
        """Get the currently playing track"""
        if self.track_history:
            return self.track_history[-1]
        return None

    def get_track_history(self) -> list:
        """Get recent track history"""
        return self.track_history.copy()

    async def start(self):
        """Start the integration"""
        await self.monitor.start_monitoring()

# Example usage
async def main():
    """Example usage of the integration"""
    integration = RadioSystemIntegration()

    try:
        await integration.start()
    except KeyboardInterrupt:
        integration.monitor.stop_monitoring()
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    asyncio.run(main())