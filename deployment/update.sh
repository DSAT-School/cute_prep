#!/bin/bash

# Update deployment script
# Run this after pulling new code from git

set -e

APP_DIR="/opt/practice_portal"
APP_USER="www-data"
VENV_DIR="$APP_DIR/venv"

echo "Updating Practice Portal..."

# Pull latest code (if using git)
cd "$APP_DIR"
git pull origin main

# Install/update dependencies
"$VENV_DIR/bin/pip" install -r requirements/prod.txt

# Install/update Node dependencies
npm install

# Build TailwindCSS
npm run build

# Run migrations
sudo -u "$APP_USER" "$VENV_DIR/bin/python" manage.py migrate --settings=config.settings.prod

# Collect static files
sudo -u "$APP_USER" "$VENV_DIR/bin/python" manage.py collectstatic --noinput --settings=config.settings.prod

# Restart services
systemctl restart gunicorn
systemctl restart celery
systemctl restart celery-beat
systemctl reload nginx

echo "Update completed successfully!"
echo "Check status: systemctl status gunicorn"
