# StudioBot - AI Radio Show Generator

An AI-powered radio show system that generates GTA-style advertisements and multi-speaker conversations with voice cloning and realistic radio effects.

## 🎙️ Features

- **Real-time Ad Generation**: Uses OpenRouter API to create satirical GTA-style ads
- **Voice Cloning**: Multiple voice personalities using ChatterBox TTS
- **Radio Effects**: Vintage radio processing (muffled, telephone quality, etc.)
- **Multi-Speaker Conversations**: Natural dialogue between different characters
- **REST API**: Easy integration with other systems
- **Automatic Cleanup**: Manages temporary audio files

## 🚀 Quick Start

### Prerequisites
```bash
# Install Python dependencies
pip install torch torchaudio chatterbox-tts flask requests soundfile numpy scipy

# Set environment variable for OpenRouter
set OPENROUTER_API_KEY=your_api_key_here
```

### Basic Usage

#### 1. Start the Radio Server
```bash
python radio_server.py
```
Server runs on `http://localhost:5000`

#### 2. Generate Ads
```bash
# Via curl
curl "http://localhost:5000/generate/ad?theme=pizza&voice=announcer"

# Via browser
http://localhost:5000/generate/ad?theme=cars
```

#### 3. Test the System
```bash
python test_radio_server.py
```

#### 4. Generate Conversations
```bash
python conversation_generator.py
```

## 📁 Project Structure

```
StudioBot/
├── radio_server.py           # Main Flask server
├── conversation_generator.py # Multi-speaker conversations
├── radio_effects_working.py  # Audio processing
├── test_radio_server.py      # Server testing
├── test_chatterbox_tts.py    # Simple TTS testing
├── gta_style_ad.txt          # Sample advertisement
├── test_conversation.txt     # Sample dialogue
├── voices/                   # Voice clone files
│   ├── loner_3.wav          # Host voice
│   ├── voice_1.wav          # Test voice
│   └── voice_2.wav          # Guest voice
└── temp_audio/              # Server temporary files
```

## 🎚️ API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Server status |
| GET | `/generate/ad?theme=<theme>&voice=<voice>` | Generate themed ad |
| POST | `/generate/speech` | Custom text-to-speech |
| GET | `/audio/<filename>` | Stream audio files |
| GET | `/voices` | List available voices |

## 🎭 Voice Personalities

- **host**: Professional radio host (vintage radio effect)
- **announcer**: Advertisement announcer (super muffled effect)

## 🔊 Radio Effects

- **vintage_radio**: Classic radio sound (350-4500Hz)
- **super_muffled**: Background radio feel (500-3200Hz)
- **telephone_quality**: Old phone quality (600-3400Hz)

## 📝 Content Examples

### Sample Ad Generation
```json
{
  "success": true,
  "content": "Try FlexCorp's new Self-Destructing Coffee Mugs! They explode right after you finish drinking, saving you precious dishwashing time!",
  "audio_url": "/audio/tts_12345_processed.wav",
  "voice": "announcer",
  "theme": "kitchen"
}
```

### Sample Conversation Format
```
Host: Welcome back to K-NULL Radio!
Guest: Thanks for having me on the show.
Host: So tell us about your new product.
Guest: It's a sandwich that eats itself!
```

## 🛠️ Development

### Adding New Voices
1. Place `.wav` file in `voices/` directory
2. Update voice configuration in `radio_server.py`
3. Restart server

### Customizing Radio Effects
Edit `radio_effects_working.py` to modify audio processing parameters.

### Adding New Conversation Characters
Update the `characters` dictionary in `conversation_generator.py`.

## 🎯 Next Steps

See `next_steps.md` for future development ideas including:
- Music integration
- Full show automation
- Broadcasting capabilities
- Content scheduling

## 🐛 Troubleshooting

**Server won't start**: Ensure ChatterBox TTS is installed and CUDA is available
**No audio generated**: Check voice files exist in `voices/` folder
**API errors**: Verify OPENROUTER_API_KEY environment variable is set
**Poor audio quality**: Adjust radio effect parameters in `radio_effects_working.py`

## 📄 License

This project is for educational/entertainment purposes. Voice cloning should only be used with proper consent.