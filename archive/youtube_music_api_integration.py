# YouTube Music API Integration for AI Radio Show
# Uses th-ch/youtube-music app's built-in API server
import asyncio
import aiohttp
import json
import time
import os
import sys
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta

# Set UTF-8 encoding for Windows console
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

class YouTubeMusicAPIMonitor:
    def __init__(self,
                 api_base_url: str = "http://localhost:9863",
                 auth_id: str = "default",
                 on_track_change: Optional[Callable[[Dict[str, Any]], None]] = None,
                 on_track_ending: Optional[Callable[[Dict[str, Any], int], None]] = None,
                 pre_generate_seconds: int = 30,
                 check_interval: float = 1.0):
        """
        Initialize YouTube Music API monitor

        Args:
            api_base_url: Base URL for th-ch YouTube Music API server
            auth_id: Auth ID for getting access token (default: "default")
            on_track_change: Callback function called when track changes
            on_track_ending: Callback function called when track is about to end
            pre_generate_seconds: How many seconds before track end to trigger pre-generation
            check_interval: How often to check the API (seconds)
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.auth_id = auth_id
        self.on_track_change = on_track_change
        self.on_track_ending = on_track_ending
        self.pre_generate_seconds = pre_generate_seconds
        self.check_interval = check_interval

        self.current_track_id = None
        self.current_track_info = None
        self.pre_generation_triggered = False
        self.is_running = False
        self.session = None
        self.access_token = None

    async def create_session(self):
        """Create HTTP session for API calls"""
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def close_session(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def get_access_token(self) -> bool:
        """Get access token for API authentication"""
        try:
            await self.create_session()

            async with self.session.post(f"{self.api_base_url}/auth/{self.auth_id}") as response:
                if response.status == 200:
                    data = await response.json()
                    self.access_token = data.get("accessToken")
                    print(f"🔑 Authentication successful")
                    return True
                else:
                    print(f"❌ Authentication failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Error getting access token: {e}")
            return False

    def get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers for API requests"""
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}

    async def get_current_song(self) -> Optional[Dict[str, Any]]:
        """Get current song information from th-ch API"""
        try:
            await self.create_session()

            # Ensure we have an access token
            if not self.access_token:
                if not await self.get_access_token():
                    return None

            headers = self.get_auth_headers()

            # Try both endpoints (old and new format)
            endpoints = ["/api/v1/song", "/api/v1/song-info"]

            for endpoint in endpoints:
                try:
                    async with self.session.get(f"{self.api_base_url}{endpoint}", headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            return self.normalize_song_data(data)
                        elif response.status == 401:
                            print("🔑 Token expired, refreshing...")
                            if await self.get_access_token():
                                headers = self.get_auth_headers()
                                async with self.session.get(f"{self.api_base_url}{endpoint}", headers=headers) as retry_response:
                                    if retry_response.status == 200:
                                        data = await retry_response.json()
                                        return self.normalize_song_data(data)
                except:
                    continue

        except Exception as e:
            print(f"❌ Error fetching song info: {e}")

        return None

    def normalize_song_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize song data from API response"""
        # Handle API response format based on Swagger spec
        normalized = {
            "id": data.get("videoId", ""),
            "title": data.get("title", "Unknown"),
            "artist": data.get("artist", "Unknown Artist"),
            "album": data.get("album", ""),
            "thumbnail": data.get("imageSrc", ""),
            "duration_seconds": data.get("songDuration", 0),
            "current_time_seconds": data.get("elapsedSeconds", 0),
            "is_playing": data.get("isPaused", True) == False,  # Inverted logic
            "url": data.get("url", ""),
            "views": data.get("views", 0),
            "upload_date": data.get("uploadDate", ""),
            "playlist_id": data.get("playlistId", ""),
            "media_type": data.get("mediaType", ""),
            "timestamp": datetime.now().isoformat()
        }

        return normalized

    def calculate_time_remaining(self, song_info: Dict[str, Any]) -> int:
        """Calculate time remaining in current song"""
        duration = song_info.get("duration_seconds", 0)
        current_time = song_info.get("current_time_seconds", 0)

        if duration > 0 and current_time >= 0:
            return max(0, duration - current_time)

        return 0

    async def start_monitoring(self):
        """Start monitoring YouTube Music API for track changes and endings"""
        self.is_running = True
        print(f"🎵 YouTube Music API monitor started (checking {self.api_base_url})")

        while self.is_running:
            try:
                song_info = await self.get_current_song()

                if song_info:
                    track_id = f"{song_info['id']}_{song_info['title']}_{song_info['artist']}"

                    # Check for track change
                    if self.current_track_id != track_id:
                        self.current_track_id = track_id
                        self.current_track_info = song_info
                        self.pre_generation_triggered = False

                        print(f"🎵 Track changed: {song_info['artist']} - {song_info['title']}")

                        if song_info['duration_seconds'] > 0:
                            duration_mins = song_info['duration_seconds'] // 60
                            duration_secs = song_info['duration_seconds'] % 60
                            print(f"   ⏱️  Duration: {duration_mins}:{duration_secs:02d}")

                        if self.on_track_change:
                            self.on_track_change(song_info)

                    # Check if we need to trigger pre-generation
                    if (song_info['is_playing'] and
                        not self.pre_generation_triggered and
                        song_info['duration_seconds'] > 0):

                        time_remaining = self.calculate_time_remaining(song_info)

                        if time_remaining <= self.pre_generate_seconds and time_remaining > 0:
                            self.pre_generation_triggered = True
                            print(f"🚀 Pre-generating content ({time_remaining}s remaining)")

                            if self.on_track_ending:
                                self.on_track_ending(song_info, time_remaining)

                else:
                    # No song info available
                    if self.current_track_id is not None:
                        print("⏹️  No song currently playing")
                        self.current_track_id = None
                        self.current_track_info = None
                        self.pre_generation_triggered = False

            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")

            await asyncio.sleep(self.check_interval)

    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_running = False
        print("🛑 YouTube Music API monitor stopped")

    async def cleanup(self):
        """Cleanup resources"""
        self.stop_monitoring()
        await self.close_session()

class RadioSystemAPIIntegration:
    """Enhanced integration class for the radio system using th-ch API"""

    def __init__(self,
                 api_base_url: str = "http://localhost:9863",
                 pre_generate_seconds: int = 30):
        self.monitor = YouTubeMusicAPIMonitor(
            api_base_url=api_base_url,
            on_track_change=self.handle_track_change,
            on_track_ending=self.handle_track_ending,
            pre_generate_seconds=pre_generate_seconds
        )
        self.track_history = []
        self.pending_generation = False

    def handle_track_change(self, track_info: Dict[str, Any]):
        """Handle track changes - integrate with your radio system here"""
        # Store in history
        self.track_history.append(track_info)

        # Keep only last 10 tracks
        if len(self.track_history) > 10:
            self.track_history.pop(0)

        print(f"📻 Radio system notified: New track")
        print(f"   🎵 {track_info['artist']} - {track_info['title']}")

        if track_info['duration_seconds'] > 0:
            duration_mins = track_info['duration_seconds'] // 60
            duration_secs = track_info['duration_seconds'] % 60
            print(f"   ⏱️  Duration: {duration_mins}:{duration_secs:02d}")

    def handle_track_ending(self, track_info: Dict[str, Any], seconds_remaining: int):
        """Handle track ending - trigger content pre-generation"""
        if self.pending_generation:
            return  # Already generating

        self.pending_generation = True
        print(f"🎯 Track ending in {seconds_remaining}s - starting content generation")
        print(f"   🎵 Current: {track_info['artist']} - {track_info['title']}")

        # Here you can integrate with your radio_server.py
        # Examples:
        # 1. Generate ads using OpenRouter API
        # 2. Create conversation content
        # 3. Prepare radio effects

        # Simulate content generation
        asyncio.create_task(self.generate_content_async(track_info, seconds_remaining))

    async def generate_content_async(self, track_info: Dict[str, Any], seconds_remaining: int):
        """Async content generation (placeholder)"""
        try:
            print(f"🔄 Generating content for transition after '{track_info['title']}'...")

            # Simulate generation time (replace with actual OpenRouter API call)
            await asyncio.sleep(2)

            print(f"✅ Content generated and ready!")
            # Here you could trigger your radio_server.py ad generation

        finally:
            self.pending_generation = False

    def get_current_track(self) -> Optional[Dict[str, Any]]:
        """Get the currently playing track"""
        return self.monitor.current_track_info

    def get_track_history(self) -> list:
        """Get recent track history"""
        return self.track_history.copy()

    async def start(self):
        """Start the integration"""
        try:
            await self.monitor.start_monitoring()
        finally:
            await self.monitor.cleanup()

# Example usage and testing
async def main():
    """Example usage of the API integration"""
    print("🚀 Starting YouTube Music API integration...")
    print("📝 Make sure th-ch YouTube Music app is running with API server plugin enabled")
    print("🌐 API server should be accessible at http://localhost:9863")
    print()

    integration = RadioSystemAPIIntegration()

    try:
        await integration.start()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    finally:
        await integration.monitor.cleanup()

if __name__ == "__main__":
    asyncio.run(main())