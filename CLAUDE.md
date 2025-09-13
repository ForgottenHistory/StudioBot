# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Python Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variable for OpenRouter API
set OPENROUTER_API_KEY=your_api_key_here

# Start main radio server
python radio_server.py

# Run tests
python test_enhanced_system.py
python manual_test.py

# Generate conversations
python conversation_generator.py

# Test individual components
python test_yt_music.py
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

**radio_server.py**: Main Flask REST API server that orchestrates the entire system
- Handles ad generation using OpenRouter API
- Manages voice synthesis via ChatterBox TTS
- Applies radio effects to audio output
- Serves audio files and manages cleanup

**conversation_generator.py**: Multi-speaker conversation system
- Generates realistic dialogue between different characters
- Each character has unique voice settings and personality
- Supports vintage radio effects for authentic sound

**radio_effects_working.py**: Audio processing pipeline
- Applies vintage radio effects (frequency filtering, distortion)
- Three effect types: vintage_radio, super_muffled, telephone_quality
- Processes audio to simulate classic radio broadcast quality

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

- `test_enhanced_system.py`: Comprehensive system testing
- `manual_test.py`: Interactive testing utilities
- Individual component tests for specific features
- Frontend has separate linting and build verification