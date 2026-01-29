
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from sqlalchemy import select, update
from database.db_connect import AsyncSessionLocal
from database.models import Student

async def inject_credentials(login, password):
    print(f"Injecting credentials for {login}...")
    async with AsyncSessionLocal() as session:
        # Check if student exists
        result = await session.execute(select(Student).where(Student.hemis_login == login))
        student = result.scalar_one_or_none()
        
        if student:
            print(f"Found student ID: {student.id}. Updating password...")
            student.hemis_password = password
            # Ensure hemis_id matches login if not set (often same)
            if not student.hemis_id:
                student.hemis_id = login
            
            await session.commit()
            print("Password updated successfully.")
        else:
            print("Student not found. Creating new record...")
            # Create a placeholder student 
            new_student = Student(
                full_name="User (Manual Inject)",
                hemis_login=login,
                hemis_password=password,
                hemis_id=login,
                status="active"
            )
            session.add(new_student)
            await session.commit()
            print(f"Created new student with ID: {new_student.id}")

if __name__ == "__main__":
    # Credentials from User logs/request
    LOGIN = "395251101411"
    # We don't know the password from logs (hidden), but the goal is to make it work.
    # Wait, if I don't know the password, how can the user login via DB matching?
    # The user enters the password in the App. The App sends it to the api.
    # The API checks if DB.password == Input.password.
    # So the DB must have the correct password.
    # Since I cannot know the password, I will query the DB to see if it HAS a password.
    # If it does, I assume it's correct (from previous bot usage).
    # If not, I can't inject a fake one, or it won't match.
    
    # Correction: I will write a script to CHECK credentials existence first.
    pass

async def check_credentials(login):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Student).where(Student.hemis_login == login))
        student = result.scalar_one_or_none()
        if student:
            print(f"Student Found: {student.full_name}")
            print(f"Has Password? {'YES' if student.hemis_password else 'NO'}")
            if student.hemis_password:
                print(f"Stored Password: {student.hemis_password}")
        else:
            print("Student NOT found in Database.")

if __name__ == "__main__":
    LOGIN = "395251101411"
    asyncio.run(check_credentials(LOGIN))
