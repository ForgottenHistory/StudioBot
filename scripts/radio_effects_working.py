import numpy as np
import soundfile as sf
import os
from pathlib import Path

def apply_radio_effects(input_file, output_file, style="vintage", strength=0.8):
    """Apply radio effects using manual DSP processing like your working version"""

    try:
        # Load audio
        audio_data, sample_rate = sf.read(input_file)

        # Ensure mono
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)

        print(f"[RADIO] Processing {input_file}")
        print(f"[RADIO] Audio: {len(audio_data)} samples at {sample_rate}Hz")

        if style == "vintage_radio":
            processed = apply_vintage_radio(audio_data, sample_rate, strength)
        elif style == "super_muffled":
            processed = apply_super_muffled(audio_data, sample_rate, strength)
        elif style == "telephone_quality":
            processed = apply_telephone_quality(audio_data, sample_rate, strength)
        elif style == "studio_interview":
            processed = apply_studio_interview(audio_data, sample_rate, strength)
        else:
            processed = apply_vintage_radio(audio_data, sample_rate, strength)

        # Normalize
        processed = normalize_audio(processed, target_peak=0.8)

        # Save
        sf.write(output_file, processed, sample_rate)
        print(f"[RADIO] Saved: {output_file}")

        return True

    except Exception as e:
        print(f"[RADIO] Error: {e}")
        return False

def apply_vintage_radio(audio_data, sample_rate, strength=0.8):
    """Apply vintage radio effect using manual frequency domain processing"""

    processed = audio_data.copy()

    if len(processed) < 100:
        return processed

    print("[RADIO] Applying vintage radio EQ...")

    # FFT processing
    fft_size = len(processed)
    freqs = np.fft.fftfreq(fft_size, 1/sample_rate)
    audio_fft = np.fft.fft(processed)
    freq_response = np.ones_like(freqs, dtype=complex)

    # Frequency limits for vintage radio
    hp_freq = 350.0 + (strength * 50.0)   # 350-400Hz highpass
    lp_freq = 4500.0 - (strength * 500.0)  # 4000-4500Hz lowpass

    # High-pass filter (remove low frequencies)
    for i, freq in enumerate(freqs):
        if abs(freq) < hp_freq:
            if abs(freq) > 0:
                rolloff = (abs(freq) / hp_freq) ** 3  # Steep rolloff
            else:
                rolloff = 0
            freq_response[i] *= rolloff

    # Low-pass filter (remove high frequencies)
    for i, freq in enumerate(freqs):
        if abs(freq) > lp_freq:
            rolloff = (lp_freq / abs(freq)) ** 2
            freq_response[i] *= rolloff

    # Mid-range boost for warmth and clarity
    boost_freq = 1200.0
    boost_width = 800.0
    boost_gain = 0.4 * strength

    for i, freq in enumerate(freqs):
        abs_freq = abs(freq)
        if hp_freq <= abs_freq <= lp_freq:
            boost = boost_gain * np.exp(-((abs_freq - boost_freq) / boost_width) ** 2)
            freq_response[i] *= (1 + boost)

    # Apply frequency response
    processed_fft = audio_fft * freq_response
    processed = np.real(np.fft.ifft(processed_fft))

    # Digital processing effects
    processed = apply_digital_effects(processed, sample_rate, strength)

    return processed

def apply_super_muffled(audio_data, sample_rate, strength=0.8):
    """Super muffled version - much more aggressive"""

    processed = audio_data.copy()

    if len(processed) < 100:
        return processed

    print("[RADIO] Applying super muffled...")

    # Much more aggressive filtering
    fft_size = len(processed)
    freqs = np.fft.fftfreq(fft_size, 1/sample_rate)
    audio_fft = np.fft.fft(processed)
    freq_response = np.ones_like(freqs, dtype=complex)

    hp_freq = 500.0   # Much higher
    lp_freq = 3200.0  # Much lower

    # Very steep filtering
    for i, freq in enumerate(freqs):
        abs_freq = abs(freq)

        # High-pass
        if abs_freq < hp_freq:
            if abs_freq > 0:
                rolloff = (abs_freq / hp_freq) ** 4  # Very steep
            else:
                rolloff = 0
            freq_response[i] *= rolloff

        # Low-pass
        if abs_freq > lp_freq:
            rolloff = (lp_freq / abs_freq) ** 3  # Very steep
            freq_response[i] *= rolloff

    # Apply
    processed_fft = audio_fft * freq_response
    processed = np.real(np.fft.ifft(processed_fft))

    # Heavy digital processing
    processed = apply_digital_effects(processed, sample_rate, strength * 1.2)  # More aggressive

    return processed

