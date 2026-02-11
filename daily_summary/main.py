"""Daily Summary — main orchestrator.

Collects activity from all configured connectors, summarizes with Claude,
and emails the result.
"""

from datetime import datetime

import pytz

from daily_summary.connectors.google_calendar import fetch_calendar_events
from daily_summary.connectors.gmail import fetch_gmail_activity
from daily_summary.connectors.google_docs import fetch_docs_activity
from daily_summary.connectors.slack import fetch_slack_activity
from daily_summary.connectors.granola import fetch_granola_notes
from daily_summary.summarizer import summarize_day
from daily_summary.emailer import send_summary_email


CONNECTORS = {
    "google_calendar": fetch_calendar_events,
    "gmail": fetch_gmail_activity,
    "google_docs": fetch_docs_activity,
    "slack": fetch_slack_activity,
    "granola": fetch_granola_notes,
}


def get_today_range():
    """Return (start_of_day, now) in Pacific time."""
    pst = pytz.timezone("America/Los_Angeles")
    now = datetime.now(pst)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, now


def run():
    start, end = get_today_range()
    print(f"Collecting activity for {start.strftime('%Y-%m-%d')} ...")

    activities = {}
    for name, fetch_fn in CONNECTORS.items():
        try:
            print(f"  → {name}")
            data = fetch_fn(start, end)
            if data:
                activities[name] = data
                print(f"    ✓ got data ({len(data)} chars)")
            else:
                print(f"    — no data")
        except Exception as e:
            print(f"    ✗ error: {e}")
            activities[name] = f"[Error fetching {name}: {e}]"

    # Check if we got any real data
    real_data = {k: v for k, v in activities.items() if v and not str(v).startswith("[Error")}
    if not real_data:
        print("No activity data collected from any source. Skipping summary.")
        return

    print(f"\nSummarizing {len(real_data)} sources with Claude ...")
    summary = summarize_day(activities)

    print("Sending email ...")
    send_summary_email(summary, end)

    print("Done! Daily summary sent successfully.")


if __name__ == "__main__":
    run()
