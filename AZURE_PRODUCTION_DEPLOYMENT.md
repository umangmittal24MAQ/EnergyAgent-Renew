# Azure Deployment Guide - Energy Consumption Reporting Agent

**Target Infrastructure**: Your Existing Azure ResourceGroup  
**Date**: April 1, 2026  
**Region**: West US  
**Status**: Ready for deployment

---

## Your Azure Resources

| Resource | Name | Type | URL |
|----------|------|------|-----|
| **Backend** | energyconsumptionreportingagent-appbe | App Service (Python 3.11) | https://energyconsumptionreportingagent-appbe.azurewebsites.net |
| **Frontend** | energyconsumptionreportingagent-appfe | App Service (Node.js 18) | https://energyconsumptionreportingagent-appfe.azurewebsites.net |
| **OpenAI** | energyconsumptionreportingagent-openai | Cognitive Services | https://energyconsumptionreportingagent-openai.openai.azure.com/ |
| **Storage** | enegyagentblobs | Storage Account | (Blob storage) |
| **Identity** | energyconsumptionreportingagent-uami | User Assigned Managed Identity | (Identity for auth) |
| **Logs** | Log Analytics Workspace | Monitoring | (Query logs) |
| **Insights** | Application Insights | Frontend Monitoring | (Performance metrics) |

**Resource Group**: `energyconsumptionreportingagent`

---

## Phase 1: Deploy Backend Code

### Step 1.1: Access Backend App Service

1. Go to **https://portal.azure.com**
2. Search for: `energyconsumptionreportingagent-appbe`
3. Click on the Backend App Service

### Step 1.2: Configure Application Settings

On the App Service page:

1. Click **Configuration** (left sidebar)
2. Click **+ New application setting** for each:

**Infrastructure Settings:**
```
API_HOST                 =  0.0.0.0
API_PORT                 =  8000
APP_ENV                  =  production
DEBUG                    =  false
API_RELOAD               =  false
LOG_LEVEL                =  INFO
```

**Azure OpenAI Integration:**
```
AZURE_OPENAI_ENDPOINT            =  https://energyconsumptionreportingagent-openai.openai.azure.com/
AZURE_OPENAI_API_VERSION         =  2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME     =  (your deployed model name - e.g., gpt-4, gpt-35-turbo)
OPENAI_ENABLE                    =  true
```

**Storage Account Integration:**
```
STORAGE_ACCOUNT_NAME     =  enegyagentblobs
STORAGE_CONTAINER_NAME   =  reports
AZURE_STORAGE_ENABLE     =  true
```

**UAMI Authentication (No API Keys!):**
```
USE_MANAGED_IDENTITY     =  true
MANAGED_IDENTITY_CLIENT_ID  =  (check UAMI details in Portal)
```

**Optional: SharePoint (if using):**
```
SHAREPOINT_SITE_URL      =  https://yourcompany.sharepoint.com/sites/energy
SHAREPOINT_CLIENT_ID     =  (from Azure AD)
SHAREPOINT_CLIENT_SECRET =  (store in Key Vault, not here)
```

**Optional: Email Configuration:**
```
SMTP_HOST                =  smtp.gmail.com
SMTP_PORT                =  587
SMTP_USERNAME            =  your-email@gmail.com
SMTP_PASSWORD            =  (store in Key Vault, not here)
```

3. Click **Save** at the top

✅ **Verify**: Green notification "Application settings updated"

### Step 1.3: Set Startup Command

Still on Configuration page:

1. Click **General settings** tab
2. Find **Startup Command** field
3. Enter:
   ```
   gunicorn --workers 4 --bind 0.0.0.0:8000 app.api.main:app
   ```
4. Click **Save**

✅ **Verify**: Green notification

### Step 1.4: Deploy Backend Code

Still on Backend App Service:

1. Click **Deployment Center** (left sidebar)
2. Choose deployment method:

#### **Method A: GitHub (Recommended - Auto-Deploy)**

