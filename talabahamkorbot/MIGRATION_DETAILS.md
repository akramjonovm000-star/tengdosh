# Server Migration Details

Ushbu hujjat yangi serverga ko'chish uchun kerakli barcha ma'lumotlarni o'z ichiga oladi.

## 1. Ma'lumotlar Bazasi (Database)

*   **Database Turi:** PostgreSQL
*   **Database Nomi:** `talabahamkorbot_db`
*   **Foydalanuvchi (User):** `postgres`
*   **Parol (Password):** `Mukhammadali2623`
*   **Host:** `localhost`
*   **Port:** `5432`

### Backup Fayli
Joriy ma'lumotlar bazasining to'liq nusxasi (backup) quyidagi manzilda tayyorlandi:
*   **Manzil:** `/var/www/talabahamkorbot/latest_backup.sql`
*   **Tiklash uchun buyruq (Yangi serverda):**
    ```bash
    psql -U postgres -h localhost -d talabahamkorbot_db -f latest_backup.sql
    ```

## 2. Loyiha Fayllari

*   **Asosiy papka:** `/var/www/talabahamkorbot`
*   **Environment fayli:** `.env` (barcha maxfiy kalitlar shu yerda)
*   **Talablar (Dependencies):** `requirements.txt`
    *   O'rnatish: `pip install -r requirements.txt`

## 3. Tizim Sozlamalari (Systemd)

Bot odatda `systemd` orqali fonda ishlaydi. 
*   **Service fayli:** Odatda `/etc/systemd/system/talabahamkorbot.service` manzilida bo'ladi.
*   **Taxminiy Service Fayl Namunasi:**

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

[Install]
WantedBy=multi-user.target
```

## 4. Webhook va Domain

*   **Domain:** `tengdoshbozor.uz`
*   **Webhook URL:** `https://tengdoshbozor.uz/webhook/bot`
*   **Nginx Config:** `/etc/nginx/sites-available/default` (yoki domenga mos fayl) ichida `proxy_pass http://127.0.0.1:YOUR_PORT;` bo'lishi kerak.

Agar qo'shimcha yordam kerak bo'lsa, xabar bering!
