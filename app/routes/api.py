"""
JSON API endpoints for AJAX requests
"""
from flask import Blueprint, jsonify, request, current_app
from app.auth import requires_strava, get_valid_token, get_athlete_id
from app.strava_api import StravaAPI, StravaAPIError, RateLimitError, AuthenticationError
from app.cache import cache, get_activities_cache_key, get_stats_cache_key, clear_athlete_cache
from app.stats import (
    calculate_totals, calculate_averages, find_personal_records,
    group_by_activity_type, calculate_weekly_summary, calculate_monthly_summary,
    calculate_yearly_summary, prepare_chart_data
)
from app.utils import filter_activities, parse_date_range

api = Blueprint("api", __name__, url_prefix="/api")


def error_response(message, error_type="error", status_code=400, **kwargs):
    """Generate consistent error response"""
    return jsonify({
        "success": False,
        "error": {
            "type": error_type,
            "message": message,
            **kwargs
        }
    }), status_code


def success_response(data):
    """Generate consistent success response"""
    return jsonify({
        "success": True,
        "data": data
    })


def fetch_all_activities(strava_api, max_activities=None):
    """
    Fetch all activities using time-based pagination for complete history

    Args:
        strava_api: StravaAPI instance
        max_activities: Maximum number of activities to fetch (None = all)

    Returns:
        List of all activities
    """
    from datetime import datetime

    all_activities = []
    per_page = 200  # Maximum allowed by Strava
    before = None  # Start with no time limit (most recent)
    iteration = 0
    max_iterations = 100  # Safety limit (100 * 200 = 20,000 activities max)

    while iteration < max_iterations:
        # Fetch batch of activities
        activities = strava_api.get_athlete_activities(
            per_page=per_page,
            page=1,  # Always use page 1 with time-based pagination
            before=before
        )

        if not activities:
            current_app.logger.info(f"No more activities. Stopping at iteration {iteration}")
            break

        # Add to our collection
        all_activities.extend(activities)
        iteration += 1

        current_app.logger.info(
            f"Batch {iteration}: Fetched {len(activities)} activities, "
            f"total: {len(all_activities)}, "
            f"oldest: {activities[-1].get('start_date', 'unknown')[:10]}"
        )

        # Stop if we've reached max_activities
        if max_activities and len(all_activities) >= max_activities:
            all_activities = all_activities[:max_activities]
            break

        # Stop if we got fewer than requested (reached the end)
        if len(activities) < per_page:
            current_app.logger.info(f"Got {len(activities)} < {per_page}. Reached end of history.")
            break

        # Use the timestamp of the oldest activity for next batch
        oldest_timestamp = activities[-1].get('start_date')
        if oldest_timestamp:
            dt = datetime.strptime(oldest_timestamp, "%Y-%m-%dT%H:%M:%SZ")
            before = int(dt.timestamp())
        else:
            break

    current_app.logger.info(f"✅ Total activities fetched: {len(all_activities)}")
    return all_activities


@api.route("/activities")
@requires_strava
def get_activities():
    """
    Get activities with optional filtering
    Query params: type, start_date, end_date, min_distance, max_distance, search, page, per_page
    """
    try:
        token = get_valid_token()
        athlete_id = get_athlete_id()

        if not token or not athlete_id:
            return error_response("Authentication required", "auth_error", 401)

        # Get query parameters
        activity_type = request.args.get("type")
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        min_distance = request.args.get("min_distance", type=float)
        max_distance = request.args.get("max_distance", type=float)
        search_query = request.args.get("search")
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 30, type=int)

        # Generate cache key based on page only (we'll filter client-side for now)
        cache_key = get_activities_cache_key(athlete_id, page=page, per_page=per_page)

        # Try to get from cache
        activities = cache.get(cache_key)

        if activities is None:
            # Fetch from Strava API
            strava_api = StravaAPI(token)

            # Parse date range if provided
            start_timestamp, end_timestamp = parse_date_range(start_date_str, end_date_str)

            activities = strava_api.get_athlete_activities(
                per_page=per_page,
                page=page,
                after=start_timestamp,
                before=end_timestamp
            )

            # Cache for 5 minutes
            cache.set(cache_key, activities, timeout=300)

        # Apply client-side filters
        filtered_activities = filter_activities(
            activities,
            activity_type=activity_type,
            start_date=None,  # Already filtered by API
            end_date=None,
            min_distance=min_distance * 1000 if min_distance else None,  # Convert km to m
            max_distance=max_distance * 1000 if max_distance else None,
            search_query=search_query
        )

        return success_response({
            "activities": filtered_activities,
            "count": len(filtered_activities),
            "page": page,
            "per_page": per_page
        })

    except RateLimitError as e:
        return error_response(str(e), "rate_limit", 429, retry_after=e.retry_after)

    except AuthenticationError as e:
        return error_response(str(e), "auth_error", 401)

    except StravaAPIError as e:
        current_app.logger.error(f"Strava API error: {e}")
        return error_response(str(e), "api_error", 500)

    except Exception as e:
        current_app.logger.error(f"Unexpected error in get_activities: {e}")
        return error_response("An unexpected error occurred", "server_error", 500)


