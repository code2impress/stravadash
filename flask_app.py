"""
Strava Dashboard Application
Entry point for Flask application
"""
from app import create_app

# Create Flask application
app = create_app()

# =========================
# RUN LOCAL
# =========================

if __name__ == "__main__":
    app.run(debug=True)