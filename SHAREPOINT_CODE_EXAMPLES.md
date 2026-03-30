"""
Common Integration Scenarios - Copy & Paste Ready Code
Actual code examples you can use in your projects
"""

# ==============================================================================
# SCENARIO 1: Add SharePoint Write to Ingestion Script
# ==============================================================================
# Location: backend/energy-dashboard/Ingestion-agent/exporter.py (or similar)
# Time to integrate: 5 minutes

"""
# ADD THIS AT THE TOP OF THE FILE:
from sharepoint_integration import dual_write_json_to_sharepoint
import logging

logger = logging.getLogger(__name__)

# THEN, IN YOUR MAIN EXPORT FUNCTION:
def export_data():
    # ... your existing code ...
    
    data_rows = [
        {"Date": "2026-03-30", "Time": "10:00", "Grid Units Consumed (KWh)": 100},
        {"Date": "2026-03-30", "Time": "11:00", "Grid Units Consumed (KWh)": 110},
    ]
    
    # Your EXISTING Google Sheets write:
    writer = GoogleSheetsWriter(credentials_path)
    success = writer.append_data_to_sheet('unified_solar', data_rows)
    logger.info(f"Google Sheets write: {success}")
    
    # ADD THIS: SharePoint write (will skip if not enabled)
    sharepoint_success = dual_write_json_to_sharepoint('unified_solar', data_rows)
    logger.info(f"SharePoint write: {sharepoint_success}")
    
    return success and sharepoint_success
"""

# ==============================================================================
# SCENARIO 2: Read Data with Fallback Logic
# ==============================================================================
# Location: backend/api/routers/data.py (or any read endpoint)
# Time to integrate: 10 minutes

"""
from backend.api.services.dual_read_service import get_dual_read_service

@router.get("/api/data/unified-solar")
async def get_unified_solar_data(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    source: Optional[str] = None,  # Optional: "google", "sharepoint", None=auto
):
    '''Get unified solar data with intelligent fallback'''
    
    service = get_dual_read_service()
    
    # Get data (auto-fallback from SharePoint to Google)
    df = service.get_by_date_range(
        sheet_key="unified_solar",
        start_date=start_date,
        end_date=end_date,
        source=source  # None = auto-fallback
    )
    
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="No data available")
    
    # Convert to response format
    data = df.to_dict('records')
    
    # Get source info (for debugging)
    status = service.get_status()
    
    return {
        "data": data,
        "rows": len(data),
        "source_info": status
    }
"""

# ==============================================================================
# SCENARIO 3: Dual-Write with Status Tracking
# ==============================================================================
# Location: backend/api/routers/admin.py (or admin endpoint)
# Time to integrate: 15 minutes

"""
from backend.api.services.dual_write_service import create_dual_write_service
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.post("/api/admin/sync-to-sharepoint")
async def sync_data_to_sharepoint(
    sheet_key: str,  # e.g., "unified_solar"
    data: List[Dict[str, Any]]
):
    '''Manually sync data to both Google Sheets and SharePoint'''
    
    if not data:
        raise HTTPException(status_code=400, detail="Empty data")
    
    # Create service with dual-write mode
    service = create_dual_write_service(mode="dual")
    
    # Write data
    result = service.write_data(sheet_key, data)
    
    # Build response
    return {
        "summary": {
            "total_rows": len(data),
            "dual_write_mode": service.mode,
        },
        "google_sheets": {
            "success": result.google_sheets_success,
            "error": result.google_sheets_error,
        },
        "sharepoint": {
            "success": result.sharepoint_success,
            "error": result.sharepoint_error,
        },
        "overall_success": result.google_sheets_success and result.sharepoint_success,
    }

@router.get("/api/admin/data-source-status")
async def get_data_source_status():
    '''Check health of both data sources'''
    
    service = create_dual_write_service(mode="dual")
    status = service.get_status()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "google_sheets": status["google_sheets"],
        "sharepoint": status["sharepoint"],
        "mode": status["mode"],
    }
"""

# ==============================================================================
# SCENARIO 4: Check Configuration & Credentials
# ==============================================================================
# Location: Any script, CLI tool, or startup verification
# Time to integrate: 5 minutes

