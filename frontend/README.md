# Enhanced Radio Server Frontend

A modern React + Tailwind CSS interface for controlling the Enhanced Radio Server.

## Features

- **Real-time server status monitoring**
- **Content generation interface** - Generate ads and conversations with dropdowns
- **Audio playback** - Play generated audio files directly in browser
- **Content browser** - View topics, personalities, and generated content history
- **Scheduler control** - Start/stop automatic content generation

## Quick Start

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm run dev
   ```

3. **Start the radio server** (in another terminal):
   ```bash
   cd ..
   python server.py
   ```

4. **Open your browser:**
   - Frontend: http://localhost:5173 (Vite dev server)
   - API Server: http://localhost:5000

## Architecture

- **React 19** - Latest React with modern hooks
- **Vite** - Fast build tool and dev server
- **Tailwind CSS 4** - Utility-first styling
- **Lucide React** - Beautiful icon set
- **Custom hooks** - `useRadioServer` for API management

## Components

- `useRadioServer` - Main API hook with auto-refresh
- `ServerStatus` - Real-time server monitoring and scheduler controls
- `ContentGenerator` - Ad and conversation generation forms
- `ContentViewer` - Browse topics, personalities, and generated files

## API Integration

The frontend automatically connects to the radio server at `http://localhost:5000` and provides:

- Real-time status updates every 2 seconds
- Content generation with loading states
- Audio playback controls
- File download links
- Error handling with user-friendly messages

## Development

```bash
# Install new dependencies
npm install <package-name>

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```