1. Click **GitHub** tab
2. Click **Authorize**
3. Select:
   - **Organization**: Your GitHub account
   - **Repository**: Your Energy Dashboard repo
   - **Branch**: `main` or `master`
4. Click **Save**
5. ⏳ **Wait 5 minutes** - GitHub Actions workflow creates automatically

**Verify**: Under **Deployments**, check status = **Success** ✓

#### **Method B: Manual ZIP Upload**

1. Click **Advanced tools** → **Go** (opens Kudu)
2. Click **Debug console** → **PowerShell**
3. Navigate to `D:\home\site\wwwroot`
4. Delete existing files (except web.config if present)
5. Upload ZIP containing:
   - `backend/app/` folder
   - `backend/requirements.txt`
6. Extract: Right-click ZIP → Extract
7. Delete the ZIP file

**Verify**: In Kudu, you should see `app/` and `requirements.txt`

### Step 1.5: Verify Backend Deployment

1. Copy your Backend URL: `https://energyconsumptionreportingagent-appbe.azurewebsites.net`
2. Open in browser: `https://energyconsumptionreportingagent-appbe.azurewebsites.net/docs`
3. **Expected**: Swagger UI with 40+ endpoints

✅ **Success**: If you see API documentation

### Step 1.6: Check Backend Logs

1. Go back to Backend App Service
2. Click **Log stream** (left sidebar)
3. **Expected**: You should see startup logs and "All routers loaded successfully"

✅ **Success**: No error messages

---

## Phase 2: Deploy Frontend Code

### Step 2.1: Access Frontend App Service

1. Search for: `energyconsumptionreportingagent-appfe`
2. Click on the Frontend App Service

### Step 2.2: Configure Frontend Settings

1. Click **Configuration** (left sidebar)
2. Click **+ New application setting** for each:

**Frontend Configuration:**
```
VITE_API_BASE_URL        =  https://energyconsumptionreportingagent-appbe.azurewebsites.net
NODE_ENV                 =  production
VITE_LOG_LEVEL           =  error
```

3. Click **Save** at top

✅ **Verify**: Green notification

### Step 2.3: Deploy Frontend Code

1. Click **Deployment Center** (left sidebar)
2. Choose same method as backend:

#### **Method A: GitHub**

1. Click **Authorize** (if not already)
2. Select same repo
3. Click **Save**
4. ⏳ **Wait 5 minutes**

#### **Method B: Manual ZIP**

1. Click **Advanced tools** → **Go**
2. Click **Debug console** → **PowerShell**
3. Navigate to `D:\home\site\wwwroot`
4. Delete existing files
5. Upload ZIP containing:
   - `frontend/dist/` folder (already built from `npm run build`)
   - `frontend/package.json`
   - `frontend/web.config` ✅ (already created for you)
6. Extract and delete ZIP

✅ **Success**: File structure ready

### Step 2.4: Verify Frontend Deployment

1. Copy Frontend URL: `https://energyconsumptionreportingagent-appfe.azurewebsites.net`
2. Open in browser
3. **Expected**: Energy Dashboard UI loads

✅ **Success**: Page loads without errors

---

## Phase 3: Configure UAMI Authentication

### Step 3.1: Check UAMI Permissions

