"""
Data Processor Module
Handles data transformation and processing for API responses
"""
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def process_solar_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Process solar data DataFrame into API response format
    """
    if df.empty:
        return {
            'data': [],
            'metadata': {
                'total_records': 0,
                'date_range': {'start': None, 'end': None}
            }
        }
    
    # Convert DataFrame to list of dicts
    data = df.to_dict('records')
    
    # Calculate metadata
    dates = pd.to_datetime(df['Date'], errors='coerce').dropna().unique()
    
    return {
        'data': data,
        'metadata': {
            'total_records': len(data),
            'date_range': {
                'start': str(dates[0]) if len(dates) > 0 else None,
                'end': str(dates[-1]) if len(dates) > 0 else None
            }
        }
    }


def process_grid_data(df: pd.DataFrame) -> Dict[str, Any]:
    """Process grid energy data"""
    return process_solar_data(df)  # Same format for now


def process_diesel_data(df: pd.DataFrame) -> Dict[str, Any]:
    """Process diesel generator data"""
    return process_solar_data(df)


def process_unified_data(df: pd.DataFrame) -> Dict[str, Any]:
    """Process unified energy data"""
    return process_solar_data(df)


def process_daily_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Process daily summary data with aggregations
    """
    if df.empty:
        return {
            'data': [],
            'metadata': {
                'total_records': 0,
                'date_range': {'start': None, 'end': None}
            }
        }
    
    # Group by date and aggregate
    daily_agg = df.groupby('Date').agg({
        'generation_wh': 'sum',
        'start_value': 'first',
        'end_value': 'last'
    }).reset_index()
    
    data = daily_agg.to_dict('records')
    
    return {
        'data': data,
        'metadata': {
            'total_records': len(data),
            'date_range': {
                'start': daily_agg['Date'].min() if len(daily_agg) > 0 else None,
                'end': daily_agg['Date'].max() if len(daily_agg) > 0 else None
            }
        }
    }


def calculate_kpis(df: pd.DataFrame, metric: str = 'generation_wh') -> Dict[str, Any]:
    """
    Calculate KPIs from data
    """
    if df.empty:
        return {
            'total': 0,
            'average': 0,
            'min': 0,
            'max': 0,
            'latest': 0
        }
    
    if metric not in df.columns:
        return {
            'total': 0,
            'average': 0,
            'min': 0,
            'max': 0,
            'latest': 0
        }
    
    col_data = pd.to_numeric(df[metric], errors='coerce').dropna()
    
    return {
        'total': float(col_data.sum()),
        'average': float(col_data.mean()),
        'min': float(col_data.min()),
        'max': float(col_data.max()),
        'latest': float(col_data.iloc[-1]) if len(col_data) > 0 else 0
    }


def process_kpi_overview(current_metrics: Dict[str, Any], historical_data: pd.DataFrame) -> Dict[str, Any]:
    """
    Process overview KPIs
    """
    solar_kpi = calculate_kpis(historical_data, 'generation_wh')
    
    return {
        'solar': {
            'current_power_kw': current_metrics.get('ac_power_kw', 0),
            'day_generation_kwh': current_metrics.get('day_generation_kwh', 0),
            'total_generation_kwh': current_metrics.get('total_generation_kwh', 0),
            'kpis': solar_kpi
        },
        'grid': {
            'current_power_kw': 0,
            'day_consumption_kwh': 0,
            'kpis': calculate_kpis(historical_data)
        },
        'diesel': {
            'current_power_kw': 0,
            'day_generation_kwh': 0,
            'kpis': calculate_kpis(historical_data)
        }
    }


def process_kpi_solar(df: pd.DataFrame) -> Dict[str, Any]:
    """Process solar KPIs"""
    return {
        'solar': calculate_kpis(df, 'generation_wh'),
        'timestamp': datetime.now().isoformat()
    }


def process_kpi_grid(df: pd.DataFrame) -> Dict[str, Any]:
    """Process grid KPIs"""
    return {
        'grid': calculate_kpis(df),
        'timestamp': datetime.now().isoformat()
    }


