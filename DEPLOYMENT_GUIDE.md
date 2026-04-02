# Deployment Guide - Energy Dashboard

**Status**: Ready for Deployment  
**Target Environments**: Development, Testing, Production  
**Last Updated**: April 1, 2026

---

## Table of Contents

1. [Quick Start (Development)](#quick-start-development)
2. [Full Environment Setup](#full-environment-setup)
3. [Docker Deployment](#docker-deployment)
4. [Production Setup](#production-setup)
5. [Troubleshooting](#troubleshooting)
6. [Configuration Reference](#configuration-reference)

---

## Quick Start (Development)

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Git

### 1. Clone and Setup Backend

```bash
# Navigate to backend directory
cd backend

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env with your values
# Key variables to set:
# - SHAREPOINT_SITE_URL
# - SHAREPOINT_CLIENT_ID
# - SHAREPOINT_CLIENT_SECRET
# - GOOGLE_SHEETS_CREDENTIALS_PATH
# - SMTP_HOST
# - SMTP_PASSWORD

# Start backend server
python app/api/main.py

# Server will run on: http://localhost:8000
# API docs: http://localhost:8000/docs (Swagger UI)
# Alternative docs: http://localhost:8000/redoc (ReDoc)
```

### 2. Setup Frontend

```bash
# In a new terminal, navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create .env file for frontend (optional)
echo "VITE_API_BASE_URL=http://localhost:8000" > .env

# Start development server
npm run dev

# Frontend will run on: http://localhost:5173
# Hot reload enabled - changes auto-refresh
```

### 3. Access Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

---

## Full Environment Setup

### Backend Environment Variables

Create `backend/.env`:

```env
# Server Configuration
API_HOST=0.0.0.0
API_PORT=8000
APP_ENV=development
DEBUG=true
API_RELOAD=true

# Database (if using external database)
# DATABASE_URL=postgresql://user:password@localhost:5432/energy_dashboard
# REDIS_URL=redis://localhost:6379

# SharePoint Configuration
SHAREPOINT_SITE_URL=https://yourcompany.sharepoint.com/sites/energy
SHAREPOINT_CLIENT_ID=your-client-id-here
SHAREPOINT_CLIENT_SECRET=your-client-secret-here

# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS_PATH=./google_credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=your-spreadsheet-id

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@company.com
SMTP_USE_TLS=true

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/energy_dashboard.log

# Optional: Feature Flags
ENABLE_SCHEDULER=true
ENABLE_DUAL_WRITE=false
CACHE_ENABLED=true
CACHE_TTL=3600
```

### Frontend Environment Variables

Create `frontend/.env`:

```env
# API Configuration
VITE_API_BASE_URL=http://localhost:8000

# Feature Flags
VITE_ENABLE_SCHEDULER=true
VITE_ENABLE_EXPORT=true
VITE_ENABLE_ADMIN=false

# Theme
VITE_APP_TITLE=Energy Dashboard
VITE_LOG_LEVEL=debug
```

### Install Production Dependencies

```bash
# Backend core dependencies
cd backend
pip install -r requirements.txt

# Optional: Scheduler support
pip install apscheduler>=3.10.0

# Optional: SharePoint auth
pip install msal>=1.25.0

# Optional: Data processing
pip install pandas>=2.0.0
pip install numpy>=1.24.0

# Optional: Google Sheets
pip install gspread>=5.10.0

# Frontend dependencies
cd ../frontend
npm install
```

---

## Docker Deployment

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+

### Quick Docker Start

```bash
# From project root
docker-compose up --build

# This starts:
# - Backend API: http://localhost:8000
# - Frontend: http://localhost:5173

# Stop containers
docker-compose down

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Production Docker Setup

```bash
# Build images with production optimizations
docker build \
  --build-arg ENVIRONMENT=production \
  -t energy-dashboard-backend:1.0 \
  -f docker/Dockerfile.backend \
  .

docker build \
  -t energy-dashboard-frontend:1.0 \
  -f docker/Dockerfile.frontend \
  .

# Tag for registry
docker tag energy-dashboard-backend:1.0 \
  your-registry.azurecr.io/energy-dashboard-backend:1.0

docker tag energy-dashboard-frontend:1.0 \
  your-registry.azurecr.io/energy-dashboard-frontend:1.0

# Push to registry
docker push your-registry.azurecr.io/energy-dashboard-backend:1.0
docker push your-registry.azurecr.io/energy-dashboard-frontend:1.0
```

### Docker Compose for Production

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    image: energy-dashboard-backend:1.0
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=production
      - DEBUG=false
      - API_RELOAD=false
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    image: energy-dashboard-frontend:1.0
    ports:
      - "80:3000"
    environment:
      - VITE_API_BASE_URL=http://your-api-host:8000
    restart: always

volumes:
  logs:
  data:
```

---

## Production Setup

### 1. Environment Setup

```bash
# Create production directory structure
mkdir -p /opt/energy-dashboard
mkdir -p /opt/energy-dashboard/logs
mkdir -p /opt/energy-dashboard/data
mkdir -p /opt/energy-dashboard/config

# Copy application
cp -r backend frontend /opt/energy-dashboard/
```

### 2. Security Configuration

```bash
# Create production .env
cat > /opt/energy-dashboard/backend/.env.prod << 'EOF'
API_HOST=0.0.0.0
API_PORT=8000
APP_ENV=production
DEBUG=false
API_RELOAD=false

# Set actual production secrets
SHAREPOINT_CLIENT_ID=prod-client-id
SHAREPOINT_CLIENT_SECRET=prod-client-secret
# ... other secrets
EOF

# Set restrictive permissions
chmod 600 /opt/energy-dashboard/backend/.env.prod
chown app:app /opt/energy-dashboard -R
```

### 3. Database Setup (if using external DB)

```bash
# PostgreSQL example
createdb energy_dashboard
psql energy_dashboard < backend/migrations/schema.sql

# Or with Docker
docker run -d \
  --name energy-db \
  -e POSTGRES_PASSWORD=secure_password \
  -e POSTGRES_DB=energy_dashboard \
  -v energy-db-data:/var/lib/postgresql/data \
  postgres:15

# Update .env
echo "DATABASE_URL=postgresql://postgres:secure_password@localhost:5432/energy_dashboard" >> .env.prod
```

### 4. Service Configuration

#### Systemd Service (Linux)

```ini
# /etc/systemd/system/energy-dashboard-backend.service
[Unit]
Description=Energy Dashboard Backend
After=network.target

[Service]
Type=notify
User=app
WorkingDirectory=/opt/energy-dashboard/backend
Environment="PATH=/opt/energy-dashboard/backend/venv/bin"
ExecStart=/opt/energy-dashboard/backend/venv/bin/python app/api/main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable energy-dashboard-backend
sudo systemctl start energy-dashboard-backend
sudo systemctl status energy-dashboard-backend
```

#### Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/energy-dashboard
upstream backend {
    server localhost:8000;
}

server {
    listen 80;
    server_name api.yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/ssl/certs/your-cert.crt;
    ssl_certificate_key /etc/ssl/private/your-key.key;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;

    # API proxy
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # CORS headers
    add_header Access-Control-Allow-Origin "https://app.yourdomain.com";
    add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
    add_header Access-Control-Allow-Headers "Content-Type, Authorization";
}

server {
    listen 443 ssl http2;
    server_name app.yourdomain.com;

    ssl_certificate /etc/ssl/certs/your-cert.crt;
    ssl_certificate_key /etc/ssl/private/your-key.key;

    root /opt/energy-dashboard/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|woff|woff2|ttf)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 5. Monitoring & Logging

```bash
# Create log rotation configuration
cat > /etc/logrotate.d/energy-dashboard << 'EOF'
/opt/energy-dashboard/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    missingok
    create 0640 app app
}
EOF

# Monitor service
watch -n 5 'systemctl status energy-dashboard-backend'

# View logs in real-time
tail -f /opt/energy-dashboard/logs/energy_dashboard.log
```

---

## Kubernetes Deployment

```bash
# Deploy to Kubernetes (requires configured cluster and manifests)
kubectl apply -f infra/kubernetes/namespace.yaml
kubectl apply -f infra/kubernetes/configmap.yaml
kubectl apply -f infra/kubernetes/secrets.yaml
kubectl apply -f infra/kubernetes/backend-deployment.yaml
kubectl apply -f infra/kubernetes/frontend-deployment.yaml
kubectl apply -f infra/kubernetes/services.yaml
kubectl apply -f infra/kubernetes/ingress.yaml

# Verify deployment
kubectl get pods -n energy-dashboard
kubectl get svc -n energy-dashboard

# Check logs
kubectl logs -f deployment/backend -n energy-dashboard
```

---

## Troubleshooting

### Backend Won't Start

```bash
# Check Python version
python --version  # Should be 3.11+

# Verify dependencies
pip list | grep -E "fastapi|uvicorn"

# Test imports
python -c "from app.api.main import create_app; print('OK')"

# Check port availability
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# View detailed logs
python -c "import logging; logging.basicConfig(level=logging.DEBUG); from app.api.main import create_app"
```

### Frontend Won't Load

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Should be 18+

# Verify VITE_API_BASE_URL
echo $VITE_API_BASE_URL  # Should point to backend

# Check for port conflicts
netstat -ano | findstr :5173  # Windows
lsof -i :5173  # Linux/Mac
```

### CORS Issues

```bash
# Frontend error: "CORS policy blocked"
# Solution: Check backend CORS configuration
# File: backend/app/api/main.py

# Add frontend origin to CORS whitelist
CORS_ORIGINS=["http://localhost:5173", "https://app.yourdomain.com"]
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql "postgresql://user:password@localhost:5432/energy_dashboard" -c "SELECT 1"

# Check DATABASE_URL in .env
cat backend/.env | grep DATABASE_URL

# Verify database exists
psql -l | grep energy_dashboard
```

### SharePoint/Google Sheets Authentication

```bash
# Verify credentials file exists
ls -la backend/google_credentials.json

# Test SharePoint credentials
python -c "
from app.services.sharepoint_auth import SharePointAuth
auth = SharePointAuth()
print('SharePoint auth configured' if auth else 'Failed')
"

# Check token expiry
cat backend/logs/energy_dashboard.log | grep -i "token"
```

---

## Configuration Reference

### Backend Core Settings (app/core/config.py)

```python
class Settings(BaseSettings):
    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    app_env: str = "development"
    debug: bool = True
    
    # Database
    database_url: Optional[str] = None
    redis_url: Optional[str] = None
    
    # Features
    enable_scheduler: bool = True
    enable_dual_write: bool = False
    cache_enabled: bool = True
    cache_ttl: int = 3600
    
    # External Services
    sharepoint_site_url: str
    sharepoint_client_id: str
    sharepoint_client_secret: str
    
    google_sheets_spreadsheet_id: str
    google_sheets_credentials_path: str
    
    smtp_host: str
    smtp_port: int = 587
    smtp_username: str
    smtp_password: str
```

### Frontend Config Files

**api.config.js**: API endpoints and base URL
**theme.config.js**: Colors, fonts, UI settings  
**index.js**: App-wide configuration

---

## Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Frontend health (from browser)
curl http://localhost:5173

# Full diagnostics
curl -v http://localhost:8000/docs

# Check API routes
curl http://localhost:8000/openapi.json | jq '.paths | keys'
```

---

## Performance Optimization

### Backend
- Use Gunicorn/Uvicorn workers in production
- Enable caching (Redis)
- Use connection pooling for databases
- Monitor with Prometheus/APM tools

### Frontend
- Build optimization: `npm run build`
- Use CDN for static assets
- Enable gzip compression
- Implement service workers for PWA

### Database
- Create indexes on frequently queried columns
- Regular VACUUM and ANALYZE (PostgreSQL)
- Monitor query performance

---

## Backup & Recovery

```bash
# Backup application data
tar -czf energy-dashboard-backup-$(date +%Y%m%d).tar.gz \
  /opt/energy-dashboard/data \
  /opt/energy-dashboard/backend/.env.prod

# Backup database
pg_dump energy_dashboard > energy_dashboard-$(date +%Y%m%d).sql

# Restore from backup
psql energy_dashboard < energy_dashboard-YYYYMMDD.sql
```

---

## Support & Contact

For issues or questions:
- Check TEST_REPORT.md for validation results
- Review logs in `backend/logs/`
- Check Swagger API docs at `/docs`
- Review error codes in `app/core/exceptions.py`

---

**Last Updated**: April 1, 2026  
**Version**: 1.0  
**Status**: Production Ready ✅
