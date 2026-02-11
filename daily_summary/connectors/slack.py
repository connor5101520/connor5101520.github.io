"""Fetch today's Slack messages sent by the authenticated user."""

import os
from datetime import datetime

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


def fetch_slack_activity(start: datetime, end: datetime) -> str:
    token = os.environ.get("SLACK_USER_TOKEN")
    if not token:
        return ""

    client = WebClient(token=token)

    # Get the authenticated user's ID
    auth = client.auth_test()
    user_id = auth["user_id"]

    oldest = str(int(start.timestamp()))
    latest = str(int(end.timestamp()))

    # Search for messages sent by the user today
    try:
        result = client.search_messages(
            query=f"from:<@{user_id}>",
            sort="timestamp",
            sort_dir="asc",
            count=50,
        )
    except SlackApiError as e:
        if "missing_scope" in str(e):
            return _fallback_conversations(client, user_id, oldest, latest)
        raise

    matches = result.get("messages", {}).get("matches", [])
    if not matches:
        return ""

    lines = ["## Slack Messages Sent"]
    for msg in matches:
        ts = float(msg.get("ts", 0))
        if ts < float(oldest) or ts > float(latest):
            continue
        channel_name = msg.get("channel", {}).get("name", "DM")
        text = msg.get("text", "")[:200]
        lines.append(f"- #{channel_name}: {text}")

    return "\n".join(lines) if len(lines) > 1 else ""


def _fallback_conversations(client, user_id, oldest, latest) -> str:
    """Fallback: scan recent conversations for messages from the user."""
    convos = client.conversations_list(types="public_channel,private_channel,im,mpim", limit=50)
    channels = convos.get("channels", [])

    lines = ["## Slack Messages Sent"]
    for ch in channels:
        try:
            history = client.conversations_history(
                channel=ch["id"], oldest=oldest, latest=latest, limit=20
            )
        except SlackApiError:
            continue

        for msg in history.get("messages", []):
            if msg.get("user") == user_id:
                ch_name = ch.get("name", ch.get("id", "DM"))
                text = msg.get("text", "")[:200]
                lines.append(f"- #{ch_name}: {text}")

    return "\n".join(lines) if len(lines) > 1 else ""
