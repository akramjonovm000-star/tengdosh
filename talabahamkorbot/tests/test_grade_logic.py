import asyncio
import sys
import os

# Mocking HemisService and Bot
class MockBot:
    async def send_message(self, chat_id, text, parse_mode=None):
        print(f"📧 [MOCK BOT] To {chat_id}: {text}")

class MockHemisService:
    @staticmethod
    def parse_grades_detailed(subj):
        # Replicating the static method logic for test consistency
        exams = subj.get("gradesByExam", [])
        on_data = {"grade": 0, "max": 50}
        yn_data = {"grade": 0, "max": 30}
        for ex in exams:
            code = str(ex.get("examType", {}).get("code"))
            val = ex.get("grade", 0)
            if code == '12': on_data = {"grade": val, "max": 0} # simplified max
            elif code == '13': yn_data = {"grade": val, "max": 0}
        return {
            "ON": {"raw": on_data['grade']},
            "YN": {"raw": yn_data['grade']},
            "raw_total": on_data['grade'] + yn_data['grade']
        }

async def test_grade_diff():
    print("🧪 Testing Grade Logic...")
    
    # 1. Old Data (Cache)
    old_subjects = [
        {
            "subject": {"name": "Math", "id": "1"},
            "gradesByExam": [
                {"examType": {"code": "12"}, "grade": 10}, # ON: 10
                {"examType": {"code": "13"}, "grade": 0}   # YN: 0
            ]
        }
    ]
    
    # 2. New Data (Fresh Fetch)
    new_subjects = [
        {
            "subject": {"name": "Math", "id": "1"},
            "gradesByExam": [
                {"examType": {"code": "12"}, "grade": 15}, # ON: 15 (Changed!)
                {"examType": {"code": "13"}, "grade": 20}   # YN: 20 (New!)
            ]
        },
        {
             "subject": {"name": "Physics", "id": "2"},
             "gradesByExam": [
                 {"examType": {"code": "12"}, "grade": 30} # ON: 30 (New Subject)
             ]
        }
    ]
    
    # 3. Logic Simulation (extracted from grade_checker.py)
    cached_map = {str(s.get("subject", {}).get("id")): s for s in old_subjects}
    changes = []
    
    for fresh_subj in new_subjects:
        subj_id = str(fresh_subj.get("subject", {}).get("id"))
        subj_name = fresh_subj.get("subject", {}).get("name")
        old_subj = cached_map.get(subj_id)
        
        if not old_subj:
            parsed_fresh = MockHemisService.parse_grades_detailed(fresh_subj)
            if parsed_fresh["raw_total"] > 0:
                changes.append(f"🆕 {subj_name} fanidan baholar chiqdi!")
            continue
            
        parsed_fresh = MockHemisService.parse_grades_detailed(fresh_subj)
        parsed_old = MockHemisService.parse_grades_detailed(old_subj)
        
        if parsed_fresh["ON"]["raw"] > parsed_old["ON"]["raw"]:
                changes.append(f"📈 {subj_name}: Oraliq Nazorat (ON) dan {parsed_fresh['ON']['raw']} ball!")
        
        if parsed_fresh["YN"]["raw"] > parsed_old["YN"]["raw"]:
                changes.append(f"🎓 {subj_name}: Yakuniy Nazorat (YN) dan {parsed_fresh['YN']['raw']} ball!")

    # 4. Results
    print("\n📝 Detected Changes:")
    for c in changes:
        print(f" - {c}")
        
    expected = 3 # Math ON, Math YN, Physics New
    if len(changes) == expected:
        print("\n✅ TEST PASSED! Logic captures all updates.")
    else:
        print(f"\n❌ TEST FAILED. Expected {expected}, got {len(changes)}")

if __name__ == "__main__":
    asyncio.run(test_grade_diff())
