"""Google OAuth2 authentication helper.

Uses a stored refresh token (from GitHub Secrets) to obtain
access tokens for Gmail, Calendar, and Docs APIs.
"""

import json
import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/documents.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


def get_credentials() -> Credentials:
    """Build Credentials from environment variables set via GitHub Secrets."""
    token_json = os.environ.get("GOOGLE_TOKEN_JSON")
    if not token_json:
        raise EnvironmentError(
            "GOOGLE_TOKEN_JSON secret is not set. "
            "Run setup_google_oauth.py locally to generate it."
        )

    token_data = json.loads(token_json)
    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
        scopes=SCOPES,
    )
    return creds


def get_service(api: str, version: str):
    """Return an authenticated Google API service client."""
    creds = get_credentials()
    return build(api, version, credentials=creds)
