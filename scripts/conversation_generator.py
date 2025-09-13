import torch
import torchaudio as ta
from chatterbox.tts import ChatterboxTTS
from radio_effects_working import apply_radio_effects
import numpy as np
import soundfile as sf
import re
import os
import random

class ConversationGenerator:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading ChatterBox TTS model on {self.device}...")
        self.model = ChatterboxTTS.from_pretrained(device=self.device)

        # Define character voices and settings
        self.characters = {
            "Host": {
                "voice_file": "voices/loner_3.wav",
                "exaggeration": 1.2,
                "temperature": 0.8,
                "cfg_weight": 0.4,
                "radio_effect": "vintage_radio",
                "description": "Professional radio host"
            },
            "Bob": {
                "voice_file": "voices/voice_2.wav",  # Same voice but different settings
                "exaggeration": 0.9,
                "temperature": 1.0,
                "cfg_weight": 0.3,
                "radio_effect": "super_muffled",
                "description": "Guest caller (more muffled)"
            }
        }

        # Timing settings (ranges for randomization) - minimized for seamless audio
        self.pause_between_speakers = (0.0, 0.1)  # Minimal pause for different speakers
        self.pause_same_speaker = (0.0, 0.05)     # Almost no pause for same speaker continuing

    def parse_conversation(self, conversation_text):
        """Parse conversation text into speaker/dialogue pairs"""
        lines = conversation_text.strip().split('\n')
        parsed = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Look for "Speaker: dialogue" format
            match = re.match(r'^([^:]+):\s*(.+)$', line)
            if match:
                speaker = match.group(1).strip()
                dialogue = match.group(2).strip()
                parsed.append((speaker, dialogue))
            else:
                # If no speaker found, assume it's continuation of last speaker
                if parsed:
                    last_speaker = parsed[-1][0]
                    parsed.append((last_speaker, line))

        return parsed

    def generate_speaker_audio(self, speaker, text):
        """Generate TTS for a specific speaker"""
        if speaker not in self.characters:
            print(f"Warning: Unknown speaker '{speaker}', using Host settings")
            char_settings = self.characters["Host"]
        else:
            char_settings = self.characters[speaker]

        print(f"Generating {speaker}: '{text[:40]}...'")

        try:
            # Generate TTS with character-specific settings
            wav = self.model.generate(
                text,
                audio_prompt_path=char_settings["voice_file"],
                exaggeration=char_settings["exaggeration"],
                temperature=char_settings["temperature"],
                cfg_weight=char_settings["cfg_weight"]
            )

            return wav, char_settings["radio_effect"]

        except Exception as e:
            print(f"Error generating audio for {speaker}: {e}")
            return None, None

    def create_silence(self, duration_seconds, sample_rate):
        """Create silence audio segment"""
        samples = int(duration_seconds * sample_rate)
        return np.zeros(samples, dtype=np.float32)

    def apply_speaker_radio_effect(self, audio_data, sample_rate, effect_type, temp_file_prefix):
        """Apply radio effect to speaker audio"""
        # Save temp file
        temp_input = f"temp_{temp_file_prefix}_raw.wav"
        temp_output = f"temp_{temp_file_prefix}_processed.wav"

        try:
            # Save raw audio
            sf.write(temp_input, audio_data, sample_rate)

            # Apply radio effect
            if apply_radio_effects(temp_input, temp_output, effect_type, strength=0.8):
                # Load processed audio
                processed_audio, _ = sf.read(temp_output)

                # Clean up temp files
                os.unlink(temp_input)
                os.unlink(temp_output)

                return processed_audio
            else:
                print(f"Radio effect failed for {temp_file_prefix}")
                os.unlink(temp_input)
                return audio_data

        except Exception as e:
            print(f"Error applying radio effect: {e}")
            # Clean up any temp files
            for temp_file in [temp_input, temp_output]:
                try:
                    os.unlink(temp_file)
                except:
                    pass
            return audio_data

    def generate_conversation(self, conversation_file, output_file):
        """Generate full conversation with multiple speakers"""

        # Read conversation
        with open(conversation_file, "r", encoding="utf-8") as f:
            conversation_text = f.read()

        print(f"Parsing conversation from {conversation_file}...")
        parsed_conversation = self.parse_conversation(conversation_text)

        print(f"Found {len(parsed_conversation)} dialogue lines")

        # Generate audio for each line
        audio_segments = []
        sample_rate = self.model.sr
        last_speaker = None

        for i, (speaker, dialogue) in enumerate(parsed_conversation):
            print(f"\n[{i+1}/{len(parsed_conversation)}] Processing {speaker}...")

            # Generate TTS
            wav, radio_effect = self.generate_speaker_audio(speaker, dialogue)

            if wav is None:
                print(f"Skipping {speaker} due to generation error")
                continue

            # Convert to numpy if needed
            if hasattr(wav, 'cpu'):
                audio_data = wav.cpu().numpy().squeeze()
            else:
                audio_data = wav.squeeze()

            # Apply radio effect
            processed_audio = self.apply_speaker_radio_effect(
                audio_data, sample_rate, radio_effect, f"speaker_{i}_{speaker.lower()}"
            )

            # Add appropriate pause with randomization
            if last_speaker is None:
                # First line, no pause
                pause_duration = 0
            elif last_speaker == speaker:
                # Same speaker continuing - random short pause
                min_pause, max_pause = self.pause_same_speaker
                pause_duration = random.uniform(min_pause, max_pause)
            else:
                # Different speaker - random medium pause
                min_pause, max_pause = self.pause_between_speakers
                pause_duration = random.uniform(min_pause, max_pause)

            if pause_duration > 0:
                silence = self.create_silence(pause_duration, sample_rate)
                audio_segments.append(silence)

            audio_segments.append(processed_audio)
            last_speaker = speaker

        # Combine all segments
        print("\nCombining audio segments...")
        final_audio = np.concatenate(audio_segments)

        # Save final conversation
        sf.write(output_file, final_audio, sample_rate)

        print(f"\nConversation saved: {output_file}")
        print(f"Duration: {len(final_audio) / sample_rate:.2f} seconds")
        print(f"Characters used:")
        for speaker in set(speaker for speaker, _ in parsed_conversation):
            char_info = self.characters.get(speaker, {"description": "Unknown"})
            print(f"  - {speaker}: {char_info['description']}")

        return output_file

def main():
    """Generate conversation from test file"""

    if not os.path.exists("test_conversation.txt"):
        print("test_conversation.txt not found!")
        return

    generator = ConversationGenerator()

    output_file = "radio_conversation.wav"

    try:
        result = generator.generate_conversation("test_conversation.txt", output_file)

        if result:
            print(f"\n🎉 Conversation generated successfully!")
            print(f"🎧 Listen to: {result}")
            print(f"\nTo customize speakers:")
            print(f"  - Add more voice files to voices/ folder")
            print(f"  - Edit character settings in ConversationGenerator")
            print(f"  - Adjust timing with pause settings")

    except Exception as e:
        print(f"Error generating conversation: {e}")

if __name__ == "__main__":
    main()