@api.route("/activity/<int:activity_id>")
@requires_strava
def get_activity(activity_id):
    """Get detailed information about a specific activity"""
    try:
        token = get_valid_token()
        athlete_id = get_athlete_id()

        if not token or not athlete_id:
            return error_response("Authentication required", "auth_error", 401)

        # Try cache first
        cache_key = f"strava:{athlete_id}:activity:{activity_id}"
        activity = cache.get(cache_key)

        if activity is None:
            strava_api = StravaAPI(token)
            activity = strava_api.get_activity_details(activity_id)

            # Cache for 30 minutes
            cache.set(cache_key, activity, timeout=1800)

        return success_response({"activity": activity})

    except StravaAPIError as e:
        return error_response(str(e), "api_error", 500)

    except Exception as e:
        current_app.logger.error(f"Error getting activity {activity_id}: {e}")
        return error_response("Failed to fetch activity details", "server_error", 500)


@api.route("/stats")
@requires_strava
def get_stats():
    """Get calculated statistics for all activities"""
    try:
        token = get_valid_token()
        athlete_id = get_athlete_id()

        if not token or not athlete_id:
            return error_response("Authentication required", "auth_error", 401)

        # Try cache first
        cache_key = get_stats_cache_key(athlete_id)
        stats = cache.get(cache_key)

        if stats is None:
            # Fetch ALL activities using pagination
            strava_api = StravaAPI(token)
            current_app.logger.info("Fetching all activities from Strava...")
            activities = fetch_all_activities(strava_api)
            current_app.logger.info(f"Fetched {len(activities)} total activities")

            # Calculate statistics
            totals = calculate_totals(activities)
            averages = calculate_averages(activities)
            prs = find_personal_records(activities)
            by_type = group_by_activity_type(activities)
            chart_data = prepare_chart_data(activities)
            yearly_stats = calculate_yearly_summary(activities)

            stats = {
                "totals": totals,
                "averages": averages,
                "personal_records": prs,
                "by_type": by_type,
                "chart_data": chart_data,
                "yearly_stats": yearly_stats
            }

            # Cache for 5 minutes
            cache.set(cache_key, stats, timeout=300)

        return success_response(stats)

    except StravaAPIError as e:
        return error_response(str(e), "api_error", 500)

    except Exception as e:
        current_app.logger.error(f"Error calculating stats: {e}")
        return error_response("Failed to calculate statistics", "server_error", 500)


@api.route("/stats/weekly")
@requires_strava
def get_weekly_stats():
    """Get weekly summary statistics"""
    try:
        token = get_valid_token()
        athlete_id = get_athlete_id()

        if not token or not athlete_id:
            return error_response("Authentication required", "auth_error", 401)

        weeks = request.args.get("weeks", 4, type=int)

        strava_api = StravaAPI(token)
        activities = strava_api.get_athlete_activities(per_page=200)

        weekly_summary = calculate_weekly_summary(activities, weeks=weeks)

        return success_response({"weekly_summary": weekly_summary})

    except StravaAPIError as e:
        return error_response(str(e), "api_error", 500)

    except Exception as e:
        current_app.logger.error(f"Error calculating weekly stats: {e}")
        return error_response("Failed to calculate weekly statistics", "server_error", 500)


@api.route("/stats/monthly")
@requires_strava
def get_monthly_stats():
    """Get monthly summary statistics"""
    try:
        token = get_valid_token()
        athlete_id = get_athlete_id()

        if not token or not athlete_id:
            return error_response("Authentication required", "auth_error", 401)

        months = request.args.get("months", 6, type=int)

        strava_api = StravaAPI(token)
        activities = strava_api.get_athlete_activities(per_page=200)

        monthly_summary = calculate_monthly_summary(activities, months=months)

        return success_response({"monthly_summary": monthly_summary})

    except StravaAPIError as e:
        return error_response(str(e), "api_error", 500)

    except Exception as e:
        current_app.logger.error(f"Error calculating monthly stats: {e}")
        return error_response("Failed to calculate monthly statistics", "server_error", 500)


@api.route("/refresh", methods=["POST"])
@requires_strava
def refresh_data():
    """Force refresh cached data"""
    try:
        athlete_id = get_athlete_id()

        if not athlete_id:
            return error_response("Authentication required", "auth_error", 401)

        # Clear athlete cache
        clear_athlete_cache(athlete_id)

        return success_response({"message": "Cache cleared successfully"})

    except Exception as e:
        current_app.logger.error(f"Error clearing cache: {e}")
        return error_response("Failed to clear cache", "server_error", 500)
