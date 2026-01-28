# Botni Yangi Serverga Ko'chirish Qo'llanmasi

Ushbu qo'llanma loyihani yangi Ubuntu serverga noldan o'rnatish va ishga tushirish jarayonini qadam-ba-qadam tushuntiradi.

## 1. Tayyorgarlik (Serverda)

Serveringizga kiring va kerakli dasturlarni o'rnating:

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib libpq-dev zip unzip
```

## 2. Fayllarni Joylashtirish

1. **Faylni yuklash:** `database_files_full.zip` va source kodingizni serverga yuklang (masalan, `/var/www/talabahamkorbot` papkasiga).
2. **Arxivdan chiqarish:**

```bash
mkdir -p /var/www/talabahamkorbot
cd /var/www/talabahamkorbot
# Source kodni ochish (agar u alohida zip bo'lsa)
unzip source_code.zip
# Database fayllarini ochish
unzip database_files_full.zip
```

## 3. Python Muhitini Sozlash

```bash
cd /var/www/talabahamkorbot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

> **Eslatma:** Agar `requirements.txt` da xatolik bo'lsa, `pip install aiogram sqlalchemy asyncpg python-dotenv alembic psycopg2-binary pandas openpyxl` buyrug'ini qo'lda ishlating.

## 4. Ma'lumotlar Bazasini Tiklash

PostgreSQL da baza va foydalanuvchi yarating:

```bash
sudo -u postgres psql
```

psql ichida:
```sql
CREATE DATABASE talabahamkorbot_db;
CREATE USER postgres WITH ENCRYPTED PASSWORD 'Mukhammadali2623';
GRANT ALL PRIVILEGES ON DATABASE talabahamkorbot_db TO postgres;
\q
```

Endi backup faylni qayta tiklaymiz:

```bash
# Agar parolni so'rasa: Mukhammadali2623
psql -U postgres -h localhost -d talabahamkorbot_db -f talabahamkorbot_db_backup.sql
```

## 5. .env Faylni Sozlash

Yangi serverda `.env` fayl yaratib, ma'lumotlarni to'g'rilang:

```bash
nano .env
```

Fayl ichiga quyidagilarni yozing (o'zingizning ma'lumotlaringiz bilan):

```ini
BOT_TOKEN=8585027447:AAGhaZCoUbOphe9FX6qTZuSgFCUSLxeojKg
BOT_USERNAME=talabahamkorbot
OWNER_TELEGRAM_ID=387178074
DOMAIN=sizning-yangi-domeningiz.uz
WEBHOOK_URL=https://sizning-yangi-domeningiz.uz/webhook/bot

DB_HOST=localhost
DB_NAME=talabahamkorbot_db
DB_USER=postgres
DB_PASSWORD=Mukhammadali2623
DB_PORT=5432
```

Saqlash uchun: `Ctrl+O`, `Enter`, keyin `Ctrl+X`.

## 6. Ishga Tushirish

Botni tekshirib ko'rish:

```bash
./venv/bin/python3 main.py
```

Agar xatolik chiqmasa, `Ctrl+C` bossin va `systemd` orqali doimiy ishga tushiring.

### Systemd Service (Fonda ishlatish)

```bash
sudo nano /etc/systemd/system/talabahamkorbot.service
```

Quyidagini yozing:

```ini
[Unit]
Description=TalabaHamkor Telegram Bot
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/talabahamkorbot
ExecStart=/var/www/talabahamkorbot/venv/bin/python3 main.py
Restart=always
RestartSec=5
EnvironmentFile=/var/www/talabahamkorbot/.env

[Install]
WantedBy=multi-user.target
```

Service ni ishga tushirish:

```bash
sudo systemctl daemon-reload
sudo systemctl enable talabahamkorbot
sudo systemctl start talabahamkorbot
```

Statusni tekshirish:
```bash
sudo systemctl status talabahamkorbot
```

---
**Muammolar davom etsa:**
1. Loglarni tekshiring: `journalctl -u talabahamkorbot -f`
2. `python3 main.py` ni qo'lda yurgizib ko'ring, qanday xato chiqayotganini ko'rish uchun.
