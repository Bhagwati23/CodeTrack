#!/bin/bash

# Set default port if PORT is not set
export PORT=${PORT:-5000}

echo "Starting CodeTrack Pro on port $PORT"

# Start the application
exec gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --keep-alive 2 --max-requests 1000 --max-requests-jitter 100 main:app
