"""YouTube Music Monitor

Handles monitoring YouTube Music for track changes and natural transitions.
"""

import asyncio
import aiohttp
import logging
from typing import Optional, Dict, Any, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class YouTubeMusicMonitor:
    def __init__(self, config, on_track_change: Optional[Callable[[Dict[str, Any], Optional[Dict[str, Any]]], None]] = None):
        self.config = config
        self.on_track_change = on_track_change

        # Configuration
        self.api_base_url = config.get('youtube_music.api_base_url', 'http://localhost:9863')
        self.auth_id = config.get('youtube_music.auth_id', 'default')
        self.check_interval = config.get('youtube_music.check_interval', 1.0)

        # State
        self.current_track_id = None
        self.current_track_info = None
        self.track_start_time = None  # When current track started being monitored
        self.accumulated_play_time = 0  # Total time actually played (excluding pauses)
        self.last_update_time = None  # When we last updated the play time
        self.was_playing = False  # Previous playing state
        # Queue system handles all pre-generation
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
                    logger.info("🔑 YouTube Music authentication successful")
                    return True
                else:
                    logger.error(f"❌ Authentication failed: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ Error getting access token: {e}")
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

            if not self.access_token:
                if not await self.get_access_token():
                    return None

            headers = self.get_auth_headers()

            async with self.session.get(f"{self.api_base_url}/api/v1/song", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.normalize_song_data(data)
                elif response.status == 401:
                    logger.info("🔑 Token expired, refreshing...")
                    if await self.get_access_token():
                        headers = self.get_auth_headers()
                        async with self.session.get(f"{self.api_base_url}/api/v1/song", headers=headers) as retry_response:
                            if retry_response.status == 200:
                                data = await retry_response.json()
                                return self.normalize_song_data(data)
                elif response.status == 204:
                    # No song currently playing
                    return None

        except Exception as e:
            logger.error(f"❌ Error fetching song info: {e}")

        return None

    def normalize_song_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize song data from API response"""
        normalized = {
            "id": data.get("videoId", ""),
            "title": data.get("title", "Unknown"),
            "artist": data.get("artist", "Unknown Artist"),
            "album": data.get("album", ""),
            "thumbnail": data.get("imageSrc", ""),
            "duration_seconds": data.get("songDuration", 0),
            "current_time_seconds": data.get("elapsedSeconds", 0),
            "is_playing": data.get("isPaused", True) == False,
            "url": data.get("url", ""),
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

    def get_real_time_remaining(self, song_info: Dict[str, Any]) -> float:
        """Get actual time remaining from YouTube Music API (accounts for pauses automatically)"""
        duration = song_info.get('duration_seconds', 0)
        current_position = song_info.get('current_time_seconds', 0)

        if duration > 0:
            return max(0, duration - current_position)
        return 0

    async def start_monitoring(self):
        """Start monitoring YouTube Music for natural song endings (not manual skips)"""
        self.is_running = True
        logger.info(f"🎵 YouTube Music monitor started - detecting natural song transitions")

        while self.is_running:
            try:
                song_info = await self.get_current_song()

                if song_info:
                    track_id = f"{song_info['id']}_{song_info['title']}_{song_info['artist']}"

                    # Check for track change
                    if self.current_track_id != track_id:
                        old_track = self.current_track_info
                        old_start_time = self.track_start_time

                        # Update current track
                        self.current_track_id = track_id
                        self.current_track_info = song_info
                        self.track_start_time = datetime.now()

                        logger.info(f"🎵 Track changed to: {song_info['artist']} - {song_info['title']}")

                        # Check if this was a natural transition
                        if await self.was_natural_transition(old_track, old_start_time):
                            logger.info("🔥 Natural song transition detected - using queue content")
                            if self.on_track_change:
                                await self.on_track_change(song_info)
                        else:
                            logger.info("👤 Manual song change detected - skipping ad")

                    # Same track - update position info
                    elif self.current_track_info:
                        # Always update the current track info with latest position data
                        # so when it becomes old_track, it has the most recent position
                        self.current_track_info.update({
                            'current_time_seconds': song_info.get('current_time_seconds', 0),
                            'is_playing': song_info.get('is_playing', False)
                        })

                else:
                    # No song currently playing
                    if self.current_track_id is not None:
                        logger.info("⏹️  No song currently playing")
                        self.current_track_id = None
                        self.current_track_info = None

            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")

            await asyncio.sleep(self.check_interval)

    async def was_natural_transition(self, old_track: Optional[Dict[str, Any]], track_start_time: Optional[datetime]) -> bool:
        """Determine if this was a natural song transition or manual skip using real-time API data"""
        if not old_track or not track_start_time:
            return False  # First song or missing timing info

        try:
            old_duration = old_track.get('duration_seconds', 0)
            old_track_id = old_track.get('id')

            logger.info(f"   Checking transition for: {old_track.get('title', 'Unknown')} (Duration: {old_duration}s)")

            # Get the current API state to see what YouTube Music thinks the position was
            # right before/during the transition
            try:
                current_song = await self.get_current_song()
                if current_song:
                    current_track_id = current_song.get('id')

                    # If we're still on the same track, use current position
                    if current_track_id == old_track_id:
                        current_position = current_song.get('current_time_seconds', 0)
                        logger.info(f"   Current API position (same track): {current_position:.1f}s / {old_duration}s")

                        if old_duration > 0:
                            time_remaining = old_duration - current_position
                            logger.info(f"   Time remaining: {time_remaining:.1f}s")

                            if time_remaining <= 30:  # Natural transition if near end
                                logger.info("   → Natural transition (currently near end)")
                                return True
                            else:
                                logger.info("   → Manual skip (not near end)")
                                return False
                    else:
                        # Track already changed, use the last known position from old_track
                        # But this should be more recent than initial detection
                        last_known_position = old_track.get('current_time_seconds', 0)
                        logger.info(f"   Last known position before switch: {last_known_position:.1f}s / {old_duration}s")

                        if old_duration > 0:
                            time_remaining_at_switch = old_duration - last_known_position
                            logger.info(f"   Time remaining at switch: {time_remaining_at_switch:.1f}s")

                            # If the last known position was within 30 seconds of the end, likely natural
                            if time_remaining_at_switch <= 30:
                                logger.info("   → Natural transition (was near end)")
                                return True
                            else:
                                logger.info("   → Manual skip (was not near end)")
                                return False
                else:
                    # Fallback to old logic if API call fails
                    last_known_position = old_track.get('current_time_seconds', 0)
                    logger.info(f"   Fallback - last known position: {last_known_position:.1f}s / {old_duration}s")

                    if old_duration > 0:
                        time_remaining = old_duration - last_known_position
                        if time_remaining <= 30:
                            logger.info("   → Natural transition (fallback logic)")
                            return True
                        else:
                            logger.info("   → Manual skip (fallback logic)")
                            return False

            except Exception as e:
                logger.warning(f"Could not determine transition type: {e}")
                # Fallback to time-based calculation
                current_time = datetime.now()
                monitoring_duration = (current_time - track_start_time).total_seconds()

                # If we monitored for most of the song duration, likely natural
                if old_duration > 0 and monitoring_duration >= (old_duration * 0.7):  # 70% of song
                    logger.info(f"   → Natural transition (monitored {monitoring_duration:.1f}s of {old_duration}s song)")
                    return True
                else:
                    logger.info(f"   → Manual skip (only monitored {monitoring_duration:.1f}s of {old_duration}s song)")
                    return False

        except Exception as e:
            logger.error(f"Error calculating transition type: {e}")

        return False  # Default to manual when in doubt

    async def pause_playback(self) -> bool:
        """Pause YouTube Music playback"""
        try:
            if not self.access_token:
                if not await self.get_access_token():
                    return False

            headers = self.get_auth_headers()
            async with self.session.post(f"{self.api_base_url}/api/v1/pause", headers=headers) as response:
                if response.status == 204:
                    logger.info("⏸️  YouTube Music paused")
                    return True
                else:
                    logger.error(f"❌ Failed to pause: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"❌ Error pausing playback: {e}")
            return False

    async def resume_playback(self) -> bool:
        """Resume YouTube Music playback"""
        try:
            if not self.access_token:
                if not await self.get_access_token():
                    return False

            headers = self.get_auth_headers()
            async with self.session.post(f"{self.api_base_url}/api/v1/play", headers=headers) as response:
                if response.status == 204:
                    logger.info("▶️  YouTube Music resumed")
                    return True
                else:
                    logger.error(f"❌ Failed to resume: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"❌ Error resuming playback: {e}")
            return False

    async def skip_to_next(self) -> bool:
        """Skip to next track in YouTube Music"""
        try:
            if not self.access_token:
                if not await self.get_access_token():
                    return False

            headers = self.get_auth_headers()
            async with self.session.post(f"{self.api_base_url}/api/v1/next", headers=headers) as response:
                if response.status == 204:
                    logger.info("⏭️  Skipped to next track")
                    return True
                else:
                    logger.error(f"❌ Failed to skip: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"❌ Error skipping track: {e}")
            return False

    async def get_volume(self) -> Optional[int]:
        """Get current YouTube Music volume"""
        try:
            if not self.access_token:
                if not await self.get_access_token():
                    return None

            headers = self.get_auth_headers()
            async with self.session.get(f"{self.api_base_url}/api/v1/volume", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    volume = data.get('state', 80)
                    logger.debug(f"📊 Current volume: {volume}%")
                    return volume
                else:
                    logger.error(f"❌ Failed to get volume: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"❌ Error getting volume: {e}")
            return None

    async def set_volume(self, volume: int) -> bool:
        """Set YouTube Music volume (0-100)"""
        try:
            if not self.access_token:
                if not await self.get_access_token():
                    return False

            headers = self.get_auth_headers()
            payload = {"volume": volume}

            async with self.session.post(f"{self.api_base_url}/api/v1/volume",
                                       headers=headers, json=payload) as response:
                if response.status == 204:
                    logger.info(f"🔊 Volume set to {volume}%")
                    return True
                else:
                    logger.error(f"❌ Failed to set volume: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"❌ Error setting volume: {e}")
            return False

    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_running = False
        logger.info("🛑 YouTube Music monitor stopped")