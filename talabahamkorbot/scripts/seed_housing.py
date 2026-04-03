import asyncio
from datetime import datetime
from database.db_connect import AsyncSessionLocal
from database.models import MarketItem, MarketCategory, Student
from sqlalchemy import select

async def populate_mock_housing():
    async with AsyncSessionLocal() as db:
        # Get a real student to associate with
        result = await db.execute(select(Student).limit(1))
        student = result.scalar_one_or_none()
        
        if not student:
            print("No students found in DB. Please register at least one student first.")
            return

        print(f"Adding mock housing items for student: {student.full_name}")

        mock_items = [
            {
                "title": "Chilonzor 9-kvartal, 2 xonali kvartira bo'sh 🏠",
                "description": "Talaba yigitlar uchun joy bor. Hamma sharoitlar bor: kir yuvish mashinasi, muzlatgich, Wi-Fi. Universitetga yaqin.",
                "price": "100$",
                "contact_phone": "+998 90 123 4567",
                "telegram_username": "talaba_home"
            },
            {
                "title": "Ijaraga sherik kerak (qizlar uchun) 👭",
                "description": "O'zMU talabasiман. Beruniy metrosi yaqinida kvartira bor, 1 ta sherik kerak. Uy tinch va ozoda.",
                "price": "800.000 so'm",
                "contact_phone": "+998 93 777 8899",
                "telegram_username": "student_girl"
            },
            {
                "title": "Novza metrosi yaqinida hovli uy 🏡",
                "description": "4 nafar talaba uchun alohida xonalar. Egalari bilan emas. Hamma jihozlari bilan.",
                "price": "1.200.000 so'm",
                "contact_phone": "+998 94 444 5566",
                "telegram_username": "islom_property"
            }
        ]

        for item_data in mock_items:
            item = MarketItem(
                student_id=student.id,
                title=item_data["title"],
                description=item_data["description"],
                price=item_data["price"],
                category=MarketCategory.HOUSING.value,
                contact_phone=item_data["contact_phone"],
                telegram_username=item_data["telegram_username"],
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.add(item)
        
        await db.commit()
        print("✅ Mock housing items added successfully!")

if __name__ == "__main__":
    asyncio.run(populate_mock_housing())
