#!/bin/bash
echo "Restarting community service..."
sudo systemctl restart talabahamkor-community
echo "Restarting main bot service..."
sudo systemctl restart talabahamkorbot
echo "Stopping redundant bot service..."
sudo systemctl stop talabahamkor_bot
echo "Disabling redundant bot service..."
sudo systemctl disable talabahamkor_bot
echo "Reloading Nginx..."
sudo systemctl reload nginx
echo "Done."
