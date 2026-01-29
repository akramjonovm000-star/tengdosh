import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.reminder_service import sync_all_students_weekly_schedule, run_lesson_reminders

async def manual_trigger():
    print("--- 1. Running Weekly Sync (For Tomorrow & Week) ---")
    await sync_all_students_weekly_schedule()
    
    print("\n--- 2. Checking Reminders (Simulated) ---")
    # Note: Reminder check relies on current time. 
    # If no lesson starts in 30 mins from NOW, no message is sent.
    await run_lesson_reminders()
    print("--- Done ---")

if __name__ == "__main__":
    asyncio.run(manual_trigger())
