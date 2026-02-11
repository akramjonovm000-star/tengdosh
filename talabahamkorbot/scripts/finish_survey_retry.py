import httpx
import asyncio
import json

BASE_URL = "https://student.jmcu.uz/rest/v1"
TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJoZW1pcy4zOTUiLCJhdWQiOiJzdHVkZW50IiwiZXhwIjoxNzcxMDM4NzYyLCJqdGkiOiIzOTUyNTExMDIwNDAiLCJzdWIiOiI5MTk1In0.-QVRYmAh7IQ9rR7yKLFtdYNZ2z5iy3Eh2XynKY-y72g"
SURVEY_ID = 4
THEME_ID = 25

async def retry_finish():
    client = httpx.AsyncClient(verify=False, timeout=30.0)
    client.headers["Authorization"] = f"Bearer {TOKEN}"
    
    # Check status first
    print("[-] Checking status...")
    r = await client.get(f"{BASE_URL}/student/survey")
    print(json.dumps(r.json(), indent=4, ensure_ascii=False)[:1000])

    print("\n[-] Retrying Finish...")
    
    attempts = [
        {"quiz_rule_id": SURVEY_ID},
        {"quizRuleId": SURVEY_ID},
        {"ruleId": SURVEY_ID},
        {"rule_id": SURVEY_ID},
    ]
    
    for body in attempts:
        try:
            print(f"POST /student/survey-finish with {body}")
            r = await client.post(f"{BASE_URL}/student/survey-finish", json=body)
            print(f"    Code: {r.status_code}")
            print(f"    Response: {r.text}")
            if r.status_code == 200:
                print("    [!] SUCCESS!")
                break
        except Exception as e:
            print(f"    Error: {e}")

    await client.aclose()

if __name__ == "__main__":
    asyncio.run(retry_finish())