1. Search for: `energyconsumptionreportingagent-uami` (Managed Identity)
2. Click on it
3. Note the **Client ID** (you'll need it)

### Step 3.2: Assign UAMI to Backend Service

1. Go to Backend App Service: `energyconsumptionreportingagent-appbe`
2. Click **Identity** (left sidebar)
3. Switch to **User assigned** tab
4. Click **+ Add**
5. Select: `energyconsumptionreportingagent-uami`
6. Click **Add**

✅ **Verify**: UAMI now shows in the list

### Step 3.3: Assign UAMI to Frontend Service

1. Go to Frontend App Service: `energyconsumptionreportingagent-appfe`
2. Click **Identity** (left sidebar)
3. Switch to **User assigned** tab
4. Click **+ Add**
5. Select: `energyconsumptionreportingagent-uami`
6. Click **Add**

✅ **Verify**: UAMI now shows in the list

### Step 3.4: Grant UAMI Permissions

**For Azure OpenAI:**
1. Go to: `energyconsumptionreportingagent-openai` (Cognitive Services)
2. Click **Access Control (IAM)** (left sidebar)
3. Click **+ Add** → **Add role assignment**
4. **Role**: `Cognitive Services OpenAI User`
5. **Assign to**: `User`
6. **Select**: Search for `energyconsumptionreportingagent-uami`
7. Click **Review + assign**

✅ **Verify**: Role assigned

**For Storage Account:**
1. Go to: `enegyagentblobs` (Storage Account)
2. Click **Access Control (IAM)**
3. Click **+ Add** → **Add role assignment**
4. **Role**: `Storage Blob Data Contributor` (for read/write)
5. **Assign to**: `User-assigned managed identity`
6. **Select**: `energyconsumptionreportingagent-uami`
7. Click **Review + assign**

✅ **Verify**: Role assigned

---

## Phase 4: Test Deployments

### Step 4.1: Backend API Test

**Test Endpoint 1: Health Check**
```
URL: https://energyconsumptionreportingagent-appbe.azurewebsites.net/health
Expected: 200 OK response
```

**Test Endpoint 2: Swagger Documentation**
```
URL: https://energyconsumptionreportingagent-appbe.azurewebsites.net/docs
Expected: Swagger UI with 40+ endpoints listed
```

**Test Endpoint 3: OpenAPI Schema**
```
URL: https://energyconsumptionreportingagent-appbe.azurewebsites.net/openapi.json
Expected: JSON schema of all API endpoints
```

✅ **Success**: If all 3 return data

### Step 4.2: Frontend Test

**Test Page Load**
```
URL: https://energyconsumptionreportingagent-appfe.azurewebsites.net
Expected: Energy Dashboard UI loads
```

**Test Browser Console (F12)**
- Open DevTools (F12)
- Go to **Console** tab
- Expected: No red errors
- OK to see warnings

**Test Network Tab**
- Go to **Network** tab
- Refresh page
- Expected: API calls to backend succeed (status 200)

✅ **Success**: If UI loads and no errors in console

### Step 4.3: Test Backend ↔ Frontend Communication

1. On the Frontend page, click a button (e.g., Dashboard tab)
2. Open DevTools (F12) → **Network** tab
3. Perform an action that calls the API
4. **Expected**: See API call to `energyconsumptionreportingagent-appbe.azurewebsites.net`
5. Response status should be **200** (not 404 or 500)

✅ **Success**: If API calls work

---

## Phase 5: Configure Azure OpenAI Integration

### Step 5.1: Verify OpenAI Resource

1. Search for: `energyconsumptionreportingagent-openai`
2. Click on it
3. Check **Keys and Endpoint** section:
   - Note the **Endpoint** URL
   - Note the **Api Key** (if not using UAMI)

### Step 5.2: Check Deployed Models

1. Still on OpenAI resource
2. Click **Model deployments** (left sidebar)
3. **See which models are deployed** (e.g., gpt-4, gpt-35-turbo)
4. Note the **Deployment name**

### Step 5.3: Update Backend Configuration

If you haven't already:

1. Go to Backend App Service: `energyconsumptionreportingagent-appbe`
2. Click **Configuration**
3. Edit these settings:

```
AZURE_OPENAI_ENDPOINT            =  https://energyconsumptionreportingagent-openai.openai.azure.com/
AZURE_OPENAI_API_VERSION         =  2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME     =  (your model name from step 5.2)
OPENAI_ENABLE                    =  true
```

4. Click **Save**

### Step 5.4: Test OpenAI Integration

Add this endpoint to your backend (example code):

```python
# In backend/app/routes/data.py or new routes/ai.py
from fastapi import APIRouter, HTTPException
from openai import AzureOpenAI
import os

router = APIRouter()

@router.post("/ai/analyze")
async def analyze_data(data: dict):
    """Test OpenAI integration"""
    try:
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {"role": "system", "content": "You are an energy consumption analyst."},
                {"role": "user", "content": str(data)}
            ]
        )
        
        return {"analysis": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

✅ **Test**: Call endpoint from Frontend or Swagger UI

---

## Phase 6: Configure Storage Integration

### Step 6.1: Verify Storage Account

1. Search for: `enegyagentblobs`
2. Click on it
3. Click **Containers** (left sidebar)
4. **Expected**: See containers like "reports", "data", etc.
5. If none exist, click **+ Container** to create:
   - Name: `reports`
   - Access level: `Private`
   - Click **Create**

### Step 6.2: Configure Backend for Storage

1. Go to Backend App Service: `energyconsumptionreportingagent-appbe`
2. Click **Configuration**
3. Add/update settings:

```
STORAGE_ACCOUNT_NAME     =  enegyagentblobs
STORAGE_CONTAINER_NAME   =  reports
AZURE_STORAGE_ENABLE     =  true
USE_MANAGED_IDENTITY     =  true
```

4. Click **Save**

### Step 6.3: Code Example - Storage Integration

```python
# In backend/app/services/storage_service.py
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential

class StorageService:
    def __init__(self):
        self.client = BlobServiceClient(
            account_url=f"https://{os.getenv('STORAGE_ACCOUNT_NAME')}.blob.core.windows.net",
            credential=DefaultAzureCredential()
        )
        self.container = self.client.get_container_client(
            os.getenv('STORAGE_CONTAINER_NAME')
        )
    
    async def upload_report(self, filename: str, data: bytes):
        """Upload report to blob storage"""
        blob_client = self.container.get_blob_client(filename)
        blob_client.upload_blob(data, overwrite=True)
        return f"Report uploaded: {filename}"
    
    async def download_report(self, filename: str):
        """Download report from blob storage"""
        blob_client = self.container.get_blob_client(filename)
        return blob_client.download_blob().readall()
```

---

## Phase 7: Configure Monitoring

### Step 7.1: Verify Application Insights

1. Search for: Application Insights
2. You should see one connected to `energyconsumptionreportingagent-appfe`
3. Click on it
4. **Expected**: See real-time data (page views, requests, errors)

### Step 7.2: Check Log Analytics

1. Search for: Log Analytics Workspace
2. Click on it
3. Click **Logs** (left sidebar)
4. Run a simple query:
   ```kusto
   AppTraces | take 10
   ```
5. **Expected**: See logs from your services

### Step 7.3: Set Up Alerts

1. Go to Application Insights
2. Click **Alerts** (left sidebar)
3. Click **+ Create** → **Alert Rule**
4. **Condition**: Select something like:
   - "Failed requests > 5 in 5 minutes"
   - "Response time > 2 seconds"
5. **Action group**: Select existing or create
6. **Save alert**

✅ **Verify**: Alert created

---

## Phase 8: Verification Checklist

### Backend Verification
- [ ] App Service shows "Running" status
- [ ] `/docs` endpoint returns Swagger UI
- [ ] `/health` endpoint returns 200 OK
- [ ] Log stream shows no errors
- [ ] Configuration settings all set
- [ ] UAMI assigned and permissions granted
- [ ] OpenAI integration working (if implemented)
- [ ] Storage integration working (if implemented)

### Frontend Verification
- [ ] App Service shows "Running" status
- [ ] Home page loads in browser
- [ ] No red errors in browser console (F12)
- [ ] API calls to backend succeed
- [ ] Configuration settings all set
- [ ] VITE_API_BASE_URL points to correct backend
- [ ] Frontend can call backend endpoints

### Integration Verification
- [ ] Frontend → Backend communication working
- [ ] Backend → OpenAI communication working (if enabled)
- [ ] Backend → Storage communication working (if enabled)
- [ ] Logs appearing in Log Analytics
- [ ] Metrics appearing in Application Insights
- [ ] No authentication errors in logs

### URLs Working
- [ ] Backend Swagger: https://energyconsumptionreportingagent-appbe.azurewebsites.net/docs
- [ ] Backend Health: https://energyconsumptionreportingagent-appbe.azurewebsites.net/health
- [ ] Frontend App: https://energyconsumptionreportingagent-appfe.azurewebsites.net

---

## Troubleshooting

### Backend Won't Start

**Check logs:**
1. Go to Backend App Service
2. Click **Log stream**
3. Look for error messages

**Common issues:**
- Missing `requirements.txt` → Redeploy with correct files
- Python version mismatch → Check runtime is Python 3.11
- Import errors → Check code files are complete
- Port conflict → Ensure `API_PORT=8000`

**Fix:**
1. Correct the issue
2. Re-upload files or push to GitHub
3. Click **Restart** on App Service

### Frontend Shows Blank Page

**Check:**
1. Open DevTools (F12)
2. Go to **Console** tab
3. Look for JavaScript errors

**Common issues:**
- VITE_API_BASE_URL wrong → Check it matches backend URL
- API calls failing → Check backend is running
- Build missing → Ensure `dist/` folder uploaded

**Fix:**
1. Check Configuration settings
2. Verify backend URL is correct
3. Rebuild: `npm run build`
4. Re-upload files

### API Calls Fail

**Check:**
1. Frontend DevTools → Network tab
2. Look at API request details
3. Check response (should be 200, not 404/500)

**Common issues:**
- CORS blocked → Check backend CORS settings
- Wrong endpoint → Check API path in frontend
- Backend offline → Check backend running

**Fix:**
1. Go to Backend Configuration
2. Add CORS header for frontend domain
3. Click Save and Restart

### OpenAI Connection Failed

**Check:**
1. Backend logs: See specific error
2. Verify UAMI has OpenAI permissions
3. Verify endpoint URL is correct

**Fix:**
1. Go to OpenAI resource → Access Control (IAM)
2. Verify UAMI has `Cognitive Services OpenAI User` role
3. Wait a few minutes for permissions to propagate
4. Restart backend

### Storage Connection Failed

**Check:**
1. Backend logs for authentication error
2. Verify storage account name spelled correctly (enegyagentblobs)
3. Verify container exists

**Fix:**
1. Go to Storage Account → Access Control (IAM)
2. Verify UAMI has `Storage Blob Data Contributor` role
3. Verify container exists, create if needed
4. Restart backend

---

## Next Steps

1. ✅ Deploy backend code
2. ✅ Deploy frontend code
3. ✅ Configure UAMI
4. ✅ Test all connections
5. → Configure CI/CD (optional)
6. → Set up Key Vault for secrets (recommended)
7. → Create custom monitoring dashboards
8. → Document API changes

---

## Useful Commands

### Azure CLI (if preferred)

```powershell
# View deployment logs
az webapp deployment log show --name energyconsumptionreportingagent-appbe --resource-group energyconsumptionreportingagent

# Restart backend
az webapp restart --name energyconsumptionreportingagent-appbe --resource-group energyconsumptionreportingagent

# View live logs
az webapp log tail --name energyconsumptionreportingagent-appbe --resource-group energyconsumptionreportingagent

# Update configuration
az webapp config appsettings set --name energyconsumptionreportingagent-appbe --resource-group energyconsumptionreportingagent --settings API_HOST=0.0.0.0 API_PORT=8000
```

---

## Support

- **Azure Portal**: https://portal.azure.com
- **Backend URL**: https://energyconsumptionreportingagent-appbe.azurewebsites.net
- **Frontend URL**: https://energyconsumptionreportingagent-appfe.azurewebsites.net
- **Log Analytics**: Search for "Log Analytics Workspace"
- **Application Insights**: Should be linked to frontend service

---

**Status**: Ready to deploy  
**Time Estimate**: 45-60 minutes for full deployment  
**Next**: Start with Phase 1!

