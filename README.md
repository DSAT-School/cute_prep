# Practice Portal

A modern Django application built with Clean Architecture, Domain-Driven Design (DDD), PostgreSQL, Redis, and TailwindCSS. **Runs directly on Linux servers without Docker.**

## Features

- **Clean Architecture**: Separation of concerns with clear layers
- **Custom User Model**: UUID-based primary keys
- **Global Timezone Support**: Automatic timezone detection for users worldwide
- **PostgreSQL Database**: Robust relational database
- **Redis Caching**: Fast caching and session storage
- **TailwindCSS**: Modern, responsive UI
- **REST API**: Django REST Framework
- **Testing**: pytest with 80%+ coverage
- **Celery**: Asynchronous task processing
- **Systemd Services**: Production-ready service management
- **Nginx**: Reverse proxy configuration

## Tech Stack

- Django 4.2, Django REST Framework
- PostgreSQL 15, Redis 7
- Gunicorn, Nginx
- TailwindCSS 3
- pytest, factory-boy
- Black, isort, Flake8, mypy

## Prerequisites

- Python 3.11+
- PostgreSQL 12+
- Redis 5+
- Node.js 18+
- Nginx
- Linux server (Ubuntu/Debian recommended)

## Quick Start (Development)

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements/dev.txt
npm install

# Set up database
sudo -u postgres createdb practice_portal
sudo -u postgres createuser practice_portal_user

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Build CSS
npm run build

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server with health checks (recommended)
python run.py

# Or run traditional Django server
python manage.py runserver
```

## Production Deployment

### Automated Deployment

```bash
sudo bash deployment/deploy.sh
```

This script handles:
- System dependencies installation
- Application setup at `/opt/practice_portal`
- Database and user creation
- Systemd services configuration
- Nginx setup
- All necessary permissions

### Manual Deployment

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed manual deployment instructions.

### After Deployment

1. Update `.env` at `/opt/practice_portal/.env`
2. Update Nginx config with your domain
3. Create superuser: `sudo -u www-data /opt/practice_portal/venv/bin/python /opt/practice_portal/manage.py createsuperuser`
4. Set up SSL: `sudo certbot --nginx -d your-domain.com`

## Service Management

```bash
# Check status
sudo systemctl status gunicorn
sudo systemctl status celery
sudo systemctl status celery-beat

# Restart services
sudo systemctl restart gunicorn
sudo systemctl restart celery

# View logs
sudo journalctl -u gunicorn -f
tail -f /var/log/practice_portal/error.log
```

## Update Deployment

```bash
sudo bash deployment/update.sh
```

## Testing

```bash
pytest                    # Run all tests
pytest --cov              # With coverage
pytest -m unit            # Unit tests only
pytest -m integration     # Integration tests only
```

## Development Commands

```bash
# Run server with health checks (recommended)
python run.py                    # Default: 127.0.0.1:8000
python run.py --host 0.0.0.0     # Bind to all interfaces
python run.py --port 8080        # Custom port
python run.py -h 0.0.0.0 -p 3000 # Custom host and port

# Traditional Django commands
python manage.py runserver       # Run without health checks
python manage.py shell           # Django shell
python manage.py makemigrations  # Create migrations
python manage.py migrate         # Apply migrations
```

## Code Quality

```bash
black .                   # Format code
isort .                   # Sort imports
flake8                    # Lint
mypy apps/                # Type check
./scripts/quality.sh      # Run all
```

## Project Structure

```
practice_portal/
├── apps/core/              # Core app with User model
├── config/                 # Settings and configuration
│   └── settings/           # Split settings (base, dev, prod)
├── deployment/             # Deployment files
│   ├── systemd/            # Systemd service files
│   ├── nginx/              # Nginx configuration
│   ├── deploy.sh           # Deployment script
│   └── update.sh           # Update script
├── docs/                   # Documentation
├── requirements/           # Python dependencies
├── scripts/                # Utility scripts
├── static/                 # Static files
├── templates/              # Django templates
└── tests/                  # Test suite
```

## Documentation

- [README.md](README.md) - This file
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [docs/architecture.md](docs/architecture.md) - Architecture details
- [docs/api-reference.md](docs/api-reference.md) - API documentation
- [docs/database-schema.md](docs/database-schema.md) - Database schema
- [docs/TIMEZONE.md](docs/TIMEZONE.md) - Timezone handling guide

## Environment Variables

Key variables in `.env`:

```bash
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com
DB_NAME=practice_portal
DB_USER=practice_portal_user
DB_PASSWORD=secure_password
DB_HOST=localhost
REDIS_URL=redis://127.0.0.1:6379/0
```

## API Endpoints

- `/api/health` - Health check
- `/api/users/` - User management
- `/api/users/me/` - Current user
- `/admin/` - Admin interface

## Systemd Services

- `gunicorn.service` - Django application server
- `celery.service` - Celery worker
- `celery-beat.service` - Celery scheduler
- `practice-portal.socket` - Gunicorn socket

## Production Checklist

- [ ] `DEBUG=False`
- [ ] Strong `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set database credentials
- [ ] Set up SSL/HTTPS
- [ ] Configure firewall
- [ ] Set up log rotation
- [ ] Create superuser
- [ ] Test health endpoint

## Troubleshooting

### Database Issues
```bash
sudo systemctl status postgresql
sudo tail -f /var/log/postgresql/postgresql-*.log
```

### Redis Issues
```bash
sudo systemctl status redis-server
redis-cli ping
```

### Application Issues
```bash
sudo systemctl status gunicorn
sudo journalctl -u gunicorn -f
tail -f /var/log/practice_portal/error.log
```

### Nginx Issues
```bash
sudo nginx -t
sudo systemctl restart nginx
tail -f /var/log/nginx/error.log
```

## Security

- Environment-based configuration
- CSRF and XSS protection
- SQL injection prevention (ORM)
- Secure password hashing
- HTTPS enforcement (production)
- Rate limiting on APIs
- Security headers configured

## Contributing

1. Follow Clean Architecture principles
2. Write tests (80%+ coverage)
3. Follow PEP8 and code quality standards
4. Use conventional commits
5. Submit PRs for review

## License

[Your License]

## Support

Create an issue for bugs or questions.
