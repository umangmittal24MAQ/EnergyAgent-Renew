"""
SharePoint Integration Example for Ingestion Pipeline
Shows how to add SharePoint writes to existing ingestion scripts
USAGE:
    1. In your ingestion scripts (e.g., exporter.py), import this module
    2. After writing to Google Sheets, call dual_write() to also write to SharePoint
    3. SharePoint writes will only happen if enabled in config.yaml
    
EXAMPLE INTEGRATION:
    from sharepoint_integration import dual_write_json_to_sharepoint
    
    # Your existing Google Sheets write code...
    writer.append_data_to_sheet('unified_solar', data_rows)
    
    # Add SharePoint write (will be skipped if not enabled)
    dual_write_json_to_sharepoint('unified_solar', data_rows)
"""
import logging
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "app" / "services"))

logger = logging.getLogger(__name__)


def is_sharepoint_enabled_for_ingestion() -> bool:
    """
    Check if SharePoint is enabled in config.yaml
    
    Returns:
        True if SharePoint integration is enabled
    """
    try:
        # Try to import config loader
        from api.services.sharepoint_config import is_sharepoint_enabled
        return is_sharepoint_enabled()
    except Exception as e:
        logger.warning(f"Could not load SharePoint config: {e}")
        return False


def dual_write_json_to_sharepoint(
    sheet_key: str,
    data_rows: List[Dict[str, Any]],
    verbose: bool = True
) -> bool:
    """
    Write JSON data to SharePoint (if enabled)
    This function should be called AFTER Google Sheets write in your pipeline
    
    Args:
        sheet_key: Configuration key (e.g., 'unified_solar')
        data_rows: List of dictionaries to write
        verbose: Print debug messages
        
    Returns:
        True if write successful or skipped (not enabled)
    """
    if not data_rows:
        if verbose:
            print(f"[INFO] No data to write to SharePoint for {sheet_key}")
        return True
    
    if not is_sharepoint_enabled_for_ingestion():
        if verbose:
            print(f"[DEBUG] SharePoint integration is disabled (config.yaml sharepoint.enabled=false)")
        return True  # Treat as success since not enabled
    
    try:
        from api.energy_dashboard.Ingestion_agent.sharepoint_writer import SharePointExcelWriter
        from api.services.sharepoint_auth import load_auth_config_from_env, SharePointAuthManager
        
        if verbose:
            print(f"[INFO] Attempting to write {len(data_rows)} rows to SharePoint: {sheet_key}")
        
        # Initialize auth and writer
        config = load_auth_config_from_env()
        auth_manager = SharePointAuthManager(config)
        writer = SharePointExcelWriter(auth_manager)
        
        if not writer.authenticated:
            print(f"[WARNING] SharePoint not authenticated. Skipping write.")
            print(f"[INFO] To enable: set SHAREPOINT_CLIENT_ID, SHAREPOINT_TENANT_ID environment variables")
            return False
        
        # Write data
        success = writer.append_data_to_sheet(sheet_key, data_rows)
        
        if success and verbose:
            print(f"[OK] Successfully wrote {len(data_rows)} rows to SharePoint: {sheet_key}")
        
        return success
    
    except Exception as e:
        logger.error(f"Exception writing to SharePoint: {e}")
        print(f"[ERROR] Failed to write to SharePoint: {str(e)}")
        return False


def dual_write_excel_to_sharepoint(
    sheet_key: str,
    excel_file_path: str,
    verbose: bool = True
) -> bool:
    """
    Write Excel file to SharePoint (if enabled)
    Useful for bulk uploads
    
    Args:
        sheet_key: Configuration key
        excel_file_path: Path to Excel file to upload
        verbose: Print debug messages
        
    Returns:
        True if write successful or skipped
    """
    if not is_sharepoint_enabled_for_ingestion():
        if verbose:
            print(f"[DEBUG] SharePoint integration is disabled")
        return True
    
    try:
        from api.energy_dashboard.Ingestion_agent.sharepoint_writer import SharePointExcelWriter
        from api.services.sharepoint_auth import load_auth_config_from_env, SharePointAuthManager
        import openpyxl
        import pandas as pd
        
        excel_path = Path(excel_file_path)
        if not excel_path.exists():
            print(f"[ERROR] Excel file not found: {excel_file_path}")
            return False
        
        if verbose:
            print(f"[INFO] Uploading Excel file to SharePoint: {sheet_key}")
        
        # Read Excel file
        df = pd.read_excel(excel_path)
        data_rows = df.to_dict('records')
        
        # Write to SharePoint
        config = load_auth_config_from_env()
        auth_manager = SharePointAuthManager(config)
        writer = SharePointExcelWriter(auth_manager)
        
        success = writer.append_data_to_sheet(sheet_key, data_rows)
        
        if success and verbose:
            print(f"[OK] Successfully uploaded Excel file to SharePoint: {sheet_key}")
        
        return success
    
    except Exception as e:
        logger.error(f"Exception uploading Excel to SharePoint: {e}")
        print(f"[ERROR] Failed to upload Excel: {str(e)}")
        return False


# Example usage (uncomment to test)
if __name__ == "__main__":
    print("SharePoint Ingestion Integration Examples")
    print("=" * 50)
    
    # Test data
    test_data = [
        {
            "Date": "2026-03-30",
            "Time": "10:00",
            "Grid Units Consumed (KWh)": 100,
            "Solar Units Consumed(KWh)": 50,
        }
    ]
    
    # Example 1: Check if SharePoint is enabled
    enabled = is_sharepoint_enabled_for_ingestion()
    print(f"\nSharePoint enabled: {enabled}")
    
    # Example 2: Write to SharePoint
    if enabled:
        print("\nAttempting test write to SharePoint...")
        success = dual_write_json_to_sharepoint("master_data", test_data)
        print(f"Write result: {success}")
    else:
        print("\nSharePoint not enabled. To enable:")
        print("1. Set environment variables: SHAREPOINT_CLIENT_ID, SHAREPOINT_TENANT_ID, SHAREPOINT_CLIENT_SECRET")
        print("2. Set sharepoint.enabled: true in config.yaml")
        print("3. Add site_url and drive_id for each sheet in config.yaml")
