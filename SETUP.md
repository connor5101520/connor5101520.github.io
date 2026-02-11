# Daily Summary Bot — Setup Guide

Automated daily email summarizing your Granola notes, Slack messages, Gmail, Calendar, and Google Docs activity. Runs via GitHub Actions at 5pm PST.

## Architecture

```
Granola API ──┐
Slack API ────┤
Gmail API ────┼──→ Claude API (summarize) ──→ SendGrid ──→ Email
Calendar API ─┤
Drive API ────┘
```

Scheduled by GitHub Actions cron. Each connector fails gracefully — if one service is unavailable, the others still work.

---

## Step 1: GitHub Secrets

Go to your repo → **Settings → Secrets and variables → Actions** and add these secrets:

| Secret Name | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Claude API key from [console.anthropic.com](https://console.anthropic.com) |
| `SENDGRID_API_KEY` | Yes | SendGrid API key (free tier: 100 emails/day) |
| `SENDGRID_SENDER_EMAIL` | Yes | Verified sender email in SendGrid |
| `GOOGLE_TOKEN_JSON` | Yes | OAuth token JSON (see Step 2) |
| `SLACK_USER_TOKEN` | Yes | Slack User OAuth Token (see Step 3) |
| `GRANOLA_API_TOKEN` | No | Granola API token (Enterprise plan only) |

---

## Step 2: Google Workspace Setup

### 2a. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (e.g., "Daily Summary Bot")
3. Enable these APIs:
   - **Google Calendar API**
   - **Gmail API**
   - **Google Docs API**
   - **Google Drive API**

### 2b. Create OAuth Credentials

1. Go to **APIs & Services → Credentials**
2. Click **Create Credentials → OAuth Client ID**
3. Application type: **Desktop app**
4. Download the credentials JSON file

### 2c. Generate Refresh Token

Run the setup script locally:

```bash
pip install google-auth-oauthlib
python setup_google_oauth.py /path/to/downloaded-credentials.json
```

This opens a browser for Google login. After authorizing, it prints a JSON string. Copy that entire JSON and save it as the `GOOGLE_TOKEN_JSON` GitHub Secret.

---

## Step 3: Slack Setup

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and create a new app
2. Under **OAuth & Permissions**, add these **User Token Scopes**:
   - `search:read` (preferred — enables message search)
   - `channels:history`, `groups:history`, `im:history`, `mpim:history` (fallback)
   - `channels:read`, `groups:read`, `im:read`, `mpim:read`
3. Install the app to your workspace
4. Copy the **User OAuth Token** (starts with `xoxp-`)
5. Save it as the `SLACK_USER_TOKEN` GitHub Secret

---

## Step 4: SendGrid Setup

1. Sign up at [sendgrid.com](https://sendgrid.com) (free tier = 100 emails/day)
2. Create an API key with **Mail Send** permission
3. Verify a sender email under **Settings → Sender Authentication**
4. Save the API key as `SENDGRID_API_KEY` and the verified email as `SENDGRID_SENDER_EMAIL`

---

## Step 5: Granola (Optional)

Granola API access requires an **Enterprise plan**.

- If you have Enterprise: get your API token from Granola admin settings
- Save it as `GRANOLA_API_TOKEN`
- If you don't have Enterprise, the connector is silently skipped

---

## Testing

Trigger the workflow manually:

1. Go to **Actions** tab in your repo
2. Select **Daily Summary Email**
3. Click **Run workflow**

Or run locally:

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-..."
export GOOGLE_TOKEN_JSON='{"refresh_token":"...","client_id":"...","client_secret":"..."}'
export SLACK_USER_TOKEN="xoxp-..."
export SENDGRID_API_KEY="SG..."
export SENDGRID_SENDER_EMAIL="you@example.com"
python -m daily_summary.main
```

---

## Schedule

The GitHub Actions workflow runs daily at **5:00 PM PST** (1:00 AM UTC). You can adjust the schedule in `.github/workflows/daily-summary.yml`.
