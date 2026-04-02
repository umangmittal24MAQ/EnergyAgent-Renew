"""
KPI endpoints router
"""
from fastapi import APIRouter, Query
from typing import Optional
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from app.core.config_legacy import GRID_COST_PER_UNIT, DIESEL_COST_PER_UNIT, SOLAR_TARGET_PERCENTAGE
from app.services.google_sheets_data_service import get_service as get_gs_service

try:
    from mail_scheduling_agent.emailer import generate_smart_summary
except ImportError:
    mail_agent_path = Path(__file__).resolve().parents[2] / "energy-dashboard"
    if mail_agent_path.exists() and str(mail_agent_path) not in sys.path:
        sys.path.append(str(mail_agent_path))
    try:
        from mail_scheduling_agent.emailer import generate_smart_summary
    except ImportError:
        generate_smart_summary = None


def convert_numpy_types(obj):
    """Convert numpy types to Python native types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {key: convert_numpy_types(val) for key, val in obj.items()}
    if isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    return obj


router = APIRouter(prefix="/api/kpis", tags=["kpis"])


def _as_number(row: pd.Series, keys: list[str]) -> float:
    for key in keys:
        if key in row and row[key] is not None and str(row[key]).strip() != "":
            try:
                return float(row[key])
            except (TypeError, ValueError):
                continue
    return 0.0


def _sum_column(df: pd.DataFrame, keys: list[str]) -> float:
    for key in keys:
        if key in df.columns:
            return float(pd.to_numeric(df[key], errors="coerce").fillna(0).sum())
    return 0.0


def _first_existing_col(df: pd.DataFrame, keys: list[str]) -> Optional[str]:
    for key in keys:
        if key in df.columns:
            return key
    return None


def _max_column(df: pd.DataFrame, keys: list[str]) -> float:
    for key in keys:
        if key in df.columns:
            return float(pd.to_numeric(df[key], errors="coerce").fillna(0).max())
    return 0.0


def _mean_column(df: pd.DataFrame, keys: list[str]) -> float:
    for key in keys:
        if key in df.columns:
            return float(pd.to_numeric(df[key], errors="coerce").fillna(0).mean())
    return 0.0


def _get_live_unified_df(start_date: Optional[str], end_date: Optional[str]) -> pd.DataFrame:
    gs_service = get_gs_service()
    if not gs_service.is_authenticated():
        return pd.DataFrame()

    df = gs_service.get_unified_solar_data()
    if df is None or df.empty:
        return pd.DataFrame()

    df = gs_service.filter_by_date_range(df, start_date, end_date)
    return df


def _get_live_report_df(start_date: Optional[str], end_date: Optional[str]) -> pd.DataFrame:
    """Load normalized daily rows used by the Overview detailed report."""
    try:
        from .data import _build_live_report_rows

        rows = _build_live_report_rows(start_date, end_date)
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()


def _prepare_summary_input_df(df: pd.DataFrame) -> pd.DataFrame:
    """Create compatibility columns expected by the smart-summary generator."""
    if df is None or df.empty:
        return pd.DataFrame()

    working = df.copy()

    grid_source = _first_existing_col(
        working,
        [
            "Grid KWh",
            "Grid Units Consumed (kWh)",
            "Grid Units Consumed (KWh)",
            "Day Import (kWh)",
            "Total Import (kWh)",
            "Total_Import_kWh",
        ],
    )
    if grid_source:
        working["Grid KWh"] = pd.to_numeric(working[grid_source], errors="coerce").fillna(0)

    solar_source = _first_existing_col(
        working,
        [
            "Solar KWh",
            "Solar Units Consumed (kWh)",
            "Solar Units Consumed (KWh)",
            "Solar Units Generated (KWh)",
            "Day Generation (kWh)",
            "Total Generation (kWh)",
        ],
    )
    if solar_source:
        working["Solar KWh"] = pd.to_numeric(working[solar_source], errors="coerce").fillna(0)

    if "Total KWh" not in working.columns:
        working["Total KWh"] = pd.to_numeric(working.get("Grid KWh", 0), errors="coerce").fillna(0) + pd.to_numeric(
            working.get("Solar KWh", 0),
            errors="coerce",
        ).fillna(0)

    diesel_source = _first_existing_col(
        working,
        [
            "Diesel consumed",
            "Diesel Consumed (Litres)",
            "Fuel Consumed (Litres)",
            "DG Units Consumed (KWh)",
            "Diesel KWh",
        ],
    )
    if diesel_source:
        working["Diesel consumed"] = pd.to_numeric(working[diesel_source], errors="coerce").fillna(0)
    elif "Diesel consumed" not in working.columns:
        working["Diesel consumed"] = 0.0

    return working


@router.get("/overview")
async def get_overview_kpis(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get overview KPIs computed from live Google Sheets unified data."""
    df = _get_live_unified_df(start_date, end_date)
    if df.empty:
        return {
            "total_energy_kwh": 0.0,
            "total_grid_kwh": 0.0,
            "total_solar_kwh": 0.0,
            "total_diesel_kwh": 0.0,
            "total_cost_inr": 0.0,
            "solar_contribution_pct": 0.0,
            "insights": [],
            "recommendations": [],
            "insights_source": "live_sheets",
        }

    total_grid = _sum_column(df, ["Grid KWh", "Grid Units Consumed (KWh)", "Total_Import_kWh", "Total Import (kWh)"])
    total_solar = _sum_column(df, ["Solar KWh", "Solar Units Generated (KWh)", "Day_Generation_kWh", "Day Generation (kWh)", "Total Generation (kWh)"])
    total_diesel = _sum_column(df, ["Diesel KWh", "DG Units Consumed (KWh)"])

    total_energy = _sum_column(df, ["Total KWh", "Total Units Consumed (KWh)"])
    if total_energy <= 0:
        total_energy = total_grid + total_solar + total_diesel

    total_cost = _sum_column(df, ["Total Cost (INR)", "Total Units Consumed in INR", "Total Cost"])
    if total_cost <= 0:
        total_cost = (total_grid * float(GRID_COST_PER_UNIT)) + (total_diesel * float(DIESEL_COST_PER_UNIT))

    solar_pct = (total_solar / total_energy * 100.0) if total_energy > 0 else 0.0

    kpis = {
        "total_energy_kwh": total_energy,
        "total_grid_kwh": total_grid,
        "total_solar_kwh": total_solar,
        "total_diesel_kwh": total_diesel,
        "total_cost_inr": total_cost,
        "solar_contribution_pct": solar_pct,
        "insights": [
            f"Solar contributed {solar_pct:.1f}% of total energy in the selected period",
            f"Grid dependency is {max(0.0, 100.0 - solar_pct):.1f}% based on live sheet rows",
        ],
        "recommendations": [
            "Increase high-irradiance hour utilization to improve solar contribution",
            "Monitor import spikes using Timestamp and Total_Import_kWh trend",
        ],
        "insights_source": "live_sheets",
        "solar_target_pct": float(SOLAR_TARGET_PERCENTAGE),
    }

    if generate_smart_summary:
        summary_df = _get_live_report_df(start_date, end_date)
        if summary_df.empty:
            summary_df = df.copy()
        summary_df = _prepare_summary_input_df(summary_df)

        current_date = None
        if "Date" in summary_df.columns and len(summary_df) > 0:
            try:
                parsed_dates = pd.to_datetime(summary_df["Date"], errors="coerce").dropna()
                if len(parsed_dates) > 0:
                    current_date = parsed_dates.max().strftime("%Y-%m-%d")
            except Exception:
                current_date = None

        try:
            summary = generate_smart_summary(summary_df, kpis, current_date=current_date)
            if summary:
                kpis["insights"] = summary.get("insights", kpis["insights"])
                kpis["recommendations"] = summary.get("recommendations", kpis["recommendations"])
                kpis["insights_source"] = summary.get("source", "llm")
        except Exception:
            kpis["insights_source"] = "llm_fallback"

    return convert_numpy_types(kpis)


