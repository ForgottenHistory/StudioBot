#!/usr/bin/env python3
"""Jingle Preprocessing Script

Converts all jingle files to the correct format for the radio system:
- Sample rate: 24000 Hz (matches TTS output)
- Channels: Mono
- Format: WAV

Run this script whenever you add new jingle files.
"""

import os
import sys
import json
from pathlib import Path
import soundfile as sf
import numpy as np

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))


def convert_audio_format(input_path: Path, output_path: Path, target_sr: int = 24000) -> bool:
    """Convert audio file to target format (mono, specific sample rate)"""
    try:
        # Read the audio file
        audio_data, original_sr = sf.read(str(input_path))
        print(f"  Original: {original_sr} Hz, {audio_data.ndim} channels, {len(audio_data)} samples")

        # Convert to mono if stereo
        if audio_data.ndim > 1:
            # Average all channels to create mono
            audio_data = np.mean(audio_data, axis=1)
            print(f"  Converted to mono")

        # Resample if needed
        if original_sr != target_sr:
            # Simple resampling using scipy if available, otherwise basic interpolation
            try:
                from scipy import signal
                # Use scipy for high-quality resampling
                num_samples = int(len(audio_data) * target_sr / original_sr)
                audio_data = signal.resample(audio_data, num_samples)
                print(f"  Resampled: {original_sr} Hz -> {target_sr} Hz (scipy)")
            except ImportError:
                # Fallback to basic resampling
                ratio = original_sr / target_sr
                if ratio > 1:
                    # Downsample
                    step = int(ratio)
                    audio_data = audio_data[::step]
                    print(f"  Downsampled: {original_sr} Hz -> {target_sr} Hz (basic)")
                elif ratio < 1:
                    # Upsample
                    step = int(1 / ratio)
                    audio_data = np.repeat(audio_data, step)
                    print(f"  Upsampled: {original_sr} Hz -> {target_sr} Hz (basic)")

        # Save as WAV
        sf.write(str(output_path), audio_data, target_sr)
        print(f"  Saved: {target_sr} Hz, mono, {len(audio_data)} samples")
        return True

    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def process_jingles():
    """Process all jingle files in the configured directory"""

    # Load config to get jingle directory
    config_path = Path("config.json")
    if not config_path.exists():
        print("ERROR: config.json not found. Run this script from the project root.")
        return False

    with open(config_path, 'r') as f:
        config = json.load(f)

    # Get jingle configuration
    jingle_config = config.get('audio', {}).get('jingles', {})
    jingle_dir = Path(jingle_config.get('jingle_dir', 'content/audio/radio_jingle'))

    if not jingle_dir.exists():
        print(f"ERROR: Jingle directory not found: {jingle_dir}")
        return False

    print(f"Processing jingles in: {jingle_dir}")
    print("=" * 60)

    # Create processed directory
    processed_dir = jingle_dir
    processed_dir.mkdir(exist_ok=True)

    # Find all audio files
    audio_extensions = {'.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac'}
    jingle_files = []

    for file_path in jingle_dir.glob('*'):
        if file_path.is_file() and file_path.suffix.lower() in audio_extensions:
            if file_path.parent.name != "processed":  # Skip already processed files
                jingle_files.append(file_path)

    if not jingle_files:
        print("No jingle files found to process.")
        return True

    print(f"Found {len(jingle_files)} jingle files to process:")
    processed_count = 0
    failed_count = 0

    for jingle_file in jingle_files:
        print(f"\nProcessing: {jingle_file.name}")

        # Create output filename (always .wav)
        output_name = jingle_file.stem + "_processed.wav"
        output_path = processed_dir / output_name

        # Convert the file
        if convert_audio_format(jingle_file, output_path, target_sr=24000):
            processed_count += 1
            print(f"  [OK] Success: {output_name}")
        else:
            failed_count += 1
            print(f"  [FAIL] Failed: {jingle_file.name}")

    # Summary
    print("\n" + "=" * 60)
    print("PROCESSING COMPLETE")
    print(f"Processed: {processed_count}")
    print(f"Failed: {failed_count}")
    print(f"Output directory: {processed_dir}")

    if processed_count > 0:
        print("\nTo use the processed jingles:")
        print(f"1. Update config.json jingle_dir to: \"{processed_dir}\"")
        print("2. Or copy processed files back to the original directory")
        print("3. Restart your radio server")

    return failed_count == 0


if __name__ == "__main__":
    print("Radio Jingle Preprocessing Tool")
    print("=" * 60)

    try:
        success = process_jingles()
        if success:
            print("\nAll jingles processed successfully!")
        else:
            print("\nSome jingles failed to process. Check the errors above.")
    except KeyboardInterrupt:
        print("\nProcessing cancelled by user.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()