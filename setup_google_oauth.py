#!/usr/bin/env python3
"""One-time setup: Generate Google OAuth2 refresh token.

Run this locally to authorize the app and get a GOOGLE_TOKEN_JSON
value to store as a GitHub Secret.

Usage:
    1. Create a Google Cloud project at https://console.cloud.google.com
    2. Enable: Calendar API, Gmail API, Google Docs API, Google Drive API
    3. Create OAuth 2.0 credentials (Desktop app type)
    4. Download the credentials JSON file
    5. Run: python setup_google_oauth.py /path/to/credentials.json
    6. Copy the output JSON and save it as GOOGLE_TOKEN_JSON in GitHub Secrets
"""

import json
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/documents.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


def main():
    if len(sys.argv) < 2:
        print("Usage: python setup_google_oauth.py <path-to-credentials.json>")
        print("\nDownload OAuth credentials from Google Cloud Console first.")
        sys.exit(1)

    creds_file = sys.argv[1]
    flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
    creds = flow.run_local_server(port=8080)

    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
    }

    token_json = json.dumps(token_data)

    print("\n" + "=" * 60)
    print("SUCCESS! Copy the JSON below and save it as a GitHub Secret")
    print("named GOOGLE_TOKEN_JSON:")
    print("=" * 60)
    print(token_json)
    print("=" * 60)


if __name__ == "__main__":
    main()
