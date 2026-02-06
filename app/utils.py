"""
Utility functions for formatting and data transformation
"""
import polyline


def format_distance(meters, unit="km"):
    """
    Format distance from meters to km or miles

    Args:
        meters: Distance in meters
        unit: 'km' or 'miles'

    Returns:
        Formatted string with unit
    """
    if unit == "miles":
        miles = meters / 1609.34
        return f"{miles:.2f} mi"
    else:
        km = meters / 1000
        return f"{km:.2f} km"


def format_pace(seconds_per_km, unit="km"):
    """
    Format pace in min/km or min/mile

    Args:
        seconds_per_km: Pace in seconds per kilometer
        unit: 'km' or 'miles'

    Returns:
        Formatted string like "5:30 /km"
    """
    if unit == "miles":
        seconds_per_mile = seconds_per_km * 1.60934
        minutes = int(seconds_per_mile // 60)
        seconds = int(seconds_per_mile % 60)
        return f"{minutes}:{seconds:02d} /mi"
    else:
        minutes = int(seconds_per_km // 60)
        seconds = int(seconds_per_km % 60)
        return f"{minutes}:{seconds:02d} /km"


def format_duration(seconds):
    """
    Format duration from seconds to HH:MM:SS or MM:SS

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


def format_elevation(meters, unit="m"):
    """
    Format elevation gain

    Args:
        meters: Elevation in meters
        unit: 'm' or 'ft'

    Returns:
        Formatted string with unit
    """
    if unit == "ft":
        feet = meters * 3.28084
        return f"{feet:.0f} ft"
    else:
        return f"{meters:.0f} m"


def format_speed(meters_per_second, unit="kph"):
    """
    Format speed from m/s to kph or mph

    Args:
        meters_per_second: Speed in meters per second
        unit: 'kph' or 'mph'

    Returns:
        Formatted string with unit
    """
    if unit == "mph":
        mph = meters_per_second * 2.23694
        return f"{mph:.1f} mph"
    else:
        kph = meters_per_second * 3.6
        return f"{kph:.1f} kph"


def decode_polyline(encoded_polyline):
    """
    Decode Strava polyline to list of [lat, lng] coordinates

    Args:
        encoded_polyline: Encoded polyline string from Strava

    Returns:
        List of [lat, lng] coordinate pairs
    """
    if not encoded_polyline:
        return []

    try:
        # polyline.decode returns list of (lat, lng) tuples
        coords = polyline.decode(encoded_polyline)
        # Convert to [lat, lng] format for Leaflet.js
        return [[lat, lng] for lat, lng in coords]
    except Exception as e:
        print(f"Error decoding polyline: {e}")
        return []


def parse_date_range(start_date_str, end_date_str):
    """
    Parse date range strings to Unix timestamps

    Args:
        start_date_str: Start date in YYYY-MM-DD format
        end_date_str: End date in YYYY-MM-DD format

    Returns:
        Tuple of (start_timestamp, end_timestamp) or (None, None) if invalid
    """
    from datetime import datetime

    try:
        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            start_timestamp = int(start_date.timestamp())
        else:
            start_timestamp = None

        if end_date_str:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            # Add 23:59:59 to include the entire end day
            end_timestamp = int(end_date.timestamp()) + 86399
        else:
            end_timestamp = None

        return start_timestamp, end_timestamp

    except ValueError:
        return None, None


def filter_activities(activities, activity_type=None, start_date=None, end_date=None,
                     min_distance=None, max_distance=None, search_query=None):
    """
    Filter activities based on criteria

    Args:
        activities: List of activity dictionaries
        activity_type: Activity type to filter by (e.g., 'Run', 'Ride')
        start_date: Unix timestamp for start date
        end_date: Unix timestamp for end date
        min_distance: Minimum distance in meters
        max_distance: Maximum distance in meters
        search_query: Search term for activity name

    Returns:
        Filtered list of activities
    """
    from datetime import datetime

    filtered = activities

    # Filter by type
    if activity_type:
        filtered = [a for a in filtered if a.get("type") == activity_type]

    # Filter by date range
    if start_date or end_date:
        filtered = [
            a for a in filtered
            if (not start_date or datetime.strptime(a["start_date"], "%Y-%m-%dT%H:%M:%SZ").timestamp() >= start_date) and
               (not end_date or datetime.strptime(a["start_date"], "%Y-%m-%dT%H:%M:%SZ").timestamp() <= end_date)
        ]

    # Filter by distance
    if min_distance is not None:
        filtered = [a for a in filtered if a.get("distance", 0) >= min_distance]

    if max_distance is not None:
        filtered = [a for a in filtered if a.get("distance", 0) <= max_distance]

    # Filter by search query
    if search_query:
        query_lower = search_query.lower()
        filtered = [
            a for a in filtered
            if query_lower in a.get("name", "").lower()
        ]

    return filtered
