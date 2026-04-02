# Azure App Service Environment Configuration
# Copy these settings to your Azure App Service Configuration
# 
# Instructions:
# 1. Go to Azure Portal
# 2. Open your App Service
# 3. Go to Configuration (left menu)
# 4. Click "+ New application setting"
# 5. Add each setting below
# 6. Click Save
#
# ============================================================================
# BACKEND SETTINGS (energy-dashboard-api)
# ============================================================================

# Server Configuration
API_HOST=0.0.0.0
API_PORT=8000
APP_ENV=production
DEBUG=false
API_RELOAD=false

# ============================================================================
# OPTIONAL: SharePoint Configuration
# (Leave empty if not using SharePoint)
# ============================================================================
SHAREPOINT_SITE_URL=https://yourcompany.sharepoint.com/sites/energy
SHAREPOINT_CLIENT_ID=your-sharepoint-client-id-here
SHAREPOINT_CLIENT_SECRET=your-sharepoint-client-secret-here

# ============================================================================
# OPTIONAL: Google Sheets Configuration
# (Leave empty if not using Google Sheets)
# ============================================================================
GOOGLE_SHEETS_SPREADSHEET_ID=your-spreadsheet-id-here
GOOGLE_SHEETS_CREDENTIALS_PATH=./google_credentials.json

# ============================================================================
# OPTIONAL: Email/SMTP Configuration
# (Leave empty if not using email features)
# ============================================================================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
SMTP_FROM=noreply@yourcompany.com
SMTP_USE_TLS=true

# ============================================================================
# OPTIONAL: Database Configuration
# (Leave empty if not using external database)
# ============================================================================
# For Azure SQL Database:
# DATABASE_URL=mssql+pyodbc://username:password@server.database.windows.net/database?driver=ODBC+Driver+17+for+SQL+Server

# For PostgreSQL:
# DATABASE_URL=postgresql://username:password@server:5432/database

# ============================================================================
# OPTIONAL: Redis Cache Configuration
# (Leave empty if not using Redis)
# ============================================================================
# REDIS_URL=redis://username:password@your-redis-server:6379/0

# ============================================================================
# OPTIONAL: Feature Flags
# ============================================================================
ENABLE_SCHEDULER=true
ENABLE_DUAL_WRITE=false
CACHE_ENABLED=true
CACHE_TTL=3600

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
LOG_LEVEL=INFO
LOG_FILE=logs/energy_dashboard.log

# ============================================================================
# FRONTEND SETTINGS (energy-dashboard-app)
# ============================================================================

VITE_API_BASE_URL=https://energy-dashboard-api.azurewebsites.net
NODE_ENV=production
VITE_LOG_LEVEL=error

# ============================================================================
# MONITORING & DIAGNOSTICS
# ============================================================================
WEBSITE_NODE_DEFAULT_VERSION=18.17.1
SCM_DO_BUILD_DURING_DEPLOYMENT=true

# ============================================================================
# INSTRUCTIONS BY SERVICE TYPE
# ============================================================================

# --- BACKEND APP SERVICE SETTINGS ---
# Service Name: energy-dashboard-api
# Runtime: Python 3.11
# 
# Add ALL settings from "SERVER CONFIGURATION" section
# Add OPTIONAL settings you plan to use (SharePoint, Email, Database, etc.)
# Add LOGGING configuration
# 
# Startup Command: gunicorn --workers 4 --bind 0.0.0.0:8000 app.api.main:app
# 
# ============================================================================

# --- FRONTEND APP SERVICE SETTINGS ---
# Service Name: energy-dashboard-app
# Runtime: Node 18 LTS
#
# Add settings from "FRONTEND SETTINGS" section
# Add MONITORING & DIAGNOSTICS section
#
# Startup Command: (leave empty - Azure handles Node.js)
#
# ============================================================================

# HOW TO ADD SETTINGS IN AZURE PORTAL:
# 
# 1. Go to https://portal.azure.com
# 2. Find your App Service (e.g., energy-dashboard-api)
# 3. Click "Configuration" in the left sidebar
# 4. Click "+ New application setting"
# 5. Enter:
#    Name: (e.g., API_HOST)
#    Value: (e.g., 0.0.0.0)
# 6. Click OK
# 7. Repeat for all settings
# 8. Click "Save" at the top
# 9. App automatically restarts with new settings
#
# ============================================================================

# IMPORTANT NOTES:
#
# - Settings in Azure take precedence over .env files
# - Changes apply immediately after clicking Save
# - App Service automatically restarts
# - Use Key Vault for sensitive values (API keys, passwords)
# - Never commit secrets to GitHub
# - Test each configuration:
#   Backend: https://your-service.azurewebsites.net/docs
#   Frontend: https://your-frontend.azurewebsites.net
#
# ============================================================================

# TROUBLESHOOTING:
#
# - If app won't start: check Log Stream
# - If settings don't work: verify Key is spelled correctly
# - If connection fails: check firewall rules (database)
# - If CORS fails: check VITE_API_BASE_URL is correct
#
# ============================================================================
