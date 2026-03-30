# SharePoint Credentials Template

This file shows exactly what credentials you need to collect from Azure AD and where to put them.

## 📋 Azure AD Credentials (Collect from Azure Portal)

Get these from: https://portal.azure.com

### 1. SHAREPOINT_TENANT_ID
- **Location:** Azure Active Directory → Properties → Tenant ID
- **Format:** UUID (e.g., `12345678-1234-1234-1234-123456789012`)
- **Copy Value:** _____________________________________

### 2. SHAREPOINT_CLIENT_ID
- **Location:** App registrations → [Your App] → Application ID
- **Format:** UUID (e.g., `87654321-4321-4321-4321-210987654321`)
- **Copy Value:** _____________________________________

### 3. SHAREPOINT_CLIENT_SECRET
- **Location:** App registrations → [Your App] → Certificates & secrets → New client secret
- **Format:** String (sensitive - keep secure!)
- **Note:** You can only see this value once after creation!
- **Copy Value:** _____________________________________

---

## 📍 SharePoint Site Information (Collect from SharePoint)

For each data collection type, you need:

### UNIFIED_SOLAR Sheet
**Site URL:**
- Format: `https://yourtenant.sharepoint.com/sites/SiteName`
- Get from: SharePoint site browser URL
- Example: `https://acmecorp.sharepoint.com/sites/EnergyData`
- **Value:** _____________________________________

**Drive ID:**
- Format: UUID starting with `b!`
- Get via: Microsoft Graph Explorer → GET /sites/{site-name}/drive → copy "id"
- Example: `b!abc123def456-ghi789-jkl012`
- **Value:** _____________________________________

---

### LAST_7_DAYS Sheet
**Site URL:** _____________________________________
**Drive ID:** _____________________________________

---

### SMB_STATUS Sheet
**Site URL:** _____________________________________
**Drive ID:** _____________________________________

---

### GRID_AND_DIESEL Sheet
**Site URL:** _____________________________________
**Drive ID:** _____________________________________

---

### MASTER_DATA Sheet
**Site URL:** _____________________________________
**Drive ID:** _____________________________________

---

## 🔧 Configuration Steps

### Step 1: Create/Update .env file

```bash
# backend/energy-dashboard/.env

# EXISTING CREDENTIALS (keep unchanged)
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=sender@company.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=sender@company.com

# NEW: SharePoint Credentials
SHAREPOINT_TENANT_ID=[VALUE FROM STEP 1 ABOVE]
SHAREPOINT_CLIENT_ID=[VALUE FROM STEP 2 ABOVE]
SHAREPOINT_CLIENT_SECRET=[VALUE FROM STEP 3 ABOVE]
```

### Step 2: Update config.yaml

File: `backend/energy-dashboard/config.yaml`

```yaml
sharepoint:
  enabled: true                    # ← Change from false to true
  mode: "dual"                     # Options: "google", "sharepoint", "dual"
  
  unified_solar:
    site_url: "[SITE_URL FROM ABOVE]"
    drive_id: "[DRIVE_ID FROM ABOVE]"
    file_name: unified_solar.xlsx
  
  last_7_days:
    site_url: "[SITE_URL FROM ABOVE]"
    drive_id: "[DRIVE_ID FROM ABOVE]"
    file_name: last_7_days.xlsx
  
  smb_status:
    site_url: "[SITE_URL FROM ABOVE]"
    drive_id: "[DRIVE_ID FROM ABOVE]"
    file_name: smb_status.xlsx
  
  grid_and_diesel:
    site_url: "[SITE_URL FROM ABOVE]"
    drive_id: "[DRIVE_ID FROM ABOVE]"
    file_name: grid_and_diesel.xlsx
  
  master_data:
    site_url: "[SITE_URL FROM ABOVE]"
    drive_id: "[DRIVE_ID FROM ABOVE]"
    file_name: master_data.xlsx
```

---

## ✅ Verification Checklist

After setting up credentials:

- [ ] .env file has SHAREPOINT_TENANT_ID set
- [ ] .env file has SHAREPOINT_CLIENT_ID set
- [ ] .env file has SHAREPOINT_CLIENT_SECRET set
- [ ] config.yaml has sharepoint.enabled: true
- [ ] config.yaml has site_url for each sheet
- [ ] config.yaml has drive_id for each sheet
- [ ] Backend is restarted after changes
- [ ] Python can import sharepoint modules without error