"""
import os
import sys
from pathlib import Path

def verify_sharepoint_setup():
    '''Verify SharePoint is properly configured and authenticated'''
    
    print("Verifying SharePoint Setup...")
    print("-" * 50)
    
    # 1. Check environment variables
    print("\n1. Environment Variables:")
    tenant_id = os.getenv("SHAREPOINT_TENANT_ID")
    client_id = os.getenv("SHAREPOINT_CLIENT_ID")
    client_secret = os.getenv("SHAREPOINT_CLIENT_SECRET")
    
    print(f"   TENANT_ID: {'✓' if tenant_id else '✗'}")
    print(f"   CLIENT_ID: {'✓' if client_id else '✗'}")
    print(f"   CLIENT_SECRET: {'✓' if client_secret else '✗'}")
    
    if not (tenant_id and client_id and client_secret):
        print("\n   ⚠ Missing credentials. Set them in .env file")
        return False
    
    # 2. Check imports
    print("\n2. Imports:")
    try:
        from backend.api.services.sharepoint_auth import SharePointAuthManager, load_auth_config_from_env
        from backend.api.services.sharepoint_config import is_sharepoint_enabled
        print("   ✓ All imports successful")
    except Exception as e:
        print(f"   ✗ Import error: {e}")
        return False
    
    # 3. Check configuration
    print("\n3. Configuration:")
    enabled = is_sharepoint_enabled()
    print(f"   Enabled in config.yaml: {'✓' if enabled else '✗ (set enabled: true)'}")
    
    # 4. Test authentication
    print("\n4. Authentication:")
    try:
        config = load_auth_config_from_env()
        auth = SharePointAuthManager(config)
        token = auth.get_access_token()
        
        if token:
            print("   ✓ Successfully acquired access token")
            print(f"   Token length: {len(token)} characters")
            print("   ✓ Ready to use SharePoint!")
            return True
        else:
            print("   ✗ Failed to acquire access token")
            return False
    except Exception as e:
        print(f"   ✗ Auth error: {e}")
        return False

if __name__ == "__main__":
    success = verify_sharepoint_setup()
    sys.exit(0 if success else 1)
"""

# ==============================================================================
# SCENARIO 5: Background Task for Periodic SharePoint Sync
# ==============================================================================
# Location: backend/api/services/scheduler.py (or celery tasks)
# Time to integrate: 20 minutes

"""
from backend.api.services.dual_write_service import create_dual_write_service
import schedule
import time

def sync_to_sharepoint_task():
    '''Background task to sync data to SharePoint periodically'''
    
    logger.info("Starting SharePoint sync task")
    
    try:
        # Create dual-write service
        service = create_dual_write_service(mode="dual", fail_open=True)
        
        # Get data from your data source
        from backend.api.services.data_service import get_latest_data
        
        sheet_types = ['unified_solar', 'last_7_days', 'smb_status', 'grid_and_diesel', 'master_data']
        
        for sheet_key in sheet_types:
            try:
                data = get_latest_data(sheet_key)
                if data:
                    result = service.write_data(sheet_key, data)
                    logger.info(f"{sheet_key}: GS={result.google_sheets_success}, SP={result.sharepoint_success}")
            except Exception as e:
                logger.error(f"Error syncing {sheet_key}: {e}")
        
        logger.info("SharePoint sync task completed")
        
    except Exception as e:
        logger.error(f"SharePoint sync task failed: {e}")

# Schedule the task (using schedule library)
schedule.every(1).hour.do(sync_to_sharepoint_task)

# Run scheduler in background
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

# Or use APScheduler:
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(
    func=sync_to_sharepoint_task,
    trigger="interval",
    hours=1,
    id="sharepoint_sync",
    name="Periodic SharePoint Sync"
)
scheduler.start()
"""

# ==============================================================================
# SCENARIO 6: API Endpoint for Manual Data Upload
# ==============================================================================
# Location: backend/api/routers/admin.py (or data management endpoint)
# Time to integrate: 15 minutes

"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.api.services.dual_write_service import create_dual_write_service
import pandas as pd
import io

router = APIRouter()

