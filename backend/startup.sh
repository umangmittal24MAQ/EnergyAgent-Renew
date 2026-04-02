#!/bin/bash
# Startup script for Azure App Service - Python/FastAPI Backend
# This script runs when the App Service starts

# Set working directory
cd /home/site/wwwroot

# Activate virtual environment (if exists)
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install/update dependencies from requirements.txt
echo "Installing dependencies..."
pip install --no-cache-dir -r requirements.txt

# Run migrations if database is configured
if [ ! -z "$DATABASE_URL" ]; then
    echo "Database configured, running migrations..."
    alembic upgrade head || echo "Alembic not configured, skipping migrations"
fi

# Start the application with Gunicorn (production ASGI server)
echo "Starting FastAPI application..."

# Use Gunicorn for production
gunicorn \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    app.api.main:app

# Alternative (if Gunicorn is not preferred):
# python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --workers 4
