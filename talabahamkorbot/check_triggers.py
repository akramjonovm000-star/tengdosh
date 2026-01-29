
import asyncio
from sqlalchemy import text
from database.db_connect import engine

async def check_triggers():
    async with engine.connect() as conn:
        res = await conn.execute(text("""
            SELECT trigger_name, event_manipulation, event_object_table, action_statement
            FROM information_schema.triggers
            WHERE event_object_table = 'student_feedback';
        """))
        triggers = res.all()
        if triggers:
            for t in triggers:
                print(f"Trigger: {t.trigger_name}, Event: {t.event_manipulation}, Table: {t.event_object_table}")
                print(f"Action: {t.action_statement}")
        else:
            print("No triggers found on student_feedback.")

if __name__ == "__main__":
    asyncio.run(check_triggers())
