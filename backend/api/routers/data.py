"""
Data endpoints router
Provides ingestion-backed data and refresh controls.
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Dict, Any
import pandas as pd
from datetime import datetime
import json
from pathlib import Path
from ..services import data_service
from ..services.google_sheets_data_service import get_service as get_gs_service
from ..services.cache_service import get_cache
from ..services.ingestion_bridge import run_ingestion_once, run_inverter_backfill_once
from ..schemas.energy import EnergyDataResponse

router = APIRouter(prefix="/api/data", tags=["data"])


def _to_float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(",", "").strip())
    except (ValueError, TypeError):
        text = str(value)
        match = pd.Series([text]).str.extract(r"([-+]?\d*\.?\d+)")[0].iloc[0]
        try:
            return float(match) if pd.notna(match) else 0.0
        except (ValueError, TypeError):
            return 0.0


def _parse_row_datetime(row: Dict[str, Any]) -> Optional[datetime]:
    ts = row.get("Timestamp")
    if ts:
        parsed = pd.to_datetime(ts, errors="coerce")
        if pd.notna(parsed):
            return parsed.to_pydatetime()

    date_val = row.get("Date")
    time_val = row.get("Time")
    if date_val and time_val:
        parsed = pd.to_datetime(f"{date_val} {time_val}", errors="coerce")
        if pd.notna(parsed):
            return parsed.to_pydatetime()
    if date_val:
        parsed = pd.to_datetime(date_val, errors="coerce")
        if pd.notna(parsed):
            return parsed.to_pydatetime()
    return None


def _pick_first(row: Dict[str, Any], keys: list[str], default: Any = "") -> Any:
    for key in keys:
        if key in row and row.get(key) not in (None, ""):
            return row.get(key)
    return default


def _pick_first_with_key(row: Dict[str, Any], keys: list[str]) -> tuple[str, Any]:
    for key in keys:
        if key in row and row.get(key) not in (None, ""):
            return key, row.get(key)
    return "", None


def _to_kwh(value: Any, source_key: str = "") -> float:
    number = _to_float(value)
    key = str(source_key or "").lower()
    # Convert Wh values to kWh when source field is explicitly in Wh.
    if "wh" in key and "kwh" not in key:
        return number / 1000.0
    return number


def _clean_text_or_number(value: Any, default: str = "") -> Any:
    if value in (None, ""):
        return default
    text = str(value).strip()
    if not text:
        return default
    match = pd.Series([text]).str.extract(r"([-+]?\d*\.?\d+)")[0].iloc[0]
    if pd.notna(match):
        parsed = _to_float(match)
        if abs(parsed - round(parsed)) < 1e-9:
            return int(round(parsed))
        return round(parsed, 2)
    return text


def _to_report_row(row: Dict[str, Any]) -> Dict[str, Any]:
    parsed_dt = _parse_row_datetime(row)

    if parsed_dt:
        date_key = parsed_dt.strftime("%Y-%m-%d")
        display_date = parsed_dt.strftime("%d/%m/%Y")
        default_day = parsed_dt.strftime("%A")
        default_time = parsed_dt.strftime("%H:%M:%S")
        sort_timestamp = parsed_dt.isoformat()
    else:
        date_key = str(_pick_first(row, ["Date", "date", "Timestamp", "timestamp"], "")).strip()[:10]
        parsed_fallback = pd.to_datetime(date_key, errors="coerce")
        display_date = parsed_fallback.strftime("%d/%m/%Y") if pd.notna(parsed_fallback) else str(date_key)
        default_day = parsed_fallback.strftime("%A") if pd.notna(parsed_fallback) else ""
        default_time = "00:00:00"
        sort_timestamp = f"{date_key}T00:00:00"

    day_text = str(_pick_first(row, ["Day", "day"], default_day)).strip() or default_day
    time_text = str(_pick_first(row, ["Time", "time"], default_time)).strip() or default_time

    ambient_raw = _pick_first(
        row,
        [
            "Ambient Temperature (°C)",
            "Ambient Temperature °C",
            "Ambient Temperature (C)",
            "Ambient Temperature",
            "Ambient Temp (°C)",
            "Ambient Temp (C)",
            "Ambient Temp",
            "Temperature (°C)",
            "Temperature",
            "ambient_temp",
            "temp",
        ],
        "",
    )
    ambient_temperature = (
        str(ambient_raw).strip() if ambient_raw not in (None, "") else ""
    )

    grid_key, grid_raw = _pick_first_with_key(
        row,
        [
            "Grid Units Consumed (KWh)",
            "Grid Units Consumed (kWh)",
            "Grid KWh",
            "Total_Import_kWh",
            "Day Import (kWh)",
            "Total Import (kWh)",
        ],
    )
    grid_kwh = _to_kwh(grid_raw, grid_key)

    solar_key, solar_raw = _pick_first_with_key(
        row,
        [
            "Solar Units Consumed(KWh)",
            "Solar Units Consumed (KWh)",
            "Solar Units Consumed (kWh)",
            "Solar Units Generated (KWh)",
            "Solar Units Generated (kWh)",
            "Solar KWh",
            "Day Generation (kWh)",
            "Generation (Wh)",
            "Total Generation (Wh)",
        ],
    )
    solar_kwh = _to_kwh(solar_raw, solar_key)

    total_units = _to_float(
        _pick_first(
            row,
            [
                "Total Units Consumed (KWh)",
                "Total Units Consumed (kWh)",
                "Total KWh",
            ],
            0,
        )
    )
    if total_units <= 0:
        total_units = grid_kwh + solar_kwh

    total_cost_inr = _to_float(
        _pick_first(
            row,
            [
                "Total Cost (INR)",
                "Total Units Consumed in INR",
            ],
            0,
        )
    )
    if total_cost_inr <= 0:
        total_cost_inr = round(total_units * 7.11, 2)

    solar_savings_inr = _to_float(
        _pick_first(
            row,
            [
                "Solar Cost Savings (INR)",
                "solar cost savings (INR)",
                "Energy Saving (INR)",
                "Energy Saving in INR",
            ],
            0,
        )
    )
    if solar_savings_inr <= 0:
        solar_savings_inr = round(solar_kwh * 7.11, 2)

    panels_cleaned = _clean_text_or_number(
        _pick_first(row, ["Panels Cleaned", "Number of Panels Cleaned", "number_of_panels_cleaned"], "0"),
        default="0",
    )

    diesel_consumed = _clean_text_or_number(
        _pick_first(
            row,
            [
                "Diesel Consumed (Litres)",
                "Diesel consumed",
                "Diesel Consumed",
                "diesel consumed",
                "diesel_litres",
                "diesel litres",
                "DG Consumed",
                "Fuel Consumed (Litres)",
                "Fuel Consumed",
                "Diesel",
            ],
            "",
        ),
        default="",
    )

    water_stp = _clean_text_or_number(
        _pick_first(
            row,
            [
                "Water Treated through STP (kilo Litres)",
                "Water treated through STP (kilo Litres)",
                "Water treated through STP",
                "STP",
            ],
            "0",
        ),
        default="0",
    )

    water_wtp = _clean_text_or_number(
        _pick_first(
            row,
            [
                "Water Treated through WTP (kilo Litres)",
                "Water treated through WTP (kilo Litres)",
                "Water treated through WTP",
                "WTP",
            ],
            "0",
        ),
        default="0",
    )

    issues = str(_pick_first(row, ["Issues", "Issue", "issues"], "no issues")).strip() or "no issues"

    inv_1 = _pick_first(
        row,
        ["INV_1", "inv_1", "Inv_1", "Inverter_1", "inverter_1", "Inverter 1"],
        "",
    )
    inv_2 = _pick_first(
        row,
        ["INV_2", "inv_2", "Inv_2", "Inverter_2", "inverter_2", "Inverter 2"],
        "",
    )
    inv_3 = _pick_first(
        row,
        ["INV_3", "inv_3", "Inv_3", "Inverter_3", "inverter_3", "Inverter 3"],
        "",
    )
    inv_4 = _pick_first(
        row,
        ["INV_4", "inv_4", "Inv_4", "Inverter_4", "inverter_4", "Inverter 4"],
        "",
    )
    inv_5 = _pick_first(
        row,
        ["INV_5", "inv_5", "Inv_5", "Inverter_5", "inverter_5", "Inverter 5"],
        "",
    )

    return {
        "Date": display_date,
        "Day": day_text,
        "Time": time_text,
        "Ambient Temperature (°C)": ambient_temperature,
        "Grid Units Consumed (kWh)": round(grid_kwh, 3),
        "Solar Units Consumed (kWh)": round(solar_kwh, 3),
        "Total Units Consumed (kWh)": round(total_units, 3),
        "Total Cost (INR)": round(total_cost_inr, 2),
        "Solar Cost Savings (INR)": round(solar_savings_inr, 2),
        "Panels Cleaned": panels_cleaned,
        "Diesel Consumed (Litres)": diesel_consumed,
        "Water Treated through STP (kilo Litres)": water_stp,
        "Water Treated through WTP (kilo Litres)": water_wtp,
        "Issues": issues,
        "INV_1": inv_1,
        "INV_2": inv_2,
        "INV_3": inv_3,
        "INV_4": inv_4,
        "INV_5": inv_5,
        "_date_key": date_key,
        "_sort_ts": sort_timestamp,
    }


def _row_quality_score(report_row: Dict[str, Any]) -> float:
    score = 0.0
    if _to_float(report_row.get("Grid Units Consumed (kWh)")) > 0:
        score += 100.0
    if str(report_row.get("Day", "")).strip():
        score += 10.0

    time_text = str(report_row.get("Time", "")).strip()
    if time_text not in ("", "0", "0:00", "00:00", "00:00:00"):
        score += 5.0

    if str(report_row.get("Panels Cleaned", "")).strip() not in ("", "0"):
        score += 2.0
    if str(report_row.get("Water Treated through STP (kilo Litres)", "")).strip() not in ("", "0"):
        score += 2.0
    if str(report_row.get("Water Treated through WTP (kilo Litres)", "")).strip() not in ("", "0"):
        score += 2.0
    if str(report_row.get("Issues", "")).strip().lower() not in ("", "no issues"):
        score += 1.0

    return score


def _build_live_report_rows(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> list[Dict[str, Any]]:
    gs_service = get_gs_service()
    if not gs_service.is_authenticated():
        return []

    # Prefer raw master_data rows so values like "10-20" remain intact.
    df = gs_service.fetch_sheet_data("master_data")
    if df is None or df.empty:
        df = gs_service.get_master_data()
    if df is None or df.empty:
        df = gs_service.get_grid_and_diesel_data()
    if df is None or df.empty:
        return []

    filtered_df = gs_service.filter_by_date_range(df, start_date, end_date)
    records = filtered_df.fillna("").to_dict("records")

    best_by_date: Dict[str, Dict[str, Any]] = {}
    score_by_date: Dict[str, float] = {}

    for row in records:
        report_row = _to_report_row(row)
        date_key = str(report_row.get("_date_key") or "")
        if not date_key:
            continue

        score = _row_quality_score(report_row)
        if date_key not in best_by_date or score > score_by_date.get(date_key, -1.0):
            best_by_date[date_key] = report_row
            score_by_date[date_key] = score

    ordered = sorted(
        best_by_date.values(),
        key=lambda item: str(item.get("_sort_ts") or item.get("_date_key") or ""),
        reverse=True,
    )

    cleaned_rows = []
    for row in ordered:
        item = dict(row)
        item.pop("_date_key", None)
        item.pop("_sort_ts", None)
        cleaned_rows.append(item)

    return cleaned_rows


def _frontend_unified_row(row: Dict[str, Any]) -> Dict[str, Any]:
    parsed_dt = _parse_row_datetime(row)
    if parsed_dt:
        date_text = parsed_dt.strftime("%Y-%m-%d")
        time_text = parsed_dt.strftime("%H:%M:%S")
        day_text = parsed_dt.strftime("%A")
        timestamp_text = parsed_dt.isoformat()
    else:
        date_text = str(row.get("Date") or "")
        time_text = str(row.get("Time") or "00:00:00")
        day_text = row.get("Day") or ""
        timestamp_text = str(row.get("Timestamp") or "")

    grid_kwh = _to_float(
        row.get("Day Import (kWh)")
        or row.get("Total Import (kWh)")
        or row.get("Grid Units Consumed (KWh)")
        or row.get("Grid KWh")
    )
    solar_kwh = _to_float(
        row.get("Day Generation (kWh)")
        or row.get("Solar Units Generated (KWh)")
        or row.get("Solar KWh")
    )
    diesel_kwh = _to_float(
        row.get("DG Units Consumed (KWh)")
        or row.get("Diesel Units Consumed (KWh)")
        or row.get("Diesel KWh")
        or row.get("Diesel consumed")
        or row.get("diesel consumed")
        or row.get("diesel_consumed")
    )
    explicit_total_kwh = _to_float(
        row.get("Total Units Consumed (KWh)")
        or row.get("Total KWh")
    )
    total_kwh = explicit_total_kwh if explicit_total_kwh > 0 else (grid_kwh + solar_kwh + diesel_kwh)

    return {
        "Date": date_text,
        "Day": day_text,
        "Time": time_text,
        "Timestamp": timestamp_text,
        "Date Formatted": row.get("Date Formatted") or date_text,
        "Grid Units Consumed (KWh)": grid_kwh,
        "Solar Units Generated (KWh)": solar_kwh,
        "DG Units Consumed (KWh)": diesel_kwh,
        "Fuel Consumed (Litres)": diesel_kwh,
        "Total Units Consumed (KWh)": total_kwh,
        "Grid KWh": grid_kwh,
        "Solar KWh": solar_kwh,
        "Total KWh": total_kwh,
        "Total Units Consumed in INR": _to_float(
            row.get("Total Units Consumed in INR") or row.get("Total Cost (INR)")
        ),
        "Grid Cost (INR)": _to_float(row.get("Grid Cost (INR)")),
        "Diesel Cost (INR)": _to_float(row.get("Diesel Cost (INR)")),
        "Total Cost (INR)": _to_float(
            row.get("Total Cost (INR)") or row.get("Total Units Consumed in INR")
        ),
        "Energy Saving (INR)": _to_float(
            row.get("Energy Saving (INR)")
            or row.get("Energy Saving in INR")
            or row.get("Energy Saved (INR)")
        ),
        "Inverter Status": row.get("Inverter Status") or "All Online",
        "DC_Power_kW": _to_float(row.get("DC Power (kW)")),
        "AC_Power_kW": _to_float(row.get("AC Power (kW)")),
        "Current_Total_A": _to_float(row.get("Current Total (A)")),
        "Current_Average_A": _to_float(row.get("Current Average (A)")),
        "Active_Power_kW": _to_float(row.get("Active Power (kW)")),
        "Power_Factor": _to_float(row.get("Power Factor")),
        "Frequency_Hz": _to_float(row.get("Frequency (Hz)")),
        "Voltage_VLL": _to_float(row.get("Voltage Phase-to-Phase (V)")),
        "Voltage_VLN": _to_float(row.get("Voltage Phase-to-Neutral (V)")),
        "V1": _to_float(row.get("V1 (V)")),
        "V2": _to_float(row.get("V2 (V)")),
        "V3": _to_float(row.get("V3 (V)")),
        "Day_Generation_kWh": solar_kwh,
        "Total_Import_kWh": _to_float(row.get("Total Import (kWh)")),
        "Total_Export_kWh": _to_float(row.get("Total Export (kWh)")),
        "DC_Capacity_kWp": _to_float(row.get("DC Capacity (kWp)")),
        "AC_Capacity_kW": _to_float(row.get("AC Capacity (kW)")),
    }


def _frontend_last_7_row(row: Dict[str, Any]) -> Dict[str, Any]:
    parsed = pd.to_datetime(row.get("Date"), errors="coerce")
    date_text = parsed.strftime("%Y-%m-%d") if pd.notna(parsed) else str(row.get("Date") or "")
    day_text = parsed.strftime("%A") if pd.notna(parsed) else ""
    generation_wh = _to_float(row.get("Generation (Wh)"))
    return {
        "Date": date_text,
        "Day": day_text,
        "Date Formatted": row.get("Date Formatted") or date_text,
        "Start Value": _to_float(row.get("Start Value")),
        "End Value": _to_float(row.get("End Value")),
        "Generation (Wh)": generation_wh,
        "Total Generation (Wh)": generation_wh,
        "Total Generation (kWh)": round(generation_wh / 1000.0, 3),
    }


def _frontend_smb_row(row: Dict[str, Any]) -> Dict[str, Any]:
    date_raw = row.get("Date")
    date_only = pd.to_datetime(date_raw, errors="coerce")
    normalized_date = date_only.strftime("%Y-%m-%d") if pd.notna(date_only) else str(date_raw or "")

    parsed = pd.to_datetime(f"{normalized_date} {row.get('Time', '00:00:00')}", errors="coerce")
    timestamp_text = parsed.isoformat() if pd.notna(parsed) else ""
    date_text = normalized_date or (parsed.strftime("%Y-%m-%d") if pd.notna(parsed) else "")
    day_text = row.get("Day") or (parsed.strftime("%A") if pd.notna(parsed) else "")
    return {
        "Date": date_text,
        "Day": day_text,
        "Time": row.get("Time") or "00:00:00",
        "Timestamp": timestamp_text,
        "SMB1 (kW)": _to_float(row.get("SMB1") or row.get("SMB1 (kW)")),
        "SMB2 (kW)": _to_float(row.get("SMB2") or row.get("SMB2 (kW)")),
        "SMB3 (kW)": _to_float(row.get("SMB3") or row.get("SMB3 (kW)")),
        "SMB4 (kW)": _to_float(row.get("SMB4") or row.get("SMB4 (kW)")),
        "SMB5 (kW)": _to_float(row.get("SMB5") or row.get("SMB5 (kW)")),
        "SMB1 Status": row.get("SMB1_status") or row.get("SMB1 Status") or "UNKNOWN",
        "SMB2 Status": row.get("SMB2_status") or row.get("SMB2 Status") or "UNKNOWN",
        "SMB3 Status": row.get("SMB3_status") or row.get("SMB3 Status") or "UNKNOWN",
        "SMB4 Status": row.get("SMB4_status") or row.get("SMB4 Status") or "UNKNOWN",
        "SMB5 Status": row.get("SMB5_status") or row.get("SMB5 Status") or "UNKNOWN",
    }


def _date_range_from_rows(rows: list[Dict[str, Any]]) -> Dict[str, Optional[str]]:
    if not rows:
        return {"min_date": None, "max_date": None}
    all_dates = pd.to_datetime(
        [r.get("Date") or r.get("Timestamp") for r in rows],
        errors="coerce",
        dayfirst=True,
    )
    valid = all_dates.dropna()
    if len(valid) == 0:
        return {"min_date": None, "max_date": None}
    return {
        "min_date": valid.min().strftime("%Y-%m-%d"),
        "max_date": valid.max().strftime("%Y-%m-%d"),
    }


def _load_filtered_solar_panel_json() -> Dict[str, Any]:
    ingestion_path = (
        Path(__file__).resolve().parent.parent.parent
        / "energy-dashboard"
        / "Ingestion-agent"
        / "filtered_solar_panel_data.json"
    )
    if not ingestion_path.exists():
        return {}
    try:
        return json.loads(ingestion_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _get_live_unified_rows(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> list[Dict[str, Any]]:
    """Load unified live rows from Google Sheets and normalize for frontend."""
    gs_service = get_gs_service()
    if not gs_service.is_authenticated():
        return []

    df = gs_service.get_unified_solar_data()
    if df is None or df.empty:
        return []

    filtered_df = gs_service.filter_by_date_range(df, start_date, end_date)
    return [_frontend_unified_row(row) for row in filtered_df.to_dict("records")]


def _build_daily_summary_from_rows(rows: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """Aggregate live unified rows into daily summary rows."""
    grouped: Dict[str, Dict[str, Any]] = {}

    for row in rows:
        date_key = str(row.get("Date") or "")
        if not date_key:
            continue

        if date_key not in grouped:
            grouped[date_key] = {
                "Date": date_key,
                "Grid Units Consumed (KWh)": 0.0,
                "Solar Units Generated (KWh)": 0.0,
                "DG Units Consumed (KWh)": 0.0,
                "Total Units Consumed (KWh)": 0.0,
                "Total Units Consumed in INR": 0.0,
                "Energy Saving (INR)": 0.0,
            }

        day = grouped[date_key]
        day["Grid Units Consumed (KWh)"] += _to_float(row.get("Grid Units Consumed (KWh)"))
        day["Solar Units Generated (KWh)"] += _to_float(row.get("Solar Units Generated (KWh)"))
        day["DG Units Consumed (KWh)"] += _to_float(row.get("DG Units Consumed (KWh)"))
        day["Total Units Consumed (KWh)"] += _to_float(row.get("Total Units Consumed (KWh)"))
        day["Total Units Consumed in INR"] += _to_float(row.get("Total Units Consumed in INR"))
        day["Energy Saving (INR)"] += _to_float(row.get("Energy Saving (INR)"))

    return [grouped[k] for k in sorted(grouped.keys())]


@router.get("/unified", response_model=EnergyDataResponse)
async def get_unified_data(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get unified energy data (grid + solar + diesel)"""
    return data_service.load_unified_data(start_date, end_date)


