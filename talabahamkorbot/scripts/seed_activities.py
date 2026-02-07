import asyncio
import random
from datetime import datetime, timedelta
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student, UserActivity, UserActivityImage

CATEGORIES = ["Sport", "Ilmiy", "Ma'naviy", "Volontyorlik", "Tadbir"]
DESCRIPTIONS = [
    "Universitet miqyosidagi tadbirda qatnashdim.",
    "Maqola yozdim va chop yetildi.",
    "Zakovat o'yinida 1-o'rinni oldik.",
    "Shanbalikda faol ishtirok etdim.",
    "Hech qanday izoh yo'q."
]
IMAGES = [
    "https://picsum.photos/200/300",
    "https://picsum.photos/400/300", 
    None
]

async def seed_activities():
    async with AsyncSessionLocal() as db:
        # Get all students with groups
        result = await db.execute(select(Student).where(Student.group_number.is_not(None)))
        students = result.scalars().all()
        
        if not students:
            print("No students found with groups. Cannot seed activities.")
            return

        # Clear existing activities
        print("Clearing existing activities...")
        await db.execute(select(UserActivity)) # Just to ensure we're connected? No, delete
        from sqlalchemy import delete
        await db.execute(delete(UserActivityImage))
        await db.execute(delete(UserActivity))
        await db.commit()
        print("Cleared.")

        print(f"Found {len(students)} students. Generating limited activities...")
        
        count = 0
        for student in students:
            # Generate 0-1 activities per student (Sparse)
            if random.random() > 0.3: # 30% chance of having activity
                continue
                
            num_activities = 1
            
            for _ in range(num_activities):
                is_today = random.random() > 0.3 # 70% chance of being today
                date_offset = 0 if is_today else random.randint(1, 4)
                created_at = datetime.utcnow() - timedelta(days=date_offset)
                
                status = "pending"
                if not is_today:
                    status = random.choice(["pending", "accepted", "rejected"])
                
                activity = UserActivity(
                    student_id=student.id,
                    category=random.choice(CATEGORIES),
                    name=f"Demo Faollik #{random.randint(1000, 9999)}",
                    description=random.choice(DESCRIPTIONS),
                    status=status,
                    created_at=created_at,
                    date=created_at.strftime("%Y-%m-%d")
                )
                db.add(activity)
                await db.flush() # Get ID
                
                # Add image randomly
                img_url = random.choice(IMAGES)
                if img_url:
                    img = UserActivityImage(
                        activity_id=activity.id,
                        file_id=img_url, # Using URL as file_id for demo
                        file_type="photo"
                    )
                    db.add(img)
                
                count += 1
        
        await db.commit()
        print(f"Successfully added {count} demo activities.")

if __name__ == "__main__":
    asyncio.run(seed_activities())
