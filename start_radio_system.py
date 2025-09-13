#!/usr/bin/env python3
# Radio System Startup Script
# Starts both the radio server and music integration

import subprocess
import sys
import time
import os
import signal
import json
from pathlib import Path

# Set UTF-8 encoding for Windows console
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

class RadioSystemManager:
    def __init__(self):
        self.processes = []
        self.config_file = "config.json"

    def check_dependencies(self):
        """Check if all required dependencies and files exist"""
        print("🔍 Checking system dependencies...")

        # Check config file
        if not Path(self.config_file).exists():
            print(f"❌ Config file {self.config_file} not found!")
            print("   Run: python -c \"import json; print(json.dumps({'youtube_music': {'api_base_url': 'http://localhost:9863'}}, indent=2))\" > config.json")
            return False

        # Check environment variables
        if not os.getenv('OPENROUTER_API_KEY'):
            print("❌ OPENROUTER_API_KEY environment variable not set!")
            print("   Run: set OPENROUTER_API_KEY=your_api_key_here")
            return False

        # Check Python modules
        required_modules = ['flask', 'torch', 'aiohttp', 'requests']
        missing = []

        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing.append(module)

        if missing:
            print(f"❌ Missing Python modules: {', '.join(missing)}")
            print(f"   Run: pip install {' '.join(missing)}")
            return False

        # Check voice files
        voices_dir = Path("voices")
        if not voices_dir.exists():
            print("❌ Voices directory not found!")
            print("   Make sure you have voice files in the 'voices/' directory")
            return False

        required_voices = ["loner_3.wav", "voice_2.wav"]
        for voice in required_voices:
            if not (voices_dir / voice).exists():
                print(f"⚠️  Voice file {voice} not found in voices/ directory")

        print("✅ Dependencies check completed")
        return True

    def check_youtube_music_api(self):
        """Check if YouTube Music API is accessible"""
        print("🎵 Checking YouTube Music API...")

        try:
            import requests
            with open(self.config_file, 'r') as f:
                config = json.load(f)

            api_url = config.get('youtube_music', {}).get('api_base_url', 'http://localhost:9863')

            # Test API connection - try swagger endpoint first
            response = requests.get(f"{api_url}/swagger", timeout=5)
            if response.status_code == 200:
                print("✅ YouTube Music API is accessible")
                return True
            else:
                print(f"❌ YouTube Music API returned status {response.status_code}")
                print("   Make sure th-ch YouTube Music is running with API Server plugin enabled")
                return False

        except Exception as e:
            print(f"❌ Cannot connect to YouTube Music API: {e}")
            print("   Make sure th-ch YouTube Music is running with API Server plugin enabled")
            return False

    def start_radio_server(self):
        """Start the radio server"""
        print("📻 Starting Radio Server...")

        try:
            process = subprocess.Popen([
                sys.executable, "radio_server.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            self.processes.append(("Radio Server", process))
            print("✅ Radio Server started")

            # Wait a bit for server to initialize
            time.sleep(3)

            return process

        except Exception as e:
            print(f"❌ Failed to start Radio Server: {e}")
            return None

    def start_music_integration(self):
        """Start the music integration"""
        print("🎵 Starting Music Integration...")

        try:
            process = subprocess.Popen([
                sys.executable, "radio_music_integration.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            self.processes.append(("Music Integration", process))
            print("✅ Music Integration started")

            return process

        except Exception as e:
            print(f"❌ Failed to start Music Integration: {e}")
            return None

    def monitor_processes(self):
        """Monitor running processes"""
        print("👁️  Monitoring system processes...")
        print("   Press Ctrl+C to shutdown all processes")
        print("   Logs are shown below:")
        print("-" * 60)

        try:
            while True:
                # Check if any process died
                for name, process in self.processes:
                    if process.poll() is not None:
                        print(f"❌ {name} process died!")
                        # Get any error output
                        _, stderr = process.communicate(timeout=1)
                        if stderr:
                            print(f"   Error: {stderr}")

                        # Remove from active processes
                        self.processes = [(n, p) for n, p in self.processes if p != process]

                        if not self.processes:
                            print("❌ All processes died, shutting down...")
                            return

                # Print any new output from processes
                for name, process in self.processes:
                    if process.stdout:
                        try:
                            line = process.stdout.readline()
                            if line:
                                print(f"[{name}] {line.strip()}")
                        except:
                            pass

                time.sleep(0.5)

        except KeyboardInterrupt:
            print("\n🛑 Shutdown requested...")
            self.shutdown()

    def shutdown(self):
        """Shutdown all processes"""
        print("🔄 Shutting down all processes...")

        for name, process in self.processes:
            try:
                print(f"   Stopping {name}...")
                process.terminate()

                # Wait for graceful shutdown
                try:
                    process.wait(timeout=5)
                    print(f"   ✅ {name} stopped")
                except subprocess.TimeoutExpired:
                    print(f"   ⚠️  Force killing {name}...")
                    process.kill()

            except Exception as e:
                print(f"   ❌ Error stopping {name}: {e}")

        self.processes.clear()
        print("✅ All processes stopped")

    def run(self):
        """Run the complete radio system"""
        print("🚀 Starting AI Radio System")
        print("=" * 50)

        # Check dependencies
        if not self.check_dependencies():
            print("\n❌ Dependency check failed!")
            return 1

        # Check YouTube Music API
        if not self.check_youtube_music_api():
            print("\n❌ YouTube Music API check failed!")
            print("   Please start th-ch YouTube Music and enable the API Server plugin")
            return 1

        print("\n✅ All checks passed, starting system...")
        print("=" * 50)

        # Start radio server
        radio_process = self.start_radio_server()
        if not radio_process:
            return 1

        # Wait for radio server to be ready
        time.sleep(2)

        # Start music integration
        music_process = self.start_music_integration()
        if not music_process:
            self.shutdown()
            return 1

        # Monitor processes
        self.monitor_processes()

        print("\n👋 Radio System shutdown complete")
        return 0

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--check-only":
        # Only run checks, don't start system
        manager = RadioSystemManager()
        if manager.check_dependencies() and manager.check_youtube_music_api():
            print("✅ All checks passed!")
            return 0
        else:
            print("❌ Checks failed!")
            return 1

    # Run the full system
    manager = RadioSystemManager()
    return manager.run()

if __name__ == "__main__":
    sys.exit(main())