"""
Statistics calculator for Strava activities
"""
from datetime import datetime, timedelta
from collections import defaultdict


def calculate_totals(activities):
    """
    Calculate total distance, time, and elevation gain

    Args:
        activities: List of activity dictionaries from Strava API

    Returns:
        Dictionary with total_distance (meters), total_time (seconds), total_elevation (meters)
    """
    totals = {
        "total_distance": 0,
        "total_time": 0,
        "total_elevation": 0,
        "activity_count": len(activities)
    }

    for activity in activities:
        totals["total_distance"] += activity.get("distance", 0)
        totals["total_time"] += activity.get("moving_time", 0)
        totals["total_elevation"] += activity.get("total_elevation_gain", 0)

    return totals


def calculate_averages(activities):
    """
    Calculate average pace, speed, and distance

    Args:
        activities: List of activity dictionaries

    Returns:
        Dictionary with average values
    """
    if not activities:
        return {
            "avg_distance": 0,
            "avg_speed": 0,
            "avg_pace": 0,
            "avg_duration": 0
        }

    totals = calculate_totals(activities)
    count = len(activities)

    return {
        "avg_distance": totals["total_distance"] / count,
        "avg_speed": totals["total_distance"] / totals["total_time"] if totals["total_time"] > 0 else 0,
        "avg_pace": totals["total_time"] / (totals["total_distance"] / 1000) if totals["total_distance"] > 0 else 0,
        "avg_duration": totals["total_time"] / count
    }


def find_personal_records(activities):
    """
    Find personal records (longest distance, fastest pace, highest elevation)

    Args:
        activities: List of activity dictionaries

    Returns:
        Dictionary with PR activities
    """
    if not activities:
        return {
            "longest_distance": None,
            "fastest_pace": None,
            "highest_elevation": None,
            "longest_duration": None
        }

    prs = {
        "longest_distance": max(activities, key=lambda a: a.get("distance", 0)),
        "highest_elevation": max(activities, key=lambda a: a.get("total_elevation_gain", 0)),
        "longest_duration": max(activities, key=lambda a: a.get("moving_time", 0))
    }

    # Fastest pace (min/km) - lower is better, only for runs
    runs = [a for a in activities if a.get("type") == "Run" and a.get("distance", 0) > 0 and a.get("moving_time", 0) > 0]
    if runs:
        prs["fastest_pace"] = min(
            runs,
            key=lambda a: a.get("moving_time", 0) / (a.get("distance", 0) / 1000)
        )
    else:
        prs["fastest_pace"] = None

    return prs


def group_by_activity_type(activities):
    """
    Group activities by type and calculate statistics for each

    Args:
        activities: List of activity dictionaries

    Returns:
        Dictionary mapping activity type to statistics
    """
    grouped = defaultdict(list)

    for activity in activities:
        activity_type = activity.get("type", "Unknown")
        grouped[activity_type].append(activity)

    stats_by_type = {}
    for activity_type, type_activities in grouped.items():
        stats_by_type[activity_type] = {
            "count": len(type_activities),
            **calculate_totals(type_activities)
        }

    return stats_by_type


def calculate_weekly_summary(activities, weeks=4):
    """
    Calculate weekly summaries for the last N weeks

    Args:
        activities: List of activity dictionaries
        weeks: Number of weeks to include

    Returns:
        List of weekly summaries
    """
    today = datetime.now()
    weekly_data = []

    for week_num in range(weeks):
        week_start = today - timedelta(days=today.weekday() + 7 * week_num + 7)
        week_end = week_start + timedelta(days=7)

        week_activities = [
            a for a in activities
            if week_start <= datetime.strptime(a["start_date"], "%Y-%m-%dT%H:%M:%SZ") < week_end
        ]

        totals = calculate_totals(week_activities)
        weekly_data.append({
            "week_start": week_start.strftime("%Y-%m-%d"),
            "week_end": week_end.strftime("%Y-%m-%d"),
            "week_label": f"Week of {week_start.strftime('%b %d')}",
            **totals
        })

    return list(reversed(weekly_data))


def calculate_monthly_summary(activities, months=6):
    """
    Calculate monthly summaries for the last N months

    Args:
        activities: List of activity dictionaries
        months: Number of months to include

    Returns:
        List of monthly summaries
    """
    today = datetime.now()
    monthly_data = []

    for month_offset in range(months):
        # Calculate the month
        year = today.year
        month = today.month - month_offset

        while month <= 0:
            month += 12
            year -= 1

        month_start = datetime(year, month, 1)

        # Get next month for end date
        next_month = month + 1
        next_year = year
        if next_month > 12:
            next_month = 1
            next_year += 1
        month_end = datetime(next_year, next_month, 1)

        month_activities = [
            a for a in activities
            if month_start <= datetime.strptime(a["start_date"], "%Y-%m-%dT%H:%M:%SZ") < month_end
        ]

        totals = calculate_totals(month_activities)
        monthly_data.append({
            "month": month_start.strftime("%Y-%m"),
            "month_label": month_start.strftime("%B %Y"),
            **totals
        })

    return list(reversed(monthly_data))


def calculate_yearly_summary(activities):
    """
    Calculate yearly summaries for all years with activities

    Args:
        activities: List of activity dictionaries

    Returns:
        List of yearly summaries
    """
    if not activities:
        return []

    # Get all unique years from activities
    years = set()
    for activity in activities:
        year = datetime.strptime(activity["start_date"], "%Y-%m-%dT%H:%M:%SZ").year
        years.add(year)

    yearly_data = []
    for year in sorted(years):
        year_start = datetime(year, 1, 1)
        year_end = datetime(year + 1, 1, 1)

        year_activities = [
            a for a in activities
            if year_start <= datetime.strptime(a["start_date"], "%Y-%m-%dT%H:%M:%SZ") < year_end
        ]

        totals = calculate_totals(year_activities)
        yearly_data.append({
            "year": year,
            "year_label": str(year),
            **totals
        })

    return yearly_data


def prepare_chart_data(activities):
    """
    Prepare data for frontend charts

    Args:
        activities: List of activity dictionaries

    Returns:
        Dictionary with formatted chart data
    """
    # Sort activities by date
    sorted_activities = sorted(
        activities,
        key=lambda a: a.get("start_date", "")
    )

    # Distance over time
    distance_over_time = [
        {
            "date": a.get("start_date_local", a.get("start_date", ""))[:10],
            "distance": a.get("distance", 0) / 1000,  # Convert to km
            "name": a.get("name", "Unknown")
        }
        for a in sorted_activities
    ]

    # Activity type breakdown
    type_stats = group_by_activity_type(activities)
    activity_type_breakdown = [
        {
            "type": activity_type,
            "count": stats["count"],
            "distance": stats["total_distance"] / 1000
        }
        for activity_type, stats in type_stats.items()
    ]

    # Pace trends (for runs only)
    runs = [a for a in sorted_activities if a.get("type") == "Run" and a.get("distance", 0) > 0]
    pace_trends = [
        {
            "date": r.get("start_date_local", r.get("start_date", ""))[:10],
            "pace": r.get("moving_time", 0) / (r.get("distance", 0) / 1000),  # seconds per km
            "name": r.get("name", "Unknown")
        }
        for r in runs
    ]

    return {
        "distance_over_time": distance_over_time,
        "activity_type_breakdown": activity_type_breakdown,
        "pace_trends": pace_trends
    }
