from flask import Flask, request, jsonify, send_file
import torch
import torchaudio as ta
from chatterbox.tts import ChatterboxTTS
from radio_effects_working import apply_radio_effects
import numpy as np
import soundfile as sf
import os
import requests
import json
import random
import time
from pathlib import Path
import threading
from datetime import datetime

app = Flask(__name__)

class RadioServer:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[RADIO SERVER] Initializing on {self.device}...")

        # Load TTS model
        self.model = ChatterboxTTS.from_pretrained(device=self.device)

        # OpenRouter API key from environment
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        if not self.openrouter_api_key:
            print("[ERROR] OPENROUTER_API_KEY environment variable not found!")
        else:
            print("[RADIO SERVER] OpenRouter API key loaded")

        # Voice settings
        self.voices = {
            "host": {
                "voice_file": "voices/loner_3.wav",
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

        # Content cache
        self.content_cache = {}
        self.cache_expiry = 300  # 5 minutes

        # Create temp directory for audio files
        self.temp_dir = Path("temp_audio")
        self.temp_dir.mkdir(exist_ok=True)

        print("[RADIO SERVER] Initialization complete")

    def generate_ad_content(self, theme=None):
        """Generate ad content using OpenRouter"""
        if not self.openrouter_api_key:
            # Fallback content if no API key
            fallback_ads = [
                "Try MegaCorp's new SelfDestructing Coffee Mugs! They explode right after you finish drinking, saving you precious dishwashing time!",
                "Introducing FlexFix Unlimited! Our repair service fixes everything by hitting it with progressively larger hammers until it works or becomes unrecognizable!",
                "Get TurboSleep Pills today! Fall asleep instantly, anywhere, anytime! Side effects may include sleeping through your own wedding, job interviews, and apocalyptic events!"
            ]
            return random.choice(fallback_ads)

        # OpenRouter API call
        url = "https://openrouter.ai/api/v1/chat/completions"

        theme_prompt = f" about {theme}" if theme else ""

        prompt = f"""Create a satirical GTA-style radio advertisement{theme_prompt}. Make it absurd and funny, like something from Vice City or San Andreas radio. Keep it under 60 words. Include:
- A ridiculous product or service
- Over-the-top marketing claims
- Absurd side effects or disclaimers
- Corporate name that sounds fake but professional

Make it sound like a real radio ad but completely ridiculous. No special characters, just plain text."""

        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "moonshotai/kimi-k2-0905",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 150,
            "temperature": 0.6
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()

            result = response.json()
            ad_content = result['choices'][0]['message']['content'].strip()

            print(f"[RADIO SERVER] Generated ad: {ad_content[:50]}...")
            return ad_content

        except Exception as e:
            print(f"[RADIO SERVER] OpenRouter API error: {e}")
            # Return fallback
            return "Welcome to WKRP Generic Radio! We play music and talk about stuff! Call us maybe!"

    def generate_track_transition_ad(self, track_info, time_remaining):
        """Generate ad content specifically for track transitions"""
        if not self.openrouter_api_key:
            # Fallback content for track transitions
            fallback_ads = [
                f"That was some great music! Speaking of great, try NukeIt Fast Food! Our burgers are so radioactive, they glow in the dark and cook themselves!",
                f"Hope you enjoyed that track! Now here's a message from UltraClean Laundry - we wash your clothes so hard, we accidentally wash away your memories too!",
                f"Great song there! This ad break brought to you by MegaDent Toothpaste - now with 500% more fluoride! Your teeth will be so white, they'll need sunglasses!"
            ]
            return random.choice(fallback_ads)

        # OpenRouter API call for contextual ad
        url = "https://openrouter.ai/api/v1/chat/completions"

        track_title = track_info.get('title', 'that great song')
        track_artist = track_info.get('artist', 'that amazing artist')

        prompt = f"""Create a satirical GTA-style radio advertisement that transitions from the song '{track_title}' by {track_artist}. Make it feel like a natural radio transition but absurdly funny. Keep it under 70 words.

Start with a brief transition mentioning the song that just played, then move into a ridiculous advertisement. Include:
- Natural radio transition feel
- A completely absurd product or service
- Over-the-top claims
- Fake corporate name

Make it sound like a real radio DJ transition into an ad break. No special characters, just plain text."""

        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "anthropic/claude-3-haiku",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 200,
            "temperature": 0.7
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()

            result = response.json()
            ad_content = result['choices'][0]['message']['content'].strip()

            print(f"[RADIO SERVER] Generated transition ad: {ad_content[:50]}...")
            return ad_content

        except Exception as e:
            print(f"[RADIO SERVER] OpenRouter API error: {e}")
            # Return fallback with track context
            return f"That was '{track_title}' by {track_artist}! Speaking of great music, try SoundBlaster Hearing Aids - they amplify sound so much, you can hear your neighbor's thoughts! Side effects may include involuntary mind reading and severe social awkwardness."

    def generate_tts_audio(self, text, voice="host"):
        """Generate TTS audio for given text and voice"""
        voice_config = self.voices.get(voice, self.voices["host"])

        print(f"[RADIO SERVER] Generating TTS with {voice} voice: {text[:30]}...")

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
                # Clean up raw file
                temp_raw.unlink()
                return str(temp_processed)
            else:
                # Return raw if processing failed
                return str(temp_raw)

        except Exception as e:
            print(f"[RADIO SERVER] TTS generation error: {e}")
            return None

    def cleanup_old_files(self):
        """Clean up old temp audio files"""
        try:
            current_time = time.time()
            for file_path in self.temp_dir.glob("*.wav"):
                if current_time - file_path.stat().st_mtime > 3600:  # 1 hour old
                    file_path.unlink()
        except Exception as e:
            print(f"[RADIO SERVER] Cleanup error: {e}")

# Global server instance
radio_server = RadioServer()

@app.route('/')
def index():
    """Server status page"""
    return jsonify({
        "status": "running",
        "server": "AI Radio Server",
        "time": datetime.now().isoformat(),
        "tts_device": radio_server.device,
        "openrouter_available": bool(radio_server.openrouter_api_key)
    })

@app.route('/generate/ad', methods=['GET', 'POST'])
def generate_ad():
    """Generate and return an ad"""
    if request.method == 'GET':
        theme = request.args.get('theme')
        voice = request.args.get('voice', 'announcer')
    else:  # POST
        data = request.json or {}
        theme = data.get('theme')
        voice = data.get('voice', 'announcer')

    print(f"[RADIO SERVER] Ad request - theme: {theme}, voice: {voice}")

    try:
        # Generate ad content
        ad_content = radio_server.generate_ad_content(theme)

        # Generate TTS audio
        audio_file = radio_server.generate_tts_audio(ad_content, voice)

        if audio_file and os.path.exists(audio_file):
            return jsonify({
                "success": True,
                "content": ad_content,
                "audio_url": f"/audio/{os.path.basename(audio_file)}",
                "voice": voice,
                "theme": theme
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to generate audio"
            }), 500

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/generate/speech', methods=['POST'])
def generate_speech():
    """Generate TTS for custom text"""
    data = request.json
    if not data or 'text' not in data:
        return jsonify({"error": "Text required"}), 400

    text = data['text']
    voice = data.get('voice', 'host')

    print(f"[RADIO SERVER] Speech request - voice: {voice}")

    try:
        audio_file = radio_server.generate_tts_audio(text, voice)

        if audio_file and os.path.exists(audio_file):
            return jsonify({
                "success": True,
                "content": text,
                "audio_url": f"/audio/{os.path.basename(audio_file)}",
                "voice": voice
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to generate audio"
            }), 500

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/audio/<filename>')
def serve_audio(filename):
    """Serve generated audio files"""
    file_path = radio_server.temp_dir / filename

    if file_path.exists():
        return send_file(file_path, mimetype='audio/wav')
    else:
        return jsonify({"error": "File not found"}), 404

@app.route('/voices')
def list_voices():
    """List available voices"""
    return jsonify({
        "voices": list(radio_server.voices.keys()),
        "voice_details": {
            name: {
                "description": config.get("description", ""),
                "radio_effect": config["radio_effect"]
            }
            for name, config in radio_server.voices.items()
        }
    })

@app.route('/generate_ad', methods=['POST'])
def generate_ad_for_track():
    """Generate ad based on current music track context"""
    data = request.json
    if not data:
        return jsonify({"error": "JSON data required"}), 400

    print(f"[RADIO SERVER] Music-triggered ad generation request")

    # Extract track context
    current_track = data.get('current_track', {})
    time_remaining = data.get('time_remaining', 0)
    ad_type = data.get('ad_type', 'transition')

    # Create contextual theme for ad generation
    track_title = current_track.get('title', 'Unknown')
    track_artist = current_track.get('artist', 'Unknown Artist')

    # Generate theme based on track context
    theme_context = f"transitioning from '{track_title}' by {track_artist}"

    print(f"[RADIO SERVER] Generating ad for track transition: {track_artist} - {track_title}")
    print(f"[RADIO SERVER] Time remaining: {time_remaining} seconds")

    try:
        # Generate contextual ad content
        ad_content = radio_server.generate_track_transition_ad(current_track, time_remaining)

        # Generate TTS audio with announcer voice (good for ads)
        audio_file = radio_server.generate_tts_audio(ad_content, "announcer")

        if audio_file and os.path.exists(audio_file):
            response_data = {
                "success": True,
                "message": "Ad generated successfully",
                "content": ad_content,
                "audio_url": f"/audio/{os.path.basename(audio_file)}",
                "context": {
                    "track": current_track,
                    "time_remaining": time_remaining,
                    "ad_type": ad_type
                },
                "generated_at": datetime.now().isoformat()
            }

            print(f"[RADIO SERVER] ✅ Ad generated: {ad_content[:50]}...")
            return jsonify(response_data)
        else:
            print(f"[RADIO SERVER] ❌ Failed to generate audio")
            return jsonify({
                "success": False,
                "error": "Failed to generate audio",
                "content": ad_content
            }), 500

    except Exception as e:
        print(f"[RADIO SERVER] ❌ Ad generation error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/cleanup', methods=['POST'])
def cleanup():
    """Manual cleanup of old files"""
    radio_server.cleanup_old_files()
    return jsonify({"success": True, "message": "Cleanup completed"})

# Background cleanup task
def background_cleanup():
    """Background task to clean up old files"""
    while True:
        time.sleep(1800)  # Run every 30 minutes
        radio_server.cleanup_old_files()

if __name__ == '__main__':
    # Start background cleanup
    cleanup_thread = threading.Thread(target=background_cleanup, daemon=True)
    cleanup_thread.start()

    print("[RADIO SERVER] Starting server...")
    print("[RADIO SERVER] Available endpoints:")
    print("  GET  / - Server status")
    print("  GET  /generate/ad?theme=cars&voice=announcer - Generate ad")
    print("  POST /generate/speech - Generate custom speech")
    print("  GET  /audio/<filename> - Serve audio files")
    print("  GET  /voices - List available voices")
    print("")
    print("Example usage:")
    print("  curl 'http://localhost:5000/generate/ad?theme=pizza'")
    print("  curl -X POST http://localhost:5000/generate/speech -H 'Content-Type: application/json' -d '{\"text\":\"Hello world\",\"voice\":\"host\"}'")

    app.run(debug=True, host='0.0.0.0', port=5000)