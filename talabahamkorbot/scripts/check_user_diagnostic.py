
import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import TgAccount, Staff, Student

async def check():
    async with AsyncSessionLocal() as s:
        target_ids = [7476703866, 395251101397]
        for tid in target_ids:
            print(f"\n--- Checking {tid} ---")
            # Try finding as Telegram ID
            res = await s.execute(select(TgAccount).where(TgAccount.telegram_id == tid))
            acc = res.scalar_one_or_none()
            if acc:
                print(f'Account: id={acc.id}, staff_id={acc.staff_id}, student_id={acc.student_id}, role={acc.current_role}')
                if acc.staff_id:
                    res = await s.execute(select(Staff).where(Staff.id == acc.staff_id))
                    st = res.scalar_one_or_none()
                    if st:
                        print(f'  Linked Staff: id={st.id}, name={st.full_name}, role={st.role}')
                if acc.student_id:
                    res = await s.execute(select(Student).where(Student.id == acc.student_id))
                    stu = res.scalar_one_or_none()
                    if stu:
                        print(f'  Linked Student: id={stu.id}, name={stu.full_name}, login={stu.hemis_login}')
            else:
                # Try finding as HEMIS Login in Student table
                res = await s.execute(select(Student).where(Student.hemis_login == str(tid)))
                stu = res.scalar_one_or_none()
                if stu:
                    print(f'Student found by legacy login: id={stu.id}, name={stu.full_name}')
                    # Find related TgAccount
                    res = await s.execute(select(TgAccount).where(TgAccount.student_id == stu.id))
                    acc = res.scalar_one_or_none()
                    if acc:
                        print(f'  Linked Account: id={acc.id}, staff_id={acc.staff_id}, role={acc.current_role}')
                        if acc.staff_id:
                            res = await s.execute(select(Staff).where(Staff.id == acc.staff_id))
                            st = res.scalar_one_or_none()
                            if st:
                                print(f'    Staff: id={st.id}, role={st.role}')
                else:
                    print('No account or student found')

if __name__ == "__main__":
    asyncio.run(check())
