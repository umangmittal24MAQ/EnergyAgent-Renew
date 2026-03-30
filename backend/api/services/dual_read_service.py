"""
Dual-Read Service
Handles reading from both Google Sheets and SharePoint with fallback logic
"""
import logging
from typing import Optional, Dict, Any
import pandas as pd

from .google_sheets_data_service import GoogleSheetsDataService
from .sharepoint_data_service import SharePointDataService
from .sharepoint_config import is_sharepoint_enabled, get_sharepoint_mode

logger = logging.getLogger(__name__)


class DualReadService:
    """
    Service for reading from Google Sheets and SharePoint
    With intelligent fallback logic based on configuration
    """
    
    def __init__(
        self,
        google_sheets_service: Optional[GoogleSheetsDataService] = None,
        sharepoint_service: Optional[SharePointDataService] = None,
    ):
        """
        Initialize dual-read service
        
        Args:
            google_sheets_service: GoogleSheetsDataService instance
            sharepoint_service: SharePointDataService instance
        """
        self.gs_service = google_sheets_service
        self.sp_service = sharepoint_service
    
    def get_sheet_data(
        self,
        sheet_key: str,
        source: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """
        Get data from configured source with fallback
        
        Args:
            sheet_key: Sheet identifier (e.g., 'unified_solar')
            source: Force specific source ("google", "sharepoint", None for auto)
            
        Returns:
            DataFrame or None if no data available
        """
        mode = get_sharepoint_mode()
        
        # Determine source strategy
        if source:
            # Explicit source request
            if source == "google":
                return self._fetch_from_google(sheet_key)
            elif source == "sharepoint":
                return self._fetch_from_sharepoint(sheet_key)
        
        # Auto mode based on config
        if mode == "google":
            return self._fetch_from_google(sheet_key)
        elif mode == "sharepoint":
            return self._fetch_from_sharepoint(sheet_key)
        elif mode == "dual":
            # Try SharePoint first, fallback to Google
            df = self._fetch_from_sharepoint(sheet_key)
            if df is not None and not df.empty:
                logger.info(f"Using data from SharePoint: {sheet_key}")
                return df
            
            logger.info(f"SharePoint failed or empty, falling back to Google Sheets: {sheet_key}")
            df = self._fetch_from_google(sheet_key)
            if df is not None and not df.empty:
                logger.info(f"Using data from Google Sheets: {sheet_key}")
                return df
            
            logger.warning(f"Could not fetch data from either source: {sheet_key}")
            return None
        
        return None
    
    def get_latest_data(
        self,
        sheet_key: str,
        limit: int = 1,
        source: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """
        Get latest N rows with fallback
        
        Args:
            sheet_key: Sheet identifier
            limit: Number of rows to return
            source: Force specific source or None for auto
            
        Returns:
            DataFrame with latest rows
        """
        mode = get_sharepoint_mode()
        
        if source == "google":
            return self._fetch_latest_google(sheet_key, limit)
        elif source == "sharepoint":
            return self._fetch_latest_sharepoint(sheet_key, limit)
        elif mode == "dual":
            # Try SharePoint first, fallback to Google
            df = self._fetch_latest_sharepoint(sheet_key, limit)
            if df is not None and not df.empty:
                return df
            return self._fetch_latest_google(sheet_key, limit)
        elif mode == "google":
            return self._fetch_latest_google(sheet_key, limit)
        elif mode == "sharepoint":
            return self._fetch_latest_sharepoint(sheet_key, limit)
        
        return None
    
    def get_by_date_range(
        self,
        sheet_key: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        source: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """
        Get data filtered by date range
        
        Args:
            sheet_key: Sheet identifier
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            source: Force specific source or None for auto
            
        Returns:
            Filtered DataFrame
        """
        mode = get_sharepoint_mode()
        
        if source == "google":
            return self._fetch_range_google(sheet_key, start_date, end_date)
        elif source == "sharepoint":
            return self._fetch_range_sharepoint(sheet_key, start_date, end_date)
        elif mode == "dual":
            df = self._fetch_range_sharepoint(sheet_key, start_date, end_date)
            if df is not None and not df.empty:
                return df
            return self._fetch_range_google(sheet_key, start_date, end_date)
        elif mode == "google":
            return self._fetch_range_google(sheet_key, start_date, end_date)
        elif mode == "sharepoint":
            return self._fetch_range_sharepoint(sheet_key, start_date, end_date)
        
        return None
    
    def _fetch_from_google(self, sheet_key: str) -> Optional[pd.DataFrame]:
        """Fetch data from Google Sheets"""
        if not self.gs_service:
            return None
        try:
            return self.gs_service.fetch_sheet_data(sheet_key)
        except Exception as e:
            logger.error(f"Error fetching from Google Sheets: {e}")
            return None
    
    def _fetch_from_sharepoint(self, sheet_key: str) -> Optional[pd.DataFrame]:
        """Fetch data from SharePoint"""
        if not self.sp_service or not is_sharepoint_enabled():
            return None
        try:
            return self.sp_service.fetch_sheet_data(sheet_key)
        except Exception as e:
            logger.error(f"Error fetching from SharePoint: {e}")
            return None
    
    def _fetch_latest_google(self, sheet_key: str, limit: int) -> Optional[pd.DataFrame]:
        """Get latest rows from Google Sheets"""
        if not self.gs_service:
            return None
        try:
            return self.gs_service.get_latest_rows(sheet_key, limit)
        except Exception as e:
            logger.error(f"Error fetching latest from Google Sheets: {e}")
            return None
    
    def _fetch_latest_sharepoint(self, sheet_key: str, limit: int) -> Optional[pd.DataFrame]:
        """Get latest rows from SharePoint"""
        if not self.sp_service or not is_sharepoint_enabled():
            return None
        try:
            return self.sp_service.get_latest_rows(sheet_key, limit)
        except Exception as e:
            logger.error(f"Error fetching latest from SharePoint: {e}")
            return None
    
    def _fetch_range_google(
        self,
        sheet_key: str,
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> Optional[pd.DataFrame]:
        """Get date range from Google Sheets"""
        if not self.gs_service:
            return None
        try:
            return self.gs_service.get_data_by_date_range(sheet_key, start_date, end_date)
        except Exception as e:
            logger.error(f"Error fetching date range from Google Sheets: {e}")
            return None
    
    def _fetch_range_sharepoint(
        self,
        sheet_key: str,
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> Optional[pd.DataFrame]:
        """Get date range from SharePoint"""
        if not self.sp_service or not is_sharepoint_enabled():
            return None
        try:
            return self.sp_service.get_data_by_date_range(sheet_key, start_date, end_date)
        except Exception as e:
            logger.error(f"Error fetching date range from SharePoint: {e}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of data sources"""
        return {
            "google_sheets": {
                "available": self.gs_service is not None,
                "authenticated": getattr(self.gs_service, 'authenticated', False) if self.gs_service else False,
                "error": getattr(self.gs_service, 'last_error', None) if self.gs_service else None,
            },
            "sharepoint": {
                "enabled": is_sharepoint_enabled(),
                "available": self.sp_service is not None,
                "authenticated": getattr(self.sp_service, 'authenticated', False) if self.sp_service else False,
                "error": getattr(self.sp_service, 'last_error', None) if self.sp_service else None,
            },
            "mode": get_sharepoint_mode(),
        }


# Singleton instance
_dual_read_service: Optional[DualReadService] = None


def get_dual_read_service() -> DualReadService:
    """Get or create the dual-read service singleton"""
    global _dual_read_service
    
    if _dual_read_service is None:
        from .google_sheets_data_service import get_service as get_gs_service
        from .sharepoint_data_service import get_service as get_sp_service
        
        gs_service = get_gs_service()
        sp_service = get_sp_service() if is_sharepoint_enabled() else None
        
        _dual_read_service = DualReadService(
            google_sheets_service=gs_service,
            sharepoint_service=sp_service,
        )
    
    return _dual_read_service


def reset_dual_read_service():
    """Reset the dual-read service singleton (for testing)"""
    global _dual_read_service
    _dual_read_service = None
