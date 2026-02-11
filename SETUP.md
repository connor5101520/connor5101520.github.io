# Daily Summary Bot — Setup Guide

A single Google Apps Script that collects your Gmail, Calendar, Docs, Slack, and Granola activity, summarizes it with Claude, and emails you at 5pm PST.

## Setup (5 minutes)

### 1. Create the Script

1. Go to [script.google.com](https://script.google.com)
2. Click **New Project**
3. Delete the placeholder code, paste the contents of `daily-summary.gs`
4. Save (Ctrl+S), name it "Daily Summary Bot"

### 2. Add API Keys

Go to **Project Settings** (gear icon) → **Script Properties** → **Add Script Property**:

| Property | Required | How to get it |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | [console.anthropic.com](https://console.anthropic.com) → API Keys |
| `SLACK_USER_TOKEN` | Yes | See "Slack Setup" below |
| `GRANOLA_API_TOKEN` | No | Granola Enterprise admin settings |

### 3. Authorize & Test

1. In the script editor, select `sendDailySummary` from the function dropdown
2. Click **Run**
3. Google will ask you to authorize access to Gmail, Calendar, and Drive — click through
4. Check your email at `connor.smith@atlan.com`

### 4. Schedule It

1. Click the **clock icon** (Triggers) in the left sidebar
2. Click **Add Trigger**:
   - Function: `sendDailySummary`
   - Event source: **Time-driven**
   - Type: **Day timer**
   - Time: **5pm to 6pm**
3. Save

That's it — you'll get a daily summary email every evening.

---

## Slack Setup

1. Go to [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → **From scratch**
2. Name it "Daily Summary Bot", select your workspace
3. Go to **OAuth & Permissions** → **User Token Scopes**, add:
   - `search:read` (preferred)
   - `channels:history`, `groups:history`, `im:history`, `mpim:history` (fallback)
   - `channels:read`, `groups:read`, `im:read`, `mpim:read`
4. Click **Install to Workspace**, authorize
5. Copy the **User OAuth Token** (`xoxp-...`)

---

## Granola (Optional)

Granola API access requires an **Enterprise plan**. If you have it, add your API token as the `GRANOLA_API_TOKEN` script property. Otherwise it's silently skipped.
