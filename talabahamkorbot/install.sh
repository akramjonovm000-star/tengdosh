#!/bin/bash
set -e

# Ranglar
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}>>> TalabaHamkorBot Avtomatik O'rnatish Skripti${NC}"

# Root huquqini tekshirish
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Iltimos, ushbu skriptni root sifatida ishlating (sudo bash install.sh)${NC}"
  exit 1
fi

PROJECT_DIR=$(pwd)
echo -e "${GREEN}>>> Joriy papka: ${PROJECT_DIR}${NC}"

# 1. Tizim paketlarini yangilash va o'rnatish
echo -e "${GREEN}>>> 1. Tizim paketlarini yangilash va o'rnatish...${NC}"
apt-get update
apt-get install -y python3 python3-pip python3-venv postgresql postgresql-contrib libpq-dev zip unzip

# 2. Python environment
echo -e "${GREEN}>>> 2. Python virtual muhitini sozlash...${NC}"
if [ ! -d "venv" ]; then
    echo "Virtual muhit yaratilmoqda..."
    python3 -m venv venv
else
    echo "Virtual muhit mavjud."
fi

source venv/bin/activate

echo "Kutubxonalarni o'rnatish..."
# Xatolik bo'lsa ham davom etishga harakat qiladi (common libs bilan)
pip install -r requirements.txt || pip install aiogram sqlalchemy asyncpg python-dotenv alembic psycopg2-binary pandas openpyxl

# 3. Database connection
echo -e "${GREEN}>>> 3. Ma'lumotlar bazasini sozlash...${NC}"
service postgresql start

# Baza borligini tekshirish va yaratish
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = 'talabahamkorbot_db'" | grep -q 1 || sudo -u postgres psql -c "CREATE DATABASE talabahamkorbot_db"

# User parolini yangilash
echo "User paroli sozlanmoqda..."
sudo -u postgres psql -c "ALTER USER postgres WITH ENCRYPTED PASSWORD 'Mukhammadali2623';"

# 4. Backupdan tiklash
# Backup fayl zipdan tashqarida (parent papkada) yoki shu papkada bo'lishi mumkin
BACKUP_FILE="../latest_full_db_backup.sql"
LOCAL_BACKUP="./talabahamkorbot_db_backup.sql"

if [ -f "$BACKUP_FILE" ]; then
    TARGET_BACKUP="$BACKUP_FILE"
elif [ -f "$LOCAL_BACKUP" ]; then
    TARGET_BACKUP="$LOCAL_BACKUP"
else
    TARGET_BACKUP=""
fi

if [ -n "$TARGET_BACKUP" ]; then
    echo -e "${GREEN}>>> Backup fayl topildi: $TARGET_BACKUP. Qayta tiklanmoqda...${NC}"
    export PGPASSWORD=Mukhammadali2623
    psql -U postgres -h localhost -d talabahamkorbot_db -f "$TARGET_BACKUP" > /dev/null 2>&1 || echo -e "${RED}Tiklashda xatolik bo'ldi, lekin davom etyapmiz...${NC}"
else
    echo -e "${RED}!!! OGOHLANTIRISH: Backup fayl topilmadi. Baza bo'sh qolishi mumkin.${NC}"
fi

# 5. Systemd Service
echo -e "${GREEN}>>> 4. Systemd service o'rnatish...${NC}"
SERVICE_FILE="/etc/systemd/system/talabahamkorbot.service"

cat > $SERVICE_FILE <<EOF
[Unit]
Description=TalabaHamkor Telegram Bot
After=network.target

[Service]
User=root
WorkingDirectory=${PROJECT_DIR}
ExecStart=${PROJECT_DIR}/venv/bin/python3 main.py
Restart=always
RestartSec=5
EnvironmentFile=${PROJECT_DIR}/.env

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable talabahamkorbot
systemctl restart talabahamkorbot

echo -e "${GREEN}>>> O'RNATISH MUVAFFAQIYATLI YAKUNLANDI!${NC}"
echo "Bot holatini tekshirish: systemctl status talabahamkorbot"
echo "Loglarni ko'rish: journalctl -u talabahamkorbot -f"
