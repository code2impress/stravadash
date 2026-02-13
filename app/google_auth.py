"""
Google OAuth 2.0 authentication (manual implementation using requests).
"""
import requests
from flask import current_app
from urllib.parse import quote

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def get_google_auth_url(state=None):
    """Build the Google OAuth authorization URL."""
    params = {
        "client_id": current_app.config["GOOGLE_CLIENT_ID"],
        "redirect_uri": current_app.config["GOOGLE_REDIRECT_URI"],
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    if state:
        params["state"] = state

    query = "&".join(f"{k}={quote(str(v))}" for k, v in params.items())
    return f"{GOOGLE_AUTH_URL}?{query}"


def exchange_google_code(code):
    """Exchange authorization code for tokens."""
    r = requests.post(GOOGLE_TOKEN_URL, data={
        "client_id": current_app.config["GOOGLE_CLIENT_ID"],
        "client_secret": current_app.config["GOOGLE_CLIENT_SECRET"],
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": current_app.config["GOOGLE_REDIRECT_URI"],
    }, timeout=10)
    r.raise_for_status()
    return r.json()


def get_google_user_info(access_token):
    """Fetch user profile from Google."""
    r = requests.get(GOOGLE_USERINFO_URL, headers={
        "Authorization": f"Bearer {access_token}"
    }, timeout=10)
    r.raise_for_status()
    return r.json()