@router.get("/grid", response_model=EnergyDataResponse)
async def get_grid_data(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get grid energy data"""
    return data_service.load_grid_data(start_date, end_date)


@router.get("/solar", response_model=EnergyDataResponse)
async def get_solar_data(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get solar energy data with SMB breakdown"""
    return data_service.load_solar_data(start_date, end_date)


@router.get("/diesel", response_model=EnergyDataResponse)
async def get_diesel_data(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get diesel generator data"""
    return data_service.load_diesel_data(start_date, end_date)


@router.get("/daily-summary", response_model=EnergyDataResponse)
async def get_daily_summary(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get daily aggregated summary"""
    return data_service.load_daily_summary(start_date, end_date)


@router.get("/live/unified", response_model=EnergyDataResponse)
async def get_live_unified_data(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get live unified data normalized to email-report-ready rows."""
    frontend_rows = _build_live_report_rows(start_date, end_date)

    return {
        "data": frontend_rows,
        "date_range": _date_range_from_rows(frontend_rows),
        "total_records": len(frontend_rows),
    }


@router.get("/live/solar", response_model=EnergyDataResponse)
async def get_live_solar_data(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: Optional[int] = Query(None, description="Maximum number of records to return")
):
    """Get live solar rows directly from Google Sheets with timestamp filtering."""
    gs_service = get_gs_service()
    if not gs_service.is_authenticated():
        return {
            "data": [],
            "date_range": {"min_date": None, "max_date": None},
            "total_records": 0,
        }

    df = gs_service.get_unified_solar_data()
    if df is None or df.empty:
        return {
            "data": [],
            "date_range": {"min_date": None, "max_date": None},
            "total_records": 0,
        }

    filtered_df = gs_service.filter_by_date_range(df, start_date, end_date)

    date_col = "Timestamp" if "Timestamp" in filtered_df.columns else "Date"
    all_dates = (
        pd.to_datetime(filtered_df[date_col], errors="coerce")
        if date_col in filtered_df.columns
        else pd.Series(dtype="datetime64[ns]")
    )

    frontend_rows = [_frontend_unified_row(row) for row in filtered_df.to_dict("records")]
    data = {
        "data": frontend_rows,
        "date_range": _date_range_from_rows(frontend_rows),
        "total_records": len(frontend_rows),
    }
    
    # Apply limit if specified
    if limit and limit > 0 and data.get("data"):
        data["data"] = data["data"][:limit]
        data["total_records"] = len(data["data"])
    
    return data


@router.get("/live/grid", response_model=EnergyDataResponse)
async def get_live_grid_data(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """Get live grid data from the dedicated grid_and_diesel sheet (fallback: unified rows)."""
    gs_service = get_gs_service()
    rows: list[Dict[str, Any]] = []

    if gs_service.is_authenticated():
        grid_df = gs_service.get_grid_and_diesel_data()
        if grid_df is not None and not grid_df.empty:
            filtered_df = gs_service.filter_by_date_range(grid_df, start_date, end_date)
            rows = [_frontend_unified_row(row) for row in filtered_df.to_dict("records")]

    # Keep fallback so grid card still works if grid sheet is temporarily unavailable.
    if not rows:
        rows = _get_live_unified_rows(start_date, end_date)

    return {
        "data": rows,
        "date_range": _date_range_from_rows(rows),
        "total_records": len(rows),
    }


@router.get("/live/diesel", response_model=EnergyDataResponse)
async def get_live_diesel_data(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """Get live diesel data from the grid_and_diesel sheet (fallback: unified sheet)."""
    gs_service = get_gs_service()
    rows: list[Dict[str, Any]] = []

    if gs_service.is_authenticated():
        grid_diesel_df = gs_service.get_grid_and_diesel_data()
        if grid_diesel_df is not None and not grid_diesel_df.empty:
            filtered_df = gs_service.filter_by_date_range(grid_diesel_df, start_date, end_date)
            rows = [_frontend_unified_row(row) for row in filtered_df.to_dict("records")]

    # Keep existing behavior as a safety fallback when grid_and_diesel is unavailable.
    if not rows:
        rows = _get_live_unified_rows(start_date, end_date)

    return {
        "data": rows,
        "date_range": _date_range_from_rows(rows),
        "total_records": len(rows),
    }


@router.get("/live/daily-summary", response_model=EnergyDataResponse)
async def get_live_daily_summary(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """Get live daily summary aggregated from Google Sheets-backed unified rows."""
    rows = _get_live_unified_rows(start_date, end_date)
    daily_rows = _build_daily_summary_from_rows(rows)
    return {
        "data": daily_rows,
        "date_range": _date_range_from_rows(daily_rows),
        "total_records": len(daily_rows),
    }


@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_ingestion_data():
    """Trigger one ingestion pipeline run so API data files are refreshed."""
    try:
        success = run_ingestion_once()
        return {
            "status": "success" if success else "failed",
            "message": "Ingestion pipeline executed" if success else "Ingestion pipeline reported failures",
            "pipeline_success": success,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to run ingestion pipeline: {exc}") from exc


@router.post("/backfill-inverter-columns", response_model=Dict[str, Any])
async def backfill_inverter_columns():
    """Backfill INV_1..INV_5 values for existing master-grid rows once."""
    try:
        success = run_inverter_backfill_once()
        return {
            "status": "success" if success else "failed",
            "message": (
                "Inverter column backfill completed"
                if success
                else "Inverter column backfill reported failures"
            ),
            "backfill_success": success,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to backfill inverter columns: {exc}") from exc


@router.get("/live/smb-status", response_model=EnergyDataResponse)
async def get_live_smb_status():
    """Get live SMB status data from Google Sheets"""
    gs_service = get_gs_service()
    cache = get_cache()
    
    if not gs_service.is_authenticated():
        return {
            "data": [],
            "date_range": {"min_date": None, "max_date": None},
            "total_records": 0
        }
    
    smb_data = cache.get('smb_status', for_frontend=True)
    if not smb_data:
        # Try to fetch directly
        df = gs_service.get_smb_status_data()
        if df is not None and not df.empty:
            smb_data = df.to_dict('records')
        else:
            smb_data = []
    
    import pandas as pd
    frontend_rows = [_frontend_smb_row(row) for row in smb_data] if isinstance(smb_data, list) else []

    return {
        "data": frontend_rows,
        "date_range": _date_range_from_rows(frontend_rows),
        "total_records": len(frontend_rows)
    }


@router.get("/live/inverter-status", response_model=Dict[str, Any])
async def get_live_inverter_status():
    """Get inverter status rows from ingestion output (INV_1..INV_n)."""
    payload = _load_filtered_solar_panel_json()
    extraction_info = payload.get("data_extraction_info", {})
    device_status = payload.get("device_status", {})
    inverters = device_status.get("inverters", {}) if isinstance(device_status, dict) else {}

    rows = []
    for inv_key, inv_data in inverters.items():
        if not isinstance(inv_data, dict):
            continue
        status_text = str(inv_data.get("status") or "UNKNOWN").upper()
        rows.append({
            "name": inv_key,
            "status": status_text,
            "status_code": inv_data.get("status_code"),
            "user_status": inv_data.get("user_status"),
            "power_w": _to_float(inv_data.get("power_w")),
            "temperature_c": _to_float(inv_data.get("temperature_c")),
        })

    rows.sort(key=lambda r: str(r.get("name", "")))
    return {
        "data": rows,
        "last_update": extraction_info.get("last_update"),
        "total_records": len(rows),
    }


@router.get("/live/last-7-days", response_model=EnergyDataResponse)
async def get_live_last_7_days(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """Get live 7-day summary data directly from Google Sheets."""
    gs_service = get_gs_service()
    if not gs_service.is_authenticated():
        return {
            "data": [],
            "date_range": {"min_date": None, "max_date": None},
            "total_records": 0,
        }

    df = gs_service.get_last_7_days_data()
    if df is None or df.empty:
        return {
            "data": [],
            "date_range": {"min_date": None, "max_date": None},
            "total_records": 0,
        }

    filtered_df = gs_service.filter_by_date_range(df, start_date, end_date)
    date_col = "Timestamp" if "Timestamp" in filtered_df.columns else "Date"
    all_dates = (
        pd.to_datetime(filtered_df[date_col], errors="coerce")
        if date_col in filtered_df.columns
        else pd.Series(dtype="datetime64[ns]")
    )

    frontend_rows = [_frontend_last_7_row(row) for row in filtered_df.to_dict("records")]
    return {
        "data": frontend_rows,
        "date_range": _date_range_from_rows(frontend_rows),
        "total_records": len(frontend_rows),
    }


@router.get("/debug/status", response_model=Dict[str, Any])
async def get_integration_status():
    """
    Debug endpoint showing Google Sheets integration status
    Useful for troubleshooting timestamp and data mapping issues
    """
    gs_service = get_gs_service()
    cache = get_cache()
    
    cache_stats = {
        "authenticated": gs_service.is_authenticated(),
        "last_error": gs_service.get_last_error(),
        "sheets_config": {
            "unified_solar": "https://docs.google.com/spreadsheets/d/1_lm81sKpds3y_SCskKsiSYbOQo7On-mXBGekAN95FMc/edit?usp=sharing",
            "grid_and_diesel": "https://docs.google.com/spreadsheets/d/134mi3kO-gcDtkQC9kGvK_zmO0LPQg1Fyj5A0qwM53DA/edit?usp=sharing",
            "last_7_days": "https://docs.google.com/spreadsheets/d/1FqMyIESL1TDOSqynXCqB-75RQeC-2TTpSSka7DqmwWI/edit?usp=sharing",
            "smb_status": "https://docs.google.com/spreadsheets/d/1cWwIp13hPkE2Pz06QU4PmmUvJLYPlj11GgCV1h7WdmA/edit?usp=sharing"
        }
    }
    
    # Try to get cached data info
    for key in ['unified_solar', 'last_7_days', 'smb_status']:
        try:
            data = cache.get(key, for_frontend=True)
            cache_stats[f"{key}_cached"] = bool(data) and (isinstance(data, list) and len(data) > 0)
            if isinstance(data, list) and data:
                cache_stats[f"{key}_record_count"] = len(data)
        except Exception as e:
            cache_stats[f"{key}_error"] = str(e)
    
    return {
        "status": "integrated",
        "timestamp": str(data_service.datetime.now()),
        "google_sheets": cache_stats
    }
