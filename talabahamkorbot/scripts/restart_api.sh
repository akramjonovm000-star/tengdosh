#!/bin/bash
# Restart script for TalabaHamkor API

APP_DIR="/home/user/talabahamkor/talabahamkorbot"
VENV_PYTHON="$APP_DIR/venv/bin/python3"
MAIN_SCRIPT="$APP_DIR/main.py"
LOG_FILE="$APP_DIR/nohup_api.out"

echo "Stopping existing API processes..."
pkill -f "python3 main.py"
pkill -f "multiprocessing.spawn"

# Wait a bit
sleep 2

echo "Starting API in background..."
cd $APP_DIR
nohup $VENV_PYTHON $MAIN_SCRIPT > $LOG_FILE 2>&1 &

echo "Restart complete. PID: $!"
tail -n 20 $LOG_FILE
