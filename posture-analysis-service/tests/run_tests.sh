#!/bin/bash
# Test runner script for posture analysis service

set -e

echo "=== Running Posture Analysis Service Tests ==="

# Run unit tests
echo ""
echo "Running unit tests..."
pytest tests/unit/ -v --cov=app --cov-report=term-missing

# Run integration tests
echo ""
echo "Running integration tests..."
pytest tests/integration/ -v --cov=app --cov-report=term-missing --cov-append

# Generate coverage report
echo ""
echo "Generating coverage report..."
pytest --cov=app --cov-report=html --cov-report=term

echo ""
echo "=== Tests Complete ==="
echo "Coverage report generated in htmlcov/index.html"
