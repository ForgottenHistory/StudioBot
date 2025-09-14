"""YouTube Music Content Generator

Handles ad and conversation generation, audio playback, and content breaks.
"""

import asyncio
import aiohttp
import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ContentGenerator:
    def __init__(self, config):
        self.config = config
        self.radio_host = config.get('radio_server.host', 'localhost')
        self.radio_port = config.get('radio_server.port', 5000)
        self.generation_timeout = config.get('ad_generation.generation_timeout', 45)
        self.youtube_music_monitor = None  # Will be set by integration

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
                await self.execute_immediate_content_break(new_track_info, audio_url, ad_content, "ad")
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
                            words = len(content.split())
                            estimated_duration = max(8, (words / 150) * 60)
                            await asyncio.sleep(estimated_duration)
                    else:
                        logger.error(f"❌ Audio file not found: {audio_file_path}")
                        # Still wait estimated duration
                        words = len(content.split())
                        estimated_duration = max(8, (words / 150) * 60)
                        await asyncio.sleep(estimated_duration)
            else:
                words = len(content.split())
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