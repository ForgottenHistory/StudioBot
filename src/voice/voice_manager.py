"""Voice Management System

Handles TTS generation and voice configuration for radio personalities.
"""

import os
import time
from pathlib import Path
from typing import Optional, List
import torch
import torchaudio as ta
import numpy as np
import soundfile as sf
from chatterbox.tts import ChatterboxTTS
from scripts.radio_effects_working import apply_radio_effects
from src.voice.conversation_tts import ConversationTTSHandler
from src.audio.jingle_manager import JingleManager
from src.content.content_types import content_type_registry


class VoiceManager:
    def __init__(self, content_manager, config=None, temp_dir="temp_audio"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.content_manager = content_manager
        self.config = config

        # Ensure we use absolute path for temp directory
        self.temp_dir = Path(temp_dir)
        if not self.temp_dir.is_absolute():
            self.temp_dir = Path.cwd() / self.temp_dir
        self.temp_dir.mkdir(exist_ok=True)

        # Load TTS model
        print(f"[VOICE] Loading TTS model on {self.device}...")
        self.model = ChatterboxTTS.from_pretrained(device=self.device)

        # Build voice mapping
        self.voice_mapping = self._build_voice_mapping()

        # Initialize conversation TTS handler
        self.conversation_handler = ConversationTTSHandler(self)

        # Initialize jingle manager
        self.jingle_manager = JingleManager(config) if config else None
        if self.jingle_manager and self.jingle_manager.enabled:
            print(f"[VOICE] Jingle system initialized: {len(self.jingle_manager.jingle_files)} jingles loaded")
        elif config:
            print(f"[VOICE] Jingle system disabled in config")
        else:
            print(f"[VOICE] No config provided for jingle system")

    def _build_voice_mapping(self):
        """Build dynamic voice mapping from available voice files and personality roles"""
        voice_mapping = {}
        voices_dir = Path("voices")

        if not voices_dir.exists():
            print("[VOICE] Warning: voices directory not found")
            return self._get_default_voice_mapping()

        # Map roles to voice files and settings
        role_voice_config = {
            "main_host": {
                "voice_file": "voices/host.wav",
                "exaggeration": 1.2,
                "temperature": 0.8,
                "cfg_weight": 0.4,
                "radio_effect": "vintage_radio"
            },
            "frequent_caller": {
                "voice_file": "voices/frequent_caller.wav",
                "exaggeration": 1.3,
                "temperature": 0.9,
                "cfg_weight": 0.45,
                "radio_effect": "phone_call"
            },
            "expert_guest": {
                "voice_file": "voices/expert_guest.wav",
                "exaggeration": 1.1,
                "temperature": 0.7,
                "cfg_weight": 0.35,
                "radio_effect": "super_muffled"
            }
        }

        # Check which voice files actually exist and build mapping
        for role, config in role_voice_config.items():
            voice_file = Path(config["voice_file"])
            if voice_file.exists():
                voice_mapping[role] = config
                print(f"[VOICE] Mapped role '{role}' to {voice_file}")
            else:
                print(f"[VOICE] Warning: Voice file not found for role '{role}': {voice_file}")

        # Add fallback mappings for old voice types
        if any(voice_mapping.values()):
            voice_mapping["host"] = voice_mapping.get("main_host", list(voice_mapping.values())[0])
            voice_mapping["announcer"] = voice_mapping.get("expert_guest", list(voice_mapping.values())[0])

        return voice_mapping if voice_mapping else self._get_default_voice_mapping()

    def _get_default_voice_mapping(self):
        """Fallback voice mapping if no voice files are found"""
        return {
            "host": {
                "voice_file": "voices/voice_2.wav",
                "exaggeration": 1.2,
                "temperature": 0.8,
                "cfg_weight": 0.4,
                "radio_effect": "vintage_radio"
            },
            "announcer": {
                "voice_file": "voices/voice_2.wav",
                "exaggeration": 1.1,
                "temperature": 0.7,
                "cfg_weight": 0.35,
                "radio_effect": "super_muffled"
            }
        }

    def get_personality_voice_config(self, personality_name: str):
        """Get voice configuration for a personality - first from file, then fallback to role mapping"""
        personality = self.content_manager.personalities.get(personality_name.lower().replace(' ', '_'))

        if personality:
            # First priority: check if personality has voice_settings in their file
            if 'voice_settings' in personality.extra_data and personality.extra_data['voice_settings']:
                voice_settings = personality.extra_data['voice_settings']
                # Ensure all required fields are present
                config = {
                    "voice_file": voice_settings.get('voice_file', 'voices/host.wav'),
                    "exaggeration": voice_settings.get('exaggeration', 1.2),
                    "temperature": voice_settings.get('temperature', 0.8),
                    "cfg_weight": voice_settings.get('cfg_weight', 0.4),
                    "radio_effect": voice_settings.get('radio_effect', 'vintage_radio')
                }
                return config

            # Second priority: try to match by role
            if personality.role in self.voice_mapping:
                return self.voice_mapping[personality.role]

            # Third priority: fallback to voice field if it exists in mapping
            if personality.voice in self.voice_mapping:
                return self.voice_mapping[personality.voice]
        # Default fallback
        return self.voice_mapping.get("host", self.voice_mapping.get("announcer", list(self.voice_mapping.values())[0]))

    def generate_tts_audio(self, text, voice_config=None, personality_name=None):
        """Generate TTS audio with enhanced personality support"""
        if personality_name and not voice_config:
            voice_config = self.get_personality_voice_config(personality_name)
        elif not voice_config:
            voice_config = self.voice_mapping["host"]

        print(f"[VOICE] Generating TTS for {'personality: ' + personality_name if personality_name else 'default'}")
        print(f"[VOICE] Text: {text[:100]}{'...' if len(text) > 100 else ''}")
        print(f"[VOICE] Full text length: {len(text)} characters")
        print(f"[VOICE] TTS Settings:")
        print(f"  - Voice file: {voice_config['voice_file']}")
        print(f"  - Exaggeration: {voice_config['exaggeration']}")
        print(f"  - Temperature: {voice_config['temperature']}")
        print(f"  - CFG Weight: {voice_config['cfg_weight']}")
        print(f"  - Radio Effect: {voice_config['radio_effect']}")

        try:
            # Generate TTS
            wav = self.model.generate(
                text,
                audio_prompt_path=voice_config["voice_file"],
                exaggeration=voice_config["exaggeration"],
                temperature=voice_config["temperature"],
                cfg_weight=voice_config["cfg_weight"]
            )

            # Convert to numpy
            if hasattr(wav, 'cpu'):
                audio_data = wav.cpu().numpy().squeeze()
            else:
                audio_data = wav.squeeze()

            # Create temp files
            timestamp = int(time.time() * 1000)
            temp_raw = self.temp_dir / f"tts_{timestamp}_raw.wav"
            temp_processed = self.temp_dir / f"tts_{timestamp}_processed.wav"

            # Save raw audio
            sf.write(temp_raw, audio_data, self.model.sr)

            # Apply radio effects
            if apply_radio_effects(str(temp_raw), str(temp_processed),
                                 voice_config["radio_effect"], strength=0.8):
                temp_raw.unlink()
                return str(temp_processed)
            else:
                return str(temp_raw)

        except Exception as e:
            print(f"[VOICE] TTS generation error: {e}")
            return None

    def cleanup_old_files(self):
        """Clean up old temp audio files"""
        try:
            current_time = time.time()
            for file_path in self.temp_dir.glob("*.wav"):
                if current_time - file_path.stat().st_mtime > 3600:
                    file_path.unlink()
        except Exception as e:
            print(f"[VOICE] Cleanup error: {e}")

    def get_voice_info(self):
        """Get voice configuration information for display"""
        info = {
            "role_mappings": {},
            "personality_settings": {}
        }

        # Role-based mappings
        for role, config in self.voice_mapping.items():
            voice_file = Path(config['voice_file'])
            info["role_mappings"][role] = {
                "file": voice_file.name,
                "exists": voice_file.exists()
            }

        # Personality-specific settings
        for name, personality in self.content_manager.personalities.items():
            if 'voice_settings' in personality.extra_data and personality.extra_data['voice_settings']:
                voice_settings = personality.extra_data['voice_settings']
                voice_file = Path(voice_settings.get('voice_file', ''))
                info["personality_settings"][personality.name] = {
                    "file": voice_file.name,
                    "exists": voice_file.exists(),
                    "custom": True
                }
            else:
                info["personality_settings"][personality.name] = {
                    "custom": False
                }

        # Jingle system information
        if self.jingle_manager:
            info["jingles"] = self.jingle_manager.get_jingle_info()
        else:
            info["jingles"] = {"enabled": False}

        return info

    def stitch_audio_segments(self, audio_segments):
        """Stitch multiple audio segments into one complete conversation audio"""
        if not audio_segments:
            return None

        try:
            # Collect all audio file paths
            audio_files = []
            for segment in audio_segments:
                audio_url = segment.get('audio_url', '')
                if audio_url.startswith('/audio/'):
                    # Remove /audio/ prefix to get filename
                    filename = audio_url[7:]
                    audio_path = self.temp_dir / filename
                    if audio_path.exists():
                        audio_files.append(str(audio_path))

            if not audio_files:
                print("[VOICE] No valid audio files found for stitching")
                return None

            # Load and concatenate audio files
            combined_audio = []
            sample_rate = None

            for audio_file in audio_files:
                try:
                    audio_data, sr = sf.read(audio_file)
                    if sample_rate is None:
                        sample_rate = sr
                    elif sr != sample_rate:
                        # Resample if needed (basic implementation)
                        print(f"[VOICE] Warning: Sample rate mismatch in {audio_file}")
                        continue

                    combined_audio.append(audio_data)

                except Exception as e:
                    print(f"[VOICE] Error loading audio file {audio_file}: {e}")
                    continue

            if not combined_audio:
                print("[VOICE] No audio data could be loaded")
                return None

            # Concatenate all audio segments
            final_audio = np.concatenate(combined_audio)

            # Generate output filename
            timestamp = int(time.time())
            output_filename = f"conversation_complete_{timestamp}.wav"
            output_path = self.temp_dir / output_filename

            # Save the stitched audio
            sf.write(str(output_path), final_audio, sample_rate)

            print(f"[VOICE] Stitched conversation audio saved: {output_filename}")
            return str(output_path)

        except Exception as e:
            print(f"[VOICE] Error stitching audio segments: {e}")
            return None

    def generate_conversation_tts(self, conversation_text: str, host_personality: str, guest_personality: str, audio_effect: str = "vintage_radio") -> Optional[str]:
        """Generate multi-voice TTS for a conversation between two personalities"""
        # Generate the base conversation audio with specified effect
        conversation_audio = self.conversation_handler.generate_conversation_audio(
            conversation_text, host_personality, guest_personality, audio_effect
        )

        # Add jingles if enabled and conversation was successfully generated
        if conversation_audio and self.jingle_manager and self.jingle_manager.enabled:
            print(f"[VOICE] Adding jingles to conversation: {conversation_audio}")
            conversation_with_jingles = self.jingle_manager.add_jingles_to_conversation(
                conversation_audio, self.temp_dir
            )
            if conversation_with_jingles != conversation_audio:
                print(f"[VOICE] Jingles added successfully: {conversation_with_jingles}")
            else:
                print(f"[VOICE] No jingles were added")
            return conversation_with_jingles
        else:
            if not conversation_audio:
                print(f"[VOICE] No conversation audio to add jingles to")
            elif not self.jingle_manager:
                print(f"[VOICE] Jingle manager not initialized")
            elif not self.jingle_manager.enabled:
                print(f"[VOICE] Jingle system disabled")
            else:
                print(f"[VOICE] Unknown jingle issue")

        return conversation_audio

    def generate_personality_tts(self, text: str, personality: str) -> Optional[str]:
        """Generate TTS for a specific personality - wrapper for API compatibility"""
        return self.generate_tts_audio(text, personality_name=personality)

    def stitch_audio_files(self, audio_files: list) -> Optional[str]:
        """Stitch multiple audio files together - wrapper for API compatibility"""
        # Convert audio file URLs to actual file paths
        segments = []
        for audio_file in audio_files:
            if audio_file.startswith('/audio/'):
                filename = audio_file[7:]  # Remove '/audio/' prefix
                segments.append({'audio_url': audio_file})
            else:
                # Assume it's already a file path
                segments.append({'audio_url': f'/audio/{Path(audio_file).name}'})

        return self.stitch_audio_segments(segments)

    def generate_content_tts(self, content_type_name: str, content: str, personalities: List[str] = None) -> Optional[str]:
        """Generate TTS for any content type using the generic system"""
        # Get content type for audio settings
        content_type = content_type_registry.get(content_type_name)
        if not content_type:
            print(f"[VOICE] Unknown content type: {content_type_name}")
            return None

        # Get audio settings for this content type
        from src.content.content_types import ContentGenerationParams
        params = ContentGenerationParams(personalities=personalities)
        audio_settings = content_type.get_audio_settings(params)

        print(f"[VOICE] Generating {content_type.display_name} TTS")
        print(f"[VOICE] Audio effect: {audio_settings.effect_type}")
        print(f"[VOICE] Multi-voice: {audio_settings.multi_voice}")

        if audio_settings.multi_voice and personalities and len(personalities) >= 2:
            # Multi-voice generation (conversations, interviews)
            return self.generate_conversation_tts(content, personalities[0], personalities[1], audio_settings.effect_type)
        else:
            # Single voice generation (ads)
            personality = personalities[0] if personalities else audio_settings.personality_roles[0]
            voice_config = self.get_personality_voice_config(personality)

            # Override effect type for this content type
            voice_config["radio_effect"] = audio_settings.effect_type

            return self.generate_tts_audio(content, voice_config=voice_config, personality_name=personality)