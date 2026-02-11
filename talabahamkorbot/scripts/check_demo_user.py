import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import Student, Staff
from sqlalchemy.future import select

async def check_user():
    async with AsyncSessionLocal() as session:
        print("--- Deep Inspection for 'sanjar_botirovich' ---")
        
        # 1. Check Staff by ID 888888 (The hardcoded ID from api/auth.py)
        f_query = select(Staff).where(Staff.hemis_id == 888888)
        f_res = await session.execute(f_query)
        sf = f_res.scalar_one_or_none()
        if sf:
            print(f"FOUND STAFF (ID: 888888):")
            print(f"  Name: {sf.full_name}")
            print(f"  Role: {sf.role}")
            print(f"  Premium: {sf.is_premium}")
            print(f"  Active: {sf.is_active}")
        else:
            print("Staff ID 888888 not found.")

        # 2. Check Staff by JSHSHIR 98765432109876
        j_query = select(Staff).where(Staff.jshshir == "98765432109876")
        j_res = await session.execute(j_query)
        sfj = j_res.scalar_one_or_none()
        if sfj:
            print(f"FOUND STAFF (JSHSHIR: 98765432109876):")
            print(f"  Name: {sfj.full_name}")
            print(f"  Role: {sfj.role}")
            print(f"  Premium: {sfj.is_premium}")
        else:
            print("Staff JSHSHIR 98765432109876 not found.")

        # 3. Check Student by Login 'demo.rahbar'
        s_query = select(Student).where(Student.hemis_login == 'demo.rahbar')
        s_res = await session.execute(s_query)
        st = s_res.scalar_one_or_none()
        if st:
            print(f"FOUND STUDENT (Login: demo.rahbar):")
            print(f"  Name: {st.full_name}")
            print(f"  Role: {st.hemis_role}")
            print(f"  Premium: {st.is_premium}")
        else:
            print("Student login 'demo.rahbar' not found.")

        # 4. Check for any record with "Sanjar Botirovich" in name
        n_query = select(Staff).where(Staff.full_name.ilike('%Sanjar Botirovich%'))
        n_res = await session.execute(n_query)
        sfn = n_res.scalar_one_or_none()
        if sfn:
            print(f"FOUND STAFF BY NAME 'Sanjar Botirovich':")
            print(f"  ID: {sfn.id}, Role: {sfn.role}")

if __name__ == "__main__":
    asyncio.run(check_user())
