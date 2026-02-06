import os
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

    # Token storage
    TOKEN_FILE = "strava_token.json"

    # Cache configuration
    CACHE_TYPE = "FileSystemCache"
    CACHE_DIR = "cache"
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    CACHE_THRESHOLD = 500  # Maximum number of cached items

    # Strava API rate limits
    STRAVA_RATE_LIMIT_15MIN = 100
    STRAVA_RATE_LIMIT_DAILY = 1000

    # Auto-refresh interval (milliseconds)
    AUTO_REFRESH_INTERVAL = 300000  # 5 minutes


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    STRAVA_REDIRECT_URI = os.getenv(
        "STRAVA_REDIRECT_URI",
        "http://localhost:5000/authorized"
    )


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # Use environment variables for all sensitive data in production


# Configuration dictionary
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig
}
