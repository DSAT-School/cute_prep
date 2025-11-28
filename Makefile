.PHONY: help install setup migrate makemigrations createsuperuser shell test coverage quality format lint clean run celery

help:
	@echo "Available commands:"
	@echo "  make install        - Install all dependencies"
	@echo "  make setup          - Setup development environment"
	@echo "  make run            - Run development server"
	@echo "  make celery         - Run Celery worker"
	@echo "  make migrate        - Run database migrations"
	@echo "  make makemigrations - Create new migrations"
	@echo "  make createsuperuser- Create Django superuser"
	@echo "  make shell          - Open Django shell"
	@echo "  make test           - Run test suite"
	@echo "  make coverage       - Run tests with coverage"
	@echo "  make quality        - Run code quality checks"
	@echo "  make format         - Format code with Black and isort"
	@echo "  make lint           - Lint code with Flake8"
	@echo "  make clean          - Clean temporary files"

install:
	pip install -r requirements/dev.txt
	npm install

setup:
	@bash scripts/setup.sh

run:
	python manage.py runserver

celery:
	celery -A config worker --loglevel=info

migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations

createsuperuser:
	python manage.py createsuperuser

shell:
	python manage.py shell

test:
	pytest

coverage:
	pytest --cov=apps --cov-report=html --cov-report=term-missing

quality:
	@bash scripts/quality.sh

format:
	black apps/ config/ tests/
	isort apps/ config/ tests/

lint:
	flake8 apps/ config/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info

# TailwindCSS commands
tailwind-build:
	npm run build

tailwind-watch:
	npm run dev

# Production deployment commands
deploy:
	sudo bash deployment/deploy.sh

update-prod:
	sudo bash deployment/update.sh

# Service management (production)
status:
	sudo systemctl status gunicorn celery celery-beat

restart-services:
	sudo systemctl restart gunicorn celery celery-beat

logs-prod:
	sudo journalctl -u gunicorn -f
