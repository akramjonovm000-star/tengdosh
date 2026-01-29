import asyncio
import json
from services.hemis_service import HemisService

# User Token
USER_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJ2MVwvYXV0aFwvbG9naW4iLCJhdWQiOiJ2MVwvYXV0aFwvbG9naW4iLCJleHAiOjE3NjkxNjE4OTcsImp0aSI6IjM5NTI1MTEwMTQxMSIsInN1YiI6IjgzMDAifQ.Wxer16yq1E5eSJT7x2aLqTPRWO_TljCIkQsbEJ-2NHg"

async def main():
    print("Fetching Subject List...")
    data = await HemisService.get_student_subject_list(USER_TOKEN)
    
    if data:
        # Find "MEDIADA AXBOROT..." or "PR VA REKLAMA"
        target = next((item for item in data if "MEDIADA" in item.get("curriculumSubject", {}).get("subject", {}).get("name", "")), None)
        
        if target:
            print("\nFOUND TARGET SUBJECT:")
            print(json.dumps(target, indent=2))
        else:
            print("\nTarget subject not found, dumping first item:")
            print(json.dumps(data[0], indent=2))
    else:
        print("No data.")

if __name__ == "__main__":
    asyncio.run(main())
