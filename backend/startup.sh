#!/bin/bash

APP_DIR="/home/site/wwwroot"
echo "Starting app from: $APP_DIR"
cd $APP_DIR

# Install dependencies directly on the Linux container
echo "Installing dependencies..."
pip install -r requirements.txt --quiet

# Verify app module exists
if [ ! -d "app" ]; then
    echo "ERROR: app directory not found in $APP_DIR"
    ls -la
    exit 1
fi

echo "Starting gunicorn..."

# Start gunicorn with Uvicorn worker
python3 -m gunicorn app.api.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:${PORT:-8000} \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -