# Azure Portal Deployment Guide - Energy Dashboard

**Target**: Azure App Service (Backend + Frontend)  
**Estimated Time**: 30-45 minutes  
**Cost**: Free tier available for demo  
**Last Updated**: April 1, 2026

---

## Table of Contents

1. [Quick Overview](#quick-overview)
2. [Step 1: Azure Portal Setup](#step-1-azure-portal-setup)
3. [Step 2: Create App Services](#step-2-create-app-services)
4. [Step 3: Database Setup (Optional)](#step-3-database-setup-optional)
5. [Step 4: Configure & Deploy](#step-4-configure--deploy)
6. [Step 5: Map Domain (Optional)](#step-5-map-domain-optional)
7. [Step 6: Monitor Deployment](#step-6-monitor-deployment)
8. [Troubleshooting](#troubleshooting)

---

## Quick Overview

You'll create:
- **Backend App Service** (Python FastAPI)
- **Frontend App Service** (Node.js React)
- **Container Registry** (optional, for Docker)
- **Application Insights** (monitoring)
- **Key Vault** (secrets management)

---

## Step 1: Azure Portal Setup

### 1.1 Prerequisites
- [x] Azure account (create free at azure.microsoft.com)
- [x] Project code ready (already done ✓)
- [x] requirements.txt (already done ✓)

### 1.2 Log In to Azure Portal

1. Go to https://portal.azure.com
2. Sign in with your Microsoft account
3. If prompted, create a new subscription or use existing

### 1.3 Create Resource Group

This groups all your resources together for easy management.

**Steps:**
1. Click **Create a resource**
2. Search for **Resource Group**
3. Click **Create**
4. Fill in:
   - **Subscription**: Your subscription
   - **Resource group name**: `energy-dashboard-rg`
   - **Region**: Select closest to you (e.g., `East US`, `West Europe`)
5. Click **Review + create** → **Create**

---

## Step 2: Create App Services

### 2.1 Create Backend App Service (FastAPI)

**Steps:**

1. Click **Create a resource**
2. Search for **App Service**
3. Click **Create**

4. **Basics Tab:**
   - **Subscription**: Your subscription
   - **Resource Group**: `energy-dashboard-rg`
   - **Name**: `energy-dashboard-api` (must be globally unique)
   - **Runtime stack**: `Python 3.11`
   - **Operating System**: `Linux`
   - **Region**: Same as resource group
   - **App Service Plan**: Click "Create new"
     - **Name**: `energy-dashboard-plan`
     - **Sku and size**: `Free F1` (or `Basic B1` if Free isn't available)
     - Click **OK**

5. Click **Review + create** → **Create**

6. **Wait** for deployment to complete (2-3 minutes)

7. Go to the deployed Backend App Service
   - Click **Configuration** (left menu)
   - Click **+ New application setting**
   
   Add these settings:
   ```
   API_HOST = 0.0.0.0
   API_PORT = 8000
   APP_ENV = production
   DEBUG = false
   API_RELOAD = false
   ```

   **For SharePoint (if using):**
   ```
   SHAREPOINT_SITE_URL = your-site-url
   SHAREPOINT_CLIENT_ID = your-client-id
   SHAREPOINT_CLIENT_SECRET = your-secret
   ```

   **For Email (if using):**
   ```
   SMTP_HOST = smtp.gmail.com
   SMTP_PORT = 587
   SMTP_USERNAME = your-email@gmail.com
   SMTP_PASSWORD = your-app-password
   ```

   Click **Save**

---

### 2.2 Create Frontend App Service (React)

**Steps:**

1. Click **Create a resource**
2. Search for **App Service**
3. Click **Create**

4. **Basics Tab:**
   - **Subscription**: Your subscription
   - **Resource Group**: `energy-dashboard-rg`
   - **Name**: `energy-dashboard-app` (must be globally unique)
   - **Runtime stack**: `Node 18 LTS` (or Node 20 if available)
   - **Operating System**: `Linux`
   - **Region**: Same as resource group
   - **App Service Plan**: Select `energy-dashboard-plan` (created above)

5. Click **Review + create** → **Create**

6. **Wait** for deployment to complete (2-3 minutes)

7. Go to the deployed Frontend App Service
   - Click **Configuration** (left menu)
   - Click **+ New application setting**
   
   Add:
   ```
   VITE_API_BASE_URL = https://energy-dashboard-api.azurewebsites.net
   NODE_ENV = production
   ```

   Replace `energy-dashboard-api` with your actual backend service name.
   
   Click **Save**

---

## Step 3: Database Setup (Optional)

Skip this if using only file-based storage or Google Sheets.

### 3.1 Azure SQL Database

**If you need a database:**

1. Click **Create a resource**
2. Search for **SQL Database**
3. Click **Create**

4. **Basics Tab:**
   - **Subscription**: Your subscription
   - **Resource Group**: `energy-dashboard-rg`
   - **Database name**: `energy_dashboard_db`
   - **Server**: Click "Create new"
     - **Server name**: `energy-dashboard-server` (globally unique)
     - **Location**: Same region
     - **Authentication method**: Use SQL authentication
     - **Admin username**: `sqladmin`
     - **Password**: Create strong password (save this!)
     - Click **OK**
   - **Compute + storage**: `Free` (DTU-based) if available
   - **Backup redundancy**: `Locally-redundant`

5. Click **Review + create** → **Create**

6. After creation, add the connection string to your Backend App Service:
   - Go back to Backend App Service
   - **Configuration** tab
   - Add new setting:
     ```
     DATABASE_URL = mssql+pyodbc://sqladmin:YOUR_PASSWORD@energy-dashboard-server.database.windows.net/energy_dashboard_db?driver=ODBC+Driver+17+for+SQL+Server
     ```

---

## Step 4: Configure & Deploy

### 4.1 Deploy Backend (Method A: Git Integration - Easiest)

**Prerequisites:**
- Your code on GitHub (or Azure DevOps)

**Steps:**

1. Go to your **Backend App Service**
2. Click **Deployment Center** (left menu)
3. Select **GitHub** (or Azure DevOps)
4. Click **Authorize** and login
5. Fill in:
   - **Organization**: Your GitHub account
   - **Repository**: Your Energy Dashboard repo
   - **Branch**: `main` or `master`
   - **Build type**: `GitHub Actions`
6. Click **Save**

Azure will automatically:
- Create a GitHub Actions workflow
- Deploy on every push to `main`
- Build and run your app

---

### 4.2 Deploy Backend (Method B: Zip Upload - Manual)

**If not using Git:**

1. Create a zip file:
   ```powershell
   # Go to project root
   cd c:\Users\UmangMittalMAQSoftwa\Downloads\EnergyAgent\backend
   
   # Create zip with app directory
   Compress-Archive -Path "app", "requirements.txt" -DestinationPath "backend.zip"
   ```

2. Go to **Backend App Service**
3. Click **Advanced Tools** → **Go** (opens Kudu dashboard)
4. Go to **Debug console** → **PowerShell** tab
5. Navigate to `D:\home\site\wwwroot`
6. Upload `backend.zip` via the file uploader
7. Extract: Right-click zip → Extract
8. Delete the zip file

---

### 4.3 Deploy Frontend (Method A: Git Integration)

**Same as Backend:**

1. Go to **Frontend App Service**
2. Click **Deployment Center**
3. Select **GitHub**
4. Fill in repository info
5. Click **Save**

---

### 4.4 Deploy Frontend (Method B: Manual Build)

**If not using Git:**

1. Build React application:
   ```powershell
   cd c:\Users\UmangMittalMAQSoftwa\Downloads\EnergyAgent\frontend
   npm install
   npm run build
   ```

2. Create zip of build output:
   ```powershell
   Compress-Archive -Path "dist", "package.json" -DestinationPath "frontend.zip"
   ```

3. Upload to **Frontend App Service**:
   - Click **Advanced Tools** → **Go**
   - Navigate to `D:\home\site\wwwroot`
   - Upload and extract `frontend.zip`

4. Create `web.config` file for Node.js static hosting:
   ```xml
   <?xml version="1.0" encoding="utf-8"?>
   <configuration>
     <system.webServer>
       <rewrite>
         <rules>
           <rule name="React Routes" stopProcessing="true">
             <match url=".*" />
             <conditions logicalGrouping="MatchList">
               <add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" />
               <add input="{REQUEST_FILENAME}" matchType="IsDirectory" negate="true" />
             </conditions>
             <action type="Rewrite" url="/" />
           </rule>
         </rules>
       </rewrite>
       <staticContent>
         <mimeMap fileExtension=".json" mimeType="application/json" />
         <mimeMap fileExtension=".wasm" mimeType="application/wasm" />
       </staticContent>
     </system.webServer>
   </configuration>
   ```

   Save as `web.config` in root directory.

---

### 4.5 Configure Startup Command

**For Backend:**

1. Go to **Backend App Service**
2. Click **Configuration** → **General settings**
3. Set **Startup command**:
   ```
   gunicorn --workers 4 --bind 0.0.0.0:8000 app.api.main:app
   ```
   
   Or for direct Python:
   ```
   python app/api/main.py
   ```

4. Click **Save**

**For Frontend:**

1. Go to **Frontend App Service**
2. Click **Configuration** → **General settings**
3. Set **Startup command**:
   ```
   npm start
   ```

4. Click **Save**

---

## Step 5: Map Domain (Optional)

### 5.1 Custom Domain Setup

**If you have a custom domain:**

1. Go to **Backend App Service**
2. Click **Custom domains** (left menu)
3. Add custom domain:
   - Enter your domain (e.g., `api.yourdomain.com`)
   - Add DNS records as shown
   - Validate and add

**Repeat for Frontend** with subdomain like `app.yourdomain.com`

---

## Step 6: Monitor Deployment

### 6.1 Check Deployment Status

**Backend:**
1. Go to **Backend App Service**
2. Click **Deployment slots** or **Deployments** (left menu)
3. Check status (should show "Success" ✓)

**Frontend:**
1. Go to **Frontend App Service**
2. Check deployments similar to above

### 6.2 View Logs

**Backend Logs:**
1. Go to **Backend App Service**
2. Click **Log stream** (left menu)
3. Watch real-time logs as app runs

**Frontend Logs:**
1. Go to **Frontend App Service**
2. Click **Log stream**
3. Watch for errors

### 6.3 Test Your App

**Backend:**
```
https://energy-dashboard-api.azurewebsites.net/docs
```

Should show Swagger UI with all 40 routes ✓

**Frontend:**
```
https://energy-dashboard-app.azurewebsites.net
```

Should show your Energy Dashboard UI ✓

---

## Troubleshooting

### Backend Not Starting

**Check:**
1. Go to **Deployment Center** → Check deployment history
2. Go to **Log stream** → Look for error messages
3. Check **Application settings** → Verify all variables set

**Common Issues:**
- Missing dependencies: Ensure `requirements.txt` is in root
- Wrong Python version: Check "Runtime stack" is Python 3.11+
- Port binding: Ensure `API_PORT=8000` and `API_HOST=0.0.0.0`

**Fix:**
```powershell
# SSH into backend
# Go to Advanced Tools → SSH

# Check Python
python --version

# Check installed packages
pip list | grep fastapi

# Install requirements
pip install -r requirements.txt

# Test import
python -c "from app.api.main import create_app; print('OK')"
```

### Frontend Not Loading

**Check:**
1. Go to **Browser Developer Tools** (F12)
2. Check **Network** tab for failed requests
3. Check **Console** tab for JavaScript errors
4. Check `VITE_API_BASE_URL` points to correct backend

**Common Issues:**
- CORS blocked from backend
- API_BASE_URL pointing to localhost
- React app not built (`dist` folder missing)

**Fix:**
1. Update Frontend App Service settings:
   ```
   VITE_API_BASE_URL = https://energy-dashboard-api.azurewebsites.net
   ```
2. Rebuild and redeploy frontend

### CORS Errors

**Fix in Backend:**

1. Go to **Backend App Service** → **Configuration**
2. Add application setting:
   ```
   ALLOWED_ORIGINS = https://energy-dashboard-app.azurewebsites.net,https://yourdomain.com
   ```

3. Update `app/api/main.py` CORS configuration:
   ```python
   from fastapi.middleware.cors import CORSMiddleware
   
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://energy-dashboard-app.azurewebsites.net"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

4. Redeploy

### Database Connection Issues

**Check connection string:**
- Go to Backend App Service → Configuration
- Verify `DATABASE_URL` is correct
- Format: `mssql+pyodbc://user:password@server/database?driver=ODBC+Driver+17+for+SQL+Server`

**Test connection:**
```powershell
# SSH into backend
# Create test script
cat > test_db.py << 'EOF'
import os
from sqlalchemy import create_engine

db_url = os.getenv('DATABASE_URL')
try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        print("Connection successful!")
except Exception as e:
    print(f"Connection failed: {e}")
EOF

python test_db.py
```

---

## Scaling & Performance

### Scale Up (More Power)

1. Go to **App Service Plan** (shared by both services)
2. Click **Scale up** (left menu)
3. Select higher tier (Basic, Standard, etc.)
4. Click **Apply**

### Scale Out (Multiple Instances)

1. Go to **App Service Plan**
2. Click **Scale out** (left menu)
3. Change **Instance count**: Default 1 → 2, 3, etc.
4. Click **Save**

---

## Cost Optimization

### Use Free Tier
- Free tier includes:
  - 1GB storage
  - 1GB RAM
  - Limited CPU
  - Perfect for demo/testing

### Use Linux
- Linux is cheaper than Windows
- Already using Linux ✓

### Shut Down When Not Used
- Production: Leave running
- Testing: Stop when not in use
  - App Service → Click **Stop**
  - Restart when needed

---

## Backup & Recovery

### Enable Backups

1. Go to **Backend App Service**
2. Click **Backup** (left menu)
3. Click **Configure**
4. Select storage account for backups
5. Set schedule (daily recommended)
6. Click **Save**

### Restore from Backup

1. Go to **Backups**
2. Select backup version
3. Click **Restore**
4. Confirm

---

## SSL/TLS Certificates

### Azure Managed Certificates (Free)

1. Go to **TLS/SSL settings** (left menu)
2. Click **Add TLS/SSL binding**
3. Select your domain
4. Azure automatically handles certificate renewal ✓

---

## Monitoring with Application Insights

### Enable Monitoring

1. Go to **Backend App Service**
2. Look for **Application Insights** (left menu)
3. Click "Turn on Application Insights"
4. Create new insights resource
5. Click **Apply**

This gives you:
- Performance metrics
- Error tracking
- User activity
- Custom alerts

---

## Advanced: CI/CD with GitHub Actions

### Automatic Deployment on Push

Azure creates GitHub Actions workflow automatically.

**If using manual Git integration:**

1. Workflow file location: `.github/workflows/` (automatically created)
2. Workflow triggers on: Push to main branch
3. It will:
   - Install dependencies
   - Run tests (if any)
   - Build application
   - Deploy to Azure App Service

**Monitor workflow:**
- Go to your GitHub repo
- Click **Actions** tab
- Watch deployment progress

---

## URLs After Deployment

| Service | URL |
|---------|-----|
| Backend API | `https://energy-dashboard-api.azurewebsites.net` |
| Backend Docs | `https://energy-dashboard-api.azurewebsites.net/docs` |
| Frontend App | `https://energy-dashboard-app.azurewebsites.net` |
| Custom Backend | `https://api.yourdomain.com` (if configured) |
| Custom Frontend | `https://app.yourdomain.com` (if configured) |

---

## Final Checklist

- [ ] Resource Group created (`energy-dashboard-rg`)
- [ ] Backend App Service created (`energy-dashboard-api`)
- [ ] Frontend App Service created (`energy-dashboard-app`)
- [ ] Application settings configured in both services
- [ ] Backend deployed and running (check `/docs`)
- [ ] Frontend deployed and running
- [ ] API Base URL pointing to correct backend
- [ ] CORS configured if needed
- [ ] Database created (if using SQL)
- [ ] Monitoring enabled (Application Insights)
- [ ] Custom domain configured (optional)
- [ ] SSL certificates active
- [ ] Backups enabled

---

## Next Steps

1. ✅ Complete deployment checklist above
2. Test API: `https://energy-dashboard-api.azurewebsites.net/docs`
3. Test Frontend: `https://energy-dashboard-app.azurewebsites.net`
4. Monitor logs in Log Stream
5. Set up alerts in Application Insights
6. Configure auto-scaling if traffic increases
7. Enable backups for data protection

---

## Support

- Azure Documentation: https://docs.microsoft.com/azure/
- FastAPI Deployment: https://fastapi.tiangolo.com/deployment/
- React Deployment: https://react.dev/learn/deployment

---

**Status**: Ready for Azure Deployment ✅  
**Estimated Cost**: Free tier available  
**Deployment Time**: 30-45 minutes  
**Last Updated**: April 1, 2026
