# SharePoint Integration - Implementation Checklist

## ✅ COMPLETED: Code Implementation

### Core Services
- [x] **sharepoint_auth.py** - MSAL authentication with Azure AD
  - Service Principal (Client Credentials) flow
  - Token acquisition and refresh
  - Bearer token generation for Graph API

- [x] **sharepoint_data_service.py** - Read Excel files from SharePoint
  - File discovery via Graph API
  - Excel content fetching
  - Date range filtering
  - Latest rows functionality

- [x] **sharepoint_writer.py** - Write Excel files to SharePoint
  - Automatic file creation
  - Append rows to sheets
  - Update last row functionality
  - Error handling and logging

### Integration Services
- [x] **sharepoint_config.py** - Configuration management
  - YAML-based settings
  - Environment variable overrides
  - Per-sheet configuration

- [x] **dual_write_service.py** - Simultaneous Google + SharePoint writes
  - Coordinated writes to both destinations
  - Fallback strategy (fail-open)
  - Result tracking

- [x] **dual_read_service.py** - Intelligent read with fallback
  - Try SharePoint first, fallback to Google
  - Configurable mode selection
  - Status and health checks

### Bridge & Orchestration
- [x] **ingestion_bridge.py** - Updated with SharePoint support
  - get_sharepoint_writer() function
  - write_to_sharepoint_once() function

- [x] **sharepoint_integration.py** - Ingestion pipeline helpers
  - dual_write_json_to_sharepoint() - Easy integration
  - dual_write_excel_to_sharepoint() - Bulk uploads
  - Configuration checks

### Configuration
- [x] **config.yaml** - Added sharepoint section with placeholders
  - enabled: false (to be changed after setup)
  - mode: "dual" (configurable)
  - Per-sheet site_url, drive_id, file_name

- [x] **.env.example** - Added credentials documentation
  - SHAREPOINT_TENANT_ID placeholder
  - SHAREPOINT_CLIENT_ID placeholder
  - SHAREPOINT_CLIENT_SECRET placeholder

### Documentation
- [x] **SHAREPOINT_SETUP_GUIDE.md** - Complete setup instructions
  - Azure AD app registration steps
  - Environment configuration
  - Testing procedures
  - Troubleshooting guide

- [x] **SHAREPOINT_DEVELOPER_GUIDE.md** - Developer quick reference
  - Code examples for all scenarios
  - Configuration structure
  - Performance notes
  - Migration path

- [x] **IMPLEMENTATION_SUMMARY.md** - Overview of implementation
  - What was built
  - Architecture overview
  - Quick start guide
  - Next steps

---

## 📋 TODO: When Credentials Are Provided

### Phase 1: Azure AD & Credentials (15 minutes - Done by Admin/DevOps)

- [ ] Register application in Azure AD
- [ ] Create Client Secret
- [ ] Grant required API permissions:
  - [ ] Files.ReadWrite.All
  - [ ] Sites.ReadWrite.All
  - [ ] Directory.Read.All (optional)
- [ ] Document:
  - [ ] SHAREPOINT_TENANT_ID
  - [ ] SHAREPOINT_CLIENT_ID
  - [ ] SHAREPOINT_CLIENT_SECRET

### Phase 2: Environment Setup (5 minutes - Dev Engineer)

- [ ] Create/update .env file with credentials:
  ```
  SHAREPOINT_TENANT_ID=<value>
  SHAREPOINT_CLIENT_ID=<value>
  SHAREPOINT_CLIENT_SECRET=<value>
  ```
- [ ] Verify environment variables are loaded
- [ ] Test Python script to verify auth works

### Phase 3: SharePoint Configuration (10 minutes - Dev Engineer)

- [ ] Create/identify SharePoint site
- [ ] Get SharePoint Site URL for each data collection:
  - [ ] unified_solar
  - [ ] last_7_days
  - [ ] smb_status
  - [ ] grid_and_diesel
  - [ ] master_data

- [ ] Get Drive ID using Microsoft Graph Explorer or PowerShell:
  - [ ] For each site, run: `GET /sites/{site-name}/drive`
  - [ ] Copy the "id" field

- [ ] Update **config.yaml** for each sheet:
  ```yaml
  sharepoint:
    enabled: true  # ← Change from false to true
    mode: "dual"   # Keep as is for parallel operation
    
    unified_solar:
      site_url: "https://yourtenant.sharepoint.com/sites/YourSite"
      drive_id: "b!abc123..."
      file_name: unified_solar.xlsx
    # Repeat for other sheets
  ```

### Phase 4: Integration Testing (10 minutes - Dev Engineer)

- [ ] Restart backend service
- [ ] Test authentication:
  ```python
  from backend.api.services.sharepoint_data_service import get_service
  service = get_service()
  print(f"Authenticated: {service.authenticated}")
  ```

- [ ] Test read from SharePoint:
  ```python
  from backend.api.services.dual_read_service import get_dual_read_service
  service = get_dual_read_service()
  df = service.get_sheet_data("unified_solar")
  print(f"Rows: {len(df)}")
  ```

