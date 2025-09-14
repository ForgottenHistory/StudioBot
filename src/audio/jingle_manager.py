"""Radio Jingle Manager

Handles loading and random selection of radio jingles for intro/outro.
"""

import os
import random
import logging
from pathlib import Path
from typing import List, Optional
import soundfile as sf
import numpy as np

logger = logging.getLogger(__name__)


class JingleManager:
    def __init__(self, config: dict):
        self.config = config
        self.jingle_config = config.get('audio', {}).get('jingles', {})
        self.enabled = self.jingle_config.get('enabled', True)
        self.jingle_dir = Path(self.jingle_config.get('jingle_dir', 'content/audio/radio_jingle'))
        self.volume = self.jingle_config.get('volume', 0.7)
        self.add_intro = self.jingle_config.get('add_intro', True)
        self.add_outro = self.jingle_config.get('add_outro', True)
        # Small overlap for smooth transitions (in seconds)
        self.overlap_duration = self.jingle_config.get('overlap_duration', 0.2)

        # Load available jingle files
        self.jingle_files = self._load_jingle_files()

        if self.enabled:
            logger.info(f"[JINGLE] Loaded {len(self.jingle_files)} jingle files from {self.jingle_dir}")
        else:
            logger.info("[JINGLE] Jingle system disabled")

    def _load_jingle_files(self) -> List[Path]:
        """Load all audio files from the jingle directory"""
        if not self.jingle_dir.exists():
            logger.warning(f"[JINGLE] Directory not found: {self.jingle_dir}")
            return []

        audio_extensions = {'.mp3', '.wav', '.ogg', '.flac', '.m4a'}
        jingle_files = []

        for file_path in self.jingle_dir.glob('*'):
            if file_path.is_file() and file_path.suffix.lower() in audio_extensions:
                jingle_files.append(file_path)

        return jingle_files

    def get_random_jingle(self) -> Optional[Path]:
        """Get a random jingle file"""
        if not self.enabled or not self.jingle_files:
            return None

        jingle = random.choice(self.jingle_files)
        logger.debug(f"[JINGLE] Selected: {jingle.name}")
        return jingle

    def _crossfade_overlap(self, audio1: np.ndarray, audio2: np.ndarray, sample_rate: int) -> np.ndarray:
        """Create a crossfade overlap between two audio segments"""
        overlap_samples = int(self.overlap_duration * sample_rate)

        if overlap_samples <= 0 or overlap_samples >= min(len(audio1), len(audio2)):
            # If overlap is too small or too large, just concatenate
            return np.concatenate([audio1, audio2])

        # Split the segments for overlap
        audio1_main = audio1[:-overlap_samples]
        audio1_tail = audio1[-overlap_samples:]
        audio2_head = audio2[:overlap_samples]
        audio2_main = audio2[overlap_samples:]

        # Create fade curves
        fade_out = np.linspace(1.0, 0.0, overlap_samples)
        fade_in = np.linspace(0.0, 1.0, overlap_samples)

        # Apply crossfade
        crossfade_segment = (audio1_tail * fade_out) + (audio2_head * fade_in)

        # Combine all segments
        return np.concatenate([audio1_main, crossfade_segment, audio2_main])

    def add_jingles_to_conversation(self, conversation_audio_path: str, temp_dir: Path) -> Optional[str]:
        """Add intro and/or outro jingles to a conversation audio file"""
        if not self.enabled:
            return conversation_audio_path

        try:
            # Load the conversation audio
            conversation_audio, sample_rate = sf.read(conversation_audio_path)

            # Start with conversation audio
            final_audio = conversation_audio
            jingles_added = False

            # Add intro jingle with crossfade
            if self.add_intro:
                intro_jingle = self.get_random_jingle()
                if intro_jingle:
                    intro_audio, intro_sr = sf.read(str(intro_jingle))

                    # Check format (should be pre-processed to match)
                    if intro_sr != sample_rate:
                        logger.error(f"[JINGLE] Sample rate mismatch: {intro_sr} vs {sample_rate}. Run scripts/prepare_jingles.py")
                        return conversation_audio_path

                    if intro_audio.ndim != 1:
                        logger.error(f"[JINGLE] Audio should be mono. Run scripts/prepare_jingles.py")
                        return conversation_audio_path

                    # Apply volume adjustment
                    intro_audio = intro_audio * self.volume

                    # Crossfade intro with conversation
                    final_audio = self._crossfade_overlap(intro_audio, final_audio, sample_rate)
                    jingles_added = True
                    logger.info(f"[JINGLE] Added intro with crossfade: {intro_jingle.name}")

            # Add outro jingle with crossfade
            if self.add_outro:
                outro_jingle = self.get_random_jingle()
                if outro_jingle:
                    outro_audio, outro_sr = sf.read(str(outro_jingle))

                    # Check format (should be pre-processed to match)
                    if outro_sr != sample_rate:
                        logger.error(f"[JINGLE] Sample rate mismatch: {outro_sr} vs {sample_rate}. Run scripts/prepare_jingles.py")
                        return conversation_audio_path

                    if outro_audio.ndim != 1:
                        logger.error(f"[JINGLE] Audio should be mono. Run scripts/prepare_jingles.py")
                        return conversation_audio_path

                    # Apply volume adjustment
                    outro_audio = outro_audio * self.volume

                    # Crossfade conversation with outro
                    final_audio = self._crossfade_overlap(final_audio, outro_audio, sample_rate)
                    jingles_added = True
                    logger.info(f"[JINGLE] Added outro with crossfade: {outro_jingle.name}")

            # If no jingles were added, return original
            if not jingles_added:
                return conversation_audio_path

            # Generate output filename
            import time
            timestamp = int(time.time())
            output_filename = f"conversation_with_jingles_{timestamp}.wav"
            output_path = temp_dir / output_filename

            # Save the final audio
            sf.write(str(output_path), final_audio, sample_rate)

            logger.info(f"[JINGLE] Created conversation with jingles: {output_filename}")
            return str(output_path)

        except Exception as e:
            logger.error(f"[JINGLE] Error adding jingles: {e}")
            return conversation_audio_path

    def get_jingle_info(self) -> dict:
        """Get information about available jingles"""
        return {
            "enabled": self.enabled,
            "jingle_count": len(self.jingle_files),
            "jingle_dir": str(self.jingle_dir),
            "add_intro": self.add_intro,
            "add_outro": self.add_outro,
            "volume": self.volume,
            "overlap_duration": self.overlap_duration,
            "available_jingles": [f.name for f in self.jingle_files]
        }