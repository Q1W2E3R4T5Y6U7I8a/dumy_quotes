import asyncio
import aiohttp
import aiofiles
import os
from pathlib import Path

FOLDER = "downloaded_images"
TOTAL_IMAGES = 1500

async def download_image(session, url, path):
    try:
        async with session.get(url) as response:
            if response.status == 200:
                async with aiofiles.open(path, 'wb') as f:
                    await f.write(await response.read())
                return True
    except Exception as e:
        print(f"Failed: {e}")
    return False

async def main():
    Path(FOLDER).mkdir(exist_ok=True)
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(TOTAL_IMAGES):
            # Random image from Lorem Picsum
            url = f"https://picsum.photos/1024/1024?random={i}"
            path = os.path.join(FOLDER, f"img_{i:04d}.jpg")
            
            if not os.path.exists(path):
                task = download_image(session, url, path)
                tasks.append(task)
                
            # Control concurrency
            if len(tasks) >= 50:
                await asyncio.gather(*tasks)
                tasks = []
                print(f"Downloaded {i+1}/{TOTAL_IMAGES}")
        
        # Download remaining
        if tasks:
            await asyncio.gather(*tasks)
    
    print(f"Done! Downloaded to {FOLDER}")

if __name__ == "__main__":
    asyncio.run(main())