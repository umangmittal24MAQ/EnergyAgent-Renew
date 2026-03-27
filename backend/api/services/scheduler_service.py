"""
Scheduler service (simplified for MVP)
"""
import json
import sys
import os
import re
import html as html_lib
import threading
import importlib.util
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from zoneinfo import ZoneInfo

SCHEDULER_CONFIG_FILE = Path(__file__).parent.parent.parent / "energy-dashboard" / "scheduler_config.json"
SCHEDULER_LOG_FILE = Path(__file__).parent.parent.parent / "energy-dashboard" / "output" / "scheduler_log.json"
SCHEDULER_JOB_ID = "daily_energy_report"
RETRY_JOB_ID = "daily_energy_report_retry"
RETRY_INTERVAL_MINUTES = 30
STAKEHOLDER_NOTIFICATION_EMAIL = "prajwal.khadse@maqsoftware.com"
DAILY_REPORT_CRON_TIME = "10:00"

# Load email environment variables
energy_dashboard_path = Path(__file__).parent.parent.parent / "energy-dashboard"


def _load_scheduler_env() -> None:
    """Load scheduler env vars from supported files/locations."""
    candidates = [
        energy_dashboard_path / ".env",
        energy_dashboard_path / "env",
        energy_dashboard_path.parent / ".env",
    ]
    for env_path in candidates:
        if env_path.exists():
            load_dotenv(env_path, override=True)


_load_scheduler_env()

# Add energy-dashboard to sys.path at module level so imports work throughout the module
if str(energy_dashboard_path) not in sys.path:
    sys.path.insert(0, str(energy_dashboard_path))

# Debug marker
import time
_module_load_time = time.time()
_debug_log_path = energy_dashboard_path / "output" / "scheduler_module_debug.txt"
_debug_log_path.parent.mkdir(parents=True, exist_ok=True)
with open(_debug_log_path, 'a', encoding='utf-8') as f:
    f.write(f"Module loaded at {_module_load_time}\n")

_build_email_html_cached = None
_build_email_html_cached_mtime = None
_scheduler = BackgroundScheduler(timezone=ZoneInfo("Asia/Kolkata"))
_automation_lock = threading.Lock()


def _get_env_value(*keys: str, default: str = "") -> str:
    for key in keys:
        value = os.getenv(key)
        if value is None:
            continue
        text = str(value).strip().strip('"').strip("'")
        if text:
            return text
    return default


def _to_bool(value: str, default: bool = True) -> bool:
    if value is None:
        return default
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _parse_date_input(date_input: Any) -> Optional[pd.Timestamp]:
    if date_input in (None, ""):
        return None

    text = str(date_input).strip()
    if not text:
        return None

    # Handle common date strings deterministically before general parsing.
    dmy_slash = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", text)
    if dmy_slash:
        parsed = pd.to_datetime(
            f"{dmy_slash.group(3)}-{int(dmy_slash.group(2)):02d}-{int(dmy_slash.group(1)):02d}",
            errors="coerce",
        )
        return None if pd.isna(parsed) else parsed

    parsed = pd.to_datetime(text, errors="coerce")
    if pd.notna(parsed):
        return parsed

    parsed = pd.to_datetime(text, errors="coerce", dayfirst=True)
    if pd.notna(parsed):
        return parsed

    return None


def formatDate(date_input: Any) -> str:
    parsed = _parse_date_input(date_input)
    if parsed is None:
        return str(date_input or "").strip()

    day = parsed.day
    month = parsed.strftime("%b")
    year = parsed.year
    return f"{day}-{month}-{year}"


def _format_en_in(value: float, decimals: int) -> str:
    rounded = f"{abs(value):.{decimals}f}"
    whole, frac = rounded.split(".") if "." in rounded else (rounded, "")

    if len(whole) > 3:
        last_three = whole[-3:]
        lead = whole[:-3]
        groups = []
        while len(lead) > 2:
            groups.insert(0, lead[-2:])
            lead = lead[:-2]
        if lead:
            groups.insert(0, lead)
        whole = ",".join(groups + [last_three])

    sign = "-" if value < 0 else ""
    if decimals > 0:
        return f"{sign}{whole}.{frac}"
    return f"{sign}{whole}"


def formatNumber(value: Any, decimals: int = 2) -> str:
    if value is None or value == "":
        return "-"

    try:
        num = float(str(value).replace(",", "").strip())
    except Exception:
        return str(value)

    return _format_en_in(num, decimals)


def normalizeIssueText(value: Any) -> str:
    if value is None:
        return "No issues"

    text = str(value).strip()
    if not text:
        return "No issues"

    lower = text.lower()
    return lower[:1].upper() + lower[1:]