def apply_telephone_quality(audio_data, sample_rate, strength=0.8):
    """Classic telephone bandwidth"""

    processed = audio_data.copy()

    if len(processed) < 100:
        return processed

    print("[RADIO] Applying telephone quality...")

    # Telephone bandwidth: 600Hz - 3400Hz
    fft_size = len(processed)
    freqs = np.fft.fftfreq(fft_size, 1/sample_rate)
    audio_fft = np.fft.fft(processed)
    freq_response = np.ones_like(freqs, dtype=complex)

    hp_freq = 600.0
    lp_freq = 3400.0

    # Sharp telephone-style filtering
    for i, freq in enumerate(freqs):
        abs_freq = abs(freq)

        if abs_freq < hp_freq or abs_freq > lp_freq:
            # Outside telephone bandwidth - cut aggressively
            if abs_freq < hp_freq and abs_freq > 0:
                rolloff = (abs_freq / hp_freq) ** 6
            elif abs_freq > lp_freq:
                rolloff = (lp_freq / abs_freq) ** 4
            else:
                rolloff = 0
            freq_response[i] *= rolloff

    # Apply
    processed_fft = audio_fft * freq_response
    processed = np.real(np.fft.ifft(processed_fft))

    # Heavy compression for telephone effect
    processed = apply_digital_effects(processed, sample_rate, strength * 1.3)

    return processed

def apply_digital_effects(audio_data, sample_rate, strength=0.8):
    """Apply digital transfer effects like your working version"""

    processed = audio_data.copy()

    # 1. Bit depth reduction
    bit_depth = 14 - int(strength * 2)  # 12-14 bit
    max_val = 2**(bit_depth-1) - 1
    processed = np.round(processed * max_val) / max_val

    # 2. Digital compression
    threshold = 0.12 + (strength * 0.08)
    ratio = 1.5 + (strength * 0.8)  # 1.5-2.3

    compressed_mask = np.abs(processed) > threshold
    if np.any(compressed_mask):
        over_threshold = processed[compressed_mask]
        sign = np.sign(over_threshold)
        magnitude = np.abs(over_threshold)
        compressed_magnitude = threshold + (magnitude - threshold) / ratio
        processed[compressed_mask] = sign * compressed_magnitude

    # 3. Analog-style saturation
    saturation = 0.1 + (strength * 0.1)
    processed = np.tanh(processed * (1 + saturation)) / (1 + saturation)

    # 4. High-frequency smoothing
    if len(processed) > 10:
        alpha = 0.75 + (strength * 0.15)  # 0.75-0.9
        filtered = np.zeros_like(processed)
        filtered[0] = processed[0]
        for i in range(1, len(processed)):
            filtered[i] = alpha * filtered[i-1] + (1 - alpha) * processed[i]
        processed = filtered

    return processed

