import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    # Strava API Configuration
    STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID", "195807")
    STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET", "YOUR_CLIENT_SECRET")
    STRAVA_REDIRECT_URI = os.getenv(
        "STRAVA_REDIRECT_URI",
        "https://dittrime.pythonanywhere.com/authorized"
    )

    # Google OAuth Configuration
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI = os.getenv(
        "GOOGLE_REDIRECT_URI",
        "https://dittrime.pythonanywhere.com/auth/google/callback"
    )

    # Admin Configuration
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")

    # Database
    DATABASE = os.getenv("DATABASE", "strava_users.db")

    # Session security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)

    # Cache configuration
    CACHE_TYPE = "FileSystemCache"
    CACHE_DIR = "cache"
    CACHE_DEFAULT_TIMEOUT = 300
    CACHE_THRESHOLD = 500

    # Strava API rate limits
    STRAVA_RATE_LIMIT_15MIN = 100
    STRAVA_RATE_LIMIT_DAILY = 1000

    # Auto-refresh interval (milliseconds)
    AUTO_REFRESH_INTERVAL = 300000


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    STRAVA_REDIRECT_URI = os.getenv(
        "STRAVA_REDIRECT_URI",
        "http://localhost:5000/authorized"
    )
    GOOGLE_REDIRECT_URI = os.getenv(
        "GOOGLE_REDIRECT_URI",
        "http://localhost:5000/auth/google/callback"
    )


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig
}
