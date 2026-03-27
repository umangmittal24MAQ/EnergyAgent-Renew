"""
Data Loader Module
Handles loading data from JSON files created by the ingestion scripts
"""
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Get the directory where the Ingestion-agent scripts are
INGESTION_AGENT_DIR = Path(__file__).parent


def load_json_file(filename: str) -> Dict[str, Any]:
    """Load a JSON file from the Ingestion-agent directory"""
    filepath = INGESTION_AGENT_DIR / filename

    if not filepath.exists():
        logger.warning(f"File not found: {filepath}")
        return {}

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {filename}: {e}")
        return {}


def load_current_dashboard_data() -> Dict[str, Any]:
    """Load current dashboard data (latest measurements)"""
    return load_json_file('filtered_dashboard_data.json')


def load_7day_data() -> Dict[str, Any]:
    """Load 7-day historical data"""
    return load_json_file('7day_final.json')


def load_smb_data() -> Dict[str, Any]:
    """Load SMB (Solar Box Unit) status data"""
    return load_json_file('smb_data_grid.json')


def load_solar_data(config: Any = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Load solar data and optionally filter by date range
    """
    data = load_7day_data()
    records = []

    for entry in data.get('data', []):
        date_str = entry.get('Date', '')
        if not date_str:
            continue

        # Apply date filtering if provided
        if start_date and date_str < start_date:
            continue
        if end_date and date_str > end_date:
            continue

        records.append({
            'Date': date_str,
            'Day Generation (kWh)': entry.get('Day_Generation_kWh', 0),
            'Total Generation (kWh)': entry.get('Total_Generation_kWh', 0),
        })

    return pd.DataFrame(records)


def load_grid_data(config: Any = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Load grid energy data
    """
    # Placeholder - will be populated from Google Sheets or other source
    return pd.DataFrame()


def load_diesel_data(config: Any = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Load diesel generator data
    """
    # Placeholder - will be populated from Google Sheets or other source
    return pd.DataFrame()


def load_unified_data(config: Any = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Load unified energy data (combination of all sources)
    """
    solar_df = load_solar_data(config, start_date, end_date)
    # Can add grid and diesel data when available
    return solar_df


def load_daily_summary(config: Any = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Load daily aggregated summary
    """
    return load_solar_data(config, start_date, end_date)


def load_current_metrics() -> Dict[str, Any]:
    """Get current metrics from dashboard data"""
    dashboard = load_current_dashboard_data()
    return {
        'timestamp': dashboard.get('dashboard_info', {}).get('timestamp'),
        'dc_power_kw': dashboard.get('power_data', {}).get('DC_Power_kW', 0),
        'ac_power_kw': dashboard.get('power_data', {}).get('AC_Power_kW', 0),
        'day_generation_kwh': dashboard.get('energy_data', {}).get('Day_Generation_kWh', 0),
        'total_generation_kwh': dashboard.get('energy_data', {}).get('Total_Generation_kWh', 0),
    }


def load_all(config: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load all data sources (config, grid, solar, diesel).
    Returns: (config_dict, grid_df, solar_df, diesel_df)
    """
    if config is None:
        # Load default config or create empty one
        config = {
            "grid_rate": 7.11,  # INR per kWh
            "email": {
                "default_to": "",
                "default_cc": "",
                "subject": "Daily Energy Report — Noida Campus — {date}"
            }
        }

    grid_df = load_grid_data(config)
    solar_df = load_solar_data(config)
    diesel_df = load_diesel_data(config)

    return config, grid_df, solar_df, diesel_df


def load_solar_last7_data(config: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    Load last 7 days of solar data.
    """
    return load_solar_data(config)
