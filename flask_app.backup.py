from flask import Flask, redirect, request, jsonify
import requests
import os
import time
import json

app = Flask(__name__)

# =========================
# CONFIG
# =========================

CLIENT_ID = os.getenv("STRAVA_CLIENT_ID", "195807")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET", "YOUR_CLIENT_SECRET")
REDIRECT_URI = os.getenv(
    "STRAVA_REDIRECT_URI",
    "https://dittrime.pythonanywhere.com/authorized"
)

TOKEN_FILE = "strava_token.json"

# =========================
# TOKEN HANDLING
# =========================

def save_token(data):
    with open(TOKEN_FILE, "w") as f:
        json.dump(data, f)

def load_token():
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE, "r") as f:
        return json.load(f)

def token_expired(token):
    return token["expires_at"] < int(time.time())

def refresh_access_token(refresh_token):
    r = requests.post(
        "https://www.strava.com/api/v3/oauth/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
    ).json()

    if "access_token" not in r:
        raise RuntimeError("Token refresh failed")

    save_token(r)
    return r

def get_valid_token():
    token = load_token()
    if not token:
        return None

    if token_expired(token):
        token = refresh_access_token(token["refresh_token"])

    return token["access_token"]

# =========================
# ROUTES
# =========================

@app.route("/")
def index():
    return "✅ Strava Flask backend running"

@app.route("/authorize")
def authorize():
    return redirect(
        "https://www.strava.com/oauth/authorize"
        f"?client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        f"&approval_prompt=force"
        f"&scope=read,activity:read"
    )

@app.route("/authorized")
def authorized():
    code = request.args.get("code")
    if not code:
        return "Missing authorization code", 400

    r = requests.post(
        "https://www.strava.com/api/v3/oauth/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
        },
    ).json()

    if "access_token" not in r:
        return jsonify(r), 400

    save_token(r)

    # 🔁 redirect after success
    return redirect("/fitness_data")

@app.route("/fitness_data")
def fitness_data():
    token = get_valid_token()
    if not token:
        return redirect("/authorize")

    r = requests.get(
        "https://www.strava.com/api/v3/athlete/activities",
        headers={"Authorization": f"Bearer {token}"},
        params={"per_page": 30},
    )

    return jsonify(r.json())

# =========================
# RUN LOCAL
# =========================

if __name__ == "__main__":
    app.run(debug=True)