import time
import requests
import asyncio
import aiohttp
import json

URL = "http://localhost:8000/webhook/bot"
PAYLOAD = {
    "update_id": 123456789,
    "message": {
        "message_id": 1,
        "from": {
            "id": 123456,
            "is_bot": False,
            "first_name": "Test",
            "username": "testuser",
            "language_code": "en"
        },
        "chat": {
            "id": 123456,
            "first_name": "Test",
            "type": "private"
        },
        "date": int(time.time()),
        "text": "/start",
        "entities": [{"offset": 0, "length": 6, "type": "bot_command"}]
    }
}

async def benchmark():
    print(f"Sending POST request to {URL}...")
    start = time.time()
    async with aiohttp.ClientSession() as session:
        async with session.post(URL, json=PAYLOAD) as resp:
            text = await resp.text()
            print(f"Status: {resp.status}")
            print(f"Response: {text}")
    end = time.time()
    print(f"Time taken: {end - start:.4f} seconds")

if __name__ == "__main__":
    asyncio.run(benchmark())
