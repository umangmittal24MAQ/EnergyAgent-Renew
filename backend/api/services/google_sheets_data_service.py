"""
Google Sheets Data Service
Fetches real-time data from Google Sheets using gspread and OAuth2
Enhanced with proper timestamp handling and field mapping
"""
import sys
import json
import logging
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

# Timezone for data processing
IST = ZoneInfo("Asia/Kolkata")

# OAuth2 credentials paths
INGESTION_AGENT_PATH = Path(__file__).parent.parent.parent / "energy-dashboard" / "Ingestion-agent"
CREDENTIALS_FILE = INGESTION_AGENT_PATH / "google_credentials.json"
TOKEN_FILE = INGESTION_AGENT_PATH / "token.json"


def _sheet_id_from_url(url: str) -> str:
    """Extract spreadsheet ID from a Google Sheets URL."""
    if not url:
        return ""
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
    return match.group(1) if match else ""

# Sheet configurations with field mappings
SHEETS_CONFIG = {
    "unified_solar": {
        "name": "UnifiedSolarData",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1_lm81sKpds3y_SCskKsiSYbOQo7On-mXBGekAN95FMc/edit?usp=sharing",
        "sheet_id": _sheet_id_from_url("https://docs.google.com/spreadsheets/d/1_lm81sKpds3y_SCskKsiSYbOQo7On-mXBGekAN95FMc/edit?usp=sharing"),
        "tab_name": "Sheet1",
        "timestamp_field": "Time",  # Field containing time info
        "date_field": "Date",             # Field containing date
        "numeric_columns": [
            'DC Power (kW)', 'AC Power (kW)', 'Current Total (A)',
            'Current Average (A)', 'Active Power (kW)', 'Apparent Power (kVA)',
            'Power Factor', 'Frequency (Hz)',
            'Voltage Phase-to-Phase (V)', 'Voltage Phase-to-Neutral (V)',
            'V1 (V)', 'V2 (V)', 'V3 (V)',
            'Day Generation (kWh)', 'Day Import (kWh)', 'Day Export (kWh)',
            'Total Import (kWh)', 'Total Export (kWh)',
            'DC Capacity (kWp)', 'AC Capacity (kW)'
        ]
    },
    "last_7_days": {
        "name": "last_7_days",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1FqMyIESL1TDOSqynXCqB-75RQeC-2TTpSSka7DqmwWI/edit?usp=sharing",
        "sheet_id": _sheet_id_from_url("https://docs.google.com/spreadsheets/d/1FqMyIESL1TDOSqynXCqB-75RQeC-2TTpSSka7DqmwWI/edit?usp=sharing"),
        "tab_name": "Sheet1",
        "timestamp_field": "Date",
        "date_field": "Date",
        "numeric_columns": [
            'Start Value', 'End Value', 'Generation (Wh)'
        ]
    },
    "smb_status": {
        "name": "SMB_Status",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1cWwIp13hPkE2Pz06QU4PmmUvJLYPlj11GgCV1h7WdmA/edit?usp=sharing",
        "sheet_id": _sheet_id_from_url("https://docs.google.com/spreadsheets/d/1cWwIp13hPkE2Pz06QU4PmmUvJLYPlj11GgCV1h7WdmA/edit?usp=sharing"),
        "tab_name": "Sheet1",
        "timestamp_field": "Date",
        "date_field": "Date",
        "numeric_columns": [
            'SMB1', 'SMB2', 'SMB3', 'SMB4', 'SMB5'
        ]
    },
    "grid_and_diesel": {
        "name": "grid_and_diesel",
        "sheet_url": "https://docs.google.com/spreadsheets/d/134mi3kO-gcDtkQC9kGvK_zmO0LPQg1Fyj5A0qwM53DA/edit?usp=sharing",
        "sheet_id": _sheet_id_from_url("https://docs.google.com/spreadsheets/d/134mi3kO-gcDtkQC9kGvK_zmO0LPQg1Fyj5A0qwM53DA/edit?usp=sharing"),
        "tab_name": "Sheet1",
        "timestamp_field": "Time",
        "date_field": "Date",
        "numeric_columns": [
            'Grid Units Consumed (KWh)', 'DG Units Consumed (KWh)',
            'Total Units Consumed in INR', 'Grid Cost (INR)',
            'Diesel Cost (INR)', 'Total Cost (INR)', 'Energy Saving (INR)'
        ]
    },
    "master_data": {
        "name": "master_data",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1Xa27g3NiviJF2avJMvGtNrANNSd8j_C6NIZ7OXQelfE/edit?usp=sharing",
        "sheet_id": _sheet_id_from_url("https://docs.google.com/spreadsheets/d/1Xa27g3NiviJF2avJMvGtNrANNSd8j_C6NIZ7OXQelfE/edit?usp=sharing"),
        "tab_name": "Sheet1",
        "timestamp_field": "Time",
        "date_field": "Date",
        "numeric_columns": [
            'Grid Units Consumed (KWh)', 
            'Solar Units Consumed(KWh)', 'Total Units Consumed (KWh)',
            'Total Units Consumed in INR', 'Energy Saving in INR',
            'Number of Panels Cleaned', 'Diesel consumed',
            'Water treated through STP', 'Water treated through WTP'
        ]
    }
}

