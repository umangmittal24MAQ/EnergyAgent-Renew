# Pre-Deployment Checklist - Energy Consumption Reporting Agent

**Status**: Ready to deploy to Azure  
**Target**: Your existing Azure resources  
**Date**: April 1, 2026

---

## ✅ Code Preparation

### Backend Code
- [x] Code structure organized (routes → schemas → services)
- [x] All imports working (tested 8/8 tests passed)
- [x] 40 API endpoints ready
- [x] requirements.txt with all dependencies
- [x] gunicorn added for production ASGI
- [x] startup.sh script ready
- [x] app/api/main.py creates FastAPI app with all routers
- [x] app/core/ config, logger, exceptions, constants ready

### Frontend Code
- [x] React structure complete
- [x] 6 page components created
- [x] MainLayout component ready
- [x] Config files created (api.config.js, theme.config.js, index.js)
- [x] Auth infrastructure in place
- [x] web.config created for IIS routing
- [x] package.json with all dependencies
- [x] Build ready (npm run build)

---

## 🎯 Azure Resources Ready

- [x] Resource Group: `energyconsumptionreportingagent`
- [x] Region: `West US`
- [x] Backend App: `energyconsumptionreportingagent-appbe` (Python 3.11)
- [x] Frontend App: `energyconsumptionreportingagent-appfe` (Node.js 18)
- [x] Azure OpenAI: `energyconsumptionreportingagent-openai`
- [x] Storage: `enegyagentblobs`
- [x] UAMI: `energyconsumptionreportingagent-uami`
- [x] Log Analytics Workspace
- [x] Application Insights
- [x] Action Group for alerts

---

## 📋 Deployment Steps Checklist

### Phase 1: Backend Deployment

**Setup**
- [ ] Log into Azure Portal: https://portal.azure.com
- [ ] Go to Backend App Service: `energyconsumptionreportingagent-appbe`
- [ ] Click **Configuration** in left sidebar

**Configure Settings**
- [ ] Set API_HOST = 0.0.0.0
- [ ] Set API_PORT = 8000
- [ ] Set APP_ENV = production
- [ ] Set DEBUG = false
- [ ] Set API_RELOAD = false
- [ ] Set LOG_LEVEL = INFO
- [ ] Click **Save**

**OpenAI Settings**
- [ ] Set AZURE_OPENAI_ENDPOINT = https://energyconsumptionreportingagent-openai.openai.azure.com/
- [ ] Set AZURE_OPENAI_API_VERSION = 2024-02-15-preview
- [ ] Set AZURE_OPENAI_DEPLOYMENT_NAME = (your model name)
- [ ] Set OPENAI_ENABLE = true

**Storage Settings**
- [ ] Set STORAGE_ACCOUNT_NAME = enegyagentblobs
- [ ] Set STORAGE_CONTAINER_NAME = reports
- [ ] Set AZURE_STORAGE_ENABLE = true
- [ ] Set USE_MANAGED_IDENTITY = true

**Startup Command**
- [ ] Go to **General settings** tab
- [ ] Set Startup Command: `gunicorn --workers 4 --bind 0.0.0.0:8000 app.api.main:app`
- [ ] Click **Save**

**Deploy Code**
- [ ] Method A (GitHub):
  - [ ] Click **Deployment Center**
  - [ ] Select **GitHub**
  - [ ] Authorize GitHub account
  - [ ] Select your Energy Dashboard repository
  - [ ] Select branch: `main` or `master`
  - [ ] Click **Save**
  - [ ] Wait 5 minutes for auto-deployment
  
- OR Method B (ZIP Upload):
  - [ ] Click **Advanced tools** → **Go**
  - [ ] Go to **Debug console** → **PowerShell**
  - [ ] Navigate to `D:\home\site\wwwroot`
  - [ ] Upload: `app/` folder + `requirements.txt`
  - [ ] Extract files
  - [ ] Delete ZIP file

**Verify Deployment**
- [ ] Check **Deployment Center** shows "Success"
- [ ] Click **Log stream** and wait for startup logs
- [ ] Visit: https://energyconsumptionreportingagent-appbe.azurewebsites.net/docs
- [ ] Should see Swagger UI with 40+ endpoints

