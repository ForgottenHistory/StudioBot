import requests
import time
import json
from pathlib import Path

def test_enhanced_radio_system(base_url="http://localhost:5000"):
    """Test the enhanced radio system with dynamic content"""

    print("🎙️ Testing Enhanced AI Radio System")
    print("=" * 60)

    # Test 1: Server status
    print("\n1. Testing enhanced server status...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            status = response.json()
            print(f"✓ Server running on {status['tts_device']}")
            print(f"✓ Topics loaded: {status['topics_loaded']}")
            print(f"✓ Personalities loaded: {status['personalities_loaded']}")
            print(f"✓ Scheduler running: {status['scheduler_running']}")
        else:
            print("✗ Enhanced server not responding")
            return
    except Exception as e:
        print(f"✗ Server connection failed: {e}")
        print("Make sure to run: python enhanced_radio_server.py")
        return

    # Test 2: List topics and personalities
    print("\n2. Testing content loading...")
    try:
        # Test topics
        response = requests.get(f"{base_url}/topics")
        topics = response.json()['topics']
        print(f"✓ Topics available: {', '.join(topics.keys())}")

        # Test personalities
        response = requests.get(f"{base_url}/personalities")
        personalities = response.json()['personalities']
        print(f"✓ Personalities available: {', '.join([p['name'] for p in personalities.values()])}")

    except Exception as e:
        print(f"✗ Content listing failed: {e}")

    # Test 3: Generate dynamic ad
    print("\n3. Testing dynamic ad generation...")
    try:
        # Test with specific topic and personality
        response = requests.get(f"{base_url}/generate/dynamic_ad", params={
            "topic": "food_and_restaurants",
            "personality": "crazy_larry"
        })

        if response.status_code == 200:
            ad_data = response.json()
            print(f"✓ Generated ad for {ad_data['topic']} by {ad_data['personality']}")
            print(f"  Content: {ad_data['content'][:100]}...")

            # Download audio
            audio_url = f"{base_url}{ad_data['audio_url']}"
            audio_response = requests.get(audio_url)
            if audio_response.status_code == 200:
                filename = f"dynamic_ad_{ad_data['topic']}.wav"
                with open(filename, 'wb') as f:
                    f.write(audio_response.content)
                print(f"✓ Audio saved: {filename}")
            else:
                print("✗ Failed to download audio")
        else:
            print(f"✗ Dynamic ad generation failed: {response.text}")

    except Exception as e:
        print(f"✗ Dynamic ad test error: {e}")

    # Test 4: Generate dynamic conversation
    print("\n4. Testing dynamic conversation generation...")
    try:
        response = requests.get(f"{base_url}/generate/dynamic_conversation", params={
            "host": "chuck_radioman",
            "guest": "crazy_larry",
            "topic": "technology_and_gadgets"
        })

        if response.status_code == 200:
            conv_data = response.json()
            print(f"✓ Generated conversation between {conv_data['host']} and {conv_data['guest']}")
            print(f"  Topic: {conv_data['topic']}")
            print(f"  Content preview: {conv_data['content'][:150]}...")
        else:
            print(f"✗ Dynamic conversation generation failed: {response.text}")

    except Exception as e:
        print(f"✗ Dynamic conversation test error: {e}")

    # Test 5: Scheduler functions
    print("\n5. Testing scheduler...")
    try:
        # Check status
        response = requests.get(f"{base_url}/scheduler/status")
        status = response.json()
        print(f"✓ Scheduler status: {'Running' if status['running'] else 'Stopped'}")

        # Start scheduler if not running
        if not status['running']:
            response = requests.post(f"{base_url}/scheduler/start")
            if response.status_code == 200:
                print("✓ Started scheduler")
                time.sleep(2)  # Wait a moment
        else:
            print("✓ Scheduler already running")

        # Check generated content
        response = requests.get(f"{base_url}/generated_content")
        content_data = response.json()
        print(f"✓ Generated content files: {content_data['total_files']}")

    except Exception as e:
        print(f"✗ Scheduler test error: {e}")

    print("\n" + "=" * 60)
    print("🎉 Enhanced system testing completed!")
    print("\nTo use the enhanced features:")
    print("1. Generate themed ads: /generate/dynamic_ad?topic=food&personality=larry")
    print("2. Create conversations: /generate/dynamic_conversation?host=chuck&guest=larry")
    print("3. Start automation: POST /scheduler/start")
    print("4. Browse topics: /topics")
    print("5. Browse personalities: /personalities")

def demo_automation():
    """Demonstrate the automation features"""
    base_url = "http://localhost:5000"

    print("\n🤖 Testing Automation Features")
    print("=" * 40)

    try:
        # Start scheduler
        print("Starting automation...")
        response = requests.post(f"{base_url}/scheduler/start")
        print("✓ Scheduler started")

        print("Waiting 30 seconds to see automated content generation...")
        time.sleep(30)

        # Check generated content
        response = requests.get(f"{base_url}/generated_content")
        content_data = response.json()

        print(f"\nAutomated content generated:")
        for item in content_data['generated_content'][:5]:  # Show latest 5
            print(f"  - {item['filename']} (modified: {item['modified'][:19]})")

        # Stop scheduler
        print("\nStopping automation...")
        response = requests.post(f"{base_url}/scheduler/stop")
        print("✓ Scheduler stopped")

    except Exception as e:
        print(f"✗ Automation demo error: {e}")

def show_content_structure():
    """Show the content file structure"""
    print("\n📁 Content Structure")
    print("=" * 30)

    content_dir = Path("content")
    if content_dir.exists():
        for subdir in ["topics", "personalities"]:
            subdir_path = content_dir / subdir
            if subdir_path.exists():
                print(f"\n{subdir.title()}:")
                for file in subdir_path.glob("*.txt"):
                    print(f"  - {file.stem.replace('_', ' ').title()}")
    else:
        print("Content directory not found")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "automation":
            demo_automation()
        elif sys.argv[1] == "structure":
            show_content_structure()
        else:
            print("Usage: python test_enhanced_system.py [automation|structure]")
    else:
        test_enhanced_radio_system()