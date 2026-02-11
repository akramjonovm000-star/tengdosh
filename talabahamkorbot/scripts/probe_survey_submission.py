import httpx
import asyncio
import json

BASE_URL = "https://student.jmcu.uz/rest/v1"
TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJoZW1pcy4zOTUiLCJhdWQiOiJzdHVkZW50IiwiZXhwIjoxNzcxMDM4NzYyLCJqdGkiOiIzOTUyNTExMDIwNDAiLCJzdWIiOiI5MTk1In0.-QVRYmAh7IQ9rR7yKLFtdYNZ2z5iy3Eh2XynKY-y72g"

QUESTION_ID = 18532104
SURVEY_ID = 4
THEME_ID = 25
ANSWER_TEXT = "yaxshi"
ANSWER_INDEX = 0

async def probe():
    client = httpx.AsyncClient(verify=False, timeout=30.0)
    client.headers["Authorization"] = f"Bearer {TOKEN}"
    
    print("[-] Probing Answer Submission...")
    
    attempts = [
        # Try snake_case
        {"question_id": QUESTION_ID, "answer": ANSWER_TEXT},
        
        # Try just 'id' for question
        {"id": QUESTION_ID, "answer": ANSWER_TEXT},
        
        # Try 'quiz_id'
        {"quiz_id": QUESTION_ID, "answer": ANSWER_TEXT},
        {"quizId": QUESTION_ID, "answer": ANSWER_TEXT},
        
        # Try including survey ID in body
        {"survey_id": SURVEY_ID, "question_id": QUESTION_ID, "answer": ANSWER_TEXT},
        
        # Try URL param for survey ID
        {"url_suffix": f"?id={SURVEY_ID}", "json": {"questionId": QUESTION_ID, "answer": ANSWER_TEXT}},
        {"url_suffix": f"?id={SURVEY_ID}", "json": {"question_id": QUESTION_ID, "answer": ANSWER_TEXT}},
         {"url_suffix": f"?id={SURVEY_ID}", "json": {"quizId": QUESTION_ID, "answer": ANSWER_TEXT}},
    ]
    
    for attempt in attempts:
        url = f"{BASE_URL}/student/survey-answer"
        body = attempt
        
        if "url_suffix" in attempt:
            url += attempt.pop("url_suffix")
            body = attempt.pop("json")

        try:
            print(f"[-] POST {url} with {body}")
            r = await client.post(url, json=body)
            if r.status_code == 200:
                print(f"    [!] SUCCESS: {r.status_code}")
                print(json.dumps(r.json(), indent=4, ensure_ascii=False))
                return
            else:
                print(f"    [-] Failed: {r.status_code} {r.text}")
        except Exception as e:
            print(f"    Error: {e}")

    await client.aclose()

if __name__ == "__main__":
    asyncio.run(probe())
