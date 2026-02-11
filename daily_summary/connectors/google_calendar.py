"""Fetch today's Google Calendar events."""

from datetime import datetime

from daily_summary.google_auth import get_service


def fetch_calendar_events(start: datetime, end: datetime) -> str:
    service = get_service("calendar", "v3")

    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=start.isoformat(),
            timeMax=end.isoformat(),
            singleEvents=True,
            orderBy="startTime",
            maxResults=50,
        )
        .execute()
    )

    events = events_result.get("items", [])
    if not events:
        return ""

    lines = []
    for event in events:
        event_start = event["start"].get("dateTime", event["start"].get("date"))
        summary = event.get("summary", "(no title)")
        attendees = event.get("attendees", [])
        attendee_names = [a.get("displayName", a.get("email", "")) for a in attendees]
        status = event.get("status", "")

        line = f"- {event_start}: {summary}"
        if attendee_names:
            line += f" (with {', '.join(attendee_names[:5])})"
        if status == "cancelled":
            line += " [CANCELLED]"
        lines.append(line)

    return "\n".join(lines)
