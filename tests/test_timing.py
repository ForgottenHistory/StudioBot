# Test timing information from Windows Media API
import asyncio
import sys
import os
from datetime import timedelta

if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

from winsdk.windows.media.control import \
    GlobalSystemMediaTransportControlsSessionManager as SessionManager

async def main():
    manager = await SessionManager.request_async()

    print("🔍 Testing timing information from YouTube Music...")

    while True:
        for session in manager.get_sessions():
            if (hasattr(session, 'source_app_user_model_id') and
                'youtube-music' in session.source_app_user_model_id):

                try:
                    props = await session.try_get_media_properties_async()
                    if props and props.title:
                        print(f"\n🎵 Track: {props.artist} - {props.title}")

                        # Check available timing properties
                        print("Available properties:")
                        for attr in dir(props):
                            if not attr.startswith('_'):
                                try:
                                    value = getattr(props, attr)
                                    if 'time' in attr.lower() or 'duration' in attr.lower():
                                        print(f"  {attr}: {value}")
                                except:
                                    pass

                        # Check timeline properties
                        timeline = session.get_timeline_properties()
                        if timeline:
                            print("Timeline properties:")
                            for attr in dir(timeline):
                                if not attr.startswith('_'):
                                    try:
                                        value = getattr(timeline, attr)
                                        print(f"  {attr}: {value}")
                                    except Exception as e:
                                        print(f"  {attr}: Error - {e}")

                        print("-" * 50)

                except Exception as e:
                    print(f"Error: {e}")

        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())