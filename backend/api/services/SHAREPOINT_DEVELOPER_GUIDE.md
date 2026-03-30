"""
SharePoint Integration - Developer Quick Reference
Quick guide for developers implementing SharePoint functionality
"""

# ==============================================================================
# QUICK REFERENCE: Adding SharePoint to Your Code
# ==============================================================================
#
# SCENARIO 1: Read data from SharePoint (with Google fallback)
# ==============================================================================
#
#   from backend.api.services.dual_read_service import get_dual_read_service
#
#   service = get_dual_read_service()
#   
#   # Automatically tries SharePoint first, falls back to Google
#   df = service.get_sheet_data("unified_solar")
#   
#   # Force specific source
#   df_sp = service.get_sheet_data("unified_solar", source="sharepoint")
#   df_gs = service.get_sheet_data("unified_solar", source="google")
#   
#   # Get with date filter
#   df = service.get_by_date_range(
#       "unified_solar",
#       start_date="2026-03-01",
#       end_date="2026-03-30"
#   )
#
#
# SCENARIO 2: Write data to both Google Sheets and SharePoint
# ==============================================================================
#
#   from backend.api.services.dual_write_service import create_dual_write_service
#
#   # Create service (will auto-initialize both writers)
#   service = create_dual_write_service(mode="dual")
#   
#   # Write data
#   data = [
#       {"Date": "2026-03-30", "Time": "10:00", "Grid Units Consumed (KWh)": 100},
#       {"Date": "2026-03-30", "Time": "11:00", "Grid Units Consumed (KWh)": 110},
#   ]
#   
#   result = service.write_data("unified_solar", data)
#   
#   print(f"Google Sheets: {result.google_sheets_success}")
#   print(f"SharePoint: {result.sharepoint_success}")
#   print(f"Rows written: {result.rows_written}")
#
#
# SCENARIO 3: Write only to SharePoint (in ingestion scripts)
# ==============================================================================
#
#   from sharepoint_integration import dual_write_json_to_sharepoint
#
#   # After your Google Sheets write...
#   data_rows = [...]
#   writer.append_data_to_sheet('unified_solar', data_rows)  # Google write
#   
#   # Add SharePoint (will only run if enabled in config.yaml)
#   dual_write_json_to_sharepoint('unified_solar', data_rows)  # SharePoint write
#
#
# SCENARIO 4: Direct SharePoint service (advanced)
# ==============================================================================
#
#   from backend.api.services.sharepoint_data_service import get_service
#   
#   service = get_service()
#   
#   # Check authentication
#   if not service.authenticated:
#       print(f"Auth failed: {service.get_last_error()}")
#   
#   # Read data
#   df = service.fetch_sheet_data("unified_solar")
#   df = service.get_latest_rows("unified_solar", limit=10)
#   df = service.get_data_by_date_range("unified_solar", "2026-03-01", "2026-03-30")
#
#
# SCENARIO 5: Direct SharePoint writer (advanced)
# ==============================================================================
#
#   from backend.energy_dashboard.Ingestion_agent.sharepoint_writer import (
#       SharePointExcelWriter,
#       get_sharepoint_writer
#   )
#   
#   writer = get_sharepoint_writer()
#   
#   # Append rows
#   data = [...]
#   success = writer.append_data_to_sheet("unified_solar", data)
#   
#   # Update last row
#   last_row_update = {"Grid Units Consumed (KWh)": 150}
#   success = writer.update_last_row("unified_solar", last_row_update)
#
#
# ENVIRONMENT VARIABLES
# ==============================================================================
#
#   SHAREPOINT_TENANT_ID          # Azure AD Tenant ID
#   SHAREPOINT_CLIENT_ID          # Application Client ID
#   SHAREPOINT_CLIENT_SECRET      # Client Secret (for auth)
#   SHAREPOINT_APP_ID_URI         # App ID URI (default: https://graph.microsoft.com/.default)
#
#   Optional per-sheet overrides:
#   SHAREPOINT_UNIFIED_SOLAR_SITE_URL    # Override site_url from config.yaml
#   SHAREPOINT_UNIFIED_SOLAR_DRIVE_ID    # Override drive_id from config.yaml
#
#
# CONFIG.YAML STRUCTURE
# ==============================================================================
#
#   sharepoint:
#     enabled: false              # Set to true to enable SharePoint
#     mode: "dual"                # "google", "sharepoint", or "dual"
#     
#     unified_solar:
#       site_url: ""              # e.g., https://tenant.sharepoint.com/sites/Data
#       drive_id: ""              # SharePoint document library ID
#       file_name: "unified_solar.xlsx"
#     
#     last_7_days:
#       site_url: ""
#       drive_id: ""
#       file_name: "last_7_days.xlsx"
#     
#     smb_status:
#       site_url: ""
#       drive_id: ""
#       file_name: "smb_status.xlsx"
#     
#     grid_and_diesel:
#       site_url: ""
#       drive_id: ""
#       file_name: "grid_and_diesel.xlsx"
#     
#     master_data:
#       site_url: ""
#       drive_id: ""
#       file_name: "master_data.xlsx"
#
#
# DUAL-WRITE MODES EXPLAINED
# ==============================================================================
#
#   mode: "google"
#     ✓ Google Sheets only
#     ✗ No SharePoint access
#     • Speed: Fastest
#     • Use case: Testing, Google-only deployment
#
#   mode: "sharepoint"
#     ✗ No Google Sheets access
#     ✓ SharePoint only
#     • Speed: Medium (depends on SharePoint API)
#     • Use case: SharePoint-only deployment
#
#   mode: "dual"
#     ✓ Google Sheets writes: Yes
#     ✓ SharePoint writes: Yes
#     ✓ Read tries SharePoint first, falls back to Google
#     • Speed: Slower (both API calls)
#     • Use case: Migration period, dual storage
#
#
# ERROR HANDLING
# ==============================================================================
#
#   from backend.api.services.dual_read_service import get_dual_read_service
#   
#   service = get_dual_read_service()
#   df = service.get_sheet_data("unified_solar")
#   
#   if df is None:
#       status = service.get_status()
#       print(f"Google Sheets: {status['google_sheets']}")
#       print(f"SharePoint: {status['sharepoint']}")
#       # Handle error...
#
#   # Or check individual status
#   sp_status = status.get('sharepoint', {})
#   if not sp_status.get('authenticated'):
#       print("SharePoint not authenticated")
#       print(f"Error: {sp_status.get('error')}")
#
#
# TESTING SHAREPOINT CONNECTION
# ==============================================================================
#
#   import os
#   from backend.api.services.sharepoint_data_service import get_service as get_sp_service
#   from backend.api.services.sharepoint_config import is_sharepoint_enabled
#
#   # Check environment
#   print(f"SHAREPOINT_TENANT_ID: {bool(os.getenv('SHAREPOINT_TENANT_ID'))}")
#   print(f"SHAREPOINT_CLIENT_ID: {bool(os.getenv('SHAREPOINT_CLIENT_ID'))}")
#   print(f"SHAREPOINT_CLIENT_SECRET: {bool(os.getenv('SHAREPOINT_CLIENT_SECRET'))}")
#
#   # Check config
#   print(f"SharePoint enabled: {is_sharepoint_enabled()}")
#
#   # Check authentication
#   service = get_sp_service()
#   print(f"Authenticated: {service.authenticated}")
#   if not service.authenticated:
#       print(f"Error: {service.get_last_error()}")
#
#
# DEBUGGING TIPS
# ==============================================================================
#
#   1. Check logs
#      - Look for "SharePoint" messages in backend logs
#      - Check sharepoint_auth.py logs for token issues
#      - Check sharepoint_data_service.py for API errors
#
#   2. Verify credentials
#      - Print environment variables (but never log secrets!)
#      - Test Azure AD token acquisition separately
#      - Verify permissions in Azure Portal
#
#   3. Check SharePoint configuration
#      - Verify site_url exists and is accessible
#      - Verify drive_id is correct (use Graph Explorer to get it)
#      - Verify file_name matches Excel files in SharePoint
#
#   4. Test incrementally
#      - First test: Can we authenticate?
#      - Second test: Can we list files in SharePoint?
#      - Third test: Can we download a file?
#      - Fourth test: Can we upload a test file?
#
#
# MIGRATION PATH FROM GOOGLE TO SHAREPOINT
# ==============================================================================
#
#   Phase 1: Parallel Setup (mode: "dual")
#     ✓ Google Sheets continues working
#     ✓ New data goes to both Google and SharePoint
#     ✓ Reads prefer SharePoint, fallback to Google
#     • Gradually migrate users to SharePoint
#
#   Phase 2: SharePoint Primary (mode: "dual")
#     ✓ Both systems updated simultaneously
#     • All new analytics use SharePoint
#     • Google Sheets maintained as backup
#
#   Phase 3: Google Sunset (mode: "sharepoint")
#     ✓ SharePoint is only storage
#     ✓ Decommission Google Sheets
#     • Performance improvement
#
#
# PERFORMANCE CONSIDERATIONS
# ==============================================================================
#
#   Scenario: Dual-write (mode: "dual")
#     - Google Sheets write: ~100-500ms
#     - SharePoint write: ~500-2000ms (API throttling may apply)
#     - Total: ~700-2500ms per write cycle
#     - Solution: Make writes async or run in background jobs
#
#   Scenario: Dual-read (mode: "dual")
#     - Try SharePoint first: ~500-2000ms
#     - If fails, fallback to Google: ~100-500ms
#     - Total: ~100-2000ms depending on source
#     - Solution: Implement caching for frequently accessed data
#
#   Recommendations:
#     - For real-time dashboards: Use Google Sheets or implement caching
#     - For batch reports: Use mode: "sharepoint" for better structure
#     - For hybrid: Cache SharePoint reads, use Google for fallback
#
#
# KNOWN LIMITATIONS
# ==============================================================================
#
#   1. Authentication
#      - Only supports Service Principal (no interactive login in headless mode)
#      - Credentials must be set before app starts
#      - Token refresh is automatic
#
#   2. File Operations
#      - Only supports Excel files (.xlsx)
#      - File must already exist or will be created
#      - No support for advanced Excel features (formulas, pivot tables)
#
#   3. API Limits
#      - SharePoint API has throttling
#      - Large bulk writes may hit limits
#      - Implement retry logic for production
#
#   4. Data Types
#      - Google Sheets is loosely typed
#      - SharePoint/Excel enforces types
#      - May need data validation layer
#
#\n# ==============================================================================
