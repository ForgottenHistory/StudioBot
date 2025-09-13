# Debug version to see what sessions are available
import asyncio, json, sys
from winsdk.windows.media.control import \
        GlobalSystemMediaTransportControlsSessionManager as SessionManager

async def main():
    print("Starting YouTube Music session detection...")
    manager = await SessionManager.request_async()

    print(f"Manager created: {manager}")

    sessions = manager.get_sessions()
    print(f"Found {len(sessions)} sessions:")

    for i, session in enumerate(sessions):
        try:
            print(f"Session {i}:")
            print(f"  Source app user model id: {session.source_app_user_model_id}")

            props = await session.try_get_media_properties_async()
            if props:
                print(f"  Title: {props.title}")
                print(f"  Artist: {props.artist}")
                print(f"  Album: {props.album_title}")
                print(f"  Playback type: {props.playback_type}")
                print(f"  End time: {props.end_time}")
            else:
                print("  No media properties available")

            info = session.get_playback_info()
            if info:
                print(f"  Playback status: {info.playback_status}")
                print(f"  Playback type: {info.playback_type}")
            else:
                print("  No playback info available")

        except Exception as e:
            print(f"  Error getting session info: {e}")
        print()

    if len(sessions) == 0:
        print("No media sessions found. Make sure YouTube Music is running and playing something.")

if __name__ == "__main__":
    asyncio.run(main())