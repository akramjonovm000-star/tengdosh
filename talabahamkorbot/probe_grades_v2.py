import asyncio
import json
from database.db_connect import AsyncSessionLocal
from database.models import StudentCache
from sqlalchemy import select

async def probe():
    async with AsyncSessionLocal() as session:
        # Try to find any cached subjects data
        result = await session.execute(
            select(StudentCache).where(StudentCache.key.like("subjects_%")).limit(5)
        )
        caches = result.scalars().all()
        
        if not caches:
            print("No student cache found.")
            return

        for cache in caches:
            print(f"\n=== Key: {cache.key} ===")
            data = cache.data
            if not data:
                continue
            
            for item in data:
                subj_name = item.get("curriculumSubject", {}).get("subject", {}).get("name")
                grades = item.get("gradesByExam", [])
                overall = item.get("overallScore", {})
                
                print(f"Subject: {subj_name} | Overall: {overall.get('grade')}/{overall.get('max_ball')}")
                
                if grades:
                    for ex in grades:
                        code = ex.get("examType", {}).get("code")
                        name = ex.get("examType", {}).get("name")
                        grade = ex.get("grade")
                        max_b = ex.get("max_ball")
                        print(f"  - Code: {code} | Name: {name} | Grade: {grade}/{max_b}")
                else:
                    print("  - No detailed grades found")
                print("-" * 10)

if __name__ == "__main__":
    asyncio.run(probe())
