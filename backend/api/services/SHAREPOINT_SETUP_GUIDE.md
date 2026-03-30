"""
SharePoint Integration Setup Guide
Complete instructions for enabling SharePoint functionality
"""

# ============================================================================
# SHAREPOINT INTEGRATION FOR ENERGY AGENT
# ============================================================================
#
# This guide explains how to add SharePoint Excel file storage alongside
# the existing Google Sheets implementation. Google Sheets functionality
# remains completely intact.
#
# ============================================================================
# TABLE OF CONTENTS
# ============================================================================
#
# 1. Prerequisites
# 2. Azure AD App Registration
# 3. Configuration
# 4. Integration Points
# 5. Testing
# 6. Troubleshooting
# 7. Credentials Checklist
#
# ============================================================================
# 1. PREREQUISITES
# ============================================================================
#
# Hardware/Software:
#   - Python 3.10+ (your existing setup)
#   - MSAL library (already in requirements.txt)
#   - Microsoft Graph API access
#
# Permissions Needed:
#   - Azure AD Tenant Administrator (to register app and grant permissions)
#   - SharePoint Site Admin (to configure site)
#   - Ability to create OAuth credentials
#
# ============================================================================
# 2. AZURE AD APP REGISTRATION
# ============================================================================
#
# STEP 1: Access Azure Portal
#   1. Go to https://portal.azure.com
#   2. Sign in with account that has Azure AD rights
#   3. Navigate to "Azure Active Directory" > "App registrations"
#   4. Click "+ New registration"
#
# STEP 2: Create Application
#   1. Name: "EnergyAgent-SharePoint" (or your preferred name)
#   2. Supported account types: Select "Accounts in this organizational directory only"
#   3. Redirect URI: (Optional for now) "http://localhost:8000/callback"
#   4. Click "Register"
#
# STEP 3: Copy Credentials
#   After registration, you will see:
#   - Application (client) ID ← SAVE THIS
#   - Directory (tenant) ID ← SAVE THIS
#   
#   Click on these to copy to clipboard
#
# STEP 4: Create Client Secret
#   1. In your app registration, go to "Certificates & secrets"
#   2. Click "+ New client secret"
#   3. Description: "Energy Agent Service Principal"
#   4. Expires: 24 months (adjust for your needs)
#   5. Click "Add"
#   6. IMPORTANT: Copy the secret VALUE immediately ← SAVE THIS
#      (You won't be able to see it again after leaving the page)
#
# STEP 5: Grant API Permissions
#   1. Go to "API permissions" in your app registration
#   2. Click "+ Add a permission"
#   3. Select "Microsoft Graph"
#   4. Select "Application permissions"
#   5. Search and add these permissions:
#      - Files.ReadWrite.All
#      - Sites.ReadWrite.All
#      - Directory.Read.All
#   6. Click "Grant admin consent for [your tenant]"
#   7. Confirm that permissions show as granted (green checkmarks)
#
# STEP 6: Verify SharePoint Configuration
#   - Go to your SharePoint site
#   - Document Library > Settings > Advanced Settings
#   - Enable "Create a document library client" if not already enabled
#   - Note down the Document Library (Drive) ID (see step below)
#
# ============================================================================
# 3. CONFIGURATION
# ============================================================================
#
# STEP 1: Set Environment Variables
#
#   Windows (Command Prompt):
#   ```
#   set SHAREPOINT_TENANT_ID=your_tenant_id_here
#   set SHAREPOINT_CLIENT_ID=your_client_id_here
#   set SHAREPOINT_CLIENT_SECRET=your_client_secret_here
#   ```
#
#   Windows (PowerShell):
#   ```
#   $env:SHAREPOINT_TENANT_ID="your_tenant_id_here"
#   $env:SHAREPOINT_CLIENT_ID="your_client_id_here"
#   $env:SHAREPOINT_CLIENT_SECRET="your_client_secret_here"
#   ```
#
#   Or add to your .env file:
#   ```
#   SHAREPOINT_TENANT_ID=your_tenant_id_here
#   SHAREPOINT_CLIENT_ID=your_client_id_here
#   SHAREPOINT_CLIENT_SECRET=your_client_secret_here
#   ```
#
# STEP 2: Update config.yaml
#
#   File: backend/energy-dashboard/config.yaml
#
#   ```yaml
#   sharepoint:
#     enabled: true  # Set to true to enable SharePoint writes
#     mode: "dual"   # Options: "google", "sharepoint", "dual"
#     
#     unified_solar:
#       site_url: "https://yourtenant.sharepoint.com/sites/YourSite"
#       drive_id: "your_drive_id"
#       file_name: unified_solar.xlsx
#     
#     # Repeat for other sheets (last_7_days, smb_status, etc.)
#   ```
#
# STEP 3: Find Your SharePoint Drive ID
#
#   Option A: Using Microsoft Graph Explorer
#     1. Go to https://developer.microsoft.com/en-us/graph/graph-explorer
#     2. Sign in with your account
#     3. Run: GET /sites/your-site-name/drive
#     4. Copy the "id" field ← This is your drive_id
#
#   Option B: Using PowerShell
#     ```powershell
#     $siteUrl = "https://yourtenant.sharepoint.com/sites/YourSite"
#     $drive = Get-PnPDrive
#     $drive.Id
#     ```
#
# ============================================================================
# 4. INTEGRATION POINTS
# ============================================================================
#
# The following files have been created/modified to support SharePoint:
#
# NEW FILES:
#   - backend/api/services/sharepoint_auth.py
#     Authentication and token management using MSAL
#
#   - backend/api/services/sharepoint_data_service.py
#     Reading Excel files from SharePoint
#
#   - backend/energy-dashboard/Ingestion-agent/sharepoint_writer.py
#     Writing Excel files to SharePoint
#
#   - backend/api/services/sharepoint_config.py
#     Configuration loader for SharePoint settings
#
#   - backend/api/services/dual_write_service.py
#     Dual-write logic (Google Sheets + SharePoint)
#
#   - backend/api/services/dual_read_service.py
#     Dual-read logic with fallback
#
#   - backend/energy-dashboard/Ingestion-agent/sharepoint_integration.py
#     Helper functions for ingestion pipeline integration
#
# MODIFIED FILES:
#   - backend/energy-dashboard/config.yaml
#     Added sharepoint section
#
#   - backend/energy-dashboard/.env.example
#     Added SharePoint credentials documentation
#
#   - backend/api/services/ingestion_bridge.py
#     Added get_sharepoint_writer() and write_to_sharepoint_once()
#
# ============================================================================
# 5. HOW TO INTEGRATE SHAREPOINT WRITES
# ============================================================================
#
# OPTION 1: Python Ingestion Scripts (e.g., exporter.py)
#
#   from sharepoint_integration import dual_write_json_to_sharepoint
#
#   # Your existing Google Sheets write...
#   data_rows = [...]
#   writer.append_data_to_sheet('unified_solar', data_rows)
#
#   # Add SharePoint write (will only run if enabled in config)
#   dual_write_json_to_sharepoint('unified_solar', data_rows)
#
# OPTION 2: API Endpoint (for manual testing)
#
#   POST /api/sharepoint/write
#   {
#       "sheet_key": "unified_solar",
#       "data": [...]
#   }
#
# OPTION 3: Dual-Write Service (for programmatic control)
#
#   from backend.api.services.dual_write_service import create_dual_write_service
#
#   service = create_dual_write_service(mode="dual")
#   result = service.write_data("unified_solar", data_rows)
#   print(f"Google Sheets: {result.google_sheets_success}")
#   print(f"SharePoint: {result.sharepoint_success}")
#
# ============================================================================
# 6. TESTING
# ============================================================================
#
# TEST 1: Verify Authentication
#
#   ```python
#   from backend.api.services.sharepoint_auth import load_auth_config_from_env
#
#   config = load_auth_config_from_env()
#   print(f"Tenant ID configured: {bool(config.tenant_id)}")
#   print(f"Client ID configured: {bool(config.client_id)}")
#   print(f"Client Secret configured: {bool(config.client_secret)}")
#   ```
#
# TEST 2: Test SharePoint Connection
#
#   ```python
#   from backend.api.services.sharepoint_data_service import get_service
#
#   service = get_service()
#   print(f"Authenticated: {service.authenticated}")
#   print(f"Last error: {service.last_error}")
#   ```
#
# TEST 3: Test Data Write
#
#   ```python
#   from backend.energy-dashboard.Ingestion_agent.sharepoint_integration import (
#       dual_write_json_to_sharepoint,
#       is_sharepoint_enabled_for_ingestion
#   )
#
#   if is_sharepoint_enabled_for_ingestion():
#       test_data = [
#           {"Date": "2026-03-30", "Time": "10:00", "Grid Units Consumed (KWh)": 100}
#       ]
#       result = dual_write_json_to_sharepoint("master_data", test_data)
#       print(f"Write successful: {result}")
#   ```
#
# ============================================================================
# 7. TROUBLESHOOTING
# ============================================================================
#
# ERROR: "Not authenticated"
#   → Check that SHAREPOINT_CLIENT_ID and SHAREPOINT_TENANT_ID are set
#   → Verify credentials in Azure Portal are correct
#   → Ensure client secret hasn't expired (check Azure Pod > Certificates & secrets)
#
# ERROR: "Could not find file"
#   → Verify drive_id is correct in config.yaml
#   → Check that SharePoint document library exists
#   → Verify file_name matches what exists in SharePoint
#
# ERROR: "Failed to download file"
#   → Verify API permissions are granted (Files.ReadWrite.All, Sites.ReadWrite.All)
#   → Ensure you have write access to the SharePoint site
#   → Check tenant/client credentials again
#
# ERROR: "Token acquisition failed"
#   → Verify SHAREPOINT_TENANT_ID is correct (not just a name, but the ID)
#   → Check that SHAREPOINT_CLIENT_SECRET hasn't expired
#   → Try regenerating the client secret in Azure Portal
#
# PERFORMANCE ISSUE: Slow writes
#   → SharePoint API throttling is normal
#   → Use "google_only" mode for faster processing, sync to SharePoint later
#   → Consider batch uploads instead of individual rows
#
# ============================================================================
# 8. CREDENTIALS CHECKLIST
# ============================================================================
#
# Required credentials (to be obtained from Azure Portal):
#
# [ ] SHAREPOINT_TENANT_ID
#     Location: Azure Portal > Azure Active Directory > Properties > Tenant ID
#     Example: "12345678-1234-1234-1234-123456789012"
#
# [ ] SHAREPOINT_CLIENT_ID
#     Location: Azure Portal > App registrations > Your App > Application ID
#     Example: "87654321-4321-4321-4321-210987654321"
#
# [ ] SHAREPOINT_CLIENT_SECRET
#     Location: Azure Portal > App registrations > Your App > Certificates & secrets
#     Example: "abc123xyz456ABC123XYZ456abc123"
#
# SharePoint Configuration:
#
# For each sheet type, you need:
#
# [ ] site_url
#     Format: "https://yourtenant.sharepoint.com/sites/SiteName"
#     Example: "https://acmecorp.sharepoint.com/sites/EnergyData"
#
# [ ] drive_id
#     Format: UUID
#     Example: "b!abc123def456-ghi789-jkl012"
#     Get via: Microsoft Graph Explorer > GET /sites/site-name/drive > id
#
# [ ] file_name
#     Format: "filename.xlsx"
#     Example: "unified_solar.xlsx"
#
# ============================================================================
# 9. ARCHITECTURE DECISIONS
# ============================================================================
#
# Mode Selection (in config.yaml):
#
# "google":
#   - Only uses Google Sheets
#   - No SharePoint access
#   - Fastest performance
#   - Use for: Testing without SharePoint
#
# "sharepoint":
#   - Only uses SharePoint
#   - No Google Sheets access
#   - Requires full SharePoint setup
#   - Use for: Pure SharePoint deployment
#
# "dual":
#   - Writes to BOTH Google Sheets and SharePoint
#   - Reads from SharePoint with fallback to Google
#   - Recommended for migration period
#   - Use for: Gradual transition to SharePoint
#
# ============================================================================
# 10. NEXT STEPS
# ============================================================================
#
# 1. Register Azure AD App (follow section 2 above)
# 2. Collect credentials (section 8 checklist)
# 3. Update .env file with credentials
# 4. Update config.yaml with SharePoint URLs
# 5. Set sharepoint.enabled: true in config.yaml
# 6. Restart backend
# 7. Run test (section 6)
# 8. Verify writes appear in SharePoint
# 9. Monitor logs for any issues
#
# ============================================================================
