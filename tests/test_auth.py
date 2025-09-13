import asyncio
import aiohttp

async def test_auth():
    session = aiohttp.ClientSession()
    try:
        resp = await session.post('http://localhost:9863/auth/default')
        data = await resp.json()
        print(f'Status: {resp.status}')
        print(f'Token: {data.get("accessToken", "None")}')

        if resp.status == 200:
            # Test using the token
            headers = {"Authorization": f"Bearer {data['accessToken']}"}
            song_resp = await session.get('http://localhost:9863/api/v1/song', headers=headers)
            print(f'Song API Status: {song_resp.status}')
            if song_resp.status == 200:
                song_data = await song_resp.json()
                print(f'Current Song: {song_data.get("artist")} - {song_data.get("title")}')
                print(f'Duration: {song_data.get("songDuration")}s, Elapsed: {song_data.get("elapsedSeconds")}s')
                print(f'Paused: {song_data.get("isPaused")}')

    except Exception as e:
        print(f'Error: {e}')
    finally:
        await session.close()

asyncio.run(test_auth())