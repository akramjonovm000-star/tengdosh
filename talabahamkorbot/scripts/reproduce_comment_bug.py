import asyncio
import sys
import os
import json
import httpx

# Using local IP to bypass Nginx/DNS issues while keeping Host header.
BASE_URL = "http://127.0.0.1:8000/api/v1"
HEADERS = {
    "Host": "tengdosh.uzjoku.uz",
    "User-Agent": "TalabaHamkor-Debug/1.0"
}
LOGIN = "395251101397"
PASSWORD = "ad1870724$"

async def main():
    async with httpx.AsyncClient(timeout=30.0, verify=False, headers=HEADERS) as client:
        print(f"1. Logging in as {LOGIN}...")
        login_resp = await client.post(f"{BASE_URL}/auth/hemis", json={
            "login": LOGIN,
            "password": PASSWORD
        })
        
        if login_resp.status_code != 200:
            print(f"Login Failed: {login_resp.status_code} - {login_resp.text}")
            return

        data = login_resp.json()
        token = data.get("data", {}).get("token")
        
        if not token:
            print("Failed to get token from response (checked data.token).")
            return
            
        print(f"Login Success! Token: {token[:10]}...")
        auth_headers = {"Authorization": f"Bearer {token}"}
        
        print("\n2. Fetching recent posts...")
        posts_resp = await client.get(f"{BASE_URL}/community/posts?category=university&limit=5", headers=auth_headers)
        if posts_resp.status_code != 200:
            print(f"Failed to fetch posts: {posts_resp.status_code} - {posts_resp.text}")
            return
            
        posts = posts_resp.json()
        if not posts:
            print("No posts found to comment on.")
            return
            
        post_id = posts[0]['id']
        print(f"Targeting Post ID: {post_id}")
        
        print(f"\n3. Attempting to post a comment...")
        comment_data = {
            "content": "Test comment from debug script",
            "reply_to_comment_id": None
        }
        
        comment_resp = await client.post(
            f"{BASE_URL}/community/posts/{post_id}/comments", 
            json=comment_data, 
            headers=auth_headers
        )
        
        print(f"Response Status: {comment_resp.status_code}")
        print(f"Response Body: {comment_resp.text}")
        
        if comment_resp.status_code == 200:
            print("SUCCESS: Comment posted")
        else:
            print(f"REPRODUCED/FAILED: Error {comment_resp.status_code}")

if __name__ == "__main__":
    asyncio.run(main())