---

### Phase 2: Frontend Deployment

**Setup**
- [ ] Go to Frontend App Service: `energyconsumptionreportingagent-appfe`
- [ ] Click **Configuration**

**Configure Settings**
- [ ] Set VITE_API_BASE_URL = https://energyconsumptionreportingagent-appbe.azurewebsites.net
- [ ] Set NODE_ENV = production
- [ ] Set VITE_LOG_LEVEL = error
- [ ] Click **Save**

**Deploy Code**
- [ ] Method A (GitHub):
  - [ ] Click **Deployment Center**
  - [ ] Click **Authorize** (if not already)
  - [ ] Select same repository
  - [ ] Click **Save**
  - [ ] Wait 5 minutes
  
- OR Method B (ZIP Upload):
  - [ ] Run locally: `npm run build` (creates dist/ folder)
  - [ ] Click **Advanced tools** → **Go**
  - [ ] Upload: `dist/` folder + `package.json` + `web.config`
  - [ ] Extract files
  - [ ] Delete ZIP

**Verify Deployment**
- [ ] Check **Deployments** shows "Success"
- [ ] Visit: https://energyconsumptionreportingagent-appfe.azurewebsites.net
- [ ] Should see Energy Dashboard UI
- [ ] Open DevTools (F12) → **Console** should have no red errors

---

### Phase 3: UAMI Configuration

**Assign to Backend**
- [ ] Go to Backend App Service
- [ ] Click **Identity** (left sidebar)
- [ ] Switch to **User assigned** tab
- [ ] Click **+ Add**
- [ ] Select: `energyconsumptionreportingagent-uami`
- [ ] Click **Add**

**Assign to Frontend**
- [ ] Go to Frontend App Service
- [ ] Click **Identity**
- [ ] Switch to **User assigned** tab
- [ ] Click **+ Add**
- [ ] Select: `energyconsumptionreportingagent-uami`
- [ ] Click **Add**

**Grant OpenAI Permissions**
- [ ] Go to Azure OpenAI: `energyconsumptionreportingagent-openai`
- [ ] Click **Access Control (IAM)**
- [ ] Click **+ Add** → **Add role assignment**
- [ ] Role: `Cognitive Services OpenAI User`
- [ ] Assign to: `User`
- [ ] Select: `energyconsumptionreportingagent-uami`
- [ ] Click **Review + assign**

**Grant Storage Permissions**
- [ ] Go to Storage Account: `enegyagentblobs`
- [ ] Click **Access Control (IAM)**
- [ ] Click **+ Add** → **Add role assignment**
- [ ] Role: `Storage Blob Data Contributor`
- [ ] Assign to: `User-assigned managed identity`
- [ ] Select: `energyconsumptionreportingagent-uami`
- [ ] Click **Review + assign**

---

### Phase 4: Testing

**Backend Tests**
- [ ] Health endpoint: https://energyconsumptionreportingagent-appbe.azurewebsites.net/health
  - Expected: 200 OK
- [ ] Swagger docs: https://energyconsumptionreportingagent-appbe.azurewebsites.net/docs
  - Expected: List of 40+ endpoints
- [ ] OpenAPI schema: https://energyconsumptionreportingagent-appbe.azurewebsites.net/openapi.json
  - Expected: JSON schema with all routes

**Frontend Tests**
- [ ] Page loads: https://energyconsumptionreportingagent-appfe.azurewebsites.net
  - Expected: Energy Dashboard UI
- [ ] No console errors: Open F12 → **Console** tab
  - Expected: Blue/yellow messages OK, NO red errors
- [ ] Network calls work: F12 → **Network** tab → perform action
  - Expected: API calls to backend show status 200

**Integration Tests**
- [ ] Frontend can call backend:
  - Click button/action in frontend
  - Check Network tab (F12)
  - Should see request to backend
  - Should get 200 response (not 404/500)

**Monitoring Tests**
- [ ] Log Analytics:
  - [ ] Search for "Log Analytics Workspace"
  - [ ] Click **Logs** tab
  - [ ] Run: `AppTraces | take 10`
  - [ ] Should see logs from your services
