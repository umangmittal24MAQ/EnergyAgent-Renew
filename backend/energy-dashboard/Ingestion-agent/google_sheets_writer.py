import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Fix Unicode encoding on Windows
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials as OAuth2Credentials
    from googleapiclient.discovery import build
    HAS_GOOGLE_API = True
except ImportError:
    HAS_GOOGLE_API = False
    print("WARNING: Google API libraries not installed. Installing now...")
    import subprocess
    result = subprocess.run([sys.executable, "-m", "pip", "install", "google-auth-oauthlib", "google-auth-httplib2", "google-api-python-client"], 
                           capture_output=True, text=True)
    if result.returncode != 0:
        print(f"WARNING: Installation error output: {result.stderr}")
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials as OAuth2Credentials
        from googleapiclient.discovery import build
        HAS_GOOGLE_API = True
    except ImportError:
        HAS_GOOGLE_API = False

# Get the directory of the current script
script_dir = Path(__file__).parent

# Google Sheets IDs
SHEETS_CONFIG = {
    "unified_solar": {
        "name": "UnifiedSolarData",
        "sheet_id": "1_lm81sKpds3y_SCskKsiSYbOQo7On-mXBGekAN95FMc",
        "tab_name": "Sheet1",
        "data_file": "filtered_dashboard_data.json"
    },
    "last_7_days": {
        "name": "last_7_days",
        "sheet_id": "1FqMyIESL1TDOSqynXCqB-75RQeC-2TTpSSka7DqmwWI",
        "tab_name": "Sheet1",
        "data_file": "filtered_7day_data.json"
    },
    "smb_status": {
        "name": "SMB_Status",
        "sheet_id": "1cWwIp13hPkE2Pz06QU4PmmUvJLYPlj11GgCV1h7WdmA",
        "tab_name": "Sheet1",
        "data_file": "smb_data_grid.json"
    },
    "grid_and_diesel": {
        "name": "grid_and_diesel",
        "sheet_id": "134mi3kO-gcDtkQC9kGvK_zmO0LPQg1Fyj5A0qwM53DA",
        "tab_name": "Sheet1",
        "data_file": "grid_and_diesel_data.json"
    }
}

INVERTER_COLUMNS = ["INV_1", "INV_2", "INV_3", "INV_4", "INV_5"]
ACTIVE_STATUSES = {"active", "on"}
INACTIVE_STATUSES = {"inactive", "off"}

