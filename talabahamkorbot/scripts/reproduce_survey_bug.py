import asyncio
import sys
import os
import json

# Add parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.hemis_service import HemisService

LOGIN = "395251101397"
PASSWORD = "ad1870724$"

async def main():
    print(f"1. Authenticating as {LOGIN}...")
    token, error = await HemisService.authenticate(LOGIN, PASSWORD)
    
    if not token:
        print(f"Login Failed: {error}")
        return
        
    print(f"Login Success! Token: {token[:10]}...")
    
    print("\n2. Fetching Surveys...")
    surveys = await HemisService.get_student_surveys(token)
    
    target_survey = None
    if surveys and 'data' in surveys:
        # Check finished surveys as per user instruction "Yakunlangan"
        finished = surveys['data'].get('finished', [])
        print(f"Found {len(finished)} finished surveys.")
        
        if finished:
            target_survey = finished[0]
            # Extract ID correctly
            if 'quizRuleProjection' in target_survey and 'id' in target_survey['quizRuleProjection']:
                s_id = target_survey['quizRuleProjection']['id']
            elif 'id' in target_survey:
                s_id = target_survey['id']
            else:
                s_id = None
                
            print(f"Target Survey ID: {s_id}")
            
            if s_id:
                print(f"\n3. Attempting to START survey {s_id} (The Bug Step)...")
                # This calls HemisService.start_student_survey which we patched
                result = await HemisService.start_student_survey(token, s_id)
                
                if result:
                    print("SUCCESS: Survey started/viewed successfully!")
                    print(json.dumps(result, indent=2, ensure_ascii=False))
                else:
                    print("FAILURE: returned None (Check logs for error details)")
        else:
            print("No finished surveys found to test.")
    else:
        print("Failed to fetch survey list.")

if __name__ == "__main__":
    asyncio.run(main())