SHEET_KEY_ALIASES = {
    # Canonical keys
    "unified_solar": "unified_solar",
    "last_7_days": "last_7_days",
    "smb_status": "smb_status",
    "grid_and_diesel": "grid_and_diesel",
    "master_data": "master_data",
    # External/source naming variants
    "UnifiedSolarData": "unified_solar",
    "last_7days": "last_7_days",
    "last_7_days": "last_7_days",
    "SMB_Status": "smb_status",
}


class GoogleSheetsDataService:
    """Service to fetch data from Google Sheets"""
    
    def __init__(self):
        """Initialize the service and authenticate with Google Sheets"""
        self.client = None
        self.authenticated = False
        self.last_error = None
        self._authenticate()
    
    @staticmethod
    def _parse_timestamp(value: str) -> Optional[datetime]:
        """
        Parse timestamp value from multiple formats
        
        Args:
            value: String value that may be a timestamp
            
        Returns:
            Parsed datetime with IST timezone or None
        """
        if not value or not isinstance(value, str):
            return None
        
        value = value.strip()
        
        # Try common datetime formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%d/%m/%Y %H:%M:%S',
            '%d/%m/%Y %H:%M',
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(value, fmt)
                # Add IST timezone if not present
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=IST)
                return dt
            except ValueError:
                continue
        
        # Try pd.to_datetime as fallback
        try:
            dt = pd.to_datetime(value, errors='raise')
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=IST)
            return dt
        except:
            return None
    
    @staticmethod
    def _normalize_date_column(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
        """
        Normalize date column to datetime format
        
        Args:
            df: DataFrame to process
            date_col: Name of date column
            
        Returns:
            DataFrame with normalized date column
        """
        if date_col not in df.columns:
            return df
        
        try:
            df = df.copy()
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            return df
        except Exception as e:
            logger.warning(f"Failed to normalize date column {date_col}: {e}")
            return df
    
    @staticmethod
    def _ensure_timestamp_column(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """
        Ensure DataFrame has a Timestamp column for consistent time-based filtering
        
        Args:
            df: DataFrame to process
            config: Sheet configuration with timestamp/date field info
            
        Returns:
            DataFrame with Timestamp column added if needed
        """
        df = df.copy()
        timestamp_field = config.get('timestamp_field', 'Timestamp')
        date_field = config.get('date_field', 'Date')
        
        # If already has Timestamp column, return as-is
        if 'Timestamp' in df.columns:
            return df
        
        # Try Date + Time composition when fields are distinct.
        if (
            date_field in df.columns
            and timestamp_field in df.columns
            and timestamp_field != date_field
        ):
            combined = (
                df[date_field].astype(str).str.strip() + " " + df[timestamp_field].astype(str).str.strip()
            )
            df['Timestamp'] = pd.to_datetime(combined, errors='coerce')
        # If both names point to the same column, parse that column directly.
        elif timestamp_field in df.columns:
            df['Timestamp'] = pd.to_datetime(df[timestamp_field], errors='coerce')
        # Try to create from timestamp_field only
        elif timestamp_field in df.columns and timestamp_field != 'Timestamp':
            df['Timestamp'] = pd.to_datetime(df[timestamp_field], errors='coerce')
        # Otherwise try to create from date_field only
        elif date_field in df.columns and date_field != 'Timestamp':
            df['Timestamp'] = pd.to_datetime(df[date_field], errors='coerce')
        
        return df
    
    def _authenticate(self) -> bool:
        """Authenticate with Google Sheets API using OAuth2"""
        try:
            import gspread
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials as OAuth2Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            
            # Use full spreadsheets scope to remain compatible with tokens created
            # by writer scripts that request read/write permissions.
            SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
            credentials = None
            
            # Try to load existing token
            if TOKEN_FILE.exists():
                logger.info(f"Loading stored OAuth2 credentials from {TOKEN_FILE}")
                credentials = OAuth2Credentials.from_authorized_user_file(
                    str(TOKEN_FILE), SCOPES
                )
            
            # Refresh or create new credentials
            if not credentials or not credentials.valid:
                if credentials and credentials.expired and credentials.refresh_token:
                    logger.info("Refreshing expired OAuth2 credentials")
                    credentials.refresh(Request())
                elif CREDENTIALS_FILE.exists():
                    logger.info(f"Starting OAuth2 flow with {CREDENTIALS_FILE}")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(CREDENTIALS_FILE), SCOPES
                    )
                    credentials = flow.run_local_server(port=0)
                    
                    # Save the token for future use
                    with open(TOKEN_FILE, 'w') as token:
                        token.write(credentials.to_json())
                    logger.info(f"OAuth2 token saved to {TOKEN_FILE}")
                else:
                    logger.error(f"Credentials file not found: {CREDENTIALS_FILE}")
                    self.last_error = "Google Sheets credentials not found"
                    return False
            
            # Create gspread client
            self.client = gspread.authorize(credentials)
            self.authenticated = True
            logger.info("Successfully authenticated with Google Sheets API")
            return True
            
        except Exception as e:
            logger.error(f"Google Sheets authentication failed: {e}")
            self.last_error = str(e)
            self.authenticated = False
            return False
    
    def fetch_sheet_data(self, sheet_key: str) -> Optional[pd.DataFrame]:
        """
        Fetch data from a Google Sheet
        
        Args:
            sheet_key: Key in SHEETS_CONFIG (e.g., 'unified_solar')
            
        Returns:
            DataFrame with sheet data or None if fetch fails
        """
        if not self.authenticated or self.client is None:
            logger.error("Not authenticated with Google Sheets")
            return None
        
        try:
            resolved_key = SHEET_KEY_ALIASES.get(sheet_key, sheet_key)
            config = SHEETS_CONFIG.get(resolved_key)
            if not config:
                logger.error(f"Unknown sheet key: {sheet_key}")
                return None
            
            sheet_id = config["sheet_id"]
            tab_name = config["tab_name"]
            
            logger.info(f"Fetching {resolved_key} (tab: {tab_name}) from Google Sheets")
            
            # Open the spreadsheet
            spreadsheet = self.client.open_by_key(sheet_id)
            
            # Get the worksheet
            worksheet = spreadsheet.worksheet(tab_name)
            
            # Get all values
            data = worksheet.get_all_values()
            
            if not data or len(data) < 2:
                logger.warning(f"No data found in {resolved_key}")
                return pd.DataFrame()
            
            # Convert to DataFrame
            headers = data[0]
            rows = data[1:]
            df = pd.DataFrame(rows, columns=headers)
            
            logger.info(f"Successfully fetched {len(df)} rows from {resolved_key}")
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch {resolved_key}: {e}")
            self.last_error = str(e)
            return None
    
    def get_unified_solar_data(self) -> Optional[pd.DataFrame]:
        """Fetch and process unified solar data with timestamp handling"""
        df = self.fetch_sheet_data("unified_solar")
        if df is None or df.empty:
            return None
        
        try:
            config = SHEETS_CONFIG.get("unified_solar", {})
            
            # Normalize date columns
            if 'Date' in df.columns:
                df = self._normalize_date_column(df, 'Date')
            
            # Ensure Timestamp column exists
            df = self._ensure_timestamp_column(df, config)
            
            # Convert numeric columns
            numeric_cols = config.get('numeric_columns', [])
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Sort by timestamp (newest first) if available
            if 'Timestamp' in df.columns:
                df = df.sort_values('Timestamp', ascending=False)
            
            logger.info(f"Processed unified solar data: {len(df)} rows with timestamps")
            return df
        except Exception as e:
            logger.error(f"Failed to process unified solar data: {e}")
            return None
    
    def get_last_7_days_data(self) -> Optional[pd.DataFrame]:
        """Fetch and process 7-day summary data with timestamp handling"""
        df = self.fetch_sheet_data("last_7_days")
        if df is None or df.empty:
            return None
        
        try:
            config = SHEETS_CONFIG.get("last_7_days", {})
            
            # Normalize date column
            if 'Date' in df.columns:
                df = self._normalize_date_column(df, 'Date')
            
            # Ensure Timestamp column
            df = self._ensure_timestamp_column(df, config)
            
            # Convert numeric columns
            numeric_cols = config.get('numeric_columns', [])
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Sort by timestamp (newest first)
            if 'Timestamp' in df.columns:
                df = df.sort_values('Timestamp', ascending=False)
            
            logger.info(f"Processed 7-day data: {len(df)} rows with timestamps")
            return df
        except Exception as e:
            logger.error(f"Failed to process 7-day data: {e}")
            return None
    
    def get_smb_status_data(self) -> Optional[pd.DataFrame]:
        """Fetch and process SMB status data with timestamp handling"""
        df = self.fetch_sheet_data("smb_status")
        if df is None or df.empty:
            return None
        
        try:
            config = SHEETS_CONFIG.get("smb_status", {})
            
            # Normalize date column
            if 'Date' in df.columns:
                df = self._normalize_date_column(df, 'Date')
            
            # Ensure Timestamp column
            df = self._ensure_timestamp_column(df, config)
            
            # Convert numeric columns for SMB power data
            numeric_cols = config.get('numeric_columns', [])
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Sort by timestamp (newest first)
            if 'Timestamp' in df.columns:
                df = df.sort_values('Timestamp', ascending=False)
            
            logger.info(f"Processed SMB status data: {len(df)} rows with timestamps")
            return df
        except Exception as e:
            logger.error(f"Failed to process SMB status data: {e}")
            return None

    def get_grid_and_diesel_data(self) -> Optional[pd.DataFrame]:
        """Fetch and process grid and diesel sheet with timestamp handling."""
        df = self.fetch_sheet_data("grid_and_diesel")
        if df is None or df.empty:
            return None

        try:
            config = SHEETS_CONFIG.get("grid_and_diesel", {})

            if 'Date' in df.columns:
                df = self._normalize_date_column(df, 'Date')

            df = self._ensure_timestamp_column(df, config)

            numeric_cols = config.get('numeric_columns', [])
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            if 'Timestamp' in df.columns:
                df = df.sort_values('Timestamp', ascending=False)

            logger.info(f"Processed grid_and_diesel data: {len(df)} rows with timestamps")
            return df
        except Exception as e:
            logger.error(f"Failed to process grid_and_diesel data: {e}")
            return None
    
    def get_master_data(self) -> Optional[pd.DataFrame]:
        """Fetch and process master data sheet with timestamp handling."""
        df = self.fetch_sheet_data("master_data")
        if df is None or df.empty:
            return None

        try:
            config = SHEETS_CONFIG.get("master_data", {})

            if 'Date' in df.columns:
                df = self._normalize_date_column(df, 'Date')

            df = self._ensure_timestamp_column(df, config)

            numeric_cols = config.get('numeric_columns', [])
            preserve_text_cols = {
                'Ambient Temperature °C',
                'Ambient Temperature (°C)',
                'Ambient Temperature',
            }
            for col in numeric_cols:
                if col in df.columns and col not in preserve_text_cols:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            if 'Timestamp' in df.columns:
                df = df.sort_values('Timestamp', ascending=False)

            logger.info(f"Processed master_data: {len(df)} rows with timestamps")
            return df
        except Exception as e:
            logger.error(f"Failed to process master_data: {e}")
            return None
    
    def is_authenticated(self) -> bool:
        """Check if service is authenticated"""
        return self.authenticated
    
    def get_last_error(self) -> Optional[str]:
        """Get the last error message"""
        return self.last_error
    
    def filter_by_date_range(
        self,
        df: pd.DataFrame,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Filter DataFrame by date range
        
        Args:
            df: Input DataFrame with Timestamp or Date column
            start_date: Start date in YYYY-MM-DD format or ISO format
            end_date: End date in YYYY-MM-DD format or ISO format
            
        Returns:
            Filtered DataFrame
        """
        if df.empty:
            return df
        
        df = df.copy()
        
        # Use Timestamp column if available, otherwise Date
        date_column = 'Timestamp' if 'Timestamp' in df.columns else 'Date'
        
        if date_column not in df.columns:
            logger.warning(f"No date column found in DataFrame for filtering")
            return df
        
        try:
            # Ensure date column is datetime
            if df[date_column].dtype == 'object':
                df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
            
            # Filter by start date
            if start_date:
                start = pd.to_datetime(start_date)
                df = df[df[date_column] >= start]
                logger.debug(f"Filtered from {start_date}: {len(df)} records")
            
            # Filter by end date
            if end_date:
                end = pd.to_datetime(end_date)
                # Include entire end date
                end = end + pd.Timedelta(days=1)
                df = df[df[date_column] < end]
                logger.debug(f"Filtered to {end_date}: {len(df)} records")
            
            return df
        except Exception as e:
            logger.error(f"Error filtering by date range: {e}")
            return df
    
    def get_data_by_timestamp_range(
        self,
        sheet_key: str,
        start_timestamp: Optional[datetime] = None,
        end_timestamp: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> Optional[pd.DataFrame]:
        """
        Fetch and filter data by timestamp range
        
        Args:
            sheet_key: Sheet to fetch ('unified_solar', 'last_7_days', or 'smb_status')
            start_timestamp: Start timestamp (datetime)
            end_timestamp: End timestamp (datetime)
            limit: Maximum number of records to return
            
        Returns:
            Filtered DataFrame or None if fetch fails
        """
        if sheet_key == 'unified_solar':
            df = self.get_unified_solar_data()
        elif sheet_key == 'last_7_days':
            df = self.get_last_7_days_data()
        elif sheet_key == 'smb_status':
            df = self.get_smb_status_data()
        else:
            logger.error(f"Unknown sheet key: {sheet_key}")
            return None
        
        if df is None or df.empty:
            return df
        
        try:
            df = df.copy()
            
            # Use Timestamp column if available
            if 'Timestamp' in df.columns:
                if start_timestamp:
                    df = df[df['Timestamp'] >= start_timestamp]
                if end_timestamp:
                    df = df[df['Timestamp'] <= end_timestamp]
            
            # Apply limit
            if limit and limit > 0:
                df = df.head(limit)
            
            return df
        except Exception as e:
            logger.error(f"Error filtering data by timestamp range: {e}")
            return df


# Global instance
_service_instance = None


def get_service() -> GoogleSheetsDataService:
    """Get or create the global service instance"""
    global _service_instance
    if _service_instance is None:
        _service_instance = GoogleSheetsDataService()
    return _service_instance


def reset_service():
    """Reset the global service instance"""
    global _service_instance
    _service_instance = None