def apply_studio_interview(audio_data, sample_rate, strength=0.8):
    """Apply professional studio interview/podcast microphone effect"""

    processed = audio_data.copy()

    if len(processed) < 100:
        return processed

    print("[RADIO] Applying studio interview processing...")

    # 1. Professional microphone frequency response (wider than radio)
    fft_size = len(processed)
    freqs = np.fft.fftfreq(fft_size, 1/sample_rate)
    audio_fft = np.fft.fft(processed)
    freq_response = np.ones_like(freqs, dtype=complex)

    # Professional mic frequency range - much wider than radio
    hp_freq = 80.0   # Low-end rolloff (preserve bass)
    lp_freq = 12000.0  # High-end rolloff (crisp but not harsh)

    # Presence boost around speech frequencies
    presence_freq = 3000.0
    presence_boost = 1.0 + (strength * 0.3)  # Subtle boost

    for i, freq in enumerate(freqs):
        abs_freq = abs(freq)

        # Gentle high-pass (remove rumble)
        if abs_freq < hp_freq and abs_freq > 0:
            rolloff = (abs_freq / hp_freq) ** 0.5  # Gentle slope
            freq_response[i] *= rolloff

        # Gentle low-pass (remove harsh highs)
        if abs_freq > lp_freq:
            rolloff = (lp_freq / abs_freq) ** 1.5  # Gentle slope
            freq_response[i] *= rolloff

        # Presence boost for speech clarity
        if 2000 < abs_freq < 4000:
            boost = 1.0 + (presence_boost - 1.0) * np.exp(-((abs_freq - presence_freq) / 800) ** 2)
            freq_response[i] *= boost

    # Apply frequency shaping
    processed_fft = audio_fft * freq_response
    processed = np.real(np.fft.ifft(processed_fft))

    # 2. Studio-style compression (smooth and musical)
    threshold = 0.3
    ratio = 3.0  # Moderate compression

    compressed_mask = np.abs(processed) > threshold
    if np.any(compressed_mask):
        over_threshold = processed[compressed_mask]
        sign = np.sign(over_threshold)
        magnitude = np.abs(over_threshold)
        # Musical compression curve
        compressed_magnitude = threshold + (magnitude - threshold) / ratio
        processed[compressed_mask] = sign * compressed_magnitude

    # 3. Subtle tube-style warmth (less than radio)
    warmth = strength * 0.15  # Much subtler than radio
    processed = np.tanh(processed * (1 + warmth)) / (1 + warmth)

    # 4. Studio reverb simulation (very subtle room tone)
    if len(processed) > sample_rate // 10:  # Only if audio is long enough
        reverb_strength = strength * 0.1  # Very subtle
        delay_samples = int(sample_rate * 0.02)  # 20ms early reflection

        if delay_samples < len(processed):
            reverb = np.zeros_like(processed)
            reverb[delay_samples:] = processed[:-delay_samples] * reverb_strength
            processed = processed + reverb

    # 5. Gentle de-essing (reduce harsh S sounds)
    if sample_rate > 8000:  # Only for high quality audio
        # High-frequency gentle compression
        de_ess_freq = 6000.0
        fft_size = len(processed)
        freqs = np.fft.fftfreq(fft_size, 1/sample_rate)
        audio_fft = np.fft.fft(processed)

        for i, freq in enumerate(freqs):
            abs_freq = abs(freq)
            if abs_freq > de_ess_freq:
                # Gentle compression of sibilants
                de_ess_factor = 0.8 + (0.2 * (1 - strength))
                audio_fft[i] *= de_ess_factor

        processed = np.real(np.fft.ifft(audio_fft))

    return processed

def normalize_audio(audio_data, target_peak=0.8):
    """Normalize audio to target peak"""
    peak = np.max(np.abs(audio_data))
    if peak > 0:
        return audio_data * (target_peak / peak)
    return audio_data

def test_radio_effects():
    """Test the radio effects on your existing audio"""

    # Find audio files to test
    test_files = []

    if os.path.exists("chatterbox_test_output.wav"):
        test_files.append("chatterbox_test_output.wav")

    if os.path.exists("radio_ads_final"):
        for file in os.listdir("radio_ads_final"):
            if file.endswith("_raw.wav"):
                test_files.append(f"radio_ads_final/{file}")

    if not test_files:
        print("No audio files found to test!")
        return

    # Create output directory
    os.makedirs("radio_working", exist_ok=True)

    # Test different styles
    styles = [
        ("vintage_radio", "Classic vintage radio"),
        ("super_muffled", "Super muffled"),
        ("telephone_quality", "Telephone quality")
    ]

    for audio_file in test_files[:1]:  # Test first file
        print(f"\nTesting: {audio_file}")

        base_name = Path(audio_file).stem

        for style_name, description in styles:
            output_file = f"radio_working/{base_name}_{style_name}.wav"

            print(f"  Creating {style_name}...")

            if apply_radio_effects(audio_file, output_file, style_name, strength=0.8):
                print(f"  ✓ {description}: {output_file}")
            else:
                print(f"  ✗ Failed: {style_name}")

    print(f"\nDone! Check 'radio_working' folder.")
    print("These should sound VERY different from each other!")

if __name__ == "__main__":
    test_radio_effects()