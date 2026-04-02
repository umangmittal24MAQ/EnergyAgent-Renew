"""
Standalone entry point for OS-level schedulers (cron/Task Scheduler).
Run this script daily at 10:00 AM IST to execute the flag-based automation flow.
"""

import json
import sys
import time
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from api.services import scheduler_service


def main() -> None:
    attempt = 0
    final_result = {}

    while True:
        attempt += 1

        check_result = scheduler_service.check_master_data_today_flag()
        FOUND = bool(check_result.get("found", False))
        date_checked = str(check_result.get("date_checked", ""))
        notes = str(check_result.get("notes", ""))

        if FOUND is False:
            notify_result = scheduler_service.send_stakeholder_pending_notification()
            action = "found_false_notified_stakeholder_waiting_30_minutes"
            notes = f"{notes}; notification_status={notify_result.get('status', 'Unknown')}; attempt={attempt}"

            scheduler_service._log_daily_check_attempt(
                date_checked=date_checked,
                found=FOUND,
                action=action,
                trigger_source="os_scheduler_10am",
                notes=notes,
            )

            final_result = {
                "attempt": attempt,
                "found": FOUND,
                "action": action,
                "notification": notify_result,
            }

            time.sleep(scheduler_service.RETRY_INTERVAL_MINUTES * 60)

        if FOUND is True:
            report_result = scheduler_service.send_daily_report_email_from_settings()
            action = "found_true_daily_report_sent"
            notes = f"{notes}; report_status={report_result.get('status', 'Unknown')}; attempt={attempt}"

            scheduler_service._log_daily_check_attempt(
                date_checked=date_checked,
                found=FOUND,
                action=action,
                trigger_source="os_scheduler_10am",
                notes=notes,
            )

            final_result = {
                "attempt": attempt,
                "found": FOUND,
                "action": action,
                "daily_report": report_result,
            }
            break

    print(json.dumps(final_result, indent=2, default=str))


if __name__ == "__main__":
    main()
