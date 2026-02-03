import asyncio
import httpx
import re

async def get_video_id(query):
    async with httpx.AsyncClient() as client:
        # Search YouTube
        response = await client.get(f"https://www.youtube.com/results?search_query={query}")
        html = response.text
        
        # Find first video ID
        # Pattern for video IDs in script variables usually
        video_ids = re.findall(r"\"videoId\":\"([a-zA-Z0-9_-]{11})\"", html)
        
        if video_ids:
            return video_ids[0]
        return None

async def main():
    query = "mcr i dont love you"
    video_id = await get_video_id(query)
    print(f"Query: {query}")
    print(f"Video ID: {video_id}")
    print(f"URL: https://www.youtube.com/watch?v={video_id}" if video_id else "Not found")

if __name__ == "__main__":
    asyncio.run(main())
