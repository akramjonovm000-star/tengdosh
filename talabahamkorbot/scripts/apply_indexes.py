import asyncio
from sqlalchemy import text
from database.db_connect import AsyncSessionLocal

async def apply_indexes():
    async with AsyncSessionLocal() as db:
        print("Applying indexes...")
        queries = [
            "CREATE INDEX IF NOT EXISTS idx_student_group_number ON students(group_number);",
            "CREATE INDEX IF NOT EXISTS idx_user_activity_status ON user_activities(status);",
            "CREATE INDEX IF NOT EXISTS idx_user_activity_created_at ON user_activities(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_user_activity_image_activity_id ON user_activity_images(activity_id);",
            "CREATE INDEX IF NOT EXISTS idx_user_document_student_id ON user_documents(student_id);",
            "CREATE INDEX IF NOT EXISTS idx_user_document_category ON user_documents(category);",
            "CREATE INDEX IF NOT EXISTS idx_student_feedback_target_hemis_id ON student_feedback(target_hemis_id);",
            "CREATE INDEX IF NOT EXISTS idx_student_feedback_status ON student_feedback(status);"
        ]
        
        for query in queries:
            try:
                await db.execute(text(query))
                print(f"Executed: {query}")
            except Exception as e:
                print(f"Error executing {query}: {e}")
        
        await db.commit()
        print("Finished applying indexes.")

if __name__ == "__main__":
    asyncio.run(apply_indexes())
