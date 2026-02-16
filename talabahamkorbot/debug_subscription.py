import asyncio
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, func
from database.db_connect import AsyncSessionLocal
from database.models import Student, StudentSubscription

async def debug_subscription():
    async with AsyncSessionLocal() as db:
        print("--- DEBUGGING SUBSCRIPTION ---")
        
        # 1. Get a random student to be the follower
        follower = await db.scalar(select(Student).limit(1))
        if not follower:
            print("No students found.")
            return

        # 2. Get another student to be the target
        target = await db.scalar(select(Student).where(Student.id != follower.id).limit(1))
        if not target:
            print("Not enough students to test subscription.")
            return

        print(f"Follower: {follower.id} ({follower.full_name})")
        print(f"Target: {target.id} ({target.full_name})")

        # 3. Check existing subscription
        existing = await db.scalar(
            select(StudentSubscription).where(
                StudentSubscription.follower_id == follower.id,
                StudentSubscription.target_id == target.id
            )
        )
        print(f"Initial Subscription State: {'Subscribed' if existing else 'Not Subscribed'}")

        # 4. Simulate Toggle (Subscribe)
        if not existing:
            print("Attempting to SUBSCRIBE...")
            new_sub = StudentSubscription(follower_id=follower.id, target_id=target.id)
            db.add(new_sub)
            await db.commit()
            print("Subscribed successfully (DB commit).")
        else:
            print("Already subscribed. Skipping subscribe test.")

        # 5. Verify Subscribe
        check = await db.scalar(
            select(StudentSubscription).where(
                StudentSubscription.follower_id == follower.id,
                StudentSubscription.target_id == target.id
            )
        )
        print(f"Post-Subscribe Check: {'Found' if check else 'Not Found'}")

        # 6. Simulate Toggle (Unsubscribe)
        if check:
            print("Attempting to UNSUBSCRIBE...")
            await db.delete(check)
            await db.commit()
            print("Unsubscribed successfully (DB commit).")
        
        # 7. Verify Unsubscribe
        check_final = await db.scalar(
            select(StudentSubscription).where(
                StudentSubscription.follower_id == follower.id,
                StudentSubscription.target_id == target.id
            )
        )
        print(f"Post-Unsubscribe Check: {'Found' if check_final else 'Gone'}")

if __name__ == "__main__":
    asyncio.run(debug_subscription())
