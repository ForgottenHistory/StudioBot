import requests
import json
import time
import webbrowser
import os

def test_radio_server(base_url="http://localhost:5000"):
    """Test the radio server functionality"""

    print("🎙️ Testing AI Radio Server")
    print("=" * 50)

    # Test 1: Server status
    print("\n1. Testing server status...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            status = response.json()
            print(f"✓ Server running on {status['tts_device']}")
            print(f"✓ OpenRouter available: {status['openrouter_available']}")
        else:
            print("✗ Server not responding")
            return
    except Exception as e:
        print(f"✗ Server connection failed: {e}")
        print("Make sure to run: python radio_server.py")
        return

    # Test 2: List voices
    print("\n2. Testing voice listing...")
    try:
        response = requests.get(f"{base_url}/voices")
        voices = response.json()
        print(f"✓ Available voices: {', '.join(voices['voices'])}")
    except Exception as e:
        print(f"✗ Voice listing failed: {e}")

    # Test 3: Generate ad
    print("\n3. Testing ad generation...")
    try:
        themes = ["pizza", "cars", "fitness", "technology"]
        theme = themes[0]  # Test with pizza theme

        print(f"Requesting ad about: {theme}")
        response = requests.get(f"{base_url}/generate/ad", params={
            "theme": theme,
            "voice": "announcer"
        })

        if response.status_code == 200:
            ad_data = response.json()
            print(f"✓ Generated ad: {ad_data['content'][:100]}...")
            audio_url = f"{base_url}{ad_data['audio_url']}"
            print(f"✓ Audio available at: {audio_url}")

            # Try to download and play the audio
            audio_response = requests.get(audio_url)
            if audio_response.status_code == 200:
                audio_file = f"test_ad_{theme}.wav"
                with open(audio_file, 'wb') as f:
                    f.write(audio_response.content)
                print(f"✓ Audio saved as: {audio_file}")

                # Try to play it (Windows)
                try:
                    os.system(f'start {audio_file}')
                    print("♪ Playing audio...")
                except:
                    print("→ Play the audio file manually to test")
            else:
                print("✗ Failed to download audio")
        else:
            print(f"✗ Ad generation failed: {response.text}")
    except Exception as e:
        print(f"✗ Ad generation error: {e}")

    # Test 4: Custom speech
    print("\n4. Testing custom speech generation...")
    try:
        custom_text = "Welcome to the AI Radio Server test! This is working great!"

        response = requests.post(f"{base_url}/generate/speech", json={
            "text": custom_text,
            "voice": "host"
        })

        if response.status_code == 200:
            speech_data = response.json()
            print(f"✓ Generated speech for: {speech_data['content'][:50]}...")
            audio_url = f"{base_url}{speech_data['audio_url']}"

            # Download the audio
            audio_response = requests.get(audio_url)
            if audio_response.status_code == 200:
                audio_file = "test_speech_host.wav"
                with open(audio_file, 'wb') as f:
                    f.write(audio_response.content)
                print(f"✓ Speech saved as: {audio_file}")
            else:
                print("✗ Failed to download speech audio")
        else:
            print(f"✗ Speech generation failed: {response.text}")
    except Exception as e:
        print(f"✗ Speech generation error: {e}")

    print("\n" + "=" * 50)
    print("🎉 Server testing completed!")
    print("\nTo use the server:")
    print("1. Start server: python radio_server.py")
    print("2. Generate ads: curl 'http://localhost:5000/generate/ad?theme=pizza'")
    print("3. Custom speech: curl -X POST http://localhost:5000/generate/speech -H 'Content-Type: application/json' -d '{\"text\":\"Hello\",\"voice\":\"host\"}'")
    print("4. Open http://localhost:5000 in browser for status")

def demo_multiple_ads():
    """Generate multiple ads to show variety"""
    base_url = "http://localhost:5000"
    themes = ["pizza", "cars", "fitness", "technology", "fashion", "travel"]

    print("\n🎯 Generating multiple themed ads...")

    for i, theme in enumerate(themes, 1):
        print(f"\n[{i}/{len(themes)}] Generating {theme} ad...")
        try:
            response = requests.get(f"{base_url}/generate/ad", params={
                "theme": theme,
                "voice": "announcer"
            })

            if response.status_code == 200:
                ad_data = response.json()
                print(f"✓ {theme.upper()}: {ad_data['content']}")

                # Download audio
                audio_url = f"{base_url}{ad_data['audio_url']}"
                audio_response = requests.get(audio_url)
                if audio_response.status_code == 200:
                    with open(f"demo_ad_{theme}.wav", 'wb') as f:
                        f.write(audio_response.content)
                    print(f"  → Audio: demo_ad_{theme}.wav")
            else:
                print(f"✗ Failed to generate {theme} ad")

            time.sleep(1)  # Be nice to the server
        except Exception as e:
            print(f"✗ Error with {theme}: {e}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo_multiple_ads()
    else:
        test_radio_server()