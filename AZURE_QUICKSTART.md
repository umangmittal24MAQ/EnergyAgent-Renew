# Azure Deployment - Quick Start

**Goal**: Deploy Energy Dashboard to Azure Portal only  
**Time**: 30-45 minutes  
**Cost**: Free tier available

---

## 🚀 Two Ways to Deploy

### Option 1: Using PowerShell Script (Fastest - 5 minutes)

```powershell
# 1. Open PowerShell in project root
cd c:\Users\UmangMittalMAQSoftwa\Downloads\EnergyAgent

# 2. Edit deploy-azure.ps1 and set your values:
#    - subscriptionId
#    - sharepointSiteUrl, sharepointClientId, sharepointClientSecret (if using)
#    - smtpHost, smtpUsername, smtpPassword (if using)

# 3. Run the deployment script
.\deploy-azure.ps1

# 4. Login when prompted
# 5. Wait for completion (5 minutes)

# 6. Done! Services created and configured
```

**Result:**
- ✅ Resource Group created
- ✅ App Service Plan created
- ✅ Backend App Service (Python 3.11)
- ✅ Frontend App Service (Node.js 18)
- ✅ All settings configured

**Next:** Jump to [Step 3: Deploy Code](#step-3-deploy-code) below

---

### Option 2: Manual Setup in Azure Portal (15 minutes)

Follow **AZURE_DEPLOYMENT_GUIDE.md** step-by-step with screenshots.

---

## Step 1: Prerequisites ✓

- [x] Azure account (free at azure.microsoft.com)
- [x] Azure CLI installed (for script option)
- [x] Project code ready (already done)
- [x] GitHub account (recommended for auto-deployment)

---

## Step 2: Create Services

### Using Script:
```powershell
# Just run: .\deploy-azure.ps1
# Everything is created automatically
```

### Using Portal:
See **AZURE_DEPLOYMENT_GUIDE.md** Section 2 for detailed steps

---

## Step 3: Deploy Code

### Option A: GitHub Actions (Recommended - Automatic)

**Backend:**
1. Push your code to GitHub
2. Go to Backend App Service → **Deployment Center**
3. Select **GitHub**
4. Authorize and select your repo
5. Click **Save**
6. Azure automatically deploys on every push

**Frontend:**
1. Repeat same process for Frontend App Service
2. Azure creates GitHub Actions workflows automatically
3. Deployments happen automatically

**Advantages:**
- ✓ Automatic updates on git push
- ✓ GitHub Actions free for public repos
- ✓ No manual uploads needed
- ✓ Easy version control

---

### Option B: Manual ZIP Upload (Simple - 5 minutes each)

**For Backend:**

1. Go to Backend App Service
2. Click **Advanced Tools** → **Go**
3. In Kudu, go to **Debug console** → **PowerShell**
4. Navigate to `D:\home\site\wwwroot`
5. Drag and drop or upload:
   - `app/` folder
   - `requirements.txt`
6. Extract and delete ZIP
7. Go to **Configuration** → **General settings**
8. **Startup command**: `gunicorn --workers 4 --bind 0.0.0.0:8000 app.api.main:app`
9. Click **Save**

**For Frontend:**

1. Build locally: `npm install && npm run build`
2. Go to Frontend App Service
3. Click **Advanced Tools** → **Go**
4. Upload:
   - `dist/` folder
   - `package.json`
   - `web.config` (already created for you)
5. Azure serves from `dist/` folder

**Advantages:**
- ✓ Simple and straightforward
- ✓ No GitHub setup needed
- ✓ Full control over what's uploaded

---

## Step 4: Verify Deployment

### Check Backend
```
Open: https://energy-dashboard-api.azurewebsites.net/docs

Should show:
- Swagger UI with all 40 routes
- "GET /health" endpoint
- API documentation
```

### Check Frontend
```
Open: https://energy-dashboard-app.azurewebsites.net

Should show:
- Energy Dashboard UI
- No console errors (F12)
```

### Check Connection
- Click a button in frontend
- Should call backend API
- Check browser Network tab
- Should see API call to backend URL

---

## Step 5: Configure Environment

### In Azure Portal - Backend App Service

Click **Configuration** → Add these settings:

**Required:**
```
API_HOST = 0.0.0.0
API_PORT = 8000
APP_ENV = production
DEBUG = false
API_RELOAD = false
```

**For SharePoint:**
```
SHAREPOINT_SITE_URL = https://yourcompany.sharepoint.com/sites/energy
SHAREPOINT_CLIENT_ID = your-id
SHAREPOINT_CLIENT_SECRET = your-secret
```

**For Email Scheduling:**
```
SMTP_HOST = smtp.gmail.com
SMTP_PORT = 587
SMTP_USERNAME = your-email@gmail.com
SMTP_PASSWORD = your-app-password
```

**For Database (if using):**
```
DATABASE_URL = mssql+pyodbc://...
REDIS_URL = redis://...
```

Click **Save**

### In Azure Portal - Frontend App Service

Click **Configuration** → Add:
```
VITE_API_BASE_URL = https://energy-dashboard-api.azurewebsites.net
NODE_ENV = production
```

Click **Save**

---

## Step 6: Monitor

### View Logs

**Backend logs:**
1. Go to Backend App Service
2. Click **Log stream** (left menu)
3. Watch real-time output

**Frontend logs:**
1. Go to Frontend App Service
2. Click **Log stream**
3. Watch for errors

### Check Deployment Status

1. Go to App Service
2. Click **Deployments** (left menu)
3. Should show "Success" ✓

### Enable Monitoring

1. Go to App Service
2. Look for **Application Insights** (left menu)
3. Click "Turn on"
4. See performance metrics, errors, usage

---

## Troubleshooting

### Backend shows 500 error

1. Check **Log stream** for error messages
2. Verify all `SHAREPOINT_*` settings are correct
3. Check Python version: `python --version` (should be 3.11+)

**Fix:**
```
Go to Configuration → check all settings
Fix any missing or incorrect values
Restart the app
```

### Frontend shows blank page

1. Open Developer Tools (F12)
2. Check **Console** tab for JavaScript errors
3. Check **Network** tab for failed API calls

**Fix:**
```
Check VITE_API_BASE_URL points to correct backend
Rebuild: npm run build
Redeploy to Azure
```

### API calls fail (CORS error)

1. Backend is blocking cross-origin requests
2. Update Backend App Service settings:
   ```
   ALLOWED_ORIGINS = https://energy-dashboard-app.azurewebsites.net
   ```
3. Redeploy backend

---

## Life After Deployment

### View Your App
- Backend: `https://energy-dashboard-api.azurewebsites.net`
- Frontend: `https://energy-dashboard-app.azurewebsites.net`
- Docs: `https://energy-dashboard-api.azurewebsites.net/docs`

### Make Updates

**With GitHub Actions:**
1. Make code changes locally
2. `git push` to GitHub
3. Azure deploys automatically (2-5 minutes)
4. App updates live

**With Manual Upload:**
1. Make code changes locally
2. Build: `npm run build` (frontend) or `pip install -r requirements.txt` (backend)
3. Upload ZIP to Kudu
4. App updates immediately

### Monitor Performance

1. Go to App Service → **Application Insights**
2. See:
   - Response times
   - Error rates
   - User activity
   - Custom metrics

### Scale Up

If traffic increases:
1. Go to **App Service Plan**
2. Click **Scale up**
3. Choose higher tier (Basic, Standard, Premium)
4. Click Apply

---

## Cost Calculation

| Item | Free Tier | Cost |
|------|-----------|------|
| 2 App Services | Free F1 | $0 |
| 50 GB bandwidth | Free | $0 |
| Application Insights | First 1 GB free | $0 |
| **Total** | | **$0/month** |

**Upgrade when needed:**
- Free F1: Limited to 60 minutes per day
- Basic B1: ~$50-70/month (unlimited)
- Standard S1: ~$100-150/month (better performance)

---

## Commands Reference

### Using Azure CLI

```powershell
# Login
az login

# Check deployment status
az webapp deployment list --resource-group energy-dashboard-rg

# View logs
az webapp log tail --name energy-dashboard-api --resource-group energy-dashboard-rg

# Restart app
az webapp restart --name energy-dashboard-api --resource-group energy-dashboard-rg

# Check settings
az webapp config appsettings list --name energy-dashboard-api --resource-group energy-dashboard-rg
```

### Using PowerShell in Kudu

```powershell
# SSH into backend: Go to App Service → Advanced Tools → SSH
# In SSH console:

# Check Python
python --version

# Install deps
pip install -r requirements.txt

# Test import
python -c "from app.api.main import create_app; print('OK')"

# Check logs
type D:\home\LogFiles\*.log
```

---

## Files Provided

| File | Purpose |
|------|---------|
| **AZURE_DEPLOYMENT_GUIDE.md** | Detailed step-by-step guide (15 pages) |
| **deploy-azure.ps1** | Automated script (create everything in 5 minutes) |
| **frontend/web.config** | Azure IIS configuration for React |
| **backend/startup.sh** | Backend startup configuration |
| **frontend/startup.sh** | Frontend startup configuration |

---

## Next: Choose Your Path

### Path 1: Fastest (5 minutes)
```
1. Run: .\deploy-azure.ps1
2. Upload code (manual or GitHub Actions)
3. Done!
```

### Path 2: Manual (30 minutes)
```
1. Follow AZURE_DEPLOYMENT_GUIDE.md step-by-step
2. Use Azure Portal for all steps
3. Done!
```

### Path 3: GitHub Actions (5 minutes + auto-deploy)
```
1. Push code to GitHub
2. Configure: Deployment Center → GitHub
3. Auto-deploys on every push
```

---

## Support

- Azure Help: https://docs.microsoft.com/azure/
- FastAPI: https://fastapi.tiangolo.com/deployment/azure/
- App Service: https://docs.microsoft.com/azure/app-service/
- Troubleshooting: See **AZURE_DEPLOYMENT_GUIDE.md** → Troubleshooting section

---

**Status**: ✅ Ready for Azure Deployment  
**Estimated Time**: 5-30 minutes (depending on method)  
**Cost**: Free tier available  

**Let's deploy!** 🚀

---

## Quick Reference: Required URLs After Deployment

```
Backend API:        https://energy-dashboard-api.azurewebsites.net
Backend Swagger:    https://energy-dashboard-api.azurewebsites.net/docs
Frontend App:       https://energy-dashboard-app.azurewebsites.net
Azure Portal:       https://portal.azure.com
Resource Group:     energy-dashboard-rg
```

Copy these URLs after deployment for easy access.