def process_kpi_diesel(df: pd.DataFrame) -> Dict[str, Any]:
    """Process diesel KPIs"""
    return {
        'diesel': calculate_kpis(df),
        'timestamp': datetime.now().isoformat()
    }


def build_unified_dataframe(grid: pd.DataFrame, solar: pd.DataFrame, diesel: pd.DataFrame) -> pd.DataFrame:
    """
    Build a unified dataframe combining grid, solar, and diesel data.
    Returns a dataframe with Date, Time, Grid KWh, Solar KWh, Diesel consumed, Total KWh, etc.

    Args:
        grid: DataFrame from grid_and_diesel sheet (has Grid Units Consumed, DG Units, costs, etc.)
        solar: DataFrame from last_7_days sheet (has Generation (Wh) which is solar generation)
        diesel: DataFrame (currently unused, diesel data is in grid)
    """
    # Start with grid data as the base since it has the most complete structure
    if grid is None or grid.empty:
        logger.warning("Grid dataframe is empty")
        # If we have solar data, use that as base
        if solar is not None and not solar.empty:
            unified = solar.copy()
            # Convert Generation (Wh) to Solar KWh
            if 'Generation (Wh)' in unified.columns:
                unified['Solar KWh'] = pd.to_numeric(unified['Generation (Wh)'], errors='coerce').fillna(0) / 1000.0
            elif 'Day Generation (kWh)' in unified.columns:
                unified['Solar KWh'] = pd.to_numeric(unified['Day Generation (kWh)'], errors='coerce').fillna(0)

            unified['Grid KWh'] = 0.0
            unified['Diesel consumed'] = 0.0
        else:
            return pd.DataFrame()
    else:
        unified = grid.copy()

    # Ensure Date column exists
    if 'Date' not in unified.columns:
        logger.error("No Date column found in dataframes")
        return pd.DataFrame()

    # Add Grid KWh if not present (rename from source column)
    if 'Grid KWh' not in unified.columns:
        if 'Grid Units Consumed (KWh)' in unified.columns:
            unified['Grid KWh'] = pd.to_numeric(unified['Grid Units Consumed (KWh)'], errors='coerce').fillna(0)
        else:
            unified['Grid KWh'] = 0.0

    # Add Solar KWh by merging with solar dataframe
    if solar is not None and not solar.empty and 'Date' in solar.columns:
        # Normalize dates for merging
        unified['_date_norm'] = pd.to_datetime(unified['Date'], errors='coerce').dt.normalize()
        solar_copy = solar.copy()
        solar_copy['_date_norm'] = pd.to_datetime(solar_copy['Date'], errors='coerce').dt.normalize()

        # Extract solar generation
        if 'Generation (Wh)' in solar_copy.columns:
            solar_copy['Solar KWh'] = pd.to_numeric(solar_copy['Generation (Wh)'], errors='coerce').fillna(0) / 1000.0
        elif 'Day Generation (kWh)' in solar_copy.columns:
            solar_copy['Solar KWh'] = pd.to_numeric(solar_copy['Day Generation (kWh)'], errors='coerce').fillna(0)

        # Merge solar data on date
        if 'Solar KWh' in solar_copy.columns:
            # Aggregate solar by date (sum all readings for same date)
            solar_agg = solar_copy.groupby('_date_norm')['Solar KWh'].sum().reset_index()
            unified = unified.merge(solar_agg, on='_date_norm', how='left', suffixes=('', '_solar'))

            # Use the merged solar value, fallback to 0 if missing
            if 'Solar KWh_solar' in unified.columns:
                unified['Solar KWh'] = unified['Solar KWh_solar'].fillna(0)
                unified = unified.drop(columns=['Solar KWh_solar'])
            elif 'Solar KWh' not in unified.columns:
                unified['Solar KWh'] = solar_agg['Solar KWh'].fillna(0)

        unified = unified.drop(columns=['_date_norm'], errors='ignore')

    # Ensure Solar KWh exists
    if 'Solar KWh' not in unified.columns:
        unified['Solar KWh'] = 0.0

    # Add Diesel consumed
    if 'Diesel consumed' not in unified.columns:
        if 'DG Units Consumed (KWh)' in unified.columns:
            unified['Diesel consumed'] = pd.to_numeric(unified['DG Units Consumed (KWh)'], errors='coerce').fillna(0)
        elif 'Fuel Consumed (Litres)' in unified.columns:
            unified['Diesel consumed'] = pd.to_numeric(unified['Fuel Consumed (Litres)'], errors='coerce').fillna(0)
        else:
            unified['Diesel consumed'] = 0.0

    # Calculate Total KWh (Grid + Solar, NOT including diesel)
    unified['Total KWh'] = pd.to_numeric(unified['Grid KWh'], errors='coerce').fillna(0) + pd.to_numeric(unified['Solar KWh'], errors='coerce').fillna(0)

    # Add cost calculations
    grid_rate = 7.11  # INR per kWh

    # Use existing cost columns if available, otherwise calculate
    if 'Total Cost (INR)' not in unified.columns:
        unified['Total Cost (INR)'] = unified['Total KWh'] * grid_rate

    if 'Energy Saving (INR)' not in unified.columns:
        unified['Energy Saving (INR)'] = unified['Solar KWh'] * grid_rate

    # Add time column if not present
    if 'Time' not in unified.columns:
        unified['Time'] = '00:00:00'

    # Add Day column if not present
    if 'Day' not in unified.columns:
        if 'Date' in unified.columns:
            unified['Day'] = pd.to_datetime(unified['Date'], errors='coerce').dt.day_name().fillna('')

    # Add temperature if not present (try multiple column names)
    temp_found = False
    for temp_col in ['Ambient Temp (°C)', 'Ambient Temperature °C', 'Ambient Temperature (°C)']:
        if temp_col in unified.columns:
            temp_found = True
            break

    if not temp_found:
        unified['Ambient Temp (°C)'] = 25.0  # Default placeholder

    # Add inverter status if not present
    if 'Inverter Status' not in unified.columns:
        unified['Inverter Status'] = 'All Online'

    return unified



