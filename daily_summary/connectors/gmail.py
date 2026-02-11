"""Fetch today's Gmail sent and received message summaries."""

import base64
from datetime import datetime

from daily_summary.google_auth import get_service


def _decode_header(headers: list, name: str) -> str:
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def _fetch_messages(service, query: str, max_results: int = 30) -> list[dict]:
    """Fetch message metadata matching a Gmail query."""
    result = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_results)
        .execute()
    )

    messages = []
    for msg_stub in result.get("messages", []):
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=msg_stub["id"], format="metadata",
                 metadataHeaders=["From", "To", "Subject", "Date"])
            .execute()
        )
        headers = msg.get("payload", {}).get("headers", [])
        messages.append({
            "from": _decode_header(headers, "From"),
            "to": _decode_header(headers, "To"),
            "subject": _decode_header(headers, "Subject"),
            "date": _decode_header(headers, "Date"),
            "snippet": msg.get("snippet", ""),
        })

    return messages


def fetch_gmail_activity(start: datetime, end: datetime) -> str:
    service = get_service("gmail", "v1")

    date_str = start.strftime("%Y/%m/%d")
    received = _fetch_messages(service, f"after:{date_str} in:inbox", max_results=20)
    sent = _fetch_messages(service, f"after:{date_str} in:sent", max_results=20)

    lines = []

    if received:
        lines.append("## Emails Received")
        for m in received:
            lines.append(f"- From: {m['from']} | Subject: {m['subject']}")
            if m["snippet"]:
                lines.append(f"  Preview: {m['snippet'][:120]}")

    if sent:
        lines.append("\n## Emails Sent")
        for m in sent:
            lines.append(f"- To: {m['to']} | Subject: {m['subject']}")
            if m["snippet"]:
                lines.append(f"  Preview: {m['snippet'][:120]}")

    return "\n".join(lines)
