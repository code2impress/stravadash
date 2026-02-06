"""
Authentication routes for Strava OAuth
"""
from flask import Blueprint, redirect, request, url_for, flash, current_app, render_template
from app.auth import exchange_code_for_token

auth_routes = Blueprint("auth_routes", __name__)


@auth_routes.route("/authorize")
def authorize():
    """Redirect to Strava OAuth authorization page"""
    client_id = current_app.config["STRAVA_CLIENT_ID"]
    redirect_uri = current_app.config["STRAVA_REDIRECT_URI"]

    auth_url = (
        f"https://www.strava.com/oauth/authorize"
        f"?client_id={client_id}"
        f"&response_type=code"
        f"&redirect_uri={redirect_uri}"
        f"&approval_prompt=force"
        f"&scope=read,activity:read"
    )

    return redirect(auth_url)


@auth_routes.route("/authorized")
def authorized():
    """Handle OAuth callback from Strava"""
    code = request.args.get("code")
    error = request.args.get("error")

    # Check for authorization error
    if error:
        flash(f"Authorization failed: {error}", "error")
        return render_template("auth/error.html", error=error)

    if not code:
        flash("Missing authorization code. Please try again.", "error")
        return render_template("auth/error.html", error="missing_code")

    try:
        # Exchange code for token
        token_data = exchange_code_for_token(code)

        # Get athlete info from token
        athlete = token_data.get("athlete", {})
        athlete_name = f"{athlete.get('firstname', '')} {athlete.get('lastname', '')}".strip()

        flash(f"Successfully connected to Strava! Welcome, {athlete_name or 'athlete'}!", "success")
        return redirect(url_for("main.dashboard"))

    except RuntimeError as e:
        current_app.logger.error(f"OAuth error: {e}")
        flash(str(e), "error")
        return render_template("auth/error.html", error=str(e))


@auth_routes.route("/logout")
def logout():
    """Logout and clear tokens"""
    import os
    token_file = current_app.config["TOKEN_FILE"]

    try:
        if os.path.exists(token_file):
            os.remove(token_file)
        flash("Successfully disconnected from Strava.", "info")
    except Exception as e:
        current_app.logger.error(f"Error during logout: {e}")
        flash("Error disconnecting. Please try again.", "error")

    return redirect(url_for("main.index"))
