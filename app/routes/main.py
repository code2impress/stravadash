"""
Main application routes (multi-user)
"""
from flask import Blueprint, render_template, current_app, session
from app.auth import requires_strava, get_current_user

main = Blueprint("main", __name__)


@main.route("/")
def index():
    """Landing page"""
    user_id = session.get("user_id")

    if user_id:
        from app.database import get_user
        user = get_user(user_id)
        if user:
            athlete_name = f"{user['firstname'] or ''} {user['lastname'] or ''}".strip()
            has_strava = user['athlete_id'] is not None
            return render_template("index.html", authenticated=True,
                                   athlete_name=athlete_name, has_strava=has_strava)

    return render_template("index.html", authenticated=False)


@main.route("/dashboard")
@requires_strava
def dashboard():
    """Main dashboard view"""
    user = get_current_user()

    athlete = {
        "id": user["athlete_id"],
        "firstname": user["firstname"],
        "lastname": user["lastname"],
        "profile": user["profile_pic"],
    } if user else {}

    return render_template(
        "dashboard.html",
        athlete=athlete,
        auto_refresh_interval=current_app.config["AUTO_REFRESH_INTERVAL"]
    )
