#!/usr/bin/env python3
"""
Manual Test Script - Skip Timer for Enhanced Radio Server

This script bypasses the automatic timer and triggers content generation manually.
Useful for testing without waiting for the scheduler intervals.
"""

import requests
import time
import json
from pathlib import Path
import subprocess
import os
import re
from pydub import AudioSegment
from pydub.playback import play

def manual_trigger_test(base_url="http://localhost:5000"):
    """Manually trigger content generation without waiting for timers"""

    print("🚀 Manual Content Generation Test")
    print("=" * 50)

    # Check server status
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code != 200:
            print("❌ Server not running! Start with: python enhanced_radio_server.py")
            return

        status = response.json()
        print(f"✅ Server ready - {status['topics_loaded']} topics, {status['personalities_loaded']} personalities")

    except Exception as e:
        print(f"❌ Server connection failed: {e}")
        return

    print(f"\n🎯 Manual Trigger Tests (skipping {get_scheduler_intervals(base_url)} second timers)")
    print("-" * 50)

    # Test 1: Manual ad generation (bypasses 2-minute timer)
    print("\n1. 🎬 Generating dynamic ad manually...")
    generate_manual_ad(base_url)

    # Test 2: Manual conversation generation (bypasses 5-minute timer)
    print("\n2. 🎙️ Generating conversation manually...")
    generate_manual_conversation(base_url)

    # Test 3: Rapid generation test (multiple calls)
    print("\n3. ⚡ Rapid generation test...")
    rapid_generation_test(base_url)

    # Test 4: Show generated content
    print("\n4. 📄 Checking generated content...")
    show_generated_content(base_url)

def get_scheduler_intervals(base_url):
    """Get scheduler interval information"""
    try:
        response = requests.get(f"{base_url}/scheduler/status")
        if response.status_code == 200:
            status = response.json()
            return f"ad:{status['ad_interval']}, conv:{status['conversation_interval']}"
    except:
        pass
    return "unknown"

def generate_manual_ad(base_url):
    """Generate ad manually (normally waits 2 minutes)"""
    try:
        # Get available topics first
        topics_response = requests.get(f"{base_url}/topics")
        if topics_response.status_code == 200:
            topics = list(topics_response.json()['topics'].keys())
            topic = topics[0] if topics else None

        # Get available personalities
        personalities_response = requests.get(f"{base_url}/personalities")
        if personalities_response.status_code == 200:
            personalities = personalities_response.json()['personalities']
            personality_name = list(personalities.keys())[0] if personalities else None

        # Generate ad with specific topic/personality
        params = {}
        if topic:
            params['topic'] = topic
        if personality_name:
            params['personality'] = personality_name

        response = requests.get(f"{base_url}/generate/dynamic_ad", params=params)

        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Ad generated for '{result['topic']}' by {result['personality']}")
            print(f"   📝 Content: {result['content'][:80]}...")
            print(f"   🎵 Audio: {result['audio_url']}")
        else:
            print(f"   ❌ Failed: {response.text}")

    except Exception as e:
        print(f"   ❌ Error: {e}")

def generate_manual_conversation(base_url):
    """Generate conversation manually (normally waits 5 minutes)"""
    try:
        # Get available personalities
        personalities_response = requests.get(f"{base_url}/personalities")
        topics_response = requests.get(f"{base_url}/topics")

        if personalities_response.status_code == 200 and topics_response.status_code == 200:
            personalities = list(personalities_response.json()['personalities'].keys())
            topics = list(topics_response.json()['topics'].keys())

            if len(personalities) >= 2:
                host = personalities[0]
                guest = personalities[1] if len(personalities) > 1 else personalities[0]
                topic = topics[0] if topics else None

                params = {
                    'host': host,
                    'guest': guest
                }
                if topic:
                    params['topic'] = topic

                response = requests.get(f"{base_url}/generate/dynamic_conversation", params=params)

                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ Conversation between {result['host']} & {result['guest']}")
                    print(f"   🏷️ Topic: {result['topic']}")
                    print(f"   📝 Preview: {result['content'][:100]}...")

                    # Generate full audio conversation
                    print(f"   🎵 Generating voices...")
                    audio_file = generate_conversation_audio(base_url, result)
                    if audio_file:
                        print(f"   🔊 Playing conversation...")
                        play_audio_file(audio_file)

                else:
                    print(f"   ❌ Failed: {response.text}")
            else:
                print("   ❌ Need at least 2 personalities for conversation")

    except Exception as e:
        print(f"   ❌ Error: {e}")

