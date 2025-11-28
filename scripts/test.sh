#!/bin/bash

# Run tests with coverage
echo "Running tests with coverage..."
pytest --cov=apps --cov-report=html --cov-report=term-missing

# Check coverage threshold
echo "Checking coverage threshold..."
coverage report --fail-under=80

echo "Test suite complete!"
