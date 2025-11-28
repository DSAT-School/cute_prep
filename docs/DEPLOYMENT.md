# Production Deployment Guide

## Overview

This guide walks through deploying Practice Portal on a Linux server (Ubuntu/Debian) without Docker.

## System Requirements

- Ubuntu 20.04 LTS or Debian 11+ (recommended)
- 2GB RAM minimum (4GB+ recommended)
- 20GB disk space minimum
- Python 3.11+
- PostgreSQL 12+
- Redis 5+
- Nginx
- Node.js 18+

## Automated Deployment

The easiest way to deploy is using the automated script:

```bash
sudo bash deployment/deploy.sh
```

This handles everything automatically. Continue reading for manual deployment or troubleshooting.

## Manual Deployment Steps

### 1. System Preparation

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y \
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
    npm \
    supervisor
```

### 2. Create Application User

```bash
# Application will run as www-data user
sudo usermod -s /bin/bash www-data
```

### 3. Clone Repository

```bash
# Create application directory
sudo mkdir -p /opt/practice_portal
sudo chown $USER:$USER /opt/practice_portal

# Clone repository
cd /opt
git clone <your-repo-url> practice_portal
cd practice_portal
```

### 4. Set Up Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate and install dependencies
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements/prod.txt
```

### 5. Configure PostgreSQL

```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL prompt:
CREATE DATABASE practice_portal;
CREATE USER practice_portal_user WITH PASSWORD 'your_secure_password_here';
ALTER ROLE practice_portal_user SET client_encoding TO 'utf8';
ALTER ROLE practice_portal_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE practice_portal_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE practice_portal TO practice_portal_user;
\q
```

### 6. Configure Environment

```bash
# Copy and edit environment file
cp .env.example .env
nano .env
```

Update these critical settings:
```bash
SECRET_KEY=generate_a_strong_random_secret_key_here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DB_PASSWORD=your_secure_password_here
```

Generate a secure SECRET_KEY:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 7. Install Node Dependencies

```bash
npm install
npm run build
```

### 8. Create Required Directories

```bash
# Log directory
sudo mkdir -p /var/log/practice_portal
sudo chown www-data:www-data /var/log/practice_portal

# Runtime directories
sudo mkdir -p /run/gunicorn
sudo chown www-data:www-data /run/gunicorn

sudo mkdir -p /var/run/celery
sudo chown www-data:www-data /var/run/celery

# Static and media directories
mkdir -p /opt/practice_portal/staticfiles
mkdir -p /opt/practice_portal/mediafiles
sudo chown -R www-data:www-data /opt/practice_portal/staticfiles
sudo chown -R www-data:www-data /opt/practice_portal/mediafiles
```

### 9. Run Django Setup

```bash
# Activate virtual environment
source /opt/practice_portal/venv/bin/activate

# Run migrations
python manage.py migrate --settings=config.settings.prod

# Collect static files
python manage.py collectstatic --noinput --settings=config.settings.prod

# Create superuser
python manage.py createsuperuser --settings=config.settings.prod
```

### 10. Set File Permissions

```bash
sudo chown -R www-data:www-data /opt/practice_portal
sudo chmod 600 /opt/practice_portal/.env
sudo chmod +x /opt/practice_portal/manage.py
```

### 11. Install Systemd Services

```bash
# Copy service files
sudo cp /opt/practice_portal/deployment/systemd/practice-portal.socket /etc/systemd/system/
sudo cp /opt/practice_portal/deployment/systemd/gunicorn.service /etc/systemd/system/
sudo cp /opt/practice_portal/deployment/systemd/celery.service /etc/systemd/system/
sudo cp /opt/practice_portal/deployment/systemd/celery-beat.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable practice-portal.socket
sudo systemctl enable gunicorn.service
sudo systemctl enable celery.service
sudo systemctl enable celery-beat.service

# Start services
sudo systemctl start practice-portal.socket
sudo systemctl start gunicorn.service
sudo systemctl start celery.service
sudo systemctl start celery-beat.service

# Check status
sudo systemctl status gunicorn
sudo systemctl status celery
sudo systemctl status celery-beat
```

### 12. Configure Nginx

```bash
# Copy Nginx configuration
sudo cp /opt/practice_portal/deployment/nginx/practice_portal.conf /etc/nginx/sites-available/

# Update domain in config file
sudo nano /etc/nginx/sites-available/practice_portal.conf
# Change "your-domain.com" to your actual domain

# Enable site
sudo ln -s /etc/nginx/sites-available/practice_portal.conf /etc/nginx/sites-enabled/

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### 13. Configure Firewall

```bash
# Install UFW if not installed
sudo apt-get install ufw

# Allow SSH (important!)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### 14. Set Up SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### 15. Configure Log Rotation

```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/practice_portal
```

Add this content:
```
/var/log/practice_portal/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload gunicorn
    endscript
}
```

## Post-Deployment Verification

### 1. Check Services

