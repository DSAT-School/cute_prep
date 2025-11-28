#!/bin/bash

# Setup script for local development

echo "Setting up Practice Portal development environment..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements/dev.txt

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "Please update .env with your configuration"
fi

# Install Node dependencies
echo "Installing Node dependencies..."
npm install

# Build TailwindCSS
echo "Building TailwindCSS..."
npm run build

# Make scripts executable
chmod +x scripts/*.sh

echo ""
echo "Setup complete! Next steps:"
echo "1. Update .env with your configuration"
echo "2. Start Docker services: docker-compose up -d"
echo "3. Run migrations: python manage.py migrate"
echo "4. Create superuser: python manage.py createsuperuser"
echo "5. Start development server: python manage.py runserver"
echo ""
echo "Or run everything with Docker:"
echo "  docker-compose up"