- [ ] Test write to SharePoint:
  ```python
  from backend.energy_dashboard.Ingestion_agent.sharepoint_integration import dual_write_json_to_sharepoint
  data = [{"Date": "2026-03-30", "Grid Units Consumed (KWh)": 100}]
  result = dual_write_json_to_sharepoint("master_data", data)
  print(f"Success: {result}")
  ```

### Phase 5: Ingestion Pipeline Integration (30 minutes - Backend Dev)

**Option A: Simple Integration (Recommended for Start)**

Edit your ingestion scripts (e.g., `exporter.py`, `google_sheets_writer.py`):

```python
# Add import
from sharepoint_integration import dual_write_json_to_sharepoint

# After your existing Google Sheets write, add:
writer.append_data_to_sheet('unified_solar', data_rows)  # Google write

# Add SharePoint write (will skip if not enabled)
dual_write_json_to_sharepoint('unified_solar', data_rows)
```

**Option B: Advanced Integration (Optional Later)**

Use DualWriteService in your code for more control:

```python
from backend.api.services.dual_write_service import create_dual_write_service

service = create_dual_write_service(mode="dual")
result = service.write_data("unified_solar", data_rows)
if not result.sharepoint_success:
    logger.warning(f"SharePoint write failed: {result.sharepoint_error}")
```

- [ ] Restart ingestion pipeline
- [ ] Monitor logs for SharePoint writes
- [ ] Verify data appears in SharePoint Excel files
- [ ] Check for any API throttling warnings

### Phase 6: Monitoring & Validation (10 minutes - QA)

- [ ] Verify data syncs between Google Sheets and SharePoint
- [ ] Check that read operations prefer SharePoint data
- [ ] Confirm fallback works when SharePoint unavailable
- [ ] Monitor API usage for throttling issues

---

## 📁 File Reference Guide

### Core Implementation
- `backend/api/services/sharepoint_auth.py` - MSAL authentication
- `backend/api/services/sharepoint_data_service.py` - Read from SharePoint
- `backend/energy-dashboard/Ingestion-agent/sharepoint_writer.py` - Write to SharePoint

### Configuration
- `backend/energy-dashboard/config.yaml` - Main configuration
- `backend/energy-dashboard/.env.example` - Credentials template

### Utilities
- `backend/api/services/sharepoint_config.py` - Config loader
- `backend/api/services/dual_write_service.py` - Dual-write logic
- `backend/api/services/dual_read_service.py` - Dual-read logic
- `backend/api/services/ingestion_bridge.py` - Bridge functions
- `backend/energy-dashboard/Ingestion-agent/sharepoint_integration.py` - Helpers

### Documentation
- `backend/api/services/SHAREPOINT_SETUP_GUIDE.md` - Setup instructions
- `backend/api/services/SHAREPOINT_DEVELOPER_GUIDE.md` - Developer guide
- `backend/api/services/IMPLEMENTATION_SUMMARY.md` - Overview

---

## 🔑 Key Features Ready to Use

### 1. Dual-Write (Google + SharePoint)
```python
from backend.api.services.dual_write_service import create_dual_write_service

service = create_dual_write_service(mode="dual")
result = service.write_data("unified_solar", data)
```

### 2. Dual-Read (SharePoint → Google Fallback)
```python
from backend.api.services.dual_read_service import get_dual_read_service

service = get_dual_read_service()
df = service.get_sheet_data("unified_solar")  # Auto-fallback
```

### 3. Simple Integration Helper
```python
from backend.energy-dashboard.Ingestion-agent.sharepoint_integration import dual_write_json_to_sharepoint

# Writes to SharePoint if enabled, skips silently if not
dual_write_json_to_sharepoint('unified_solar', data_rows)
```

---

## 🎯 Configuration Modes

**mode: "google"** - Google Sheets only (fastest)
**mode: "sharepoint"** - SharePoint only
**mode: "dual"** - Both systems (recommended for migration)

---

## ✨ Highlights

✅ **No changes to Google Sheets** - Completely backward compatible
✅ **Credentials placeholder** - Ready to accept credentials immediately
✅ **Dual-write capability** - Write to both simultaneously
✅ **Smart fallback** - Reads from SharePoint, falls back to Google
✅ **Configuration-driven** - Enable/disable via config.yaml
✅ **Easy integration** - Single function call wrapper available
✅ **Well documented** - Complete guides for setup and development
✅ **Error handling** - Proper logging and status reporting

---

## 📞 Next Steps

1. **Get Credentials** from Azure AD (section "Phase 1" above)
2. **Set Environment Variables** (section "Phase 2")
3. **Update config.yaml** (section "Phase 3")
4. **Test Connection** (section "Phase 4")
5. **Integrate into Pipeline** (section "Phase 5")
6. **Monitor & Validate** (section "Phase 6")

---

## 📞 Support

For questions or issues:
- Review **SHAREPOINT_SETUP_GUIDE.md** for detailed instructions
- Check **SHAREPOINT_DEVELOPER_GUIDE.md** for code examples
- See **IMPLEMENTATION_SUMMARY.md** for architecture overview