```bash
# Check all services are running
sudo systemctl status gunicorn
sudo systemctl status celery
sudo systemctl status celery-beat
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status redis-server
```

### 2. Test Application

```bash
# Test health endpoint
curl http://your-domain.com/api/health

# Should return: {"status": "healthy", "database": "connected", "cache": "connected"}
```

### 3. Check Logs

```bash
# Application logs
sudo tail -f /var/log/practice_portal/error.log
sudo tail -f /var/log/practice_portal/access.log

# Systemd logs
sudo journalctl -u gunicorn -f
sudo journalctl -u celery -f

# Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

## Updating the Application

Use the update script:

```bash
sudo bash /opt/practice_portal/deployment/update.sh
```

Or manually:

```bash
cd /opt/practice_portal
git pull origin main
source venv/bin/activate
pip install -r requirements/prod.txt
npm install
npm run build
python manage.py migrate --settings=config.settings.prod
python manage.py collectstatic --noinput --settings=config.settings.prod
sudo systemctl restart gunicorn celery celery-beat
sudo systemctl reload nginx
```

## Backup Strategy

### Database Backup

```bash
# Create backup script
sudo nano /opt/practice_portal/scripts/backup_db.sh
```

Add:
```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/practice_portal"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
pg_dump -U practice_portal_user practice_portal | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +30 -delete
```

```bash
# Make executable
sudo chmod +x /opt/practice_portal/scripts/backup_db.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e
```

Add line:
```
0 2 * * * /opt/practice_portal/scripts/backup_db.sh
```

### Application Files Backup

```bash
# Backup media files and .env
sudo tar -czf /opt/backups/practice_portal/files_$(date +%Y%m%d).tar.gz \
    /opt/practice_portal/mediafiles \
    /opt/practice_portal/.env
```

## Monitoring

### Health Check Monitoring

Set up a cron job to check health:

```bash
# Create monitoring script
sudo nano /opt/practice_portal/scripts/health_check.sh
```

Add:
```bash
#!/bin/bash
HEALTH_URL="http://localhost/api/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $RESPONSE -ne 200 ]; then
    echo "Health check failed with code: $RESPONSE"
    sudo systemctl restart gunicorn
fi
```

### Resource Monitoring

Install and configure monitoring tools:

```bash
# Install htop for process monitoring
sudo apt-get install htop

# Install netdata for comprehensive monitoring (optional)
bash <(curl -Ss https://my-netdata.io/kickstart.sh)
```

## Troubleshooting

### Service Won't Start

```bash
# Check service status
sudo systemctl status gunicorn
sudo journalctl -u gunicorn -xe

# Check permissions
sudo chown -R www-data:www-data /opt/practice_portal
sudo chmod 600 /opt/practice_portal/.env
```

### Database Connection Issues

```bash
# Test database connection
sudo -u www-data /opt/practice_portal/venv/bin/python << EOF
import psycopg2
conn = psycopg2.connect(
    dbname='practice_portal',
    user='practice_portal_user',
    password='your_password',
    host='localhost'
)
print("Connection successful!")
conn.close()
EOF
```

### Nginx 502 Bad Gateway

```bash
# Check Gunicorn is running
sudo systemctl status gunicorn

# Check socket file exists
ls -l /run/gunicorn/practice_portal.sock

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Static Files Not Loading

```bash
# Recollect static files
cd /opt/practice_portal
source venv/bin/activate
python manage.py collectstatic --noinput --settings=config.settings.prod

# Check permissions
sudo chown -R www-data:www-data /opt/practice_portal/staticfiles
```

## Security Hardening

### 1. Disable Debug Mode

Ensure in `.env`:
```bash
DEBUG=False
```

### 2. Set Strong Secret Key

```bash
SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
```

### 3. Configure ALLOWED_HOSTS

In `.env`:
```bash
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

### 4. Secure PostgreSQL

```bash
# Edit PostgreSQL config
sudo nano /etc/postgresql/*/main/pg_hba.conf

# Ensure local connections use md5 auth, not trust
```

### 5. Secure Redis

```bash
# Edit Redis config
sudo nano /etc/redis/redis.conf

# Set bind to localhost only
bind 127.0.0.1

# Set requirepass
requirepass your_redis_password

# Restart Redis
sudo systemctl restart redis-server
```

### 6. Regular Updates

```bash
# Set up automatic security updates
sudo apt-get install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

## Performance Tuning

### PostgreSQL

```bash
sudo nano /etc/postgresql/*/main/postgresql.conf
```

Adjust based on your server resources:
```
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB
```

### Gunicorn Workers

In `.env`, adjust based on CPU cores:
```bash
GUNICORN_WORKERS=4  # (2 x CPU cores) + 1
```

### Redis

```bash
sudo nano /etc/redis/redis.conf
```

```
maxmemory 256mb
maxmemory-policy allkeys-lru
```

## Support

For issues:
1. Check logs first
2. Review this guide
3. Check GitHub issues
4. Create new issue with logs and details

## Additional Resources

- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
