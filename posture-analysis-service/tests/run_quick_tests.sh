#!/bin/bash

# Quick test runner - runs essential tests only
# Use this for rapid development feedback

set -e

echo "Running Quick Test Suite..."
echo "============================\n"

# Run fast unit tests only
pytest tests/unit/ \
    -v \
    -m "unit and not slow" \
    --tb=short \
    --maxfail=3 \
    -x

echo "\n✓ Quick tests passed!"