---

## 🧪 Quick Test Script

Run this after setup to verify everything works:

```python
#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent / "backend" / "api"))

print("=" * 60)
print("SharePoint Integration Verification")
print("=" * 60)

# Check environment variables
print("\n1. Environment Variables:")
print(f"   SHAREPOINT_TENANT_ID: {bool(os.getenv('SHAREPOINT_TENANT_ID'))}")
print(f"   SHAREPOINT_CLIENT_ID: {bool(os.getenv('SHAREPOINT_CLIENT_ID'))}")
print(f"   SHAREPOINT_CLIENT_SECRET: {bool(os.getenv('SHAREPOINT_CLIENT_SECRET'))}")

# Check imports
print("\n2. Checking Imports:")
try:
    from services.sharepoint_auth import load_auth_config_from_env
    print("   ✓ sharepoint_auth imported")
except Exception as e:
    print(f"   ✗ Error importing sharepoint_auth: {e}")
    sys.exit(1)

try:
    from services.sharepoint_config import is_sharepoint_enabled
    print("   ✓ sharepoint_config imported")
except Exception as e:
    print(f"   ✗ Error importing sharepoint_config: {e}")
    sys.exit(1)

# Check configuration
print("\n3. Configuration:")
try:
    enabled = is_sharepoint_enabled()
    print(f"   SharePoint enabled: {enabled}")
    if not enabled:
        print("   ⚠ Set sharepoint.enabled: true in config.yaml")
except Exception as e:
    print(f"   ✗ Error checking config: {e}")

# Check authentication
print("\n4. Authentication:")
try:
    config = load_auth_config_from_env()
    print(f"   Tenant ID configured: {bool(config.tenant_id)}")
    print(f"   Client ID configured: {bool(config.client_id)}")
    print(f"   Client Secret configured: {bool(config.client_secret)}")
    
    if config.is_configured():
        print("   ✓ Credentials are configured")
        
        # Try to get token
        from services.sharepoint_auth import SharePointAuthManager
        auth = SharePointAuthManager(config)
        token = auth.get_access_token()
        if token:
            print("   ✓ Successfully acquired access token")
        else:
            print("   ✗ Failed to acquire access token")
            print(f"   Error: {auth.auth}")
    else:
        print("   ✗ Credentials not fully configured")
except Exception as e:
    print(f"   ✗ Error during authentication: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Verification Complete")
print("=" * 60)
```

Save as `verify_sharepoint.py` and run:
```bash
python verify_sharepoint.py
```

---

## 🆘 Troubleshooting

**Q: "Token acquisition failed"**
A: Check that:
- SHAREPOINT_TENANT_ID is the actual Tenant ID (not name)
- SHAREPOINT_CLIENT_ID is the Application ID (not display name)
- SHAREPOINT_CLIENT_SECRET hasn't expired
- API permissions are granted in Azure Portal

**Q: "Could not find file"**
A: Check that:
- drive_id is correct (try Graph Explorer)
- file_name matches Excel files in SharePoint
- site_url is the correct SharePoint site

**Q: "Not authenticated"**
A: Check that:
- All three credentials are set in .env
- .env file is loaded (check app startup logs)
- Environment variables are passed to backend process

---

## 📞 References

- **Setup Guide:** backend/api/services/SHAREPOINT_SETUP_GUIDE.md
- **Developer Guide:** backend/api/services/SHAREPOINT_DEVELOPER_GUIDE.md
- **Implementation Summary:** backend/api/services/IMPLEMENTATION_SUMMARY.md
- **Checklist:** SHAREPOINT_IMPLEMENTATION_CHECKLIST.md (root)

---

## 🔒 Security Notes

**NEVER:**
- Commit .env file to git
- Log SHAREPOINT_CLIENT_SECRET
- Share credentials via email
- Store secrets in plain text files

**ALWAYS:**
- Keep .env file in .gitignore
- Use environment variables in production
- Rotate secrets periodically
- Grant minimal required permissions in Azure AD

---
