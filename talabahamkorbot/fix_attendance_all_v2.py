import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import Student, StudentCache
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as session:
        # Check all students
        query = select(Student)
        res = await session.execute(query)
        students = res.scalars().all()
        
        fixed = 0
        for s in students:
            # Check semester list
            qs = select(StudentCache).where(StudentCache.student_id == s.id, StudentCache.key == "semesters_list")
            cs = await session.scalar(qs)
            if not cs: continue
            
            # Find current semester
            current_sem = next((x for x in cs.data if x.get('current')), None)
            if not current_sem and cs.data:
                # Use latest semester (highest ID/code)
                try: current_sem = sorted(cs.data, key=lambda x: int(str(x.get('code') or 0)), reverse=True)[0]
                except: pass
            
            if current_sem:
                sem_code = str(current_sem.get('code'))
                qa = select(StudentCache).where(StudentCache.student_id == s.id, StudentCache.key == f"attendance_{sem_code}")
                ca = await session.scalar(qa)
                if ca:
                    # Calculate total
                    total = sum(item.get("hour", 2) for item in ca.data)
                    unexcused = sum(item.get("hour", 2) for item in ca.data if not item.get("explicable"))
                    excused = total - unexcused
                    
                    if s.missed_hours != total:
                        print(f"Fixing {s.full_name} (ID {s.id}): stored={s.missed_hours}, actual={total}")
                        s.missed_hours = total
                        s.missed_hours_excused = excused
                        s.missed_hours_unexcused = unexcused
                        fixed += 1
        
        if fixed > 0:
            await session.commit()
            print(f"Total fixed: {fixed}")

asyncio.run(main())