- [ ] Application Insights:
  - [ ] Should show page views and requests
  - [ ] Should show response times
  - [ ] Should show any errors

---

## 🎯 Expected URLs After Deployment

| Service | URL |
|---------|-----|
| **Backend API** | https://energyconsumptionreportingagent-appbe.azurewebsites.net |
| **Backend Docs** | https://energyconsumptionreportingagent-appbe.azurewebsites.net/docs |
| **Backend Health** | https://energyconsumptionreportingagent-appbe.azurewebsites.net/health |
| **Frontend** | https://energyconsumptionreportingagent-appfe.azurewebsites.net |
| **Azure Portal** | https://portal.azure.com |

---

## 🔍 Quick Troubleshooting

| Issue | Check | Fix |
|-------|-------|-----|
| Backend won't start | Log stream (backend app) | Check error, fix code, redeploy |
| Frontend blank | DevTools console (F12) | Check VITE_API_BASE_URL |
| API calls fail | Network tab (F12) | Verify backend URL, check CORS |
| OpenAI error | Backend logs | Check UAMI permissions, endpoint URL |
| Storage error | Backend logs | Check UAMI has Storage role |
| 404 Not Found | API endpoint URL | Check backend deployed correctly |
| 500 Server Error | Log stream | Check backend logs for exception |

---

## 📞 Getting Help

1. **Backend issues**: Check Backend App Service → **Log stream**
2. **Frontend issues**: Check browser DevTools (F12) → **Console** & **Network**
3. **Deployment issues**: Check **Deployments** tab → view deployment logs
4. **OpenAI issues**: Verify permissions in OpenAI → **Access Control (IAM)**
5. **Storage issues**: Verify container exists and UAMI has permissions

---

## ✨ Success Indicators

✅ **Backend Deployment Success:**
- Log stream shows: "All routers loaded successfully"
- /docs endpoint returns Swagger UI
- No error messages in log stream

✅ **Frontend Deployment Success:**
- Page loads without blank screen
- No red errors in DevTools console
- API calls show 200 responses

✅ **Integration Success:**
- Frontend can communicate with backend
- Clicking UI elements triggers API calls
- Data flows between frontend and backend
- OpenAI calls work (if enabled)
- Storage operations work (if enabled)

✅ **Monitoring Success:**
- Logs appear in Log Analytics
- Metrics appear in Application Insights
- No authentication errors

---

## 🚀 After Deployment

1. **Update code in future**:
   - GitHub: `git push` → Auto-deploys (2-5 min)
   - ZIP: Re-upload files → Instant update

2. **Monitor performance**:
   - Check Application Insights for metrics
   - Set up alerts for errors
   - Review logs regularly

3. **Scale if needed**:
   - Increase App Service Plan tier
   - Add more instances
   - Enable auto-scaling

4. **Secure secrets**:
   - Move API keys to Key Vault
   - Use UAMI for all auth
   - Never hardcode secrets

---

## 📋 Final Verification

Before declaring deployment complete:

- [ ] Backend running: https://energyconsumptionreportingagent-appbe.azurewebsites.net/health → 200 OK
- [ ] Backend docs available: https://energyconsumptionreportingagent-appbe.azurewebsites.net/docs
- [ ] Frontend running: https://energyconsumptionreportingagent-appfe.azurewebsites.net
- [ ] Frontend has no console errors (DevTools F12)
- [ ] Frontend calls backend successfully (network tab shows 200)
- [ ] OpenAI integration working (if implemented)
- [ ] Storage integration working (if implemented)
- [ ] Logs in Log Analytics
- [ ] Metrics in Application Insights
- [ ] UAMI permissions verified for OpenAI and Storage

---

## 📝 Notes

- All resource names are preserved as-is from your Azure environment
- UAMI eliminates need for hardcoded API keys (security best practice)
- GitHub Actions provides automatic deployment on code push
- Application Insights tracks frontend performance automatically
- Log Analytics captures all service logs for troubleshooting

---

**You're ready to deploy!** Start with Phase 1 in AZURE_PRODUCTION_DEPLOYMENT.md 🚀

