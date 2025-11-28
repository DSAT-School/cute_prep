#!/bin/bash

# Practice Portal Deployment Script
# This script sets up the application on a Linux server

set -e

echo "==================================="
echo "Practice Portal Deployment Setup"
echo "==================================="

# Configuration
APP_DIR="/opt/practice_portal"
APP_USER="www-data"
APP_GROUP="www-data"
VENV_DIR="$APP_DIR/venv"
LOG_DIR="/var/log/practice_portal"
RUN_DIR="/var/run/celery"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run as root or with sudo"
    exit 1
fi

print_info "Installing system dependencies..."
apt-get update
apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    postgresql \
    postgresql-contrib \
    redis-server \
    nginx \
    git \
    build-essential \
    libpq-dev \
    nodejs \
    npm
print_success "System dependencies installed"

# Create application directory
print_info "Creating application directory..."
if [ ! -d "$APP_DIR" ]; then
    mkdir -p "$APP_DIR"
fi
print_success "Application directory created"

# Copy application files
print_info "Copying application files..."
if [ -d "/home/raju/dsatschool-product/practice_portal" ]; then
    rsync -av --exclude='venv' --exclude='*.pyc' --exclude='__pycache__' \
        /home/raju/dsatschool-product/practice_portal/ "$APP_DIR/"
else
    print_error "Source directory not found"
    exit 1
fi
print_success "Application files copied"

# Create virtual environment
print_info "Creating virtual environment..."
python3.11 -m venv "$VENV_DIR"
print_success "Virtual environment created"

# Install Python dependencies
print_info "Installing Python dependencies..."
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements/prod.txt"
print_success "Python dependencies installed"

# Install Node dependencies
print_info "Installing Node dependencies..."
cd "$APP_DIR"
npm install
print_success "Node dependencies installed"

# Build TailwindCSS
print_info "Building TailwindCSS..."
npm run build
print_success "TailwindCSS built"

# Create log directory
print_info "Creating log directory..."
mkdir -p "$LOG_DIR"
chown -R "$APP_USER:$APP_GROUP" "$LOG_DIR"
print_success "Log directory created"

# Create run directory for Celery
print_info "Creating Celery run directory..."
mkdir -p "$RUN_DIR"
chown -R "$APP_USER:$APP_GROUP" "$RUN_DIR"
print_success "Celery run directory created"

# Create gunicorn run directory
print_info "Creating Gunicorn run directory..."
mkdir -p /run/gunicorn
chown -R "$APP_USER:$APP_GROUP" /run/gunicorn
print_success "Gunicorn run directory created"

# Create static and media directories
print_info "Creating static and media directories..."
mkdir -p "$APP_DIR/staticfiles"
mkdir -p "$APP_DIR/mediafiles"
chown -R "$APP_USER:$APP_GROUP" "$APP_DIR/staticfiles"
chown -R "$APP_USER:$APP_GROUP" "$APP_DIR/mediafiles"
print_success "Static and media directories created"

# Set up PostgreSQL database
print_info "Setting up PostgreSQL database..."
sudo -u postgres psql << EOF
CREATE DATABASE practice_portal;
CREATE USER practice_portal_user WITH PASSWORD 'change_this_password';
ALTER ROLE practice_portal_user SET client_encoding TO 'utf8';
ALTER ROLE practice_portal_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE practice_portal_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE practice_portal TO practice_portal_user;
\q
EOF
print_success "PostgreSQL database created"

# Copy environment file
print_info "Setting up environment file..."
if [ ! -f "$APP_DIR/.env" ]; then
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    print_info "Please update $APP_DIR/.env with your configuration"
fi
print_success "Environment file created"

# Set proper permissions
print_info "Setting file permissions..."
chown -R "$APP_USER:$APP_GROUP" "$APP_DIR"
chmod -R 755 "$APP_DIR"
chmod 600 "$APP_DIR/.env"
print_success "File permissions set"

# Run migrations
print_info "Running database migrations..."
cd "$APP_DIR"
sudo -u "$APP_USER" "$VENV_DIR/bin/python" manage.py migrate --settings=config.settings.prod
print_success "Database migrations completed"

# Collect static files
print_info "Collecting static files..."
sudo -u "$APP_USER" "$VENV_DIR/bin/python" manage.py collectstatic --noinput --settings=config.settings.prod
print_success "Static files collected"

# Install systemd services
print_info "Installing systemd services..."
cp "$APP_DIR/deployment/systemd/practice-portal.socket" /etc/systemd/system/
cp "$APP_DIR/deployment/systemd/gunicorn.service" /etc/systemd/system/
cp "$APP_DIR/deployment/systemd/celery.service" /etc/systemd/system/
cp "$APP_DIR/deployment/systemd/celery-beat.service" /etc/systemd/system/
systemctl daemon-reload
print_success "Systemd services installed"

# Install Nginx configuration
print_info "Installing Nginx configuration..."
cp "$APP_DIR/deployment/nginx/practice_portal.conf" /etc/nginx/sites-available/practice_portal
ln -sf /etc/nginx/sites-available/practice_portal /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
print_success "Nginx configuration installed"

# Start Redis
print_info "Starting Redis..."
systemctl enable redis-server
systemctl start redis-server
print_success "Redis started"

# Start services
print_info "Starting application services..."
systemctl enable practice-portal.socket
systemctl start practice-portal.socket
systemctl enable gunicorn.service
systemctl start gunicorn.service
systemctl enable celery.service
systemctl start celery.service
systemctl enable celery-beat.service
systemctl start celery-beat.service
print_success "Application services started"

# Restart Nginx
print_info "Restarting Nginx..."
systemctl restart nginx
print_success "Nginx restarted"

echo ""
echo "==================================="
print_success "Deployment completed successfully!"
echo "==================================="
echo ""
echo "Next steps:"
echo "1. Update $APP_DIR/.env with your configuration"
echo "2. Update Nginx config with your domain: /etc/nginx/sites-available/practice_portal"
echo "3. Create superuser: sudo -u $APP_USER $VENV_DIR/bin/python $APP_DIR/manage.py createsuperuser"
echo "4. Set up SSL certificate (recommended): certbot --nginx -d your-domain.com"
echo ""
echo "Service commands:"
echo "  sudo systemctl status gunicorn"
echo "  sudo systemctl status celery"
echo "  sudo systemctl status celery-beat"
echo "  sudo systemctl restart gunicorn"
echo ""
echo "Logs:"
echo "  Application: $LOG_DIR/"
echo "  Nginx: /var/log/nginx/"
echo "  Systemd: journalctl -u gunicorn -f"
echo ""
echo "Access the application at: http://your-server-ip"
echo "Health check: http://your-server-ip/api/health"
