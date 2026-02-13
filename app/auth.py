"""
Authentication and token management for Strava API (multi-user with Google + Strava)
"""
import time
from functools import wraps
from flask import redirect, url_for, flash, current_app, session
import requests
from app.database import get_user, get_user_by_athlete_id, update_strava_tokens


def save_token(data, athlete_id=None):
    """Save token data to database. Used internally by exchange/refresh."""
    from app.database import upsert_user
    athlete = data.get("athlete", {})
    aid = athlete_id or athlete.get("id")

    if not aid:
        raise RuntimeError("Cannot save token: no athlete_id available")

    # For refresh (no athlete in response), just update tokens
    if athlete_id and not athlete:
        user = get_user_by_athlete_id(athlete_id)
        if user:
            update_strava_tokens(
                user_id=user["id"],
                access_token=data["access_token"],
                refresh_token=data["refresh_token"],
                expires_at=data["expires_at"]
            )
            return


def get_current_user():
    """Get the current user's DB row from session user_id."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    user = get_user(user_id)
    if user and user["is_disabled"]:
        session.clear()
        return None
    return user


def token_expired(expires_at):
    """Check if token has expired."""
    return expires_at < int(time.time())


def refresh_access_token(athlete_id, refresh_token):
    """Refresh the access token using refresh token."""
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

        save_token(data, athlete_id=athlete_id)
        return data

    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Failed to refresh token: {e}")
        raise RuntimeError("Unable to refresh authorization. Please reconnect to Strava.") from e


def get_valid_token():
    """Get a valid Strava access token for the current session user."""
    user = get_current_user()
    if not user:
        return None
    if not user["athlete_id"]:
        return None  # Google-only user, no Strava linked

    try:
        if token_expired(user["expires_at"]):
            data = refresh_access_token(user["athlete_id"], user["refresh_token"])
            return data["access_token"]
        return user["access_token"]
    except RuntimeError as e:
        current_app.logger.error(f"Failed to get valid token: {e}")
        return None


def exchange_code_for_token(code):
    """Exchange authorization code for access token."""
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

        return data

    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Failed to exchange code for token: {e}")
        raise RuntimeError("Authorization failed. Please try again.") from e


def requires_auth(f):
    """Require authentication (any method)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "info")
            return redirect(url_for("auth_routes.login"))
        user = get_current_user()
        if not user:
            session.clear()
            flash("Your session has expired. Please log in again.", "info")
            return redirect(url_for("auth_routes.login"))
        return f(*args, **kwargs)
    return decorated_function


def requires_strava(f):
    """Require Strava to be linked (for dashboard/API routes)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "info")
            return redirect(url_for("auth_routes.login"))
        user = get_current_user()
        if not user:
            session.clear()
            return redirect(url_for("auth_routes.login"))
        if not user["athlete_id"]:
            flash("Please link your Strava account to access the dashboard.", "info")
            return redirect(url_for("auth_routes.link_strava"))
        token = get_valid_token()
        if not token:
            session.clear()
            flash("Your Strava session has expired. Please reconnect.", "info")
            return redirect(url_for("auth_routes.login"))
        return f(*args, **kwargs)
    return decorated_function


def requires_admin(f):
    """Require admin privileges."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "info")
            return redirect(url_for("auth_routes.login"))
        user = get_current_user()
        if not user or not user["is_admin"]:
            flash("You do not have permission to access this page.", "error")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)
    return decorated_function


def get_athlete_id():
    """Get the Strava athlete ID from the current session user."""
    user = get_current_user()
    return user["athlete_id"] if user else None
