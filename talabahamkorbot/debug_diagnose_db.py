
import asyncio
from sqlalchemy import text
from database.db_connect import engine

async def check_db():
    print("--- DB DIAGNOSTIC TOOL ---")
    async with engine.begin() as conn:
        # 1. Check choyxona_comments table
        try:
            await conn.execute(text("SELECT id FROM choyxona_comments LIMIT 1"))
            print("✅ 'choyxona_comments' table exists.")
        except Exception as e:
            print(f"❌ 'choyxona_comments' table MISSING or Error: {e}")

        # 2. Check reply_to_user_id column
        try:
            await conn.execute(text("SELECT reply_to_user_id FROM choyxona_comments LIMIT 1"))
            print("✅ 'reply_to_user_id' column exists.")
        except Exception as e:
            print(f"❌ 'reply_to_user_id' column MISSING! This causes 500 Error.")

        # 3. Check notifications table
        try:
            await conn.execute(text("SELECT id FROM notifications LIMIT 1"))
            print("✅ 'notifications' table exists.")
        except Exception as e:
            print(f"❌ 'notifications' table MISSING! This causes 500 Error during Reply.")

    print("--- DIAGNOSTIC COMPLETE ---")

if __name__ == "__main__":
    try:
        asyncio.run(check_db())
    except ImportError:
        # Fallback if libraries wrong
        print("Error: Could not import DB modules. Ensure you are in 'talabahamkorbot' folder.")
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
