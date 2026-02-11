"""Summarize the day's activities using the Claude API."""

import os

import anthropic


def summarize_day(activities: dict[str, str]) -> str:
    """Take raw activity data from all connectors and return a polished summary."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # Build the context from all connectors
    sections = []
    source_labels = {
        "google_calendar": "Google Calendar Events",
        "gmail": "Gmail Activity",
        "google_docs": "Google Docs Activity",
        "slack": "Slack Messages",
        "granola": "Granola Meeting Notes",
    }

    for key, data in activities.items():
        if data and not str(data).startswith("[Error"):
            label = source_labels.get(key, key)
            sections.append(f"### {label}\n{data}")

    raw_data = "\n\n".join(sections)

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": f"""You are a personal productivity assistant. Based on the following raw
activity data from today, write a concise, well-organized daily summary email.

Guidelines:
- Start with a brief 2-3 sentence overview of the day's highlights
- Organize by theme/project, NOT by data source
- Highlight key meetings, decisions, and action items
- Note important emails sent or received
- Mention any documents worked on
- Keep it scannable — use bullet points and short paragraphs
- End with a brief "Action Items / Follow-ups" section if applicable
- Tone: professional but friendly, like a chief of staff briefing
- Do NOT include headers like "Daily Summary" — that will be added by the email template

Here is today's raw activity data:

{raw_data}""",
            }
        ],
    )

    return message.content[0].text
