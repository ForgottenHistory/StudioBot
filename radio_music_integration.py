# Radio Music Integration System
# Automatically generates ads before YouTube Music songs end

import asyncio
import aiohttp
import json
import os
import sys
import time
import requests
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
import logging

# Set UTF-8 encoding for Windows console
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

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

class ConfigManager:
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file {self.config_file} not found!")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            return {}

    def get(self, key_path: str, default=None):
        """Get config value using dot notation (e.g., 'youtube_music.api_base_url')"""
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

class YouTubeMusicMonitor:
    def __init__(self, config: ConfigManager, on_track_change: Optional[Callable[[Dict[str, Any], Optional[Dict[str, Any]]], None]] = None):
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
        self.ad_pre_generated = False  # Track if ad is ready
        self.pre_generated_ad = None  # Store pre-generated ad data
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

                        # SAVE the pre-generated ad before resetting
                        saved_pre_generated_ad = self.pre_generated_ad

                        # Update current track
                        self.current_track_id = track_id
                        self.current_track_info = song_info
                        self.track_start_time = datetime.now()
                        self.ad_pre_generated = False  # Reset ad generation for new track
                        self.pre_generated_ad = None  # Reset for new track

                        logger.info(f"🎵 Track changed to: {song_info['artist']} - {song_info['title']}")

                        # Check if this was a natural transition and we have a pre-generated ad
                        if await self.was_natural_transition(old_track, old_start_time):
                            logger.info("🔥 Natural song transition detected - using pre-generated ad")
                            if saved_pre_generated_ad:
                                logger.info(f"✅ Pre-generated ad available: {saved_pre_generated_ad.get('track_context', {}).get('title', 'Unknown')}")
                            else:
                                logger.info("⚠️ No pre-generated ad stored")

                            if self.on_track_change:
                                # Pass the SAVED pre-generated ad
                                await self.on_track_change(song_info, saved_pre_generated_ad)
                        else:
                            logger.info("👤 Manual song change detected - skipping ad")

                    # Same track - update position info and check pre-generation
                    elif self.current_track_info:
                        # Always update the current track info with latest position data
                        # so when it becomes old_track, it has the most recent position
                        self.current_track_info.update({
                            'current_time_seconds': song_info.get('current_time_seconds', 0),
                            'is_playing': song_info.get('is_playing', False)
                        })

                        # Check if we need to pre-generate an ad for the current song
                        if not self.ad_pre_generated:
                            await self.check_pre_generation(song_info)

                else:
                    # No song currently playing
                    if self.current_track_id is not None:
                        logger.info("⏹️  No song currently playing")
                        self.current_track_id = None
                        self.current_track_info = None
                        self.ad_pre_generated = False
                        self.pre_generated_ad = None

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

    async def check_pre_generation(self, song_info: Dict[str, Any]):
        """Check if we should pre-generate an ad for the current song using real-time API data"""
        try:
            duration = song_info.get('duration_seconds', 0)

            if duration > 60:  # Only for songs longer than 1 minute
                # Get REAL-TIME remaining time from API (accounts for pauses automatically)
                time_remaining = self.get_real_time_remaining(song_info)
                current_position = song_info.get('current_time_seconds', 0)
                is_playing = song_info.get('is_playing', False)

                # Pre-generate ad when 60 seconds remaining AND music is playing
                if time_remaining <= 60 and time_remaining > 0 and is_playing:
                    logger.info(f"🚀 Pre-generating ad (API says {time_remaining:.1f}s remaining, at {current_position:.1f}s)")
                    self.ad_pre_generated = True

                    # Generate ad in background via callback
                    if hasattr(self, 'ad_generator_callback'):
                        self.pre_generated_ad = await self.ad_generator_callback.pre_generate_ad_for_track(song_info)
                    else:
                        logger.error("❌ No ad generator callback set!")

        except Exception as e:
            logger.error(f"❌ Error checking pre-generation: {e}")

    async def pre_generate_ad(self, track_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Pre-generate ad content for upcoming transition"""
        try:
            # This will be implemented by the AdGenerator
            return {"track_info": track_info, "pre_generated": True}
        except Exception as e:
            logger.error(f"❌ Error pre-generating ad: {e}")
            return None

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

class AdGenerator:
    def __init__(self, config: ConfigManager):
        self.config = config
        self.radio_host = config.get('radio_server.host', 'localhost')
        self.radio_port = config.get('radio_server.port', 5000)
        self.generation_timeout = config.get('ad_generation.generation_timeout', 45)
        self.youtube_music_monitor = None  # Will be set by RadioMusicIntegration

    async def pre_generate_ad_for_track(self, track_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Pre-generate ad OR conversation content for upcoming natural transition (50/50 chance)"""
        import random

        try:
            # 50/50 random choice between ad and conversation
            generate_conversation = random.choice([True, False])

            if generate_conversation:
                logger.info(f"🎭 Pre-generating CONVERSATION for: {track_info['artist']} - {track_info['title']}")
                return await self.pre_generate_conversation(track_info)
            else:
                logger.info(f"📻 Pre-generating AD for: {track_info['artist']} - {track_info['title']}")
                return await self.pre_generate_ad(track_info)

        except Exception as e:
            logger.error(f"❌ Error in pre-generation: {e}")
            return None

    async def pre_generate_ad(self, track_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Pre-generate ad content for upcoming natural transition"""
        try:
            # Create ad context for pre-generation
            ad_context = {
                "current_track": {
                    "title": track_info['title'],
                    "artist": track_info['artist'],
                    "album": track_info.get('album', ''),
                },
                "ad_type": "natural_transition_pregenerated",
                "timestamp": datetime.now().isoformat()
            }

            # Generate ad via radio server
            ad_response = await self.call_radio_server_api(ad_context)

            if ad_response and ad_response.get('success'):
                logger.info("✅ Ad pre-generated successfully")
                return {
                    "content_type": "ad",
                    "audio_url": ad_response.get('audio_url', ''),
                    "content": ad_response.get('content', ''),
                    "generated_at": datetime.now().isoformat(),
                    "track_context": track_info
                }
            else:
                logger.error("❌ Ad pre-generation failed")
                return None

        except Exception as e:
            logger.error(f"❌ Error pre-generating ad: {e}")
            return None

    async def pre_generate_conversation(self, track_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Pre-generate conversation content for upcoming natural transition"""
        try:
            # Generate conversation first
            conversation_response = await self.call_conversation_api()

            if conversation_response and conversation_response.get('success'):
                # Now generate audio for the conversation using custom TTS
                content = conversation_response.get('content', '')
                host = conversation_response.get('host', 'Host')
                guest = conversation_response.get('guest', 'Guest')

                # Add track transition intro
                transition_intro = f"That was '{track_info['title']}' by {track_info['artist']}! "
                conversation_with_intro = transition_intro + content

                # Generate TTS audio for the complete conversation
                audio_response = await self.call_conversation_tts_api(conversation_with_intro, host)

                if audio_response and audio_response.get('success'):
                    logger.info("✅ Conversation pre-generated successfully")
                    return {
                        "content_type": "conversation",
                        "audio_url": audio_response.get('audio_url', ''),
                        "content": conversation_with_intro,
                        "host": host,
                        "guest": guest,
                        "generated_at": datetime.now().isoformat(),
                        "track_context": track_info
                    }
                else:
                    logger.error("❌ Conversation audio generation failed")
                    return None
            else:
                logger.error("❌ Conversation generation failed")
                return None

        except Exception as e:
            logger.error(f"❌ Error pre-generating conversation: {e}")
            return None

    async def call_conversation_api(self) -> Optional[Dict[str, Any]]:
        """Call the radio server API to generate conversation"""
        try:
            url = f"http://{self.radio_host}:{self.radio_port}/generate/dynamic_conversation"

            timeout = aiohttp.ClientTimeout(total=self.generation_timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json={}) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"❌ Conversation API failed: {response.status}")
                        return None

        except Exception as e:
            logger.error(f"❌ Error calling conversation API: {e}")
            return None

    async def call_conversation_tts_api(self, text: str, personality: str) -> Optional[Dict[str, Any]]:
        """Call the radio server API to generate TTS for conversation"""
        try:
            url = f"http://{self.radio_host}:{self.radio_port}/generate/custom_tts"

            payload = {
                "text": text,
                "personality": personality
            }

            timeout = aiohttp.ClientTimeout(total=self.generation_timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"❌ Conversation TTS API failed: {response.status}")
                        return None

        except Exception as e:
            logger.error(f"❌ Error calling conversation TTS API: {e}")
            return None

    async def handle_song_switch_with_pregenerated_content(self, new_track_info: Dict[str, Any], pre_generated_content: Dict[str, Any]):
        """Handle song switch with pre-generated content (ad or conversation) for instant playback"""
        try:
            content_type = pre_generated_content.get('content_type', 'ad')
            content_emoji = "🎭" if content_type == "conversation" else "📻"

            logger.info(f"{content_emoji} Using pre-generated {content_type.upper()} for: {new_track_info['artist']} - {new_track_info['title']}")

            audio_url = pre_generated_content.get('audio_url', '')
            content_text = pre_generated_content.get('content', '')

            if audio_url and content_text:
                # Execute immediate break with pre-generated content (ad or conversation)
                await self.execute_immediate_content_break(new_track_info, audio_url, content_text, content_type)
            else:
                logger.error("❌ Pre-generated ad missing audio_url or content")

        except Exception as e:
            logger.error(f"❌ Error using pre-generated ad: {e}")

    async def handle_song_switch(self, new_track_info: Dict[str, Any]):
        """Handle immediate song switch - interrupt new song with ad"""
        try:
            logger.info(f"🎯 Handling song switch to: {new_track_info['artist']} - {new_track_info['title']}")

            # Create ad context for the new song
            ad_context = {
                "current_track": {
                    "title": new_track_info['title'],
                    "artist": new_track_info['artist'],
                    "album": new_track_info.get('album', ''),
                },
                "ad_type": "song_switch_interrupt",
                "timestamp": datetime.now().isoformat()
            }

            # Generate ad immediately
            ad_response = await self.call_radio_server_api(ad_context)

            if ad_response and ad_response.get('success'):
                logger.info("✅ Ad generated for song switch")

                # Get audio URL and content
                audio_url = ad_response.get('audio_url', '')
                ad_content = ad_response.get('content', '')

                # Execute immediate ad break
                await self.execute_immediate_ad_break(new_track_info, audio_url, ad_content)
            else:
                logger.error("❌ Ad generation failed for song switch")

        except Exception as e:
            logger.error(f"❌ Error handling song switch: {e}")

    async def execute_immediate_content_break(self, new_track_info: Dict[str, Any], audio_url: str, content: str, content_type: str = "ad"):
        """Execute immediate content break when song switches - interrupt new song with content then resume"""
        ad_break_config = self.config.get('ad_break', {})

        if not ad_break_config.get('enabled', True):
            logger.info(f"🚫 Content break disabled in config")
            return

        try:
            # Step 1: Get current music volume BEFORE pausing
            current_volume = await self.youtube_music_monitor.get_volume()
            if current_volume is not None:
                logger.info(f"🔊 Music volume: {current_volume}%")
            else:
                current_volume = 80  # Default fallback volume
                logger.warning("⚠️ Could not get music volume, using 80% as fallback")

            # Step 2: IMMEDIATELY stop the new song that just started
            logger.info("🛑 STOPPING NEW SONG IMMEDIATELY")
            await self.youtube_music_monitor.pause_playback()
            await asyncio.sleep(0.1)
            await self.youtube_music_monitor.pause_playback()  # Double pause to be sure
            logger.info("⏸️ New song paused")

            # Step 2: Play the content immediately
            if ad_break_config.get('play_audio', True):
                content_emoji = "🎭" if content_type == "conversation" else "📻"
                logger.info(f"{content_emoji} PLAYING {content_type.upper()} BREAK")
                logger.info(f"🎙️ Content: {content[:100]}...")

                # Get audio file path
                if audio_url.startswith('/audio/'):
                    filename = audio_url.split('/')[-1]
                    audio_file_path = f"temp_audio/{filename}"

                    if os.path.exists(audio_file_path):
                        logger.info(f"🎵 Playing ad: {os.path.basename(audio_file_path)} at {current_volume}% volume")
                        success = await self.play_audio_file(audio_file_path, volume=current_volume)
                        if success:
                            logger.info("✅ Ad played successfully")
                        else:
                            logger.warning("⚠️ Audio playback failed, waiting estimated duration")
                            words = len(ad_content.split())
                            estimated_duration = max(8, (words / 150) * 60)
                            await asyncio.sleep(estimated_duration)
                    else:
                        logger.error(f"❌ Audio file not found: {audio_file_path}")
                        # Still wait estimated duration
                        words = len(ad_content.split())
                        estimated_duration = max(8, (words / 150) * 60)
                        await asyncio.sleep(estimated_duration)
            else:
                words = len(ad_content.split())
                estimated_duration = max(8, (words / 150) * 60)
                logger.info(f"⏱️ Simulating ad for {estimated_duration:.1f}s")
                await asyncio.sleep(estimated_duration)

            # Step 3: RESUME the same song that was interrupted
            logger.info("▶️ RESUMING THE SONG THAT WAS INTERRUPTED")
            resume_success = await self.youtube_music_monitor.resume_playback()

            if resume_success:
                logger.info("✅ Song resumed after ad break")
            else:
                logger.warning("⚠️ Resume failed")

            logger.info("✅ IMMEDIATE AD BREAK COMPLETE")

        except Exception as e:
            logger.error(f"❌ Error in immediate ad break: {e}")
            # Emergency - try to resume
            try:
                logger.info("🆘 Emergency recovery - resuming music")
                await self.youtube_music_monitor.resume_playback()
            except:
                logger.error("❌ Emergency recovery failed")

    async def play_audio_file(self, audio_file_path: str, volume: int = 80) -> bool:
        """Play audio file using pygame (preferred) or Windows system player"""
        try:
            # Try pygame first (better control and reliability)
            try:
                import pygame
                logger.info(f"🎮 Playing audio with pygame: {os.path.basename(audio_file_path)}")

                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=1024)
                pygame.mixer.music.load(audio_file_path)

                # Convert YouTube Music volume (0-100) to pygame volume (0.0-1.0)
                pygame_volume = volume / 100.0
                pygame.mixer.music.set_volume(pygame_volume)
                logger.info(f"🔊 Set pygame volume to {pygame_volume:.2f} (from {volume}%)")

                pygame.mixer.music.play()

                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.1)

                pygame.mixer.quit()
                logger.info("✅ Pygame audio playback completed")
                return True

            except ImportError:
                logger.info("⚠️ Pygame not available, trying system players")
            except Exception as e:
                logger.warning(f"⚠️ Pygame failed: {e}, trying system players")

            # Fallback to Windows system players
            if os.name == 'nt':  # Windows
                import subprocess

                # Try different Windows audio players
                players = [
                    ['powershell', '-c', f'(New-Object Media.SoundPlayer "{audio_file_path}").PlaySync()'],
                    ['start', '/wait', audio_file_path],  # Default system player
                ]

                for i, player_cmd in enumerate(players):
                    try:
                        logger.info(f"🖥️ Trying Windows player {i+1}: {player_cmd[0]}")
                        result = subprocess.run(player_cmd,
                                              capture_output=True,
                                              timeout=30,
                                              shell=True)
                        if result.returncode == 0:
                            logger.info(f"✅ Windows player {i+1} completed successfully")
                            return True
                        else:
                            logger.warning(f"⚠️ Windows player {i+1} failed with return code: {result.returncode}")
                    except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
                        logger.warning(f"⚠️ Windows player {i+1} failed: {e}")
                        continue

            logger.error("❌ All audio players failed")
            return False

        except Exception as e:
            logger.error(f"❌ Error playing audio: {e}")
            return False

    async def call_radio_server_api(self, ad_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call the radio server API to generate ad"""
        try:
            url = f"http://{self.radio_host}:{self.radio_port}/generate_ad"

            timeout = aiohttp.ClientTimeout(total=self.generation_timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=ad_context) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"📻 Radio server response: {result.get('message', 'Success')}")
                        return result
                    else:
                        logger.error(f"❌ Radio server error: {response.status}")
                        return None

        except asyncio.TimeoutError:
            logger.error(f"⏱️ Ad generation timeout ({self.generation_timeout}s)")
            return None
        except Exception as e:
            logger.error(f"❌ Error calling radio server: {e}")
            return None

class RadioMusicIntegration:
    def __init__(self, config_file: str = "config.json"):
        self.config = ConfigManager(config_file)
        self.ad_generator = AdGenerator(self.config)
        self.monitor = YouTubeMusicMonitor(
            self.config,
            on_track_change=self.handle_song_switch
        )

        # Connect ad generator to monitor for playback control
        self.ad_generator.youtube_music_monitor = self.monitor
        # Connect monitor to ad generator for pre-generation
        self.monitor.ad_generator_callback = self.ad_generator

    async def handle_song_switch(self, new_track_info: Dict[str, Any], pre_generated_ad: Optional[Dict[str, Any]] = None):
        """Handle immediate song switch detection"""
        logger.info(f"🔥 SONG SWITCH: {new_track_info['artist']} - {new_track_info['title']}")

        if pre_generated_ad:
            content_type = pre_generated_ad.get('content_type', 'ad')
            logger.info(f"✅ Using pre-generated {content_type} for instant playback")
            # Use pre-generated content for immediate playback
            await self.ad_generator.handle_song_switch_with_pregenerated_content(new_track_info, pre_generated_ad)
        else:
            logger.info("🚫 No pre-generated content available - skipping break to avoid delay")
            logger.info("   (Content will be pre-generated for the next natural transition)")

    async def start(self):
        """Start the radio music integration"""
        logger.info("🚀 Starting Radio Music Integration System")
        logger.info("📝 Make sure th-ch YouTube Music is running with API server enabled")
        logger.info("📻 Make sure radio_server.py is running")

        try:
            await self.monitor.start_monitoring()
        finally:
            await self.monitor.close_session()

    def stop(self):
        """Stop the integration"""
        self.monitor.stop_monitoring()

async def main():
    """Main entry point"""
    integration = RadioMusicIntegration()

    try:
        await integration.start()
    except KeyboardInterrupt:
        logger.info("👋 Shutting down...")
        integration.stop()
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(main())