def _get_build_email_html():
    """Load build_email_html directly from emailer.py to avoid package side effects."""
    global _build_email_html_cached, _build_email_html_cached_mtime

    emailer_path = energy_dashboard_path / "mail_scheduling_agent" / "emailer.py"
    current_mtime = emailer_path.stat().st_mtime if emailer_path.exists() else None

    # Reload when file changes so scheduler picks new email format without restart.
    if (
        _build_email_html_cached is not None
        and _build_email_html_cached_mtime is not None
        and current_mtime == _build_email_html_cached_mtime
    ):
        return _build_email_html_cached

    spec = importlib.util.spec_from_file_location("energy_dashboard_emailer", emailer_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load emailer module from {emailer_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _build_email_html_cached = module.build_email_html
    _build_email_html_cached_mtime = current_mtime
    return _build_email_html_cached


def _validate_send_time(send_time: str) -> tuple[int, int]:
    """Validate HH:MM time and return (hour, minute)."""
    if not isinstance(send_time, str) or ":" not in send_time:
        raise ValueError("send_time must be in HH:MM format")
    hour_str, minute_str = send_time.split(":", 1)
    if not hour_str.isdigit() or not minute_str.isdigit():
        raise ValueError("send_time must be in HH:MM format")

    hour = int(hour_str)
    minute = int(minute_str)
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise ValueError("send_time must be in HH:MM format")
    return hour, minute


def _ensure_scheduler_started() -> None:
    if not _scheduler.running:
        _scheduler.start()


def _append_scheduler_log_entry(entry: Dict[str, Any]) -> None:
    """Persist a single scheduler log entry and cap history length."""
    SCHEDULER_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    logs = []
    if SCHEDULER_LOG_FILE.exists():
        try:
            with open(SCHEDULER_LOG_FILE, "r") as f:
                logs = json.load(f)
        except (json.JSONDecodeError, ValueError):
            logs = []

    if not isinstance(logs, list):
        logs = []

    logs.insert(0, entry)
    logs = logs[:100]

    with open(SCHEDULER_LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)


def _today_ist_date_key() -> str:
    return pd.Timestamp.now(tz=ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d")


def _normalize_record_date_key(value: Any) -> str:
    if value in (None, ""):
        return ""

    parsed = pd.to_datetime(value, errors="coerce")
    if pd.notna(parsed):
        return parsed.strftime("%Y-%m-%d")

    return str(value).strip()[:10]


def _extract_record_date_key(row: Dict[str, Any]) -> str:
    for key in ["Date", "date", "Timestamp", "timestamp"]:
        if key in row and row.get(key) not in (None, ""):
            date_key = _normalize_record_date_key(row.get(key))
            if date_key:
                return date_key
    return ""


def check_master_data_today_flag() -> Dict[str, Any]:
    """
    Step 1 (flag-based): scan master-data/master-grid rows and set FOUND for today's date.
    """
    FOUND = False
    checked_date = _today_ist_date_key()
    total_records = 0
    error_message = ""
    data_source = ""

    try:
        from .google_sheets_data_service import get_service as get_gs_service

        gs_service = get_gs_service()
        if not gs_service.is_authenticated():
            error_message = gs_service.get_last_error() or "Google Sheets authentication failed"
        else:
            master_df = gs_service.get_master_data()
            if master_df is None or master_df.empty:
                master_df = gs_service.get_grid_and_diesel_data()
                data_source = "master-grid"
            else:
                data_source = "master-data"

            if master_df is None or master_df.empty:
                error_message = "Master data/master-grid sheet is empty or unavailable"
            else:
                records = master_df.fillna("").to_dict("records")
                total_records = len(records)
                for row in records:
                    row_date = _extract_record_date_key(row)
                    if row_date == checked_date:
                        FOUND = True
                        break
    except Exception as exc:
        error_message = str(exc)

    source_label = data_source or "master-data"
    notes = f"checked {total_records} rows from {source_label} for {checked_date}"
    if error_message:
        notes = f"{notes}; error={error_message}"

    return {
        "date_checked": checked_date,
        "found": FOUND,
        "rows_checked": total_records,
        "data_source": source_label,
        "error": error_message,
        "notes": notes,
    }


def _schedule_retry_loop() -> None:
    """Create or replace a single retry job that runs every 30 minutes."""
    _ensure_scheduler_started()
    trigger = IntervalTrigger(minutes=RETRY_INTERVAL_MINUTES, timezone=ZoneInfo("Asia/Kolkata"))
    _scheduler.add_job(
        _run_retry_cycle,
        trigger=trigger,
        id=RETRY_JOB_ID,
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=1800,
    )


def _stop_retry_loop() -> None:
    retry_job = _scheduler.get_job(RETRY_JOB_ID)
    if retry_job is not None:
        _scheduler.remove_job(RETRY_JOB_ID)


def send_stakeholder_pending_notification() -> Dict[str, Any]:
    """Send pending-log reminder to stakeholder when today's row is missing."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    _load_scheduler_env()

    smtp_server = _get_env_value("SMTP_SERVER", "SMTP_HOST", "MAIL_SERVER", default="smtp.gmail.com")
    smtp_port = int(_get_env_value("SMTP_PORT", default="587"))
    sender_email = _get_env_value("SENDER_EMAIL", "SMTP_USERNAME", "EMAIL_FROM", "MAIL_USERNAME", "EMAIL_USER")
    sender_password = _get_env_value("SENDER_PASSWORD", "SMTP_PASSWORD", "MAIL_PASSWORD", "EMAIL_PASSWORD")
    use_tls = _to_bool(_get_env_value("SMTP_USE_TLS", "SMTP_TLS", "SMTP_STARTTLS", default="True"), default=True)
    timeout = int(_get_env_value("SMTP_TIMEOUT", default="10"))
    login_user = _get_env_value("SMTP_USERNAME", "SENDER_EMAIL", "MAIL_USERNAME", "EMAIL_USER", default=sender_email)
    email_from = _get_env_value("EMAIL_FROM", "SENDER_EMAIL", "SMTP_USERNAME", "MAIL_FROM", "MAIL_USERNAME", default=sender_email)

    subject = "Daily energy log update is pending"
    body = "Please update the daily log for the latest date."
    to_list = [STAKEHOLDER_NOTIFICATION_EMAIL]

    msg = MIMEMultipart("alternative")
    msg["From"] = email_from
    msg["To"] = ", ".join(to_list)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        if not email_from:
            raise ValueError("Missing sender email in env (set SENDER_EMAIL / SMTP_USERNAME / EMAIL_FROM)")
        if not sender_password:
            raise ValueError("Missing sender password in env (set SENDER_PASSWORD / SMTP_PASSWORD)")

        with smtplib.SMTP(smtp_server, smtp_port, timeout=timeout) as server:
            if use_tls:
                server.starttls()
            if login_user and sender_password:
                server.login(login_user, sender_password)
            server.sendmail(email_from, to_list, msg.as_string())

        return {
            "timestamp": datetime.now().isoformat(),
            "status": "Success",
            "recipients": ", ".join(to_list),
            "attachment": None,
            "notes": "Pending-log stakeholder notification sent",
        }
    except Exception as exc:
        return {
            "timestamp": datetime.now().isoformat(),
            "status": "Failed",
            "recipients": ", ".join(to_list),
            "attachment": None,
            "notes": f"Pending-log stakeholder notification failed: {str(exc)[:200]}",
        }


def send_daily_report_email_from_settings() -> Dict[str, Any]:
    """Send the daily report using frontend-configured recipients from scheduler settings."""
    return send_email_now()


def _log_daily_check_attempt(date_checked: str, found: bool, action: str, trigger_source: str, notes: str) -> None:
    _append_scheduler_log_entry(
        {
            "timestamp": datetime.now().isoformat(),
            "status": "Check",
            "recipients": "",
            "attachment": None,
            "notes": notes,
            "date_checked": date_checked,
            "found": found,
            "action": action,
            "trigger_source": trigger_source,
        }
    )


def run_daily_report_automation(trigger_source: str = "daily_cron") -> Dict[str, Any]:
    """
    Daily automation flow:
    1) Check today's master-data presence using FOUND flag.
    2) FOUND=False -> notify stakeholder + run 30-minute retry loop.
    3) FOUND=True  -> send daily report to dynamic frontend-configured recipients and stop retry loop.
    """
    with _automation_lock:
        check_result = check_master_data_today_flag()
        FOUND = bool(check_result.get("found", False))
        date_checked = str(check_result.get("date_checked", ""))
        check_notes = str(check_result.get("notes", ""))

        action = ""
        notification_result = None
        report_result = None

        if FOUND is False:
            notification_result = send_stakeholder_pending_notification()
            _schedule_retry_loop()
            action = "found_false_notified_stakeholder_retry_scheduled"

        if FOUND is True:
            _stop_retry_loop()
            report_result = send_daily_report_email_from_settings()
            action = "found_true_daily_report_sent_retry_stopped"

        notes = check_notes
        if notification_result:
            notes = f"{notes}; notification_status={notification_result.get('status', 'Unknown')}"
        if report_result:
            notes = f"{notes}; report_status={report_result.get('status', 'Unknown')}"

        _log_daily_check_attempt(
            date_checked=date_checked,
            found=FOUND,
            action=action,
            trigger_source=trigger_source,
            notes=notes,
        )

        return {
            "timestamp": datetime.now().isoformat(),
            "trigger_source": trigger_source,
            "date_checked": date_checked,
            "found": FOUND,
            "action": action,
            "notification": notification_result,
            "daily_report": report_result,
        }


def _run_retry_cycle() -> Dict[str, Any]:
    """Retry cycle entrypoint: runs the same FOUND-flag flow every 30 minutes until FOUND=True."""
    return run_daily_report_automation(trigger_source="retry_30_minutes")


def _schedule_daily_job(send_time: str) -> None:
    # Keep function name for compatibility. This now schedules daily cron at HH:MM.
    _ = send_time
    hour, minute = _validate_send_time(DAILY_REPORT_CRON_TIME)
    _ensure_scheduler_started()

    trigger = CronTrigger(hour=hour, minute=minute, timezone=ZoneInfo("Asia/Kolkata"))
    _scheduler.add_job(
        run_daily_report_automation,
        trigger=trigger,
        id=SCHEDULER_JOB_ID,
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=1800,
    )


def _schedule_data_refresh() -> None:
    """Schedule data refresh at a configurable interval (default 30 minutes)."""
    _ensure_scheduler_started()

    # Use interval trigger for periodic refresh.
    refresh_minutes = int(os.getenv("INGESTION_REFRESH_INTERVAL_MINUTES", "30"))
    if refresh_minutes < 1:
        refresh_minutes = 1

    trigger = IntervalTrigger(minutes=refresh_minutes, timezone=ZoneInfo("Asia/Kolkata"))
    _scheduler.add_job(
        _run_data_refresh,
        trigger=trigger,
        id="data_refresh_interval",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=60,
    )
    
    with open(_debug_log_path, 'a', encoding='utf-8') as f:
            f.write(f"Scheduled ingestion data refresh every {refresh_minutes} minute(s) at {datetime.now()}\n")


def _run_data_refresh() -> None:
    """Background task to refresh ingestion data and cache layers."""
    try:
        from .data_refresh_service import DataRefreshService
        
        result = DataRefreshService.refresh_all_data()
        
        with open(_debug_log_path, 'a', encoding='utf-8') as f:
            f.write(f"Data refresh at {result['timestamp']}: {len(result['successful'])} successful, {len(result['failed'])} failed\n")
            if result['errors']:
                f.write(f"  Errors: {result['errors']}\n")
    
    except Exception as e:
        with open(_debug_log_path, 'a', encoding='utf-8') as f:
            f.write(f"Error in data refresh task: {e}\n")


def initialize_scheduler_from_config() -> None:
    """Initialize scheduler from persisted config when API starts."""
    # Start data refresh task immediately
    _schedule_data_refresh()
    
    # Start email scheduler if configured
    cfg = load_scheduler_config()
    if cfg.get("auto_start", False):
        try:
            _schedule_daily_job(DAILY_REPORT_CRON_TIME)
        except Exception as exc:
            with open(_debug_log_path, 'a', encoding='utf-8') as f:
                f.write(f"Scheduler auto-start failed: {exc}\n")


def load_scheduler_config() -> Dict[str, Any]:
    """Load scheduler configuration"""
    if SCHEDULER_CONFIG_FILE.exists():
        with open(SCHEDULER_CONFIG_FILE, 'r') as f:
            return json.load(f)
    else:
        # Return default config
        return {
            "to": "",
            "cc": "",
            "send_time": "10:00",
            "subject": "Daily Energy Report — Noida Campus — {date}",
            "custom_message": "",
            "auto_start": False,
            "include_sections": {
                "summary_kpis": True,
                "unified_table": True,
                "grid_summary": True,
                "solar_summary": True,
                "diesel_summary": True,
                "inverter_status": True,
                "raw_data": False
            },
            "uploaded_template_path": None
        }


def save_scheduler_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Save scheduler configuration"""
    config["send_time"] = DAILY_REPORT_CRON_TIME
    with open(SCHEDULER_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

    # If scheduler is already active, immediately apply updated send_time.
    if _scheduler.get_job(SCHEDULER_JOB_ID) is not None:
        _schedule_daily_job(DAILY_REPORT_CRON_TIME)

    # Respect auto_start preference for future startup and current runtime.
    if config.get("auto_start", False) and _scheduler.get_job(SCHEDULER_JOB_ID) is None:
        _schedule_daily_job(DAILY_REPORT_CRON_TIME)
    if not config.get("auto_start", False) and _scheduler.get_job(SCHEDULER_JOB_ID) is not None:
        _scheduler.remove_job(SCHEDULER_JOB_ID)

    return config


def get_scheduler_status() -> Dict[str, Any]:
    """Get scheduler status"""
    job = _scheduler.get_job(SCHEDULER_JOB_ID)
    retry_job = _scheduler.get_job(RETRY_JOB_ID)
    next_run_time = job.next_run_time if job else None
    retry_next_run = retry_job.next_run_time if retry_job else None
    history = load_scheduler_history(limit=1)
    return {
        "status": "running" if job else "stopped",
        "next_run": next_run_time.isoformat() if next_run_time else None,
        "retry_loop_active": retry_job is not None,
        "retry_next_run": retry_next_run.isoformat() if retry_next_run else None,
        "last_run": history[0] if history else None,
    }


def start_scheduler(send_time: str) -> Dict[str, Any]:
    """Start the scheduler"""
    _ = send_time
    _schedule_daily_job(DAILY_REPORT_CRON_TIME)

    # Persist chosen time so UI refresh reflects latest schedule.
    config = load_scheduler_config()
    config["send_time"] = DAILY_REPORT_CRON_TIME
    config["auto_start"] = True
    with open(SCHEDULER_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

    job = _scheduler.get_job(SCHEDULER_JOB_ID)
    next_run_time = job.next_run_time if job else None
    return {
        "status": "running",
        "next_run": next_run_time.isoformat() if next_run_time else None,
    }


def stop_scheduler() -> Dict[str, Any]:
    """Stop the scheduler"""
    if _scheduler.get_job(SCHEDULER_JOB_ID) is not None:
        _scheduler.remove_job(SCHEDULER_JOB_ID)
    if _scheduler.get_job(RETRY_JOB_ID) is not None:
        _scheduler.remove_job(RETRY_JOB_ID)

    config = load_scheduler_config()
    config["auto_start"] = False
    with open(SCHEDULER_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

    return {
        "status": "stopped"
    }


def build_energy_report_html(config: Dict[str, Any]) -> tuple:
    """Build HTML body and CSV content for Energy Consumption Report format.
    Returns: (html_content, csv_content)
    """
    try:
        from .google_sheets_data_service import get_service as get_gs_service
        from ..routers.data import _build_live_report_rows
        unit_rate_inr = 7.11

        def _num(value: Any, default: float = 0.0) -> float:
            if value is None or value == "":
                return default
            try:
                return float(str(value).replace(",", "").strip())
            except Exception:
                # Handle mixed text values like "2 Liter" by extracting first numeric token.
                match = re.search(r"[-+]?\d*\.?\d+", str(value))
                return float(match.group(0)) if match else default

        def _clean_value(value: Any) -> Any:
            if value is None or value == "":
                return value
            text = str(value).strip()
            match = re.search(r"[-+]?\d*\.?\d+", text)
            if match:
                return match.group(0)
            return text

        def _pick(row: Dict[str, Any], keys: list[str], default: Any = "") -> Any:
            for key in keys:
                if key in row and row.get(key) not in (None, ""):
                    return row.get(key)
            return default

        def _normalize_day_time(row: Dict[str, Any], fallback_date: str) -> tuple[str, str]:
            """Return sane Day/Time values even when sheet row values are shifted or malformed."""
            day_raw = str(_pick(row, ["Day"], "")).strip()
            time_raw = str(_pick(row, ["Time"], "")).strip()

            # If Day accidentally contains a time-like string, swap semantics.
            if ":" in day_raw and not _is_weekday_text(day_raw):
                time_raw = day_raw
                day_raw = ""

            parsed_dt = pd.to_datetime(f"{fallback_date} {time_raw}", errors="coerce")
            if pd.notna(parsed_dt):
                normalized_day = day_raw if _is_weekday_text(day_raw) else parsed_dt.strftime("%A")
                normalized_time = parsed_dt.strftime("%H:%M:%S")
            else:
                fallback_dt = pd.to_datetime(fallback_date, errors="coerce")
                fallback_day = fallback_dt.strftime("%A") if pd.notna(fallback_dt) else ""
                normalized_day = day_raw if _is_weekday_text(day_raw) else fallback_day
                normalized_time = time_raw or "00:00:00"

            return normalized_day, normalized_time

        def _is_weekday_text(value: Any) -> bool:
            weekdays = {
                "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
            }
            text = str(value or "").strip().lower()
            return text in weekdays

        def _row_quality_score(row: Dict[str, Any]) -> float:
            """
            Score rows to prefer complete data entries.
            Higher score = better quality row for that date.
            """
            score = 0.0
            
            # CRITICAL: Strongly prioritize rows with Grid data (most important field)
            grid_kwh = _num(_pick(row, ["Grid Units Consumed (KWh)", "Grid KWh", "Total_Import_kWh"]))
            if grid_kwh > 0:
                score += 100.0  # Very high weight for grid data presence
            
            # Prefer rows with valid weekday
            score += 10.0 if _is_weekday_text(_pick(row, ["Day"])) else 0.0
            
            # Prefer rows with non-midnight times (indicates detailed entry)
            time_str = str(_pick(row, ["Time"], "")).strip()
            if time_str not in ("", "0:00", "00:00", "0", "00:00:00"):
                score += 5.0
            
            # Prefer rows with additional data fields populated
            score += 2.0 if str(_pick(row, ["Number of Panels Cleaned", "Panels Cleaned", "number_of_panels_cleaned"], "")).strip() not in ("", "0") else 0.0
            score += 2.0 if str(_pick(row, ["Water treated through STP", "STP", "stp"], "")).strip() not in ("", "0") else 0.0
            score += 2.0 if str(_pick(row, ["Water treated through WTP", "WTP", "wtp"], "")).strip() not in ("", "0") else 0.0
            score += 1.0 if str(_pick(row, ["Issues", "Issue", "issues"], "")).strip() not in ("", "no issues") else 0.0
            
            return score

        def _date_key(row: Dict[str, Any]) -> str:
            parsed = pd.to_datetime(row.get("Date") or row.get("Timestamp"), errors="coerce")
            if pd.notna(parsed):
                return parsed.strftime("%Y-%m-%d")
            return str(row.get("Date") or "")[:10]

        gs = get_gs_service()
        if not gs.is_authenticated():
            raise RuntimeError(gs.get_last_error() or "Google Sheets authentication failed")

        smb_df = gs.get_smb_status_data()

        report_end_ts = pd.Timestamp.now(tz=ZoneInfo("Asia/Kolkata")).normalize() - pd.Timedelta(days=1)
        report_start_ts = report_end_ts - pd.Timedelta(days=29)
        report_rows = _build_live_report_rows(
            report_start_ts.strftime("%Y-%m-%d"),
            report_end_ts.strftime("%Y-%m-%d"),
        )[:30]

        requested_columns = [
            "Date",
            "Day",
            "Time",
            "Ambient Temperature (°C)",
            "Grid Units Consumed (kWh)",
            "Solar Units Consumed (kWh)",
            "Total Units Consumed (kWh)",
            "Total Cost (INR)",
            "Solar Cost Savings (INR)",
            "Panels Cleaned",
            "Diesel Consumed (Litres)",
            "Water Treated through STP (kilo Litres)",
            "Water Treated through WTP (kilo Litres)",
            "Issues",
        ]

        if not report_rows:
            raise RuntimeError("No report rows returned from live unified source")

        display_df = pd.DataFrame(report_rows).reindex(columns=requested_columns)
        display_df["_date_sort"] = pd.to_datetime(display_df["Date"], errors="coerce", dayfirst=True)
        display_df = display_df[display_df["_date_sort"].notna()].sort_values("_date_sort", ascending=False).head(30)
        if display_df.empty:
            raise RuntimeError("No report rows available after date normalization")

        previous_day_cutoff = report_end_ts.date()
        display_df["Date"] = display_df["_date_sort"].apply(formatDate)
        display_df = display_df.drop(columns=["_date_sort"])

        right_aligned_columns = {
            "Ambient Temperature (°C)",
            "Grid Units Consumed (kWh)",
            "Solar Units Consumed (kWh)",
            "Total Units Consumed (kWh)",
            "Total Cost (INR)",
            "Solar Cost Savings (INR)",
            "Panels Cleaned",
            "Diesel Consumed (Litres)",
            "Water Treated through STP (kilo Litres)",
            "Water Treated through WTP (kilo Litres)",
        }

        decimals_by_column = {
            "Grid Units Consumed (kWh)": 0,
            "Solar Units Consumed (kWh)": 0,
            "Total Units Consumed (kWh)": 0,
            "Total Cost (INR)": 2,
            "Solar Cost Savings (INR)": 2,
            "Panels Cleaned": 0,
            "Diesel Consumed (Litres)": 0,
            "Water Treated through STP (kilo Litres)": 0,
            "Water Treated through WTP (kilo Litres)": 0,
        }

        csv_content = display_df.to_csv(index=False)

        # Render the 14-column table with email-safe horizontal scrolling.
        table_parts = [
            '<div style="overflow-x:auto; width:100%; max-width:100%;">',
            '<table style="border-collapse:collapse; width:100%; min-width:1000px; font-family:Arial, Helvetica, sans-serif; font-size:12px; color:#1e293b;">',
            '<thead><tr style="background-color:#1E3A5F; color:#ffffff; font-size:12px;">',
        ]
        for col in display_df.columns:
            text_align = "right" if col in right_aligned_columns else "left"
            table_parts.append(
                f'<th style="padding:8px 10px; text-align:{text_align};">{html_lib.escape(str(col))}</th>'
            )
        table_parts.append('</tr></thead><tbody>')

        for idx, (_, row) in enumerate(display_df.iterrows()):
            bg = "#ffffff" if idx % 2 == 0 else "#f8fafc"
            table_parts.append(f'<tr style="background-color:{bg}; font-size:12px;">')
            for col in display_df.columns:
                value = row.get(col, "")
                if pd.isna(value):
                    text = ""
                elif col == "Date":
                    text = formatDate(value)
                elif col == "Ambient Temperature (°C)":
                    raw_ambient = str(value).strip()
                    if raw_ambient in {"", "-"}:
                        text = "0"
                    else:
                        try:
                            text = _format_en_in(float(raw_ambient.replace(",", "")), 0)
                        except Exception:
                            text = raw_ambient
                elif col == "Issues":
                    text = normalizeIssueText(value)
                elif col in decimals_by_column:
                    text = _format_en_in(_num(value, 0.0), decimals_by_column[col])
                else:
                    text = str(value)

                text_align = "right" if col in right_aligned_columns else "left"
                numeric_style = "font-variant-numeric:tabular-nums;" if col in right_aligned_columns else ""
                table_parts.append(
                    f'<td style="padding:7px 10px; border-bottom:1px solid #e2e8f0; text-align:{text_align}; {numeric_style}">{html_lib.escape(text)}</td>'
                )
            table_parts.append('</tr>')

        table_parts.append(
            '<tr><td colspan="14" style="padding:8px 10px; font-size:11px; color:#94a3b8; text-align:center; border-top:1px solid #e2e8f0; background-color:#f8fafc;">'
            f'Showing {len(display_df)} records &nbsp;|&nbsp; Generated by Energy Optimization Agent &nbsp;|&nbsp; Noida Campus &nbsp;|&nbsp; Do not reply'
            '</td></tr>'
        )
        table_parts.append('</tbody></table></div>')
        table_html = "\n".join(table_parts)

        custom_message = html_lib.escape(config.get('custom_message', '') or '')

        # Get yesterday's date for KPI calculation
        previous_day_display = formatDate(previous_day_cutoff)
        
        # Since table is sorted descending (newest first), the first row is yesterday's data
        if len(display_df) > 0:
            # Get the most recent date in the table (should be yesterday)
            latest_row = display_df.iloc[0]
        else:
            raise RuntimeError("No data available for previous day")
        
        current_date_display = latest_row.get("Date", previous_day_display)
        total_kwh = _num(latest_row.get("Total Units Consumed (kWh)", 0), 0.0)
        solar_kwh = _num(latest_row.get("Solar Units Consumed (kWh)", 0), 0.0)
        grid_kwh = _num(latest_row.get("Grid Units Consumed (kWh)", 0), 0.0)
        total_inr = _num(latest_row.get("Total Cost (INR)", 0), 0.0)
        saving_inr = _num(latest_row.get("Solar Cost Savings (INR)", 0), 0.0)
        solar_pct = (solar_kwh / total_kwh * 100.0) if total_kwh > 0 else 0.0

        status_map = {"SMB1": "Online", "SMB2": "Online", "SMB3": "Online", "SMB4": "Online", "SMB5": "Online"}
        if smb_df is not None and len(smb_df) > 0:
            smb_sorted = smb_df.copy()
            smb_sorted["_ts"] = pd.to_datetime(
                smb_sorted.get("Timestamp", pd.NaT),
                errors="coerce"
            )
            if "Time" in smb_sorted.columns:
                composed = smb_sorted["Date"].astype(str).str[:10] + " " + smb_sorted["Time"].astype(str)
                fallback_ts = pd.to_datetime(composed, errors="coerce")
                smb_sorted["_ts"] = smb_sorted["_ts"].fillna(fallback_ts)
            smb_sorted = smb_sorted.sort_values("_ts", ascending=False)
            latest_smb = smb_sorted.iloc[0].to_dict()
            for smb_name in ["SMB1", "SMB2", "SMB3", "SMB4", "SMB5"]:
                raw = str(latest_smb.get(f"{smb_name}_status", latest_smb.get(f"{smb_name} Status", "ON"))).strip().lower()
                status_map[smb_name] = "Online" if raw in {"on", "online", "active", "1", "true"} else "Fault"

        online_count = sum(1 for v in status_map.values() if v == "Online")
        diesel_text = f"{float(latest_row.get('Diesel Consumed (Litres)', 0) or 0):.1f}"

        insights = [
            f"The grid energy consumption is {grid_kwh:,.1f} kWh, accounting for {((grid_kwh / total_kwh) * 100 if total_kwh > 0 else 0):.1f}% of the total energy consumed.",
            f"Solar energy contribution is {solar_kwh:,.0f} kWh, making up {solar_pct:.1f}% of the total energy consumed.",
            f"A total of {online_count} out of 5 inverters are currently online and active.",
            f"The diesel consumption is {diesel_text} units.",
            f"The total energy consumption is {total_kwh:,.1f} kWh.",
        ]
        insights_html = "".join(
            f'<li style="margin:0 0 4px 0;">{html_lib.escape(item)}</li>' for item in insights
        )

        inverter_runtime_hours: Dict[str, tuple[float, float]] = {}
        report_day = pd.to_datetime(str(latest_row.get("Date", "")), dayfirst=True, errors="coerce")
        for idx, smb_name in enumerate(["SMB1", "SMB2", "SMB3", "SMB4", "SMB5"], start=1):
            up_hours = 24.0 if status_map.get(smb_name, "Online") == "Online" else 0.0
            down_hours = round(max(0.0, 24.0 - up_hours), 1)
            status_col = f"{smb_name}_status"

            if smb_df is not None and len(smb_df) > 0 and pd.notna(report_day) and status_col in smb_df.columns:
                sample = smb_df.copy()
                sample["_date"] = pd.to_datetime(sample.get("Date"), errors="coerce").dt.date
                report_date_only = report_day.date()
                day_rows = sample[sample["_date"] == report_date_only]
                if len(day_rows) > 0:
                    status_values = day_rows[status_col].astype(str).str.strip().str.lower()
                    online_mask = status_values.isin({"on", "online", "active", "1", "true"})
                    total_samples = len(status_values)
                    online_samples = int(online_mask.sum())
                    up_hours = round((online_samples / total_samples) * 24.0, 1)
                    down_hours = round(max(0.0, 24.0 - up_hours), 1)

            inverter_runtime_hours[smb_name] = (up_hours, down_hours)

        status_cards = []
        for smb_name in ["SMB1", "SMB2", "SMB3", "SMB4", "SMB5"]:
            is_online = status_map.get(smb_name, "Online") == "Online"
            dot_color = "#2E7D32" if is_online else "#D32F2F"
            label_color = dot_color
            label_text = "Online" if is_online else "Fault"
            inverter_label = f"Inverter {smb_name.replace('SMB', '')}"
            uptime_hours, downtime_hours = inverter_runtime_hours.get(smb_name, (24.0 if is_online else 0.0, 0.0 if is_online else 24.0))
            status_cards.append(
                f'<td width="20%" style="padding:10px 8px; text-align:center; border:1px solid #d9e2ee; background:#fff;">'
                f'<span style="display:inline-block; margin-top:4px; font-size:13px; font-weight:600; color:#163a70;">{inverter_label}</span><br>'
                f'<span style="display:inline-block; margin-top:2px; font-size:13px; color:{label_color};">{label_text}</span><br>'
                f'<span style="display:inline-block; margin-top:2px; font-size:13px; color:#6b7f99;">Uptime: {uptime_hours:.1f} hours</span><br>'
                f'<span style="display:inline-block; margin-top:2px; font-size:13px; color:#6b7f99;">Downtime: {downtime_hours:.1f} hours</span>'
                f'</td>'
            )
        inverter_cards_html = "".join(status_cards)

        html = f"""
        <html>
            <body style="margin:0; padding:0; background:#f2f3f5; font-family:Segoe UI, Helvetica Neue, Arial, sans-serif; font-size:13px;">
                <table width="100%" cellpadding="0" cellspacing="0" style="padding:18px 0; background:#f2f3f5;">
                    <tr>
                        <td align="center">
                            <table width="99%" cellpadding="0" cellspacing="0" style="max-width:1460px; border:1px solid #d9d9d9; background:#ffffff;">
                                <tr>
                                    <td style="background:#233f70; color:#ffffff; padding:14px 26px;">
                                        <div style="display:inline-block; vertical-align:middle; font-size:32px; font-weight:700; line-height:1.2;">Energy Consumption Report - Noida Campus</div>
                                        <div style="font-size:20px; margin-top:6px; opacity:0.95;">Report Date: {current_date_display} - Auto-generated by Energy Agent</div>
                                    </td>
                                </tr>
                               <tr></tr>
                                <tr>
                                    <td style="padding:0 24px 10px 24px;">
                                        <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse; border:1px solid #cfd7e2; background:#f5f8fd;">
                                            <tr><td style="padding:10px 14px; font-size:18px; font-weight:700; color:#1f3b69;">Insights on the basis of report generated on {current_date_display}</td></tr>
                                            <tr><td style="padding:0 14px 10px 14px;"><ul style="margin:0 0 0 18px; padding:0; font-size:13px; color:#22323f;">{insights_html}</ul></td></tr>
                                        </table>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding:10px 24px 6px 24px; font-size:13px; color:#5a6f85; font-weight:700;">Metrics shown below are for report date: {current_date_display}</td>
                                </tr>
                                <tr>
                                    <td style="padding:0 24px 8px 24px;">
                                        <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:separate; border-spacing:8px 8px;">
                                            <tr>
                                                <td width="50%" style="padding:10px 14px; background:#e9f0f9; border-left:4px solid #1f3f70;">
                                                    <div style="font-size:13px; color:#000000;">Total Campus Energy Consumption</div>
                                                    <div style="font-size:24px; line-height:1.05; font-weight:700; color:#1f3f70;">{total_kwh:,.1f} KWh</div>
                                                    <div style="font-size:13px; color:#000000;">Grid + Solar combined usage</div>
                                                </td>
                                                <td width="50%" style="padding:10px 14px; background:#e9f0f9; border-left:4px solid #1f3f70;">
                                                    <div style="font-size:13px; color:#000000;">Solar Energy Generated</div>
                                                    <div style="font-size:24px; line-height:1.05; font-weight:700; color:#1f3f70;">{solar_kwh:,.1f} KWh</div>
                                                    <div style="font-size:13px; color:#000000;">From rooftop solar plant</div>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td width="50%" style="padding:10px 14px; background:#e9f0f9; border-left:4px solid #1f3f70;">
                                                    <div style="font-size:13px; color:#000000;">Solar Contribution to Total</div>
                                                    <div style="font-size:24px; line-height:1.05; font-weight:700; color:#1f3f70;">{solar_pct:.1f}%</div>
                                                    <div style="font-size:13px; color:#000000;">Renewable energy share</div>
                                                </td>
                                                <td width="50%" style="padding:10px 14px; background:#e9f0f9; border-left:4px solid #1f3f70;">
                                                    <div style="font-size:13px; color:#000000;">Total Energy Cost</div>
                                                    <div style="font-size:24px; line-height:1.05; font-weight:700; color:#1f3f70;">&#8377;{total_inr:,.0f}</div>
                                                    <div style="font-size:13px; color:#000000;">Grid electricity expense</div>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td width="50%" style="padding:10px 14px; background:#e9f0f9; border-left:4px solid #1f3f70;">
                                                    <div style="font-size:13px; color:#000000;">Cost Savings from Solar</div>
                                                    <div style="font-size:24px; line-height:1.05; font-weight:700; color:#1f3f70;">&#8377;{saving_inr:,.0f}</div>
                                                </td>
                                                <td width="50%" style="padding:10px 14px; background:#ffffff; border-left:4px solid #ffffff;">&nbsp;</td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding:8px 24px 4px 24px; color:#1f3f70; font-weight:700; font-size:20px;">Inverter Status</td>
                                </tr>
                                <tr>
                                    <td style="padding:0 24px 8px 24px; color:#000; font-size:13px;">Expected uptime: 24 hours active during daylight hours</td>
                                </tr>
                                <tr>
                                    <td style="padding:0 24px 14px 24px;">
                                        <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:separate; border-spacing:8px 0;"> 
                                            <tr>{inverter_cards_html}</tr>
                                        </table>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding:18px 24px 8px 24px; color:#223b63; font-weight:700; font-size:20px;">Daily Report (Last 30 Days)</td>
                                </tr>
                                <tr>
                                    <td style="padding:0 24px 20px 24px;">
                                        {table_html}
                                    </td>
                                </tr>
                                {f'<tr><td style="padding:0 24px 18px 24px; font-size:13px; color:#555;">{custom_message}</td></tr>' if custom_message else ''}
                                <tr>
                                    <td style="background:#f0f0f0; padding:14px 24px; text-align:center; color:#7a7a7a; font-size:13px; border-top:1px solid #dddddd;">Generated by Energy Optimization Agent | Noida Campus | Do not reply</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

        return html, csv_content

    except Exception as e:
        # Fallback simple HTML if data loading fails
        html = f"""
        <html>
            <body style="font-family: Arial; padding: 20px;">
                <h2>Energy Consumption Report</h2>
                <p>Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Daily energy consumption and cost analysis report.</p>
                <p style='color: orange;'>Note: Could not load detailed energy data. {str(e)}</p>
            </body>
        </html>
        """
        csv_content = "Error generating report"
        return html, csv_content


def send_email_now() -> Dict[str, Any]:
    """Send email immediately with Energy Report and CSV attachment"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email import encoders
    from datetime import datetime

    with open(_debug_log_path, 'a', encoding='utf-8') as f:
        f.write("send_email_now called\n")

    config = load_scheduler_config()

    try:
        # Reload env so latest credentials apply without restart.
        _load_scheduler_env()

        # Accept both legacy and .env.example naming styles.
        smtp_server = _get_env_value("SMTP_SERVER", "SMTP_HOST", "MAIL_SERVER", default="smtp.gmail.com")
        smtp_port = int(_get_env_value("SMTP_PORT", default="587"))
        sender_email = _get_env_value("SENDER_EMAIL", "SMTP_USERNAME", "EMAIL_FROM", "MAIL_USERNAME", "EMAIL_USER")
        sender_password = _get_env_value("SENDER_PASSWORD", "SMTP_PASSWORD", "MAIL_PASSWORD", "EMAIL_PASSWORD")
        use_tls = _to_bool(_get_env_value("SMTP_USE_TLS", "SMTP_TLS", "SMTP_STARTTLS", default="True"), default=True)
        timeout = int(_get_env_value("SMTP_TIMEOUT", default="10"))
        login_user = _get_env_value("SMTP_USERNAME", "SENDER_EMAIL", "MAIL_USERNAME", "EMAIL_USER", default=sender_email)
        email_from = _get_env_value("EMAIL_FROM", "SENDER_EMAIL", "SMTP_USERNAME", "MAIL_FROM", "MAIL_USERNAME", default=sender_email)

        if not email_from:
            raise ValueError("Missing sender email in env (set SENDER_EMAIL / SMTP_USERNAME / EMAIL_FROM)")

        if not sender_password:
            raise ValueError("Missing sender password in env (set SENDER_PASSWORD / SMTP_PASSWORD)")

        # Get recipient from config or env
        default_to = _get_env_value("DEFAULT_RECIPIENT_EMAIL", "EMAIL_TO", "DEFAULT_TO", default="")
        to_list = [addr.strip() for addr in config.get("to", default_to).split(",") if addr.strip()]
        cc_list = [addr.strip() for addr in config.get("cc", "").split(",") if addr.strip()]

        if not to_list:
            raise ValueError("No recipient email address configured")

        # Build the Energy Report HTML and CSV
        html_body, csv_content = build_energy_report_html(config)

        # Create email message with mixed content (HTML + attachment)
        msg = MIMEMultipart("mixed")
        msg["From"] = email_from
        msg["To"] = ", ".join(to_list)
        if cc_list:
            msg["Cc"] = ", ".join(cc_list)

        previous_day = (pd.Timestamp.now(tz=ZoneInfo("Asia/Kolkata")) - pd.Timedelta(days=1)).date()
        subject = f"Daily Energy Report - Noida Campus - {formatDate(previous_day)}"
        msg["Subject"] = subject

        # Create alternative part for HTML
        msg_alternative = MIMEMultipart("alternative")
        msg.attach(msg_alternative)

        # Attach HTML body
        msg_alternative.attach(MIMEText(html_body, "html"))

        uploaded_template_path = config.get("uploaded_template_path")
        attachment_name = None

        if uploaded_template_path and Path(uploaded_template_path).exists():
            attachment_name = Path(uploaded_template_path).name
            with open(uploaded_template_path, "rb") as f:
                attachment_bytes = f.read()
        else:
            attachment_name = f"Energy_Report_{datetime.now().strftime('%d%m%Y')}.csv"
            attachment_bytes = csv_content.encode('utf-8')

        attachment = MIMEBase("application", "octet-stream")
        attachment.set_payload(attachment_bytes)
        encoders.encode_base64(attachment)
        attachment.add_header("Content-Disposition", f"attachment; filename= {attachment_name}")
        msg.attach(attachment)

        # Connect and send
        all_recipients = to_list + cc_list

        print(f"[DEBUG] Connecting to {smtp_server}:{smtp_port}")
        with smtplib.SMTP(smtp_server, smtp_port, timeout=timeout) as server:
            if use_tls:
                server.starttls()

            if login_user and sender_password:
                server.login(login_user, sender_password)

            server.sendmail(email_from, all_recipients, msg.as_string())

        # Log successful send
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "status": "Success",
            "recipients": ", ".join(to_list),
            "attachment": attachment_name,
            "notes": f"Email sent successfully to {', '.join(to_list)} with HTML report and attachment"
        }
        print(f"[DEBUG] Log Entry Attac: {log_entry['attachment']}", flush=True)

        logs = load_scheduler_history()
        logs.insert(0, log_entry)
        logs = logs[:50]

        with open(SCHEDULER_LOG_FILE, 'w') as f:
            json.dump(logs, f, indent=2)

        return log_entry

    except Exception as e:
        # Log failed send
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "status": "Failed",
            "recipients": config.get("to", ""),
            "attachment": None,
            "notes": f"Error: {str(e)[:150]}"
        }

        logs = load_scheduler_history()
        logs.insert(0, log_entry)
        logs = logs[:50]

        with open(SCHEDULER_LOG_FILE, 'w') as f:
            json.dump(logs, f, indent=2)

        return log_entry


def load_scheduler_history(limit: int = 10) -> list:
    """Load scheduler history"""
    if SCHEDULER_LOG_FILE.exists():
        with open(SCHEDULER_LOG_FILE, 'r') as f:
            logs = json.load(f)
            return logs[:limit]
    return []


def upload_template(file_path: str) -> Dict[str, Any]:
    """Handle template upload"""
    config = load_scheduler_config()
    config["uploaded_template_path"] = file_path

    save_scheduler_config(config)

    return {
        "filename": Path(file_path).name,
        "path": file_path,
        "uploaded_at": datetime.now().isoformat()
    }
