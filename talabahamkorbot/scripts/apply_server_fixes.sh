#!/bin/bash

# This script applies server-level fixes for Nginx and the Community service.
# It should be run with sudo.

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)"
   exit 1
fi

echo "Applying Nginx configuration fixes..."
NGINX_CONF_NEW="/home/user/talabahamkor/nginx_tengdosh_final.conf"
NGINX_CONF_DEST="/etc/nginx/sites-available/tengdosh_final"

if [ -f "$NGINX_CONF_NEW" ]; then
    cp "$NGINX_CONF_NEW" "$NGINX_CONF_DEST"
    ln -sf "$NGINX_CONF_DEST" /etc/nginx/sites-enabled/tengdosh_final
    echo "Nginx config updated."
else
    echo "Warning: New Nginx config not found at $NGINX_CONF_NEW"
fi

echo "Optimizing Community service workers..."
SERVICE_FILE="/etc/systemd/system/talabahamkor-community.service"
if [ -f "$SERVICE_FILE" ]; then
    sed -i 's/workers 2/workers 4/' "$SERVICE_FILE"
    echo "Increased workers to 4 in $SERVICE_FILE"
else
    echo "Error: Community service file not found at $SERVICE_FILE"
fi

echo "Reloading systemd and restarting services..."
systemctl daemon-reload
systemctl restart talabahamkor-community
systemctl restart nginx

echo "Server fixes applied successfully!"
