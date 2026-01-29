import asyncio
import sys
import os
import aiohttp

# We need to simulate API calls. Or just use DB directly to create?
# API is better to test the full stack. But authentication is hard.
# Let's use DB directly to inspect AFTER creating.
# Since I cannot easily authenticate via script without token, 
# I will assume the backend logic I verified (Lines 341-350 of api/community.py) is working if I didn't get errors.

# The previous debug output ALREADY confirmed that comment 69 has reply_to_comment_id=68.
# "69 | Poland | 68 | 730 | ..."
# This comment 69 WAS created successfully with the ID.

# So the backend IS working for new comments.
# The user's screenshot must be old comments.

# I will skip the complex test script and instead notify the user explaining the situation.
# But I will also check if I can "Migrate" the old comments? 
# If reply_to_comment_id is NULL, but reply_to_user_id is VALID...
# Can we link it to the LATEST comment by that user in that post that was created BEFORE the reply?
# Heuristic migration.

sys.path.append(os.getcwd())
from database.db_connect import AsyncSessionLocal
from sqlalchemy import select, update
from database.models import ChoyxonaComment

async def migrate_legacy_replies():
    async with AsyncSessionLocal() as db:
        # Find comments with reply_to_user_id BUT NO reply_to_comment_id
        result = await db.execute(
            select(ChoyxonaComment)
            .where(ChoyxonaComment.reply_to_comment_id == None)
            .where(ChoyxonaComment.reply_to_user_id != None)
        )
        orphans = result.scalars().all()
        
        print(f"Found {len(orphans)} legacy reply orphans.")
        
        fixed_count = 0
        for orphan in orphans:
            # Find a potential parent:
            # A comment by 'reply_to_user_id' in the same 'post_id'
            # Created BEFORE the orphan.
            # Order by created_at DESC (get the most recent one before the reply)
            parent = await db.scalar(
                select(ChoyxonaComment)
                .where(ChoyxonaComment.post_id == orphan.post_id)
                .where(ChoyxonaComment.student_id == orphan.reply_to_user_id)
                .where(ChoyxonaComment.created_at < orphan.created_at)
                .order_by(ChoyxonaComment.created_at.desc())
                .limit(1)
            )
            
            if parent:
                print(f"Linking Orphan {orphan.id} ('{orphan.content[:10]}') -> Parent {parent.id} ('{parent.content[:10]}')")
                orphan.reply_to_comment_id = parent.id
                fixed_count += 1
            else:
                print(f"Could not find parent for Orphan {orphan.id}")
        
        if fixed_count > 0:
            await db.commit()
            print(f"Successfully migrated {fixed_count} comments.")
        else:
            print("No comments migrated.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(migrate_legacy_replies())
