import asyncio
import os
import sys
from sqlalchemy import select, func
from collections import defaultdict
from datetime import datetime
from aiogram import Bot
from aiogram.types import FSInputFile

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import BOT_TOKEN, OWNER_TELEGRAM_ID
from database.db_connect import AsyncSessionLocal
from database.models import User

async def main():
    print("Generating minimal report...")
    async with AsyncSessionLocal() as session:
        # Fetch data: Group by Faculty and Specialty
        # specific query to count directly in DB would be more efficient, 
        # but iterating is fine for <1000 users and gives flexibility if we need to clean names.
        query = select(User.faculty_name, User.specialty_name).where(User.role == 'student')
        
        result = await session.execute(query)
        rows = result.all()
        
        # Aggregate
        stats = defaultdict(lambda: defaultdict(int))
        total_users = 0
        
        for fac, spec in rows:
            fac_name = fac or "Noma'lum Fakultet"
            spec_name = spec or "Noma'lum Yo'nalish"
            stats[fac_name][spec_name] += 1
            total_users += 1
            
        # Format Report
        lines = []
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        lines.append(f"📊 **PLATFORMA STATISTIKASI (MINIMAL)**")
        lines.append(f"📅 Vaqt: {now}")
        lines.append(f"👥 Jami foydalanuvchilar: **{total_users}** nafar\n")
        lines.append("────────────────────────")
        
        for fac, specs in sorted(stats.items()):
            # Calculate faculty total
            fac_total = sum(specs.values())
            lines.append(f"🔹 **{fac}** ({fac_total})")
            
            for spec, count in sorted(specs.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"   ▫️ {spec}: **{count}**")
            
            lines.append("") # Spacer
            
        report_text = "\n".join(lines)
        print(report_text)
        
        # Save to file (optional, but good for record)
        output_dir = "reports"
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{output_dir}/minimal_hisobot_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report_text)
            
        # Send via Telegram
        if BOT_TOKEN and OWNER_TELEGRAM_ID:
            try:
                bot = Bot(token=BOT_TOKEN)
                # Send as message first (since it's minimal and likely short enough)
                # If too long, maybe split or send as file. 
                # 4096 is limit. With 150 users it should fit, but with many majors it might not.
                # Let's send as file to be safe and clean.
                file_input = FSInputFile(filename)
                await bot.send_document(
                    chat_id=OWNER_TELEGRAM_ID,
                    document=file_input,
                    caption=f"📊 **Minimal Hisobot**\n\nFakultet va Yo'nalishlar kesimida statistika."
                )
                
                # Also try to send as text if checks pass length
                if len(report_text) < 4000:
                     await bot.send_message(
                        chat_id=OWNER_TELEGRAM_ID,
                        text=report_text,
                        parse_mode="Markdown"
                    )

                print("Sent to Telegram.")
                await bot.session.close()
            except Exception as e:
                print(f"Failed to send telegram: {e}")

if __name__ == "__main__":
    asyncio.run(main())
