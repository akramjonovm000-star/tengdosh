
import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import StudentNotification

async def test():
    async with AsyncSessionLocal() as session:
        n = StudentNotification(
            student_id=730, 
            title='Test xabarnoma', 
            body='Tizim tuzatildi! Bell icon endi ishlayapti.', 
            type='alert' # Using alert for red icon
        )
        session.add(n)
        await session.commit()
        print('Test notification created for 730')

if __name__ == "__main__":
    asyncio.run(test())
