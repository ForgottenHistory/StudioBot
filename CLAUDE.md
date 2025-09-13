# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Structure

The project has been organized for better maintainability:

```
StudioBot/
├── 📁 src/                          # Core application source code
│   ├── api/routes.py               # Flask REST API endpoints
│   ├── content/                    # Content generators and managers
│   ├── radio/radio_server.py       # Radio server core functionality
│   ├── voice/voice_manager.py      # Voice synthesis and effects
│   └── gui/radio_gui.py           # GUI components
├── 📁 scripts/                     # Utility and standalone scripts
│   ├── conversation_generator.py   # Multi-speaker conversation generator
│   ├── manual_test.py             # Interactive testing utilities
│   ├── radio_effects_working.py   # Audio processing pipeline
│   └── radio_gui.py              # Simple GUI launcher
├── 📁 tests/                       # Test files and debugging tools
│   ├── debug/debug_yt_music.py    # YouTube Music debugging
│   ├── test_enhanced_system.py     # Comprehensive system testing
│   ├── test_yt_music.py           # YouTube Music integration tests
│   └── test_*.py                  # Other unit tests
├── 📁 archive/                     # Legacy/deprecated files
├── 📁 config/                      # Configuration templates
├── 📁 content/                     # Content data (personalities, topics)
├── 📁 voices/                      # Voice clone files (.wav)
├── 📁 temp_audio/                  # Generated audio files (auto-managed)
├── 📁 logs/                        # Application logs
├── 📁 frontend/                    # React web interface
├── radio_music_integration.py      # **MAIN**: YouTube Music integration
├── server.py                      # Flask server entry point (preferred)
├── start_radio_system.py          # Complete system startup script
└── config.json                   # Main configuration file
```

## Development Commands

### Python Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variable for OpenRouter API
set OPENROUTER_API_KEY=your_api_key_here

# Start complete radio system (recommended)
python start_radio_system.py

# OR start components individually:
# - Start Flask server only
python server.py
# - Start YouTube Music integration only
python radio_music_integration.py

# Run tests
python tests/test_enhanced_system.py
python scripts/manual_test.py

# Generate conversations
python scripts/conversation_generator.py

# Test individual components
python tests/test_yt_music.py
python tests/debug/debug_yt_music.py
```

### Frontend (React/Vite)
```bash
cd frontend

# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Lint code
npm run lint

# Preview production build
npm run preview
```

## Architecture Overview

### Core Components

**radio_music_integration.py**: **Primary system** - YouTube Music integration
- Real-time song monitoring with natural transition detection
- 50/50 random chance for ads vs conversations during song transitions
- Volume matching between music and generated content
- Pre-generation system for instant playback (60s before song ends)
- Pause/resume music control for seamless ad/conversation breaks

**src/api/routes.py**: Flask REST API server with endpoints
- `/generate_ad` - Music-triggered ad generation with track context
- `/generate/dynamic_ad` - Manual ad generation
- `/generate/dynamic_conversation` - Conversation generation between personalities
- `/generate/custom_tts` - Text-to-speech with personality voices
- `/audio/<filename>` - Serve generated audio files

**scripts/conversation_generator.py**: Multi-speaker conversation system
- Generates realistic dialogue between different characters
- Each character has unique voice settings and personality
- Supports vintage radio effects for authentic sound

**scripts/radio_effects_working.py**: Audio processing pipeline
- Applies vintage radio effects (frequency filtering, distortion)
- Three effect types: vintage_radio, super_muffled, telephone_quality
- Processes audio to simulate classic radio broadcast quality

**start_radio_system.py**: Complete system launcher
- Dependency checking and validation
- Starts both Flask server and YouTube Music integration
- Process monitoring and graceful shutdown

### Voice System

The system uses ChatterBox TTS with voice cloning:
- Voice files stored in `voices/` directory (e.g., `loner_3.wav`, `voice_2.wav`)
- Each character has customizable parameters: exaggeration, temperature, cfg_weight
- Radio effects applied post-synthesis for authentic broadcast sound

### Frontend

React/Vite application with:
- TailwindCSS for styling
- Headless UI components
- Development tools: ESLint, TypeScript definitions

## Key Dependencies

- **ChatterBox TTS**: Voice synthesis and cloning
- **PyTorch/Torchaudio**: ML model execution and audio processing
- **Flask**: REST API server
- **OpenRouter API**: LLM-powered content generation
- **SoundFile/NumPy**: Audio file handling and processing

## Environment Setup

1. Ensure CUDA is available for optimal TTS performance
2. Set `OPENROUTER_API_KEY` environment variable
3. Place voice clone files in `voices/` directory
4. Temporary audio files are managed in `temp_audio/`

## Testing Strategy

- `tests/test_enhanced_system.py`: Comprehensive system testing
- `scripts/manual_test.py`: Interactive testing utilities with conversation generation
- `tests/test_yt_music.py`: YouTube Music API integration testing
- `tests/debug/debug_yt_music.py`: YouTube Music connection debugging
- Individual component tests for specific features in `tests/` directory
- Frontend has separate linting and build verification

## YouTube Music Integration

The system integrates with th-ch/YouTube Music desktop app:
- Requires API Server plugin enabled in th-ch YouTube Music
- Real-time song position monitoring every 0.3 seconds
- Distinguishes between natural song endings vs manual skips
- Pre-generates content 60 seconds before natural song transitions
- Matches volume levels between music and generated content
- Supports authentication with JWT tokens