class GoogleSheetsWriter:
    def __init__(self, credentials_path: str):
        """Initialize Google Sheets writer with OAuth2 credentials (personal Gmail account)"""
        self.credentials_path = credentials_path
        self.token_path = script_dir / "token.json"
        self.service = None
        self.sheet_service = None
        self.SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with Google Sheets API using OAuth2 and personal Gmail account"""
        if not HAS_GOOGLE_API:
            print("ERROR: Google API libraries failed to install")
            print("   Please install manually: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
            return False
        
        try:
            credentials = None
            
            # Check if token.json exists (already authenticated)
            if self.token_path.exists():
                print("[INFO] Loading stored credentials from token.json...")
                credentials = OAuth2Credentials.from_authorized_user_file(
                    str(self.token_path), self.SCOPES
                )
            
            # If no valid credentials, perform OAuth2 flow
            if not credentials or not credentials.valid:
                if credentials and credentials.expired and credentials.refresh_token:
                    print("[INFO] Refreshing expired credentials...")
                    credentials.refresh(Request())
                else:
                    print("[INFO] Starting OAuth2 authentication with your Gmail account...")
                    
                    # Check if credentials file exists
                    if not os.path.exists(self.credentials_path):
                        print(f"\n[ERROR] Credentials file not found: {self.credentials_path}")
                        print("\n[INFO] Setup Instructions:")
                        print("1. Go to https://console.cloud.google.com/")
                        print("2. Create a new project (or use existing)")
                        print("3. Enable Google Sheets API")
                        print("4. Go to 'Credentials' → 'Create Credentials' → 'OAuth 2.0 Client ID'")
                        print("5. Choose 'Desktop Application'")
                        print("6. Download the JSON file and rename it to 'google_credentials.json'")
                        print(f"7. Place it in: {self.credentials_path}")
                        return False
                    
                    # Create OAuth2 flow
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES
                    )
                    
                    # Run local server for authentication
                    print("   [INFO] A browser window will open for you to authenticate...")
                    print("   [OK] Login with your Gmail account")
                    print("   [OK] Grant permission to access Google Sheets")
                    print("   [OK] The browser will redirect back to localhost")
                    
                    credentials = flow.run_local_server(port=0)
                    
                    # Save credentials for future use
                    with open(self.token_path, 'w') as token_file:
                        token_file.write(credentials.to_json())
                    print(f"\n[OK] Credentials saved to token.json (expires: {credentials.expiry})")
            
            # Build the Sheets API service
            self.sheet_service = build('sheets', 'v4', credentials=credentials)
            print("[OK] Successfully authenticated with Google Sheets API")
            return True
            
        except Exception as e:
            print(f"[ERROR] Authentication failed: {str(e)}")
            return False
    
    def get_last_row(self, sheet_id: str, tab_name: str = "Sheet1") -> int:
        """Get the last row with data in a sheet. Returns 0 if sheet is empty."""
        try:
            result = self.sheet_service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=f"{tab_name}!A:A"
            ).execute()
            values = result.get('values', [])
            return len(values) if values else 0
        except Exception as e:
            print(f"   [WARN] Could not get last row: {str(e)}")
            return 0

    @staticmethod
    def _to_date_key(value: Any) -> str:
        """Normalize a date/timestamp value to YYYY-MM-DD."""
        if value is None:
            return ""

        text = str(value).strip()
        if not text:
            return ""

        parse_formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%d-%b-%Y",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S%z",
        ]

        for fmt in parse_formats:
            try:
                dt = datetime.strptime(text, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        # Keep ISO-like fallback behavior deterministic.
        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            return text[:10]

    @staticmethod
    def _normalize_status(value: Any) -> str:
        """Map inverter status text into active/inactive buckets."""
        text = str(value or "").strip().lower()
        if text in ACTIVE_STATUSES:
            return "active"
        if text in INACTIVE_STATUSES:
            return "inactive"
        # As requested, null/empty/unknown values count as downtime.
        return "inactive"

    @staticmethod
    def _format_inverter_stats(stats: Dict[str, float]) -> str:
        return (
            f"Uptime: {float(stats.get('uptime', 0.0)):.1f} hours"
            f" | Downtime: {float(stats.get('downtime', 0.0)):.1f} hours"
        )

    @staticmethod
    def _column_letter(index_one_based: int) -> str:
        """Convert 1-based column index to Excel/Sheets column letters."""
        result = ""
        idx = max(int(index_one_based), 1)
        while idx > 0:
            idx, rem = divmod(idx - 1, 26)
            result = chr(65 + rem) + result
        return result

    def _load_smb_daily_inverter_stats(self) -> Dict[str, Dict[int, Dict[str, float]]]:
        """
        Build per-day uptime/downtime stats for INV_1..INV_5 from SMB status sheet.
        Each row in SMB sheet represents a 30-minute reading.
        """
        stats_by_date: Dict[str, Dict[int, Dict[str, float]]] = {}
        smb_sheet_id = SHEETS_CONFIG["smb_status"]["sheet_id"]
        smb_tab_name = SHEETS_CONFIG["smb_status"]["tab_name"]

        try:
            result = self.sheet_service.spreadsheets().values().get(
                spreadsheetId=smb_sheet_id,
                range=f"{smb_tab_name}!A:Z",
            ).execute()
            values = result.get("values", [])
            if len(values) < 2:
                return stats_by_date

            headers = [str(h).strip() for h in values[0]]
            header_index = {header: idx for idx, header in enumerate(headers)}

            date_col_idx = header_index.get("Date", -1)
            if date_col_idx < 0:
                return stats_by_date

            status_col_indices: Dict[int, int] = {}
            for inv_idx in range(1, 6):
                candidates = [
                    f"SMB{inv_idx}_status",
                    f"smb{inv_idx}_status",
                    f"SMB{inv_idx} Status",
                    f"smb{inv_idx} status",
                ]
                found_idx = -1
                for candidate in candidates:
                    if candidate in header_index:
                        found_idx = header_index[candidate]
                        break
                status_col_indices[inv_idx] = found_idx

            for row in values[1:]:
                raw_date = row[date_col_idx] if date_col_idx < len(row) else ""
                date_key = self._to_date_key(raw_date)
                if not date_key:
                    continue

                if date_key not in stats_by_date:
                    stats_by_date[date_key] = {
                        inv_idx: {"active_count": 0, "inactive_count": 0}
                        for inv_idx in range(1, 6)
                    }

                for inv_idx in range(1, 6):
                    status_idx = status_col_indices.get(inv_idx, -1)
                    raw_status = row[status_idx] if status_idx >= 0 and status_idx < len(row) else ""
                    normalized = self._normalize_status(raw_status)
                    if normalized == "active":
                        stats_by_date[date_key][inv_idx]["active_count"] += 1
                    else:
                        stats_by_date[date_key][inv_idx]["inactive_count"] += 1

            # Convert counts to hours using fixed 0.5-hour intervals.
            for date_key, inv_map in stats_by_date.items():
                for inv_idx, counts in inv_map.items():
                    active_count = float(counts.get("active_count", 0))
                    inactive_count = float(counts.get("inactive_count", 0))
                    inv_map[inv_idx] = {
                        "uptime": round(active_count * 0.5, 1),
                        "downtime": round(inactive_count * 0.5, 1),
                    }

            return stats_by_date
        except Exception as e:
            print(f"   [WARN] Could not compute SMB inverter stats: {str(e)}")
            return {}

    def _ensure_grid_headers(self, sheet_id: str, tab_name: str, expected_headers: List[str]) -> bool:
        """Ensure grid_and_diesel header row contains all expected columns in order."""
        try:
            result = self.sheet_service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=f"{tab_name}!1:1",
            ).execute()
            existing_rows = result.get("values", [])
            if not existing_rows:
                return True

            existing_headers = [str(h).strip() for h in existing_rows[0]]
            missing = [h for h in expected_headers if h not in existing_headers]
            if not missing:
                return True

            updated_headers = existing_headers + missing
            self.sheet_service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=f"{tab_name}!A1",
                valueInputOption="USER_ENTERED",
                body={"values": [updated_headers]},
            ).execute()
            print(f"   [OK] Added new grid headers: {', '.join(missing)}")
            return True
        except Exception as e:
            print(f"   [WARN] Could not ensure grid headers: {str(e)}")
            return False
    
    def write_unified_solar_data(self, sheet_id: str, data: Dict[str, Any]):
        """Append unified solar data to Google Sheets"""
        try:
            tab_name = SHEETS_CONFIG["unified_solar"]["tab_name"]
            
            # Prepare headers - matching the exact order from your sheet template
            headers = [
                "Date", "Date Formatted", "Time", "DC Power (kW)", "AC Power (kW)", 
                "Current Total (A)", "Current Average (A)", "Active Power (kW)", 
                "Apparent Power (kVA)", "Power Factor", "Frequency (Hz)", 
                "Voltage Phase-to-Phase (V)", "Voltage Phase-to-Neutral (V)", 
                "V1 (V)", "V2 (V)", "V3 (V)", 
                "Day Generation (kWh)", "Day Import (kWh)", "Day Export (kWh)", 
                "Total Import (kWh)", "Total Export (kWh)",
                "DC Capacity (kWp)", "AC Capacity (kW)"
            ]
            
            # Extract data from the unified data
            dashboard_info = data.get("dashboard_info", {})
            last_update = dashboard_info.get("last_update", "")
            
            try:
                dt = datetime.fromisoformat(last_update.replace('Z', '+00:00')) if last_update else datetime.now()
            except:
                dt = datetime.now()
            
            power_data = data.get("power_data", {})
            voltage_data = data.get("voltage_data", {})
            energy_data = data.get("energy_data", {})
            plant_capacity = data.get("plant_capacity", {})
            plant_info = data.get("plant_info", {})
            
            # Create data row
            row = [
                dt.strftime("%Y-%m-%d"),                                          # Date
                dt.strftime("%A, %B %d, %Y"),                                     # Date Formatted
                dt.strftime("%H:%M:%S"),                                          # Time
                power_data.get("DC_Power_kW", ""),
                power_data.get("AC_Power_kW", ""),
                power_data.get("Current_Total_A", ""),
                power_data.get("Current_Average_A", ""),
                power_data.get("Active_Power_kW", ""),
                power_data.get("Apparent_Power_kVA", ""),
                power_data.get("Power_Factor", ""),
                power_data.get("Frequency_Hz", ""),
                voltage_data.get("Voltage_VLL_Phase_to_Phase_V", ""),
                voltage_data.get("Voltage_VLN_Phase_to_Neutral_V", ""),
                voltage_data.get("Voltage_V1_V", ""),
                voltage_data.get("Voltage_V2_V", ""),
                voltage_data.get("Voltage_V3_V", ""),
                energy_data.get("Day_Generation_kWh", ""),
                energy_data.get("Day_Import_kWh", ""),
                energy_data.get("Day_Export_kWh", ""),
                energy_data.get("Total_Import_kWh", ""),
                energy_data.get("Total_Export_kWh", ""),
                plant_capacity.get("DC_Capacity_kWp", ""),
                plant_capacity.get("AC_Capacity_kW", "")
            ]
            
            # Get the last row to determine where to append
            last_row = self.get_last_row(sheet_id, tab_name)
            
            if last_row == 0:
                # Sheet is empty, write headers and first data row
                body = {'values': [headers, row]}
                range_to_write = f"{tab_name}!A1"
                print(f"   [OK] Sheet empty, adding headers and data")
            else:
                # Append to existing data (skip headers, just append row)
                body = {'values': [row]}
                range_to_write = f"{tab_name}!A{last_row + 1}"
                print(f"   [OK] Appending to row {last_row + 1}")
            
            self.sheet_service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=range_to_write,
                valueInputOption="USER_ENTERED",
                body=body
            ).execute()
            
            print(f"   [OK] Written unified solar data (1 row appended)")
            return True
        except Exception as e:
            print(f"   [ERROR] Error writing unified solar data: {str(e)}")
            return False
    
    def write_last_7_days_data(self, sheet_id: str, data: Dict[str, Any]):
        """Append last 7 days data to Google Sheets (dynamically finding best timestamp per day)"""
        try:
            tab_name = SHEETS_CONFIG["last_7_days"]["tab_name"]
            
            # Prepare headers (without Time column as timestamps should not be written)
            headers = ["Date", "Date Formatted", "Start Value", "End Value", "Generation (Wh)"]
            
            data_rows = []
            
            # Extract daily timeline data
            daily_timeline = data.get("daily_timeline", {})
            
            for date_str in sorted(daily_timeline.keys(), reverse=True):  # Most recent first
                day_data = daily_timeline[date_str]
                all_readings = day_data.get("all_readings", [])
                
                if not all_readings:
                    print(f"   [WARN] No readings found for {date_str}")
                    continue
                
                # Find the reading with the maximum generation value for this day
                best_reading = None
                max_generation = -1
                
                for reading in all_readings:
                    generation_wh = reading.get("generation_wh", 0)
                    
                    # Find the reading with the highest generation value
                    # If multiple readings have the same max, the last one in iteration is used
                    if generation_wh >= max_generation:
                        max_generation = generation_wh
                        best_reading = reading
                
                if best_reading:
                    row = [
                        best_reading.get("date", ""),
                        day_data.get("date", ""),
                        best_reading.get("start_value", ""),
                        best_reading.get("end_value", ""),
                        best_reading.get("generation_wh", "")
                    ]
                    data_rows.append(row)
                    print(f"   [OK] Day {date_str}: Selected {best_reading.get('generation_wh')} Wh generation")
            
            if len(data_rows) == 0:
                print(f"   [WARN] No data found in filtered_7day_data.json")
                return False
            
            # Get the last row to determine where to append
            last_row = self.get_last_row(sheet_id, tab_name)
            
            if last_row == 0:
                # Sheet is empty, write headers and data rows
                all_rows = [headers] + data_rows
                body = {'values': all_rows}
                range_to_write = f"{tab_name}!A1"
                print(f"   [OK] Sheet empty, adding headers and data")
            else:
                # Append only data rows (skip headers)
                body = {'values': data_rows}
                range_to_write = f"{tab_name}!A{last_row + 1}"
                print(f"   [OK] Appending to row {last_row + 1}")
            
            self.sheet_service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=range_to_write,
                valueInputOption="USER_ENTERED",
                body=body
            ).execute()
            
            print(f"   [OK] Written last 7 days data ({len(data_rows)} rows appended)")
            return True
        except Exception as e:
            print(f"   [ERROR] Error writing last 7 days data: {str(e)}")
            return False
    
    def write_smb_status_data(self, sheet_id: str, data: List[Dict[str, Any]]):
        """Append SMB status data to Google Sheets - one row per timestamp with SMB columns"""
        try:
            tab_name = SHEETS_CONFIG["smb_status"]["tab_name"]
            
            if not data or len(data) == 0:
                print(f"   [WARN] No data found in smb_data_grid.json")
                return False
            
            # Get the base row data (first entry in the array)
            base_row = data[0]
            
            # Extract date and time
            date_str = base_row.get("Date", "")
            day_str = base_row.get("Day", "")
            time_str = base_row.get("Time", "")
            
            # Headers for SMB status sheet - columns for each SMB with power and status
            headers = ["Date", "Day", "Time", "SMB1", "SMB1_status", "SMB2", "SMB2_status", "SMB3", "SMB3_status", "SMB4", "SMB4_status", "SMB5", "SMB5_status"]
            
            # Prepare data rows - single row per timestamp with all SMBs
            data_rows = []
            
            # Extract SMB data from the grid
            # SMB columns in format: "SMB1 (kW)", "SMB1 Status", etc.
            smb_names = ["SMB1", "SMB2", "SMB3", "SMB4", "SMB5"]
            
            row = [date_str, day_str, time_str]  # Start with date, day, time
            
            for smb_name in smb_names:
                power_kw = base_row.get(f"{smb_name} (kW)", "")
                status = base_row.get(f"{smb_name} Status", "")
                
                # Format power value - use 0 for null/empty values
                power_value = f"{float(power_kw):.2f}" if power_kw else 0
                
                # Use 0 for null/empty status values
                status_value = status if status else 0
                
                row.append(power_value)  # SMB power in kW
                row.append(status_value)  # SMB status (ON/OFF)
            
            data_rows.append(row)
            
            if len(data_rows) == 0:
                print(f"   [WARN] No SMB data found in smb_data_grid.json")
                return False
            
            # Get the last row to determine where to append
            last_row = self.get_last_row(sheet_id, tab_name)
            
            if last_row == 0:
                # Sheet is empty, write headers and data rows
                all_rows = [headers] + data_rows
                body = {'values': all_rows}
                range_to_write = f"{tab_name}!A1"
                print(f"   [OK] Sheet empty, adding headers and data")
            else:
                # Append only data rows (skip headers)
                body = {'values': data_rows}
                range_to_write = f"{tab_name}!A{last_row + 1}"
                print(f"   [OK] Appending to row {last_row + 1}")
            
            self.sheet_service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=range_to_write,
                valueInputOption="USER_ENTERED",
                body=body
            ).execute()
            
            print(f"   [OK] Written SMB status data (1 row appended)")
            return True
        except Exception as e:
            print(f"   [ERROR] Error writing SMB status data: {str(e)}")
            return False

    def write_grid_and_diesel_data(self, sheet_id: str, data: List[Dict[str, Any]]):
        """Append grid and diesel rows to Google Sheets"""
        try:
            tab_name = SHEETS_CONFIG["grid_and_diesel"]["tab_name"]

            if not data or len(data) == 0:
                print("   [WARN] No data found in grid_and_diesel_data.json")
                return False

            headers = [
                "Date", "Time", "Grid Units Consumed (KWh)", "DG Units Consumed (KWh)",
                "Total Units Consumed in INR", "Grid Cost (INR)", "Diesel Cost (INR)",
                "Total Cost (INR)", "Energy Saving (INR)",
                "INV_1", "INV_2", "INV_3", "INV_4", "INV_5",
            ]

            inverter_stats_by_date = self._load_smb_daily_inverter_stats()

            data_rows = []
            for row_data in data:
                row_date_key = self._to_date_key(row_data.get("Date", ""))
                day_stats = inverter_stats_by_date.get(
                    row_date_key,
                    {
                        inv_idx: {"uptime": 0.0, "downtime": 0.0}
                        for inv_idx in range(1, 6)
                    },
                )
                row = [
                    row_data.get("Date", ""),
                    row_data.get("Time", ""),
                    row_data.get("Grid Units Consumed (KWh)", 0),
                    row_data.get("DG Units Consumed (KWh)", 0),
                    row_data.get("Total Units Consumed in INR", 0),
                    row_data.get("Grid Cost (INR)", 0),
                    row_data.get("Diesel Cost (INR)", 0),
                    row_data.get("Total Cost (INR)", 0),
                    row_data.get("Energy Saving (INR)", 0),
                    self._format_inverter_stats(day_stats.get(1, {"uptime": 0.0, "downtime": 0.0})),
                    self._format_inverter_stats(day_stats.get(2, {"uptime": 0.0, "downtime": 0.0})),
                    self._format_inverter_stats(day_stats.get(3, {"uptime": 0.0, "downtime": 0.0})),
                    self._format_inverter_stats(day_stats.get(4, {"uptime": 0.0, "downtime": 0.0})),
                    self._format_inverter_stats(day_stats.get(5, {"uptime": 0.0, "downtime": 0.0})),
                ]
                data_rows.append(row)

            last_row = self.get_last_row(sheet_id, tab_name)

            if last_row == 0:
                all_rows = [headers] + data_rows
                body = {'values': all_rows}
                range_to_write = f"{tab_name}!A1"
                print("   [OK] Sheet empty, adding headers and data")
            else:
                self._ensure_grid_headers(sheet_id, tab_name, headers)
                body = {'values': data_rows}
                range_to_write = f"{tab_name}!A{last_row + 1}"
                print(f"   [OK] Appending to row {last_row + 1}")

            self.sheet_service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=range_to_write,
                valueInputOption="USER_ENTERED",
                body=body
            ).execute()

            print(f"   [OK] Written grid and diesel data ({len(data_rows)} row(s) appended)")
            return True
        except Exception as e:
            print(f"   [ERROR] Error writing grid and diesel data: {str(e)}")
            return False

    def backfill_grid_inverter_columns(self, sheet_id: str) -> bool:
        """Backfill INV_1..INV_5 values for existing grid rows where they are missing."""
        try:
            tab_name = SHEETS_CONFIG["grid_and_diesel"]["tab_name"]
            headers = [
                "Date", "Time", "Grid Units Consumed (KWh)", "DG Units Consumed (KWh)",
                "Total Units Consumed in INR", "Grid Cost (INR)", "Diesel Cost (INR)",
                "Total Cost (INR)", "Energy Saving (INR)",
                "INV_1", "INV_2", "INV_3", "INV_4", "INV_5",
            ]

            self._ensure_grid_headers(sheet_id, tab_name, headers)

            result = self.sheet_service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=f"{tab_name}!A:Z",
            ).execute()
            values = result.get("values", [])
            if len(values) < 2:
                print("   [INFO] No existing grid rows found for inverter backfill")
                return True

            sheet_headers = [str(h).strip() for h in values[0]]
            header_index = {name: idx for idx, name in enumerate(sheet_headers)}
            date_idx = header_index.get("Date", -1)
            inv_indices = [header_index.get(col, -1) for col in INVERTER_COLUMNS]

            if date_idx < 0 or any(idx < 0 for idx in inv_indices):
                print("   [WARN] Could not resolve required columns for inverter backfill")
                return False

            stats_by_date = self._load_smb_daily_inverter_stats()
            updates = []

            inv_start_col = self._column_letter(min(inv_indices) + 1)
            inv_end_col = self._column_letter(max(inv_indices) + 1)

            for row_number, row in enumerate(values[1:], start=2):
                raw_date = row[date_idx] if date_idx < len(row) else ""
                date_key = self._to_date_key(raw_date)
                if not date_key:
                    continue

                has_inv_values = True
                for inv_idx in inv_indices:
                    existing = row[inv_idx] if inv_idx < len(row) else ""
                    if str(existing).strip() == "":
                        has_inv_values = False
                        break

                if has_inv_values:
                    continue

                day_stats = stats_by_date.get(
                    date_key,
                    {
                        idx: {"uptime": 0.0, "downtime": 0.0}
                        for idx in range(1, 6)
                    },
                )
                inv_values = [
                    self._format_inverter_stats(day_stats.get(1, {"uptime": 0.0, "downtime": 0.0})),
                    self._format_inverter_stats(day_stats.get(2, {"uptime": 0.0, "downtime": 0.0})),
                    self._format_inverter_stats(day_stats.get(3, {"uptime": 0.0, "downtime": 0.0})),
                    self._format_inverter_stats(day_stats.get(4, {"uptime": 0.0, "downtime": 0.0})),
                    self._format_inverter_stats(day_stats.get(5, {"uptime": 0.0, "downtime": 0.0})),
                ]

                updates.append(
                    {
                        "range": f"{tab_name}!{inv_start_col}{row_number}:{inv_end_col}{row_number}",
                        "values": [inv_values],
                    }
                )

            if not updates:
                print("   [INFO] No rows required inverter backfill")
                return True

            self.sheet_service.spreadsheets().values().batchUpdate(
                spreadsheetId=sheet_id,
                body={
                    "valueInputOption": "USER_ENTERED",
                    "data": updates,
                },
            ).execute()

            print(f"   [OK] Backfilled inverter columns for {len(updates)} grid row(s)")
            return True
        except Exception as e:
            print(f"   [ERROR] Error backfilling inverter columns: {str(e)}")
            return False
    
    
    def write_all_sheets(self):
        """Write data to all Google Sheets - DISABLED, use data_ingestion_agent/google_sheets_writer.py instead"""
        print("\n" + "=" * 70)
        print("[INFO] GOOGLE SHEETS WRITING DISABLED IN INGESTION-AGENT")
        print("[INFO] All Google Sheets writes are now handled by:")
        print("[INFO] data_ingestion_agent/google_sheets_writer.py")
        print("=" * 70)
        return True

def main():
    """Main entry point"""
    credentials_path = script_dir / "google_credentials.json"
    
    # Check if credentials file exists
    if not credentials_path.exists():
        print("[ERROR] google_credentials.json not found!")
        print("\n[INFO] Setup Instructions (OAuth2 with Personal Gmail Account):")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project (or use existing)")
        print("3. Enable Google Sheets API:")
        print("   - Search for 'Google Sheets API'")
        print("   - Click 'Enable'")
        print("4. Create OAuth2 Credentials:")
        print("   - Go to 'Credentials' (left sidebar)")
        print("   - Click 'Create Credentials' -> 'OAuth client ID'")
        print("   - Choose 'Desktop Application' as the type")
        print("   - Click 'Create'")
        print("   - Download the JSON file")
        print("5. Rename & Place the file:")
        print(f"   - Rename to: google_credentials.json")
        print(f"   - Place in: {credentials_path}")
        print("6. First run will open a browser for you to authenticate with Gmail")
        print("\n[OK] After setup, token.json will be automatically created for future runs")
        return False
    
    # Initialize writer and write data
    writer = GoogleSheetsWriter(str(credentials_path))
    return writer.write_all_sheets()


def backfill_inverter_columns() -> bool:
    """One-shot utility to backfill INV_1..INV_5 on existing grid rows."""
    credentials_path = script_dir / "google_credentials.json"
    if not credentials_path.exists():
        print("[ERROR] google_credentials.json not found for backfill")
        return False

    writer = GoogleSheetsWriter(str(credentials_path))
    if not writer.sheet_service:
        print("[ERROR] Not authenticated with Google Sheets API for backfill")
        return False

    return writer.backfill_grid_inverter_columns(SHEETS_CONFIG["grid_and_diesel"]["sheet_id"])

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