def rapid_generation_test(base_url, count=3):
    """Test rapid generation (bypassing all timers)"""
    print(f"   Generating {count} pieces of content rapidly...")

    for i in range(count):
        print(f"   🔄 Generation {i+1}/{count}...")

        # Alternate between ads and conversations
        if i % 2 == 0:
            response = requests.get(f"{base_url}/generate/dynamic_ad")
        else:
            response = requests.get(f"{base_url}/generate/dynamic_conversation")

        if response.status_code == 200:
            result = response.json()
            content_type = "Ad" if 'audio_url' in result else "Conversation"
            print(f"     ✅ {content_type} generated successfully")
        else:
            print(f"     ❌ Generation {i+1} failed")

        time.sleep(1)  # Small delay between requests

def show_generated_content(base_url):
    """Show what content has been generated"""
    try:
        response = requests.get(f"{base_url}/generated_content")
        if response.status_code == 200:
            content_data = response.json()
            print(f"   📊 Total generated files: {content_data['total_files']}")

            if content_data['generated_content']:
                print("   📄 Recent content:")
                for item in content_data['generated_content'][:5]:  # Show latest 5
                    print(f"     • {item['filename']} ({item['size']} bytes)")
            else:
                print("   📄 No auto-generated content found")

    except Exception as e:
        print(f"   ❌ Error checking content: {e}")

def force_scheduler_trigger(base_url):
    """Force the scheduler to trigger immediately by modifying intervals"""
    print("\n🔧 Advanced: Force scheduler trigger")
    print("   Note: This would require modifying the server to accept interval changes")
    print("   Current approach uses direct API calls instead")

def continuous_generation_mode(base_url, duration=60):
    """Generate content continuously for testing"""
    print(f"\n🔄 Continuous generation mode ({duration} seconds)")
    print("   Generating content every 5 seconds...")

    start_time = time.time()
    count = 0

    try:
        while time.time() - start_time < duration:
            count += 1
            content_type = "ad" if count % 2 == 0 else "conversation"

            print(f"   [{count:2d}] Generating {content_type}...")

            if content_type == "ad":
                response = requests.get(f"{base_url}/generate/dynamic_ad")
            else:
                response = requests.get(f"{base_url}/generate/dynamic_conversation")

            if response.status_code == 200:
                print(f"       ✅ Success")
            else:
                print(f"       ❌ Failed")

            time.sleep(5)  # Generate every 5 seconds

    except KeyboardInterrupt:
        print(f"\n   🛑 Stopped after {count} generations")

