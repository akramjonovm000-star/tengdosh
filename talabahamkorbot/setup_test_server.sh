#!/bin/bash

# Config
TEST_DIR="/var/www/talabahamkorbot_test"
PROD_DIR="/var/www/talabahamkorbot"
USER="root"
HOST="localhost" # Since we run this ON the server, or use rsync

echo "🚀 Setting up Test Server Environment..."

# 1. Create Directory
if [ ! -d "$TEST_DIR" ]; then
    echo "mkdir $TEST_DIR"
    mkdir -p "$TEST_DIR"
fi

# 2. Copy Code (Excluding venv, .env, __pycache__)
echo "📂 Copying files..."
rsync -av --exclude 'venv' --exclude '.env' --exclude '__pycache__' --exclude '.git' $PROD_DIR/ $TEST_DIR/

# 3. Create Virtual Env
echo "🐍 Creating Virtual Environment..."
cd $TEST_DIR
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# 4. Install Dependencies
echo "📦 Installing Requirements..."
./venv/bin/pip install -r requirements.txt

# 5. Create .env for Test
echo "⚙️  Configuring .env..."
if [ ! -f ".env" ]; then
    cat <<EOF > .env
BOT_TOKEN=YOUR_TEST_BOT_TOKEN_HERE
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
DB_NAME=talabahamkor_test
LOG_LEVEL=INFO
BOT_MODE=POLLING
EOF
    echo "✅ .env created! Please edit it manually."
    echo "   nano $TEST_DIR/.env"
else
    echo "⚠️  .env already exists. Skipped."
fi

# 6. Create Service File (Optional)
SERVICE_FILE="/etc/systemd/system/talabahamkor_test.service"
if [ ! -f "$SERVICE_FILE" ]; then
    echo "🛠 Creating Systemd Service..."
    cat <<EOF > $SERVICE_FILE
[Unit]
Description=TalabaHamkor TEST Bot (Polling)
After=network.target

[Service]
WorkingDirectory=$TEST_DIR
ExecStart=$TEST_DIR/venv/bin/python3 $TEST_DIR/main.py
Restart=always
RestartSec=5
User=root
Environment=BOT_MODE=POLLING

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
    echo "✅ Service created: talabahamkor_test"
else
    echo "⚠️  Service file exists. Skipped."
fi

echo "🎉 Done! To start the test bot:"
echo "1. Edit .env: nano $TEST_DIR/.env"
echo "2. Start: systemctl start talabahamkor_test"
