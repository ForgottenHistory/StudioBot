# AI Radio System with YouTube Music Integration

Automatically generates ads 1 minute before each YouTube Music song ends.

## 🚀 Quick Start

1. **Setup th-ch YouTube Music**
   - Install and run [th-ch/youtube-music](https://github.com/th-ch/youtube-music)
   - Enable the "API Server" plugin in Settings → Plugins
   - Keep authorization enabled for security

2. **Set Environment Variable**
   ```bash
   set OPENROUTER_API_KEY=your_api_key_here
   ```

3. **Install Dependencies**
   ```bash
   pip install flask torch aiohttp requests torchaudio soundfile numpy chatterbox-tts
   ```

4. **Run System Check**
   ```bash
   python start_radio_system.py --check-only
   ```

5. **Start Complete System**
   ```bash
   python start_radio_system.py
   ```

## ⚙️ Configuration

Edit `config.json` to customize behavior:

```json
{
  "youtube_music": {
    "pre_generate_seconds": 60,
    "check_interval": 1.0
  },
  "ad_generation": {
    "min_song_duration": 90,
    "max_ad_duration": 30
  }
}
```

## 📁 File Structure

```
StudioBot/
├── config.json                    # System configuration
├── radio_server.py               # Main radio server (enhanced)
├── radio_music_integration.py    # YouTube Music integration
├── start_radio_system.py         # Startup script
├── voices/                       # Voice clone files
│   ├── loner_3.wav
│   └── voice_2.wav
└── temp_audio/                   # Generated audio files
```

## 🎵 How It Works

1. **Monitor**: Watches YouTube Music for track changes
2. **Predict**: Calculates when songs will end using API timing
3. **Generate**: Creates contextual ads 1 minute before song ends
4. **Synthesize**: Converts text to speech with radio effects
5. **Serve**: Makes audio available via HTTP API

## 🔧 Advanced Usage

### Manual Ad Generation
```bash
curl -X POST http://localhost:5000/generate_ad \
  -H "Content-Type: application/json" \
  -d '{
    "current_track": {
      "title": "Song Title",
      "artist": "Artist Name"
    },
    "time_remaining": 45
  }'
```

### Check System Status
```bash
curl http://localhost:5000/
curl http://localhost:9863/api/v1/song
```

## 📊 Monitoring

The system logs to both console and `radio_integration.log`:

- 🎵 Track changes
- 🚀 Ad generation triggers
- ✅ Successful completions
- ❌ Error messages

## ⚠️ Troubleshooting

### "YouTube Music API check failed"
- Ensure th-ch YouTube Music is running
- Enable "API Server" plugin in settings
- Check if port 9863 is accessible

### "OPENROUTER_API_KEY not set"
- Set environment variable: `set OPENROUTER_API_KEY=your_key`
- Restart command prompt after setting

### "Voice files not found"
- Place voice clone files in `voices/` directory
- Required: `loner_3.wav`, `voice_2.wav`

### "Generation timeout"
- Increase timeout in config.json
- Check OpenRouter API status
- Verify API key is valid

## 🎛️ API Endpoints

### Radio Server (Port 5000)
- `GET /` - Server status
- `POST /generate_ad` - Generate track-contextual ad
- `GET /audio/<filename>` - Serve generated audio
- `GET /voices` - List available voices

### YouTube Music API (Port 9863)
- `GET /api/v1/song` - Current track info
- `POST /auth/default` - Get access token

## 🔄 System Flow

```
YouTube Music → Monitor → Pre-Generate (60s) → Radio Server → TTS → Audio File
      ↓              ↓              ↓              ↓          ↓
   Track Info → Timing Check → Ad Content → Voice Synthesis → HTTP Serve
```

## 📝 Example Output

```
🎵 New track: Artist Name - Song Title
   ⏱️  Duration: 3:45
🚀 Triggering ad generation (58s remaining)
📻 Radio server response: Ad generated successfully
✅ Ad generated: That was 'Song Title' by Artist Name! Speaking of...
```

## 🛠️ Development

### Adding New Voices
1. Place `.wav` file in `voices/` directory
2. Add voice configuration in `radio_server.py`:
```python
"new_voice": {
    "voice_file": "voices/new_voice.wav",
    "exaggeration": 1.0,
    "temperature": 0.7,
    "cfg_weight": 0.5,
    "radio_effect": "vintage_radio"
}
```

### Customizing Ad Content
Edit the prompt in `generate_track_transition_ad()` method in `radio_server.py`.

### Changing Timing
Modify `pre_generate_seconds` in `config.json` (default: 60 seconds).

## 📄 License

This project integrates with:
- [th-ch/youtube-music](https://github.com/th-ch/youtube-music) - YouTube Music desktop app
- OpenRouter API - LLM services
- ChatterBox TTS - Voice synthesis