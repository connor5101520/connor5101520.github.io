"""Fetch today's meeting notes from Granola.

Granola's API (Enterprise plan) uses Bearer token auth.
Set GRANOLA_API_TOKEN in your GitHub Secrets.
If not available, this connector is silently skipped.
"""

import os
from datetime import datetime

import requests


GRANOLA_API_BASE = "https://api.granola.ai"


def fetch_granola_notes(start: datetime, end: datetime) -> str:
    token = os.environ.get("GRANOLA_API_TOKEN")
    if not token:
        return ""

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # Fetch documents (meeting notes) created/modified today
    resp = requests.post(
        f"{GRANOLA_API_BASE}/v2/get-documents",
        headers=headers,
        json={
            "start": start.isoformat(),
            "end": end.isoformat(),
        },
        timeout=30,
    )

    if resp.status_code == 401:
        return "[Granola: invalid or expired API token]"
    if resp.status_code == 403:
        return "[Granola: API access requires Enterprise plan]"

    resp.raise_for_status()
    documents = resp.json().get("documents", resp.json() if isinstance(resp.json(), list) else [])

    if not documents:
        return ""

    lines = ["## Granola Meeting Notes"]
    for doc in documents:
        title = doc.get("title", "(untitled meeting)")
        created = doc.get("created_at", doc.get("createdAt", ""))
        lines.append(f"- {title} ({created})")

        # Try to fetch the AI-generated panels/summary for this doc
        doc_id = doc.get("id")
        if doc_id:
            summary = _fetch_document_panels(headers, doc_id)
            if summary:
                lines.append(f"  Summary: {summary}")

    return "\n".join(lines)


def _fetch_document_panels(headers: dict, doc_id: str) -> str:
    """Fetch AI-generated summary panels for a specific document."""
    try:
        resp = requests.post(
            f"{GRANOLA_API_BASE}/v1/get-document-panels",
            headers=headers,
            json={"document_id": doc_id},
            timeout=15,
        )
        resp.raise_for_status()
        panels = resp.json()

        # Extract text content from panels
        texts = []
        if isinstance(panels, list):
            for panel in panels:
                content = panel.get("content", panel.get("text", ""))
                if content:
                    texts.append(str(content)[:300])
        return " | ".join(texts) if texts else ""
    except Exception:
        return ""
