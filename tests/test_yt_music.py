# ytm_now.py  –  run in background, prints JSON at every track change
import asyncio, json, sys, os

# Set UTF-8 encoding for Windows console
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from winsdk.windows.media.control import \
        GlobalSystemMediaTransportControlsSessionManager as SessionManager

def fmt(props, playback_info=None):
    data = {
        "title": props.title or "Unknown",
        "artist": props.artist or "Unknown Artist",
        "album": props.album_title or "",
    }

    # Add playback status if available
    if playback_info:
        data["status"] = str(playback_info.playback_status)

    return json.dumps(data, ensure_ascii=False)

async def main():
    manager = await SessionManager.request_async()
    last = None
    print("Monitoring YouTube Music for track changes...", flush=True)

    while True:
        for s in manager.get_sessions():
            # Only monitor YouTube Music sessions
            if hasattr(s, 'source_app_user_model_id') and \
               'youtube-music' in s.source_app_user_model_id:
                try:
                    props = await s.try_get_media_properties_async()
                    if props and props.title:
                        playback_info = s.get_playback_info()
                        cur = fmt(props, playback_info)
                        if cur != last:
                            print(cur, flush=True)
                            last = cur
                except Exception as e:
                    # Uncomment for debugging
                    # print(f"Error: {e}", file=sys.stderr)
                    pass
        await asyncio.sleep(0.5)  # Check more frequently

if __name__ == "__main__":
    asyncio.run(main())