@router.post("/api/admin/upload-excel-to-sharepoint")
async def upload_excel_to_sharepoint(
    sheet_key: str,  # e.g., "unified_solar"
    file: UploadFile = File(...),
):
    '''Upload Excel file data to both Google Sheets and SharePoint'''
    
    try:
        # Validate file
        if not file.filename.endswith('.xlsx'):
            raise HTTPException(status_code=400, detail="Only .xlsx files supported")
        
        # Read Excel file
        content = await file.read()
        df = pd.read_excel(io.BytesIO(content))
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Excel file is empty")
        
        # Convert to list of dictionaries
        data = df.to_dict('records')
        
        # Write to both sources
        service = create_dual_write_service(mode="dual")
        result = service.write_data(sheet_key, data)
        
        return {
            "file_name": file.filename,
            "rows_uploaded": len(data),
            "google_sheets": {
                "success": result.google_sheets_success,
                "error": result.google_sheets_error,
            },
            "sharepoint": {
                "success": result.sharepoint_success,
                "error": result.sharepoint_error,
            },
            "overall_success": result.google_sheets_success and result.sharepoint_success,
        }
    
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
"""

# ==============================================================================
# SCENARIO 7: Simple CLI Tool for Testing
# ==============================================================================
# Location: scripts/test_sharepoint.py
# Run: python scripts/test_sharepoint.py
# Time to create: 10 minutes

"""
#!/usr/bin/env python3
import sys
import os
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

def main():
    print("\n" + "=" * 60)
    print("SharePoint Integration Test Tool")
    print("=" * 60)
    
    # Test 1: Configuration
    print("\n[TEST 1] Configuration Check")
    from api.services.sharepoint_config import is_sharepoint_enabled, get_sharepoint_mode
    
    enabled = is_sharepoint_enabled()
    mode = get_sharepoint_mode()
    print(f"  Enabled: {enabled}")
    print(f"  Mode: {mode}")
    
    if not enabled:
        print("  ⚠ SharePoint is disabled. Enable it in config.yaml to proceed.")
        return False
    
    # Test 2: Authentication
    print("\n[TEST 2] Authentication Test")
    from api.services.sharepoint_data_service import get_service as get_sp_service
    
    sp_service = get_sp_service()
    print(f"  Authenticated: {sp_service.authenticated}")
    
    if not sp_service.authenticated:
        print(f"  ✗ Error: {sp_service.get_last_error()}")
        return False
    else:
        print("  ✓ Successfully authenticated")
    
    # Test 3: Read Data
    print("\n[TEST 3] Read Data Test")
    try:
        df = sp_service.fetch_sheet_data("master_data")
        if df is not None:
            print(f"  ✓ Successfully read {len(df)} rows")
            print(f"  Columns: {', '.join(df.columns.tolist()[:3])}...")
        else:
            print("  ⚠ No data returned (might not exist yet)")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # Test 4: Write Data
    print("\n[TEST 4] Write Data Test")
    from api.services.dual_write_service import create_dual_write_service
    
    test_data = [{
        "Date": datetime.now().strftime("%Y-%m-%d"),
        "Time": datetime.now().strftime("%H:%M"),
        "Grid Units Consumed (KWh)": 100,
        "Solar Units Consumed(KWh)": 50,
        "Total Units Consumed (KWh)": 150,
    }]
    
    service = create_dual_write_service(mode="dual")
    result = service.write_data("master_data", test_data)
    
    print(f"  Google Sheets: {'✓' if result.google_sheets_success else '✗'}")
    if result.google_sheets_error:
        print(f"    Error: {result.google_sheets_error}")
    
    print(f"  SharePoint: {'✓' if result.sharepoint_success else '✗'}")
    if result.sharepoint_error:
        print(f"    Error: {result.sharepoint_error}")
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60 + "\n")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
"""

# ==============================================================================
# SCENARIO 8: Environment Setup Validation
# ==============================================================================
# Location: scripts/check_env.sh (or check_env.ps1 for Windows)
# Usage: Run before starting backend
# Time to create: 5 minutes

"""
# check_env.sh (Linux/Mac)
#!/bin/bash

echo "Checking SharePoint Environment..."
echo "=================================="

# Required variables
required_vars=("SHAREPOINT_TENANT_ID" "SHAREPOINT_CLIENT_ID" "SHAREPOINT_CLIENT_SECRET")

missing=0
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Missing: $var"
        missing=$((missing+1))
    else
        echo "✓ Set: $var"
    fi
done

if [ $missing -eq 0 ]; then
    echo ""
    echo "✓ All SharePoint credentials are set"
    exit 0
else
    echo ""
    echo "❌ Missing $missing credentials"
    echo "Set them in .env file before starting backend"
    exit 1
fi
"""

# ==============================================================================
