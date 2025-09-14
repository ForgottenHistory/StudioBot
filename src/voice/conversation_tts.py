"""Conversation TTS Handler

Handles multi-voice TTS generation for conversations with proper speaker separation.
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class ConversationTTSHandler:
    def __init__(self, voice_manager):
        self.voice_manager = voice_manager
        self.host_name = None
        self.guest_name = None

    def parse_conversation(self, conversation_text: str) -> List[Dict[str, str]]:
        """Parse conversation text into segments with speaker identification"""
        segments = []

        # Split by lines and identify speaker patterns
        lines = conversation_text.strip().split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Look for various speaker patterns and strip them out
            # Patterns: "HOST:", "GUEST:", "Name:", "{{hostname}} –", "Name –", etc.
            speaker_patterns = [
                r'^HOST:\s*(.+)',
                r'^GUEST:\s*(.+)',
                r'^([A-Z][a-zA-Z\s\.]+):\s*(.+)',  # "Name: text" (includes titles like Dr., Mr., etc.)
                r'^\{\{\w+\}\}\s*[–-]\s*(.+)',  # {{hostname}} – text
                r'^[A-Z][a-zA-Z\s]*[–-]\s*(.+)'  # Name – text
            ]

            text = None
            role = None

            for i, pattern in enumerate(speaker_patterns):
                match = re.match(pattern, line)
                if match:
                    # Handle different patterns based on capturing groups
                    if i == 2:  # "Name: text" pattern with two groups
                        speaker_name = match.group(1).strip()
                        text = match.group(2).strip()
                        # Determine role by alternating or by speaker name logic
                        role = "host" if len(segments) % 2 == 0 else "guest"
                    else:
                        text = match.group(1).strip()
                        # Determine role based on pattern and alternating logic
                        if i == 0:  # HOST: pattern
                            role = "host"
                        elif i == 1:  # GUEST: pattern
                            role = "guest"
                        else:  # Other patterns - use alternating
                            role = "host" if len(segments) % 2 == 0 else "guest"
                    break

            if text and role:
                # Clean stage directions from text for TTS
                clean_text = self._remove_stage_directions(text)

                segments.append({
                    "role": role,
                    "speaker": role.upper(),
                    "text": clean_text,  # This is the clean text WITHOUT name prefix or stage directions
                    "original_line": line  # Keep original for logging purposes
                })
            else:
                # If no speaker pattern, treat as continuation of previous speaker
                if segments:
                    # Clean stage directions from continuation text too
                    clean_continuation = self._remove_stage_directions(line)
                    segments[-1]["text"] += " " + clean_continuation
                else:
                    # Default to host if no previous speaker
                    clean_text = self._remove_stage_directions(line)
                    segments.append({
                        "role": "host",
                        "speaker": "HOST",
                        "text": clean_text
                    })

        return segments

    def generate_conversation_audio(self,
                                  conversation_text: str,
                                  host_personality: str,
                                  guest_personality: str) -> Optional[str]:
        """Generate multi-voice audio for a conversation"""

        try:
            # Parse conversation into segments
            segments = self.parse_conversation(conversation_text)

            if not segments:
                logger.error("No conversation segments found")
                return None

            logger.info(f"[CONVERSATION TTS] Parsed {len(segments)} segments")
            for i, segment in enumerate(segments):
                # Show the original line with personality name for better logging
                original = segment.get('original_line', f"{segment['role'].upper()}: {segment['text'][:50]}...")
                speaker_display = original[:80] + "..." if len(original) > 80 else original
                logger.info(f"  {i+1}. {speaker_display}")

            # Generate audio for each segment
            audio_files = []

            for i, segment in enumerate(segments):
                personality = host_personality if segment["role"] == "host" else guest_personality

                logger.info(f"[CONVERSATION TTS] Generating segment {i+1}/{len(segments)} ({segment['role']}: {personality})")

                # Generate TTS for this segment
                audio_file = self.voice_manager.generate_tts_audio(
                    segment["text"],
                    personality_name=personality
                )

                if audio_file:
                    audio_files.append(audio_file)
                    logger.info(f"✅ Generated: {Path(audio_file).name}")
                else:
                    logger.error(f"❌ Failed to generate audio for segment {i+1}")
                    return None

            # Stitch all segments together
            if len(audio_files) > 1:
                logger.info(f"[CONVERSATION TTS] Stitching {len(audio_files)} audio segments")

                # Convert file paths to the format expected by stitch_audio_segments
                segments = []
                for audio_file in audio_files:
                    segments.append({
                        "audio_url": f"/audio/{Path(audio_file).name}"
                    })

                final_audio = self.voice_manager.stitch_audio_segments(segments)

                # Clean up individual segment files
                for audio_file in audio_files:
                    try:
                        Path(audio_file).unlink(missing_ok=True)
                        logger.debug(f"Cleaned up: {Path(audio_file).name}")
                    except Exception as e:
                        logger.warning(f"Could not clean up {audio_file}: {e}")

                return final_audio
            elif len(audio_files) == 1:
                return audio_files[0]
            else:
                logger.error("No audio files generated")
                return None

        except Exception as e:
            logger.error(f"Error generating conversation audio: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _remove_stage_directions(self, text: str) -> str:
        """Remove stage directions in brackets from text for cleaner TTS"""
        import re

        # Remove content in square brackets like [forced baritone], [deadpan], etc.
        # Also handles nested brackets and various bracket styles
        cleaned = re.sub(r'\[([^\]]*)\]', '', text)

        # Clean up extra spaces that might be left behind
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        return cleaned