@router.get("/grid")
async def get_grid_kpis(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get grid-specific KPIs from live Google Sheets unified rows."""
    df = _get_live_unified_df(start_date, end_date)
    if df.empty:
        return {
            "total_grid_kwh": 0,
            "avg_grid_kwh": 0,
            "peak_grid_kwh": 0,
            "total_grid_cost": 0
        }

    total_grid = _sum_column(df, ["Grid Units Consumed (KWh)", "Grid KWh", "Total_Import_kWh", "Total Import (kWh)"])
    avg_grid = _mean_column(df, ["Grid Units Consumed (KWh)", "Grid KWh", "Total_Import_kWh", "Total Import (kWh)"])
    peak_grid = _max_column(df, ["Grid Units Consumed (KWh)", "Grid KWh", "Total_Import_kWh", "Total Import (kWh)"])
    total_grid_cost = _sum_column(df, ["Grid Cost (INR)", "Total Units Consumed in INR", "Total Cost (INR)"])
    if total_grid_cost <= 0:
        total_grid_cost = total_grid * float(GRID_COST_PER_UNIT)

    result = {
        "total_grid_kwh": float(total_grid),
        "avg_grid_kwh": float(avg_grid),
        "peak_grid_kwh": float(peak_grid),
        "total_grid_cost": float(total_grid_cost)
    }
    return result


@router.get("/solar")
async def get_solar_kpis(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get solar-specific KPIs with inverter status from live sheets."""
    gs_service = get_gs_service()
    solar_df = _get_live_unified_df(start_date, end_date)
    smb_df = gs_service.get_smb_status_data() if gs_service.is_authenticated() else pd.DataFrame()
    if smb_df is not None and not smb_df.empty:
        smb_df = gs_service.filter_by_date_range(smb_df, start_date, end_date)

    if solar_df.empty:
        return {
            "total_solar_kwh": 0,
            "avg_solar_kwh": 0,
            "peak_solar_kwh": 0,
            "solar_target_pct": 25.0,
            "actual_solar_pct": 0,
            "energy_saved": 0,
            "inverter_faults": 0,
            "weekly_trend": [],
        }

    total_solar = _sum_column(solar_df, ["Generation (kWh)", "Solar Units Generated (KWh)", "Solar KWh", "Day_Generation_kWh", "Day Generation (kWh)", "Total Generation (kWh)"])
    energy_saved = float(total_solar * float(GRID_COST_PER_UNIT))

    inverter_faults = 0
    if smb_df is not None and not smb_df.empty and "Inverter Status" in smb_df.columns:
        status_series = smb_df["Inverter Status"].fillna("").astype(str).str.lower()
        inverter_faults = int(status_series.str.contains("fault").sum())

    if "Date" in solar_df.columns:
        value_col = _first_existing_col(
            solar_df,
            [
                "Day_Generation_kWh",
                "Day Generation (kWh)",
                "Solar KWh",
                "Solar Units Generated (KWh)",
                "Generation (kWh)",
            ],
        )
        if value_col is None:
            weekly_trend = []
        else:
            trend_df = solar_df[["Date", value_col]].copy()
            trend_df["Date"] = pd.to_datetime(trend_df["Date"], errors="coerce")
            trend_df = trend_df.sort_values("Date")
            trend_df["Day"] = trend_df["Date"].dt.day_name()
            trend_df["Date"] = trend_df["Date"].dt.strftime("%Y-%m-%d")
            trend_df["Generation"] = pd.to_numeric(trend_df[value_col], errors="coerce").fillna(0)
            weekly_trend = trend_df[["Date", "Day", "Generation"]].to_dict("records")
    else:
        weekly_trend = []

    return {
        "total_solar_kwh": total_solar,
        "avg_solar_kwh": _mean_column(solar_df, ["Generation (kWh)", "Solar Units Generated (KWh)", "Solar KWh", "Day_Generation_kWh", "Day Generation (kWh)", "Total Generation (kWh)"]),
        "peak_solar_kwh": _max_column(solar_df, ["Generation (kWh)", "Solar Units Generated (KWh)", "Solar KWh", "Day_Generation_kWh", "Day Generation (kWh)", "Total Generation (kWh)"]),
        "solar_target_pct": float(SOLAR_TARGET_PERCENTAGE),
        "actual_solar_pct": 0.0,  # Would need unified data
        "energy_saved": energy_saved,
        "inverter_faults": inverter_faults,
        "weekly_trend": weekly_trend,
    }


@router.get("/diesel")
async def get_diesel_kpis(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get diesel generator KPIs from live Google Sheets unified rows."""
    df = _get_live_unified_df(start_date, end_date)
    if df.empty:
        return {
            "total_diesel_kwh": 0,
            "total_runtime": 0,
            "total_fuel": 0,
            "total_diesel_cost": 0
        }

    total_diesel_kwh = _sum_column(df, ["DG Units Consumed (KWh)", "Diesel KWh"])
    total_runtime = _sum_column(df, ["DG Runtime (hrs)"])
    total_fuel = _sum_column(df, ["Diesel consumed", "Fuel Consumed (Litres)"])
    total_diesel_cost = _sum_column(df, ["Diesel Cost (INR)", "Total Cost (INR)"])
    if total_diesel_cost <= 0:
        total_diesel_cost = total_diesel_kwh * float(DIESEL_COST_PER_UNIT)

    return {
        "total_diesel_kwh": float(total_diesel_kwh),
        "total_runtime": float(total_runtime),
        "total_fuel": float(total_fuel),
        "total_diesel_cost": float(total_diesel_cost)
    }
