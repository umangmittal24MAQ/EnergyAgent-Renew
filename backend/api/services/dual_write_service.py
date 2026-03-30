"""
Dual-Write Service
Handles writing to both Google Sheets and SharePoint simultaneously
Provides fallback logic and error handling
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WriteResult:
    """Result of a write operation"""
    google_sheets_success: bool
    sharepoint_success: bool
    google_sheets_error: Optional[str] = None
    sharepoint_error: Optional[str] = None
    bytes_written: int = 0
    rows_written: int = 0


class DualWriteService:
    """
    Service for dual-writing data to Google Sheets and SharePoint
    Handles both simultaneously with fallback logic
    """
    
    def __init__(
        self,
        google_sheets_writer: Optional[Any] = None,
        sharepoint_writer: Optional[Any] = None,
        mode: str = "dual",
        fail_open: bool = True
    ):
        """
        Initialize dual-write service
        
        Args:
            google_sheets_writer: GoogleSheetsWriter instance
            sharepoint_writer: SharePointExcelWriter instance
            mode: "google" (GS only), "sharepoint" (SP only), "dual" (both)
            fail_open: If True, continue even if one destination fails
        """
        self.google_sheets_writer = google_sheets_writer
        self.sharepoint_writer = sharepoint_writer
        self.mode = mode
        self.fail_open = fail_open
    
    def write_data(
        self,
        sheet_key: str,
        data: List[Dict[str, Any]],
        destination: Optional[str] = None
    ) -> WriteResult:
        """
        Write data to configured destinations
        
        Args:
            sheet_key: Sheet identifier (e.g., 'unified_solar')
            data: List of row dictionaries to write
            destination: Override destination ("google", "sharepoint", or None for default)
            
        Returns:
            WriteResult with status of each destination
        """
        result = WriteResult(
            google_sheets_success=False,
            sharepoint_success=False,
        )
        
        if not data:
            logger.warning(f"No data to write for {sheet_key}")
            return result
        
        # Determine write strategy
        target_mode = destination or self.mode
        
        try:
            # Write to Google Sheets
            if target_mode in ["google", "dual"]:
                result.google_sheets_success, result.google_sheets_error = self._write_google_sheets(
                    sheet_key, data
                )
                if result.google_sheets_success:
                    result.rows_written += len(data)
        except Exception as e:
            result.google_sheets_error = str(e)
            logger.error(f"Exception in Google Sheets write: {e}")
            if not self.fail_open:
                raise
        
        try:
            # Write to SharePoint
            if target_mode in ["sharepoint", "dual"]:
                result.sharepoint_success, result.sharepoint_error = self._write_sharepoint(
                    sheet_key, data
                )
                if result.sharepoint_success:
                    result.bytes_written += len(data) * 100  # Rough estimate
        except Exception as e:
            result.sharepoint_error = str(e)
            logger.error(f"Exception in SharePoint write: {e}")
            if not self.fail_open:
                raise
        
        # Check overall success
        if not self.fail_open:
            # All must succeed
            if target_mode == "dual" and not (result.google_sheets_success and result.sharepoint_success):
                raise RuntimeError(f"Dual write failed for {sheet_key}")
        
        return result
    
    def _write_google_sheets(self, sheet_key: str, data: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
        """
        Write data to Google Sheets
        
        Returns:
            (success, error_message)
        """
        if not self.google_sheets_writer:
            return False, "Google Sheets writer not configured"
        
        try:
            # Import here to avoid circular imports
            from ..energy_dashboard.Ingestion_agent.google_sheets_writer import SHEETS_CONFIG
            
            if sheet_key not in SHEETS_CONFIG:
                return False, f"Unknown sheet key: {sheet_key}"
            
            success = self.google_sheets_writer.append_data_to_sheet(sheet_key, data)
            if success:
                logger.info(f"Successfully wrote {len(data)} rows to Google Sheets: {sheet_key}")
                return True, None
            else:
                error = getattr(self.google_sheets_writer, 'last_error', 'Unknown error')
                logger.error(f"Google Sheets write failed: {error}")
                return False, error
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Exception writing to Google Sheets: {error_msg}")
            return False, error_msg
    
    def _write_sharepoint(self, sheet_key: str, data: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
        """
        Write data to SharePoint
        
        Returns:
            (success, error_message)
        """
        if not self.sharepoint_writer:
            return False, "SharePoint writer not configured"
        
        try:
            from .sharepoint_config import get_sheet_config, is_sharepoint_enabled
            
            if not is_sharepoint_enabled():
                return False, "SharePoint integration not enabled"
            
            # SharePoint writer returns boolean directly
            success = self.sharepoint_writer.append_data_to_sheet(sheet_key, data)
            
            if success:
                logger.info(f"Successfully wrote {len(data)} rows to SharePoint: {sheet_key}")
                return True, None
            else:
                # SharePoint writer prints errors to stdout, capture from there if possible
                return False, "SharePoint write failed (check logs)"
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Exception writing to SharePoint: {error_msg}")
            return False, error_msg
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of connected writers"""
        return {
            "google_sheets": {
                "available": self.google_sheets_writer is not None,
                "authenticated": getattr(self.google_sheets_writer, 'authenticated', False) if self.google_sheets_writer else False
            },
            "sharepoint": {
                "available": self.sharepoint_writer is not None,
                "authenticated": getattr(self.sharepoint_writer, 'authenticated', False) if self.sharepoint_writer else False
            },
            "mode": self.mode,
            "fail_open": self.fail_open
        }


def create_dual_write_service(
    mode: str = "dual",
    fail_open: bool = True
) -> DualWriteService:
    """
    Factory for creating a configured dual-write service
    
    Args:
        mode: "google", "sharepoint", or "dual"
        fail_open: If True, continue if one destination fails
        
    Returns:
        Configured DualWriteService instance
    """
    from .sharepoint_config import is_sharepoint_enabled
    
    google_sheets_writer = None
    sharepoint_writer = None
    
    try:
        # Initialize Google Sheets writer
        if mode in ["google", "dual"]:
            try:
                from ..energy_dashboard.Ingestion_agent.google_sheets_writer import GoogleSheetsWriter
                credentials_file = Path(__file__).parent.parent.parent / "energy-dashboard" / "Ingestion-agent" / "google_credentials.json"
                if credentials_file.exists():
                    google_sheets_writer = GoogleSheetsWriter(str(credentials_file))
                else:
                    logger.warning("Google credentials file not found")
            except Exception as e:
                logger.error(f"Failed to initialize Google Sheets writer: {e}")
    except Exception as e:
        logger.error(f"Error setting up Google Sheets: {e}")
    
    try:
        # Initialize SharePoint writer
        if (mode in ["sharepoint", "dual"]) and is_sharepoint_enabled():
            try:
                from .sharepoint_auth import load_auth_config_from_env, SharePointAuthManager
                from ..energy_dashboard.Ingestion_agent.sharepoint_writer import SharePointExcelWriter
                
                config = load_auth_config_from_env()
                auth_manager = SharePointAuthManager(config)
                sharepoint_writer = SharePointExcelWriter(auth_manager)
            except Exception as e:
                logger.error(f"Failed to initialize SharePoint writer: {e}")
    except Exception as e:
        logger.error(f"Error setting up SharePoint: {e}")
    
    return DualWriteService(
        google_sheets_writer=google_sheets_writer,
        sharepoint_writer=sharepoint_writer,
        mode=mode,
        fail_open=fail_open
    )


# Import Path for file checks
from pathlib import Path
