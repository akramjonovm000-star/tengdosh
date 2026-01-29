
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import StudentFeedback, Student
from api.schemas import FeedbackListSchema
from datetime import datetime

async def verify_logic():
    async with AsyncSessionLocal() as session:
        # 1. Fetch some feedbacks
        stmt = select(StudentFeedback).limit(5)
        result = await session.execute(stmt)
        results = result.scalars().all()
        
        print(f"Found {len(results)} feedbacks in DB")
        
        response_list = []
        
        print("\n--- Testing Logic ---")
        try:
            for fb in results:
                print(f"Processing ID {fb.id}...")
                
                # 1. Compute Title
                display_title = f"Murojaat #{fb.id}"
                if fb.text:
                     clean_text = fb.text.replace("\n", " ").strip()
                     if clean_text:
                         display_title = clean_text[:30] + "..." if len(clean_text) > 30 else clean_text
                
                # 2. Build Dict
                item = {
                    "id": fb.id,
                    "text": fb.text,
                    "title": display_title,
                    "status": fb.status,
                    "assigned_role": fb.assigned_role,
                    "created_at": fb.created_at, 
                    "is_anonymous": fb.is_anonymous
                }
                response_list.append(item)
                print(f"  -> Generated Item: {item['title']} (Status: {item['status']})")
                
            print("\n--- Testing Schema Validation ---")
            # 3. Simulate FastAPI Validation
            validated = [FeedbackListSchema.model_validate(x) for x in response_list]
            print("✅ Validation Successful!")
            for v in validated:
                print(f"  -> Validated: {v.title}")
                
        except Exception as e:
            print(f"❌ LOGIC ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_logic())
