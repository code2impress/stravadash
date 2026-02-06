"""
Main application routes
"""
from flask import Blueprint, render_template, current_app
from app.auth import requires_auth, get_valid_token, load_token

main = Blueprint("main", __name__)


@main.route("/")
def index():
    """Landing page"""
    # Check if user is already authenticated
    token = load_token()

    if token:
        athlete = token.get("athlete", {})
        athlete_name = f"{athlete.get('firstname', '')} {athlete.get('lastname', '')}".strip()
        return render_template("index.html", authenticated=True, athlete_name=athlete_name)

    return render_template("index.html", authenticated=False)


@main.route("/dashboard")
@requires_auth
def dashboard():
    """Main dashboard view"""
    token = load_token()
    athlete = token.get("athlete", {}) if token else {}

    return render_template(
        "dashboard.html",
        athlete=athlete,
        auto_refresh_interval=current_app.config["AUTO_REFRESH_INTERVAL"]
    )
