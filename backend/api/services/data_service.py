"""
Data service that reads dashboard data from Ingestion-agent outputs.
"""
import logging
from typing import Optional, Dict, List, Any
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

from ..config import DATA_DIR, config
from .ingestion_bridge import get_loader_processor

# Keep optional mail summary support when available.
try:
    from mail_scheduling_agent.emailer import generate_smart_summary
except ImportError:
    generate_smart_summary = None

loader, processor = get_loader_processor()

def _compute_daily_summary_fallback(unified_df: pd.DataFrame) -> pd.DataFrame:
    if unified_df is None or unified_df.empty:
        return pd.DataFrame()

    working = unified_df.copy()
    working["Date"] = pd.to_datetime(working.get("Date"), errors="coerce").dt.strftime("%Y-%m-%d")
    working = working.dropna(subset=["Date"])

    def _col(name: str) -> pd.Series:
        return pd.to_numeric(working.get(name, 0), errors="coerce").fillna(0)

    if "Grid KWh" not in working.columns and "Grid Units Consumed (KWh)" in working.columns:
        working["Grid KWh"] = _col("Grid Units Consumed (KWh)")
    if "Solar KWh" not in working.columns:
        if "Day Generation (kWh)" in working.columns:
            working["Solar KWh"] = _col("Day Generation (kWh)")
        else:
            working["Solar KWh"] = 0
    if "Diesel consumed" not in working.columns and "DG Units Consumed (KWh)" in working.columns:
        working["Diesel consumed"] = _col("DG Units Consumed (KWh)")

    grouped = working.groupby("Date", as_index=False).agg(
        {
            "Grid KWh": "sum",
            "Solar KWh": "sum",
            "Diesel consumed": "sum",
            "Total KWh": "sum" if "Total KWh" in working.columns else "size",
            "Total Cost (INR)": "sum" if "Total Cost (INR)" in working.columns else "size",
            "Energy Saving (INR)": "sum" if "Energy Saving (INR)" in working.columns else "size",
        }
    )

    if "Total KWh" in grouped.columns:
        total_kwh_series = pd.to_numeric(grouped["Total KWh"], errors="coerce").fillna(0)
        if float(total_kwh_series.sum()) <= 0:
            grouped["Total KWh"] = grouped["Grid KWh"] + grouped["Solar KWh"]
    else:
        grouped["Total KWh"] = grouped["Grid KWh"] + grouped["Solar KWh"]

    if "Total Cost (INR)" in grouped.columns:
        total_cost_series = pd.to_numeric(grouped["Total Cost (INR)"], errors="coerce").fillna(0)
        if float(total_cost_series.sum()) <= 0:
            grouped["Total Cost (INR)"] = grouped["Total KWh"] * 7.11
    else:
        grouped["Total Cost (INR)"] = grouped["Total KWh"] * 7.11

    if "Energy Saving (INR)" in grouped.columns:
        savings_series = pd.to_numeric(grouped["Energy Saving (INR)"], errors="coerce").fillna(0)
        if float(savings_series.sum()) <= 0:
            grouped["Energy Saving (INR)"] = grouped["Solar KWh"] * 7.11
    else:
        grouped["Energy Saving (INR)"] = grouped["Solar KWh"] * 7.11

    return grouped


def _get_last7_solar_date_set() -> set:
    """Get normalized date set from the latest 7 dates in rolling solar dataset."""
    try:
        solar_df = loader.load_solar_data(config)
        if len(solar_df) == 0 or 'Date' not in solar_df.columns:
            return set()

        normalized_dates = pd.to_datetime(solar_df['Date'], errors='coerce').dt.normalize().dropna()
        unique_dates = sorted(normalized_dates.unique())
        return set(unique_dates[-7:])
    except Exception:
        return set()


def _filter_to_date_set(df: pd.DataFrame, allowed_dates: set) -> pd.DataFrame:
    """Filter dataframe rows by Date column using normalized allowed date set."""
    if not allowed_dates or len(df) == 0 or 'Date' not in df.columns:
        return df
    dt_series = pd.to_datetime(df['Date'], errors='coerce').dt.normalize()
    return df[dt_series.isin(allowed_dates)].copy()


def _use_rolling_window(start_date: Optional[str], end_date: Optional[str]) -> bool:
    """Use rolling 7-day alignment only when dashboard date filter is not set."""
    return not (start_date or end_date)


