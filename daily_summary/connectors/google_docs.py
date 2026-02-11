"""Fetch Google Docs/Drive files modified today."""

from datetime import datetime

from daily_summary.google_auth import get_service


def fetch_docs_activity(start: datetime, end: datetime) -> str:
    drive_service = get_service("drive", "v3")

    query = (
        f"modifiedTime >= '{start.isoformat()}' "
        f"and mimeType = 'application/vnd.google-apps.document' "
        f"and 'me' in owners"
    )

    results = (
        drive_service.files()
        .list(
            q=query,
            fields="files(id, name, modifiedTime, webViewLink)",
            orderBy="modifiedTime desc",
            pageSize=20,
        )
        .execute()
    )

    files = results.get("files", [])
    if not files:
        return ""

    lines = ["## Google Docs Modified Today"]
    for f in files:
        lines.append(f"- {f['name']} (modified {f['modifiedTime']})")
        if f.get("webViewLink"):
            lines.append(f"  Link: {f['webViewLink']}")

    return "\n".join(lines)
