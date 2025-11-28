#!/bin/bash

# Format code with Black
echo "Running Black..."
black apps/ config/ tests/

# Sort imports with isort
echo "Running isort..."
isort apps/ config/ tests/

# Lint with Flake8
echo "Running Flake8..."
flake8 apps/ config/ tests/

# Type check with mypy
echo "Running mypy..."
mypy apps/ config/

echo "Code quality checks complete!"
