"""
Authentication and token management for Strava API
"""
import os
import json
import time
from functools import wraps
from flask import redirect, url_for, flash, current_app
import requests


def save_token(data):
    """Save token data to file"""
    token_file = current_app.config["TOKEN_FILE"]
    try:
        with open(token_file, "w") as f:
            json.dump(data, f)
    except IOError as e:
        current_app.logger.error(f"Failed to save token: {e}")
        raise


def load_token():
    """Load token data from file"""
    token_file = current_app.config["TOKEN_FILE"]
    if not os.path.exists(token_file):
        return None
    try:
        with open(token_file, "r") as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        current_app.logger.error(f"Failed to load token: {e}")
        return None


def token_expired(token):
    """Check if token has expired"""
    return token["expires_at"] < int(time.time())


def refresh_access_token(refresh_token):
    """Refresh the access token using refresh token"""
    try:
        r = requests.post(
            "https://www.strava.com/api/v3/oauth/token",
            data={
                "client_id": current_app.config["STRAVA_CLIENT_ID"],
                "client_secret": current_app.config["STRAVA_CLIENT_SECRET"],
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            timeout=10
        )
        r.raise_for_status()
        data = r.json()

        if "access_token" not in data:
            raise RuntimeError("Token refresh failed: no access_token in response")

        save_token(data)
        return data

    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Failed to refresh token: {e}")
        raise RuntimeError(f"Unable to refresh authorization. Please reconnect to Strava.") from e


def get_valid_token():
    """
    Get a valid access token, refreshing if necessary
    Returns None if no token exists or refresh fails
    """
    token = load_token()
    if not token:
        return None

    try:
        if token_expired(token):
            token = refresh_access_token(token["refresh_token"])
        return token["access_token"]
    except RuntimeError as e:
        current_app.logger.error(f"Failed to get valid token: {e}")
        return None


def exchange_code_for_token(code):
    """
    Exchange authorization code for access token
    Returns token data or raises exception
    """
    try:
        r = requests.post(
            "https://www.strava.com/api/v3/oauth/token",
            data={
                "client_id": current_app.config["STRAVA_CLIENT_ID"],
                "client_secret": current_app.config["STRAVA_CLIENT_SECRET"],
                "code": code,
                "grant_type": "authorization_code",
            },
            timeout=10
        )
        r.raise_for_status()
        data = r.json()

        if "access_token" not in data:
            raise RuntimeError("Authorization failed: no access_token in response")

        save_token(data)
        return data

    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Failed to exchange code for token: {e}")
        raise RuntimeError("Authorization failed. Please try again.") from e


def requires_auth(f):
    """
    Decorator to require authentication for routes
    Redirects to /authorize if no valid token exists
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_valid_token()
        if not token:
            flash("Please connect your Strava account to continue.", "info")
            return redirect(url_for("auth_routes.authorize"))
        return f(*args, **kwargs)
    return decorated_function


def get_athlete_id():
    """Get the athlete ID from stored token"""
    token = load_token()
    if token and "athlete" in token:
        return token["athlete"].get("id")
    return None
