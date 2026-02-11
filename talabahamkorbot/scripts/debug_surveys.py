import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_connect import AsyncSessionLocal
from database.models import Student
from sqlalchemy import select
from services.hemis_service import HemisService

async def main():
    async with AsyncSessionLocal() as session:
        # Get a student with a token
        result = await session.execute(select(Student).where(Student.hemis_token.isnot(None), Student.hemis_login == '395251101397').limit(1))
        student = result.scalar_one_or_none()
        
        if not student:
            # Fallback to any student
            result = await session.execute(select(Student).where(Student.hemis_token.isnot(None)).limit(1))
            student = result.scalar_one_or_none()
        
        if not student:
            print("No student with token found.")
            return

        print(f"Testing for student: {student.full_name} ({student.id})")
        
        # Test 1: Fetch Surveys
        print("\nFetching Surveys...")
        surveys = await HemisService.get_student_surveys(student.hemis_token)
        
        survey_id = None
        if surveys and 'data' in surveys:
            data = surveys['data']
            print("Surveys fetched successfully.")
            
            # Try to find a finished survey first, as per user report
            all_surveys = []
            if 'finished' in data: all_surveys.extend(data['finished'])
            if 'in_progress' in data: all_surveys.extend(data['in_progress'])
            if 'not_started' in data: all_surveys.extend(data['not_started'])
            
            if all_surveys:
                print(f"First Survey Object: {all_surveys[0]}")
                if 'quizRuleProjection' in all_surveys[0] and 'id' in all_surveys[0]['quizRuleProjection']:
                    survey_id = all_surveys[0]['quizRuleProjection']['id']
                elif 'id' in all_surveys[0]:
                    survey_id = all_surveys[0]['id']
                else:
                     print("Cannot find ID field in survey object")
                     return

                print(f"Target Survey ID: {survey_id}")
            else:
                print("No surveys found in list.")
        else:
            print("Failed to fetch surveys.")

        if survey_id:
            client = await HemisService.get_client()
            headers = HemisService.get_headers(student.hemis_token)
            base_url = HemisService.BASE_URL
            
            print(f"\n--- Testing Endpoints for Survey ID {survey_id} ---")
            
            # Endpoint 1: Current Implementation (Likely 404)
            url1 = f"{base_url}/education/survey-start"
            print(f"Trying: {url1}")
            try:
                r1 = await client.post(url1, headers=headers, json={"id": survey_id})
                print(f"Status: {r1.status_code}")
            except Exception as e:
                print(f"Error: {e}")

            # Endpoint 2: Hypothesis 1 (/student/survey-start)
            url2 = f"{base_url}/student/survey-start"
            print(f"Trying: {url2}")
            try:
                r2 = await client.post(url2, headers=headers, json={"id": survey_id})
                print(f"Status: {r2.status_code}")
                if r2.status_code == 200:
                    print("SUCCESS! This is the correct endpoint.")
            except Exception as e:
                print(f"Error: {e}")

            # Endpoint 3: Hypothesis 2 (/education/survey/start)
            url3 = f"{base_url}/education/survey/start"
            print(f"Trying: {url3}")
            try:
                r3 = await client.post(url3, headers=headers, json={"id": survey_id})
                print(f"Status: {r3.status_code}")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