def generate_conversation_audio(base_url, conversation_data):
    """Generate audio for a full conversation by splitting speakers and generating TTS"""
    try:
        content = conversation_data['content']
        host_name = conversation_data['host']
        guest_name = conversation_data['guest']

        # Parse conversation lines
        lines = parse_conversation_lines(content)
        if not lines:
            print("   ❌ Could not parse conversation lines")
            return None

        audio_segments = []
        temp_files = []

        for i, (speaker, text) in enumerate(lines):
            print(f"   🎤 Generating voice {i+1}/{len(lines)} ({speaker}): {text[:30]}...")

            # Generate TTS for this line using the personality's voice
            tts_response = generate_speaker_tts(base_url, speaker, text)

            if tts_response and 'audio_url' in tts_response:
                # Download the audio file
                audio_url = f"{base_url}{tts_response['audio_url']}"
                audio_response = requests.get(audio_url)

                if audio_response.status_code == 200:
                    # Save temporary file in temp_audio directory
                    temp_dir = Path("temp_audio")
                    temp_dir.mkdir(exist_ok=True)
                    temp_file = temp_dir / f"temp_speaker_{i}.wav"
                    with open(temp_file, 'wb') as f:
                        f.write(audio_response.content)

                    # Load audio segment
                    segment = AudioSegment.from_wav(temp_file)
                    audio_segments.append(segment)
                    temp_files.append(temp_file)

                    # Add small pause between speakers
                    if i < len(lines) - 1:
                        pause = AudioSegment.silent(duration=500)  # 500ms pause
                        audio_segments.append(pause)
                else:
                    print(f"   ❌ Failed to download audio for line {i+1}")
            else:
                print(f"   ❌ Failed to generate TTS for line {i+1}")

        if audio_segments:
            # Combine all audio segments
            final_audio = sum(audio_segments)

            # Save final conversation in temp_audio directory
            temp_dir = Path("temp_audio")
            temp_dir.mkdir(exist_ok=True)
            output_file = temp_dir / f"conversation_{int(time.time())}.wav"
            final_audio.export(output_file, format="wav")

            # Cleanup temporary files
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                except:
                    pass

            print(f"   ✅ Full conversation saved: {output_file}")
            return output_file

    except Exception as e:
        print(f"   ❌ Error generating conversation audio: {e}")
        return None

def parse_conversation_lines(content):
    """Parse conversation content into (speaker, text) pairs"""
    lines = []

    # Split by lines and find speaker patterns
    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue

        # Look for "Speaker Name: text" pattern
        match = re.match(r'^([^:]+):\s*(.+)$', line)
        if match:
            speaker = match.group(1).strip()
            text = match.group(2).strip()
            lines.append((speaker, text))

    return lines

def generate_speaker_tts(base_url, speaker_name, text):
    """Generate TTS for a specific speaker using custom TTS endpoint"""
    try:
        # Use the new custom TTS endpoint
        response = requests.post(f"{base_url}/generate/custom_tts", json={
            "text": text,
            "personality": speaker_name
        })

        if response.status_code == 200:
            return response.json()
        else:
            print(f"   ❌ Custom TTS failed for {speaker_name}: {response.text}")

    except Exception as e:
        print(f"   ❌ TTS generation error for {speaker_name}: {e}")

    return None

def play_audio_file(file_path):
    """Play an audio file using system default or pydub"""
    try:
        if os.path.exists(file_path):
            # Try pydub first
            try:
                audio = AudioSegment.from_wav(file_path)
                play(audio)
                return True
            except:
                # Fallback to system player
                if os.name == 'nt':  # Windows
                    os.startfile(file_path)
                elif os.name == 'posix':  # macOS/Linux
                    import sys
                    subprocess.run(['open' if sys.platform == 'darwin' else 'xdg-open', file_path])
                return True
        else:
            print(f"   ❌ Audio file not found: {file_path}")
            return False
    except Exception as e:
        print(f"   ❌ Error playing audio: {e}")
        return False

def generate_full_conversation():
    """Generate a full conversation with voices and play it"""
    base_url = "http://localhost:5000"
    print("🎭 Full Conversation Generator")
    print("=" * 40)

    # Generate conversation manually
    generate_manual_conversation(base_url)

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "continuous":
            duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60
            continuous_generation_mode("http://localhost:5000", duration)
        elif sys.argv[1] == "conversation":
            generate_full_conversation()
        else:
            print("Usage:")
            print("  python manual_test.py              - Run manual trigger tests")
            print("  python manual_test.py continuous   - Continuous generation mode")
            print("  python manual_test.py continuous 30 - Continuous for 30 seconds")
            print("  python manual_test.py conversation - Generate full conversation with voices")
    else:
        manual_trigger_test()

        # Ask if user wants to try continuous mode
        try:
            response = input("\n🤔 Try continuous generation mode? (y/n): ")
            if response.lower().startswith('y'):
                duration = input("Duration in seconds (default 30): ")
                duration = int(duration) if duration.isdigit() else 30
                continuous_generation_mode("http://localhost:5000", duration)
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")