def compute_overview_kpis(df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute overview KPIs from unified dataframe.
    Returns: dict with keys total_kwh, solar_kwh, solar_pct, total_cost, energy_saved, avg_temp
    """
    if df.empty:
        return {
            'total_kwh': 0.0,
            'solar_kwh': 0.0,
            'solar_pct': 0.0,
            'total_cost': 0.0,
            'energy_saved': 0.0,
            'avg_temp': 0.0
        }

    # Extract grid rate from config
    grid_rate = config.get('grid_rate', 7.11)

    # Calculate totals
    solar_kwh = pd.to_numeric(df.get('Solar KWh', 0), errors='coerce').fillna(0).sum()
    grid_kwh = pd.to_numeric(df.get('Grid KWh', 0), errors='coerce').fillna(0).sum()
    total_kwh = solar_kwh + grid_kwh

    # Calculate percentages
    solar_pct = (solar_kwh / total_kwh * 100) if total_kwh > 0 else 0.0

    # Calculate costs
    total_cost = total_kwh * grid_rate
    energy_saved = solar_kwh * grid_rate

    # Get average temperature
    temp_cols = ['Ambient Temp (°C)', 'Ambient Temperature °C', 'Ambient Temperature (°C)']
    avg_temp = 0.0
    for col in temp_cols:
        if col in df.columns:
            avg_temp = pd.to_numeric(df[col], errors='coerce').dropna().mean()
            if pd.notna(avg_temp) and avg_temp > 0:
                break

    return {
        'total_kwh': float(total_kwh),
        'solar_kwh': float(solar_kwh),
        'solar_pct': float(solar_pct),
        'total_cost': float(total_cost),
        'energy_saved': float(energy_saved),
        'avg_temp': float(avg_temp) if pd.notna(avg_temp) else 25.0
    }
