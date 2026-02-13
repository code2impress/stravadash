"""
Authentication routes for Strava and Google OAuth
"""
import secrets
from flask import Blueprint, redirect, request, url_for, flash, current_app, render_template, session
from app.auth import exchange_code_for_token, get_current_user
from app.database import (
    get_user, get_user_by_athlete_id, get_user_by_google_id, get_user_by_email,
    create_strava_user, update_strava_tokens, create_google_user,
    update_google_info, link_strava_to_user, check_make_admin
)

auth_routes = Blueprint("auth_routes", __name__)


@auth_routes.route("/login")
def login():
    """Login page with Google and Strava options."""
    if session.get("user_id"):
        return redirect(url_for("main.dashboard"))
    google_enabled = bool(current_app.config.get("GOOGLE_CLIENT_ID"))
    return render_template("auth/login.html", google_enabled=google_enabled)


# --- STRAVA OAUTH ---

@auth_routes.route("/authorize")
def authorize():
    """Redirect to Strava OAuth."""
    session["oauth_intent"] = request.args.get("intent", "login")

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
    """Handle Strava OAuth callback."""
    code = request.args.get("code")
    error = request.args.get("error")
    intent = session.pop("oauth_intent", "login")

    if error:
        flash(f"Strava authorization failed: {error}", "error")
        return render_template("auth/error.html", error=error)

    if not code:
        flash("Missing authorization code.", "error")
        return render_template("auth/error.html", error="missing_code")

    try:
        token_data = exchange_code_for_token(code)
        athlete = token_data.get("athlete", {})
        athlete_id = athlete.get("id")

        # Linking Strava to an existing Google-authenticated user
        if intent == "link" and session.get("user_id"):
            user_id = session["user_id"]
            link_strava_to_user(
                user_id=user_id,
                athlete_id=athlete_id,
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                expires_at=token_data["expires_at"],
                firstname=athlete.get("firstname"),
                lastname=athlete.get("lastname"),
                profile_pic=athlete.get("profile"),
            )
            flash("Strava account linked successfully!", "success")
            return redirect(url_for("main.dashboard"))

        # Fresh login with Strava
        existing = get_user_by_athlete_id(athlete_id)

        if existing:
            user_id = existing["id"]
            update_strava_tokens(
                user_id=user_id,
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                expires_at=token_data["expires_at"],
                firstname=athlete.get("firstname"),
                lastname=athlete.get("lastname"),
                profile_pic=athlete.get("profile"),
            )
        else:
            user_id = create_strava_user(
                athlete_id=athlete_id,
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                expires_at=token_data["expires_at"],
                firstname=athlete.get("firstname"),
                lastname=athlete.get("lastname"),
                profile_pic=athlete.get("profile"),
            )
            check_make_admin(user_id)

        session.clear()
        session["user_id"] = user_id
        session.permanent = True

        athlete_name = f"{athlete.get('firstname', '')} {athlete.get('lastname', '')}".strip()
        flash(f"Welcome, {athlete_name or 'athlete'}!", "success")
        return redirect(url_for("main.dashboard"))

    except Exception as e:
        current_app.logger.error(f"Strava OAuth error: {e}")
        flash(str(e), "error")
        return render_template("auth/error.html", error=str(e))


# --- GOOGLE OAUTH ---

@auth_routes.route("/auth/google")
def google_authorize():
    """Redirect to Google OAuth."""
    if not current_app.config.get("GOOGLE_CLIENT_ID"):
        flash("Google login is not configured.", "error")
        return redirect(url_for("auth_routes.login"))

    session["oauth_intent"] = request.args.get("intent", "login")
    session["oauth_state"] = secrets.token_urlsafe(32)

    from app.google_auth import get_google_auth_url
    auth_url = get_google_auth_url(state=session["oauth_state"])
    return redirect(auth_url)


@auth_routes.route("/auth/google/callback")
def google_callback():
    """Handle Google OAuth callback."""
    error = request.args.get("error")
    if error:
        flash(f"Google authorization failed: {error}", "error")
        return redirect(url_for("auth_routes.login"))

    state = request.args.get("state")
    if state != session.pop("oauth_state", None):
        flash("Invalid OAuth state. Please try again.", "error")
        return redirect(url_for("auth_routes.login"))

    code = request.args.get("code")
    if not code:
        flash("Missing authorization code.", "error")
        return redirect(url_for("auth_routes.login"))

    intent = session.pop("oauth_intent", "login")

    try:
        from app.google_auth import exchange_google_code, get_google_user_info

        token_data = exchange_google_code(code)
        access_token = token_data["access_token"]

        google_user = get_google_user_info(access_token)
        google_id = google_user["sub"]
        email = google_user.get("email", "")
        name = google_user.get("name", "")
        picture = google_user.get("picture", "")

        name_parts = name.split(" ", 1)
        firstname = name_parts[0] if name_parts else ""
        lastname = name_parts[1] if len(name_parts) > 1 else ""

        # Find existing user
        existing = get_user_by_google_id(google_id)
        if not existing and email:
            existing = get_user_by_email(email)

        if existing:
            user_id = existing["id"]
            update_google_info(user_id, google_id, email, firstname, lastname, picture)
        else:
            user_id = create_google_user(google_id, email, firstname, lastname, picture)
            check_make_admin(user_id)

        session.clear()
        session["user_id"] = user_id
        session.permanent = True

        flash(f"Welcome, {firstname or 'user'}!", "success")

        # If Google-only user (no Strava), redirect to link page
        user = get_user(user_id)
        if not user["athlete_id"]:
            return redirect(url_for("auth_routes.link_strava"))

        return redirect(url_for("main.dashboard"))

    except Exception as e:
        current_app.logger.error(f"Google OAuth error: {e}")
        flash("Google login failed. Please try again.", "error")
        return redirect(url_for("auth_routes.login"))


# --- STRAVA LINKING PAGE ---

@auth_routes.route("/link-strava")
def link_strava():
    """Prompt Google-only users to link their Strava account."""
    if "user_id" not in session:
        return redirect(url_for("auth_routes.login"))
    user = get_user(session["user_id"])
    if user and user["athlete_id"]:
        return redirect(url_for("main.dashboard"))
    return render_template("auth/link_strava.html", user=user)


# --- LOGOUT ---

@auth_routes.route("/logout")
def logout():
    """Logout: clear Flask session."""
    session.clear()
    flash("Successfully logged out.", "info")
    return redirect(url_for("main.index"))