def _apply_timestamp_filtering(
    df: pd.DataFrame,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """
    Apply timestamp-based filtering to DataFrame.
    
    Args:
        df: Input DataFrame
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        Filtered DataFrame
    """
    if df.empty or (not start_date and not end_date):
        return df
    
    df = df.copy()

    # Timestamp filtering against Ingestion-agent output data.
    date_col = 'Timestamp' if 'Timestamp' in df.columns else 'Date'
    
    if date_col in df.columns:
        # Ensure datetime type
        if df[date_col].dtype == 'object':
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
        if start_date:
            df = df[df[date_col] >= pd.to_datetime(start_date)]
        if end_date:
            end = pd.to_datetime(end_date) + pd.Timedelta(days=1)
            df = df[df[date_col] < end]
    
    return df


def load_unified_data(start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Load unified energy data with optional date/timestamp filtering
    from Ingestion-agent source data.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        Dictionary with data, date_range, and total_records
    """
    try:
        logger.info("Loading unified data from Ingestion-agent sources")
        grid_df = loader.load_grid_data(config)
        solar_df = loader.load_solar_data(config)
        diesel_df = loader.load_diesel_data(config)

        # Keep rolling 7-day alignment only when no explicit date range is requested.
        if _use_rolling_window(start_date, end_date):
            allowed_dates = _get_last7_solar_date_set()
            grid_df = _filter_to_date_set(grid_df, allowed_dates)
            solar_df = _filter_to_date_set(solar_df, allowed_dates)
            diesel_df = _filter_to_date_set(diesel_df, allowed_dates)

        # Build unified dataframe
        unified_df = processor.build_unified_dataframe(grid_df, solar_df, diesel_df)
    
    except Exception as e:
        logger.warning(f"Error loading unified data: {e}, attempting fallback")
        # Last resort fallback
        grid_df = loader.load_grid_data(config)
        solar_df = loader.load_solar_data(config)
        diesel_df = loader.load_diesel_data(config)
        
        if _use_rolling_window(start_date, end_date):
            allowed_dates = _get_last7_solar_date_set()
            grid_df = _filter_to_date_set(grid_df, allowed_dates)
            solar_df = _filter_to_date_set(solar_df, allowed_dates)
            diesel_df = _filter_to_date_set(diesel_df, allowed_dates)
        
        unified_df = processor.build_unified_dataframe(grid_df, solar_df, diesel_df)

    # Apply timestamp-aware filtering
    unified_df = _apply_timestamp_filtering(unified_df, start_date, end_date)

    # Format date for response
    if 'Timestamp' in unified_df.columns:
        unified_df['Timestamp_str'] = pd.to_datetime(unified_df['Timestamp'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
    if 'Date' in unified_df.columns and unified_df['Date'].dtype == 'datetime64[ns]':
        unified_df['Date'] = unified_df['Date'].dt.strftime('%Y-%m-%d')

    # Get date range
    date_col = 'Timestamp' if 'Timestamp' in unified_df.columns else 'Date'
    if date_col in unified_df.columns:
        all_dates = pd.to_datetime(unified_df[date_col], errors='coerce')
    else:
        all_dates = pd.Series(dtype='datetime64[ns]')
    
    date_range = {
        "min_date": all_dates.min().strftime('%Y-%m-%d') if len(all_dates) > 0 else None,
        "max_date": all_dates.max().strftime('%Y-%m-%d') if len(all_dates) > 0 else None
    }

    # Convert to dict
    unified_df = unified_df.drop(
        columns=["Irradiance (W/m²)", "DG Runtime (hrs)", "Source"],
        errors="ignore",
    )
    data = unified_df.to_dict('records')

    return {
        "data": data,
        "date_range": date_range,
        "total_records": len(data)
    }


def load_grid_data(start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """Load grid data with optional timestamp-based filtering"""
    try:
        grid_df = loader.load_grid_data(config)
    except Exception as e:
        logger.warning(f"Error loading grid data: {e}")
        return {
            "data": [],
            "date_range": {"min_date": None, "max_date": None},
            "total_records": 0
        }

    # Align to rolling 7-day only when no explicit filter range is selected
    if _use_rolling_window(start_date, end_date):
        allowed_dates = _get_last7_solar_date_set()
        grid_df = _filter_to_date_set(grid_df, allowed_dates)

    # Apply timestamp-aware filtering
    grid_df = _apply_timestamp_filtering(grid_df, start_date, end_date)

    # Format date for response
    if 'Date' in grid_df.columns and grid_df['Date'].dtype == 'datetime64[ns]':
        grid_df['Date'] = grid_df['Date'].dt.strftime('%Y-%m-%d')

    # Get date range
    date_col = 'Date'
    if date_col in grid_df.columns:
        all_dates = pd.to_datetime(grid_df[date_col], errors='coerce')
    else:
        all_dates = pd.Series(dtype='datetime64[ns]')
    
    date_range = {
        "min_date": all_dates.min().strftime('%Y-%m-%d') if len(all_dates) > 0 else None,
        "max_date": all_dates.max().strftime('%Y-%m-%d') if len(all_dates) > 0 else None
    }

    data = grid_df.to_dict('records')

    return {
        "data": data,
        "date_range": date_range,
        "total_records": len(data)
    }


def load_solar_data(start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """Load solar data with optional timestamp-based filtering"""
    try:
        solar_df = loader.load_solar_data(config)
    except Exception as e:
        logger.warning(f"Error loading solar data: {e}")
        return {
            "data": [],
            "date_range": {"min_date": None, "max_date": None},
            "total_records": 0
        }

    # Force rolling 7-day view only when user hasn't selected a date range
    if _use_rolling_window(start_date, end_date):
        allowed_dates = _get_last7_solar_date_set()
        solar_df = _filter_to_date_set(solar_df, allowed_dates)

    # Apply timestamp-aware filtering
    solar_df = _apply_timestamp_filtering(solar_df, start_date, end_date)

    # Format date for response
    if 'Date' in solar_df.columns and solar_df['Date'].dtype == 'datetime64[ns]':
        solar_df['Date'] = solar_df['Date'].dt.strftime('%Y-%m-%d')

    # Get date range
    date_col = 'Date'
    if date_col in solar_df.columns:
        all_dates = pd.to_datetime(solar_df[date_col], errors='coerce')
    else:
        all_dates = pd.Series(dtype='datetime64[ns]')
    
    date_range = {
        "min_date": all_dates.min().strftime('%Y-%m-%d') if len(all_dates) > 0 else None,
        "max_date": all_dates.max().strftime('%Y-%m-%d') if len(all_dates) > 0 else None
    }

    data = solar_df.to_dict('records')

    return {
        "data": data,
        "date_range": date_range,
        "total_records": len(data)
    }


def load_solar_last7_data() -> Dict[str, Any]:
    """Load static last-7-days solar data from configured source."""
    solar_df = loader.load_solar_last7_data(config)

    all_dates = pd.to_datetime(solar_df['Date']) if len(solar_df) > 0 else pd.Series(dtype='datetime64[ns]')
    date_range = {
        "min_date": all_dates.min().strftime('%Y-%m-%d') if len(all_dates) > 0 else None,
        "max_date": all_dates.max().strftime('%Y-%m-%d') if len(all_dates) > 0 else None
    }

    if len(solar_df) > 0:
        solar_df = solar_df.copy()
        solar_df['Date'] = pd.to_datetime(solar_df['Date']).dt.strftime('%Y-%m-%d')

    data = solar_df.to_dict('records')

    return {
        "data": data,
        "date_range": date_range,
        "total_records": len(data)
    }


def load_diesel_data(start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """Load diesel data with optional timestamp-based filtering"""
    try:
        diesel_df = loader.load_diesel_data(config)
    except Exception as e:
        logger.warning(f"Error loading diesel data: {e}")
        return {
            "data": [],
            "date_range": {"min_date": None, "max_date": None},
            "total_records": 0
        }

    # Align diesel to rolling 7-day window only when no explicit date range is selected
    if _use_rolling_window(start_date, end_date):
        allowed_dates = _get_last7_solar_date_set()
        diesel_df = _filter_to_date_set(diesel_df, allowed_dates)

    # Apply timestamp-aware filtering
    diesel_df = _apply_timestamp_filtering(diesel_df, start_date, end_date)

    # Format date for response
    if 'Date' in diesel_df.columns and diesel_df['Date'].dtype == 'datetime64[ns]':
        diesel_df['Date'] = diesel_df['Date'].dt.strftime('%Y-%m-%d')

    # Get date range
    date_col = 'Date'
    if date_col in diesel_df.columns:
        all_dates = pd.to_datetime(diesel_df[date_col], errors='coerce')
    else:
        all_dates = pd.Series(dtype='datetime64[ns]')
    
    date_range = {
        "min_date": all_dates.min().strftime('%Y-%m-%d') if len(all_dates) > 0 else None,
        "max_date": all_dates.max().strftime('%Y-%m-%d') if len(all_dates) > 0 else None
    }

    data = diesel_df.to_dict('records')

    return {
        "data": data,
        "date_range": date_range,
        "total_records": len(data)
    }


def load_daily_summary(start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """Load daily summary data"""
    # Load all data
    grid_df = loader.load_grid_data(config)
    solar_df = loader.load_solar_data(config)
    diesel_df = loader.load_diesel_data(config)

    # Keep rolling 7-day alignment only when date range is not explicitly set.
    if _use_rolling_window(start_date, end_date):
        allowed_dates = _get_last7_solar_date_set()
        grid_df = _filter_to_date_set(grid_df, allowed_dates)
        solar_df = _filter_to_date_set(solar_df, allowed_dates)
        diesel_df = _filter_to_date_set(diesel_df, allowed_dates)

    # Build unified dataframe
    unified_df = processor.build_unified_dataframe(grid_df, solar_df, diesel_df)

    # Compute daily summary
    if hasattr(processor, "compute_daily_summary"):
        daily_df = processor.compute_daily_summary(unified_df)
    else:
        daily_df = _compute_daily_summary_fallback(unified_df)

    # Filter by date if provided
    if start_date or end_date:
        daily_df['Date'] = pd.to_datetime(daily_df['Date'])
        if start_date:
            daily_df = daily_df[daily_df['Date'] >= pd.to_datetime(start_date)]
        if end_date:
            daily_df = daily_df[daily_df['Date'] <= pd.to_datetime(end_date)]
        daily_df['Date'] = daily_df['Date'].dt.strftime('%Y-%m-%d')

    all_dates = pd.to_datetime(daily_df['Date'])
    date_range = {
        "min_date": all_dates.min().strftime('%Y-%m-%d') if len(all_dates) > 0 else None,
        "max_date": all_dates.max().strftime('%Y-%m-%d') if len(all_dates) > 0 else None
    }

    data = daily_df.to_dict('records')

    return {
        "data": data,
        "date_range": date_range,
        "total_records": len(data)
    }


def compute_overview_kpis(start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """Compute overview KPIs"""
    # Load all data
    grid_df = loader.load_grid_data(config)
    solar_df = loader.load_solar_data(config)
    diesel_df = loader.load_diesel_data(config)

    # Keep rolling 7-day alignment only when date range is not explicitly set.
    if _use_rolling_window(start_date, end_date):
        allowed_dates = _get_last7_solar_date_set()
        grid_df = _filter_to_date_set(grid_df, allowed_dates)
        solar_df = _filter_to_date_set(solar_df, allowed_dates)
        diesel_df = _filter_to_date_set(diesel_df, allowed_dates)

    # Build unified dataframe
    unified_df = processor.build_unified_dataframe(grid_df, solar_df, diesel_df)

    # Filter by date if provided
    if start_date or end_date:
        unified_df['Date'] = pd.to_datetime(unified_df['Date'])
        if start_date:
            unified_df = unified_df[unified_df['Date'] >= pd.to_datetime(start_date)]
        if end_date:
            unified_df = unified_df[unified_df['Date'] <= pd.to_datetime(end_date)]

    # Compute KPIs - pass config parameter
    kpis = processor.compute_overview_kpis(unified_df, config)

    # Add smart LLM-backed summary for dashboard cards based on current day (2026-03-22)
    if generate_smart_summary:
        summary = generate_smart_summary(unified_df, kpis, current_date="2026-03-22")
        kpis["insights"] = summary.get("insights", [])
        kpis["recommendations"] = summary.get("recommendations", [])
        kpis["insights_source"] = summary.get("source", "fallback")
    else:
        kpis["insights"] = []
        kpis["recommendations"] = []
        kpis["insights_source"] = "disabled"

    return kpis
