import torch
import torchaudio as ta
from chatterbox.tts import ChatterboxTTS

def test_basic_tts():
    """Test basic English text-to-speech generation"""
    print("Loading ChatterBox TTS model...")
    
    # Initialize the model (use "cpu" if no CUDA available)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    model = ChatterboxTTS.from_pretrained(device=device)
    
    # Read the GTA-style ad text
    with open("gta_style_ad.txt", "r", encoding="utf-8") as f:
        text = f.read().strip()
    
    print(f"Generating speech for: '{text}'")
    
    # Generate speech with radio-style settings and voice cloning
    wav = model.generate(
        text,
        audio_prompt_path="voices/loner_3.wav",  # Use your voice clone
        exaggeration=1.0,   # Emotion control (0-2): 0=flat, 0.7=default, 1.5-2=theatrical
        temperature=0.6,    # Speech variation (0-2): lower=consistent, higher=varied
        cfg_weight=0.3      # Pace control (default 0.5): lower=slower/measured, higher=faster
    )
    
    # Save the raw audio
    raw_output = "chatterbox_test_output_raw.wav"
    ta.save(raw_output, wav, model.sr)

    print(f"Raw audio saved to: {raw_output}")

    # Apply super muffled radio effect
    from radio_effects_working import apply_radio_effects

    final_output = "chatterbox_test_output.wav"
    print("Applying super muffled radio effect...")

    if apply_radio_effects(raw_output, final_output, "super_muffled", strength=0.8):
        print(f"Final radio-processed audio: {final_output}")
    else:
        print("Radio effect failed, using raw audio")
        final_output = raw_output

    print(f"Sample rate: {model.sr} Hz")
    print(f"Audio duration: {len(wav[0]) / model.sr:.2f} seconds")

def test_voice_cloning():
    """Test voice cloning with a reference audio file"""
    print("\n--- Voice Cloning Test ---")
    
    # This would require a reference audio file
    # Uncomment and modify the path if you have a reference audio file
    
    # device = "cuda" if torch.cuda.is_available() else "cpu"
    # model = ChatterboxTTS.from_pretrained(device=device)
    # 
    # text = "This is a voice cloning test using ChatterBox TTS."
    # audio_prompt_path = "reference_voice.wav"  # Replace with your reference file
    # 
    # wav = model.generate(text, audio_prompt_path=audio_prompt_path)
    # ta.save("voice_cloned_output.wav", wav, model.sr)
    # print("Voice cloning test completed!")
    
    print("Voice cloning test skipped - no reference audio file provided")

if __name__ == "__main__":
    try:
        # Test basic TTS
        test_basic_tts()
        
        # Test voice cloning (optional)
        test_voice_cloning()
        
        print("\nChatterBox TTS test completed successfully!")
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure chatterbox-tts is installed: pip install chatterbox-tts")
    except Exception as e:
        print(f"Error during TTS generation: {e}")
        print("This might be due to missing dependencies or insufficient system resources")