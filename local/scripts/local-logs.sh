#!/bin/bash

cd "$(dirname "$0")/.."

# Parse arguments
SERVICE=$1

if [ -z "$SERVICE" ]; then
    echo "Following logs from all services (Ctrl+C to exit)..."
    docker compose logs -f
else
    echo "Following logs from $SERVICE (Ctrl+C to exit)..."
    docker compose logs -f "$SERVICE"
fi
