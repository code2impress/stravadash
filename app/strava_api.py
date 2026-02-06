"""
Strava API wrapper with error handling, retry logic, and rate limiting
"""
import time
import requests
from flask import current_app


class StravaAPIError(Exception):
    """Base exception for Strava API errors"""
    pass


class RateLimitError(StravaAPIError):
    """Raised when rate limit is exceeded"""
    def __init__(self, message, retry_after=60):
        super().__init__(message)
        self.retry_after = retry_after


class AuthenticationError(StravaAPIError):
    """Raised when authentication fails"""
    pass


class StravaAPI:
    """Wrapper for Strava API v3"""

    BASE_URL = "https://www.strava.com/api/v3"

    def __init__(self, access_token):
        self.access_token = access_token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {access_token}"
        })

    def _make_request(self, method, endpoint, params=None, max_retries=3):
        """
        Make HTTP request with error handling and retry logic
        """
        url = f"{self.BASE_URL}/{endpoint}"

        for attempt in range(max_retries):
            try:
                response = self.session.request(
                    method,
                    url,
                    params=params,
                    timeout=15
                )

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    raise RateLimitError(
                        "Rate limit exceeded. Please wait before making more requests.",
                        retry_after=retry_after
                    )

                # Handle authentication errors
                if response.status_code == 401:
                    raise AuthenticationError(
                        "Authentication failed. Please reconnect your Strava account."
                    )

                # Handle other errors
                response.raise_for_status()

                # Log rate limit usage
                limit_15min = response.headers.get("X-RateLimit-Limit", "").split(",")
                usage_15min = response.headers.get("X-RateLimit-Usage", "").split(",")
                if limit_15min and usage_15min:
                    current_app.logger.debug(
                        f"Strava API rate limit: {usage_15min[0]}/{limit_15min[0]} (15min), "
                        f"{usage_15min[1]}/{limit_15min[1]} (daily)"
                    )

                return response.json()

            except requests.exceptions.Timeout:
                if attempt == max_retries - 1:
                    raise StravaAPIError("Request timed out. Please try again.")
                time.sleep(1 * (attempt + 1))  # Exponential backoff

            except requests.exceptions.ConnectionError:
                if attempt == max_retries - 1:
                    raise StravaAPIError("Connection error. Please check your internet connection.")
                time.sleep(1 * (attempt + 1))

            except requests.exceptions.HTTPError as e:
                if e.response.status_code >= 500:
                    if attempt == max_retries - 1:
                        raise StravaAPIError("Strava service is temporarily unavailable. Please try again later.")
                    time.sleep(2 * (attempt + 1))
                else:
                    raise StravaAPIError(f"API error: {e.response.status_code}")

        raise StravaAPIError("Maximum retries exceeded")

    def get_athlete_activities(self, per_page=30, page=1, before=None, after=None):
        """
        Get athlete activities

        Args:
            per_page: Number of activities per page (max 200)
            page: Page number
            before: Unix timestamp to get activities before
            after: Unix timestamp to get activities after
        """
        params = {
            "per_page": min(per_page, 200),
            "page": page
        }

        if before:
            params["before"] = before
        if after:
            params["after"] = after

        return self._make_request("GET", "athlete/activities", params=params)

    def get_activity_details(self, activity_id):
        """
        Get detailed information about a specific activity

        Args:
            activity_id: The Strava activity ID
        """
        return self._make_request("GET", f"activities/{activity_id}")

    def get_athlete_stats(self, athlete_id):
        """
        Get athlete statistics

        Args:
            athlete_id: The Strava athlete ID
        """
        return self._make_request("GET", f"athletes/{athlete_id}/stats")

    def get_athlete(self):
        """Get authenticated athlete information"""
        return self._make_request("GET", "athlete")
