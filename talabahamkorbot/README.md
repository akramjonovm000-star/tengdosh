# talabahamkorbot — OWNER MODUL (boshlang'ich versiya)

Bu katalogda sizning talabahamkorbot loyihangiz uchun **owner + autentifikatsiya** qismi
tayyorlangan. Fayllarni zip qilib serverga (`/var/www/talabahamkorbot`) yuklab,
`pip install -r requirements.txt` qilasiz va `python3 main.py` bilan ishga tushirishingiz mumkin.

### Asosiy texnologiyalar

- Python 3.10+
- aiogram 3.7 (webhook bilan)
- aiohttp
- SQLAlchemy async + asyncpg
- PostgreSQL (`talabahamkorbot_db` bazasi, `postgres` useri, parol: `Mukhammadali2623`)

### Sozlamalar

`config.py` ichida:
- `BOT_TOKEN` — siz bergan token: `8585027447:AAGhaZCoUbOphe9FX6qTZuSgFCUSLxeojKg`
- `OWNER_TELEGRAM_ID` — 387178074
- `DATABASE_URL` — `postgresql+asyncpg://postgres:Mukhammadali2623@localhost:5432/talabahamkorbot_db`
- `WEBHOOK_URL` — `https://tengdoshbozor.uz/webhook/bot`

Agar kerak bo'lsa, keyinchalik `.env` bilan o'zgartirib ishlatish mumkin.

### Strukturasi (qisqacha)

- `main.py` — aiohttp + aiogram webhook server (8000-port)
- `bot.py` — `Bot` va `Dispatcher` obyektlari
- `config.py` — token, DB, webhook, owner ID
- `database/db_connect.py` — async engine, session, Base
- `database/models.py` — `University`, `Faculty`, `Staff`, `Student`, `TgAccount`
- `middlewares/db.py` — har update uchun `AsyncSession` middleware
- `models/states.py` — FSM holatlar (`AuthStates`, `OwnerStates`)
- `keyboards/reply_kb.py` — start va owner menyu tugmalari
- `keyboards/inline_kb.py` — qayta urinish / bosh menyu inline tugmalari
- `handlers/auth.py` — /start, xodim (JSHSHIR) va talaba (HEMIS) autentifikatsiyasi
- `handlers/owner.py` — owner / developer menyusi (OTM, import, e'lon, developer, sozlamalar)
- `utils/logging_config.py` — logging konfiguratsiyasi
- `requirements.txt` — kerakli paketlar ro'yxati

### Keyingi bosqichlar

1. Excel shablonlarini (universitet, fakultet, xodim, talaba) import qilish logikasini to'ldirish.
2. Owner menyusidagi har bir bo'lim uchun to'liq mantiq (kanal talablari, grant taqsimoti sozlamalari, eksport/import).
3. Rahbariyat / dekanat / tyutor modullari.
4. Talaba moduli (hujjat yuklash, faolliklar, sertifikatlar va h.k.).

Hozircha eng muhimi — **owner modulining ishonchli start nuqtasi** va
**database strukturasining skeleti** tayyor.
