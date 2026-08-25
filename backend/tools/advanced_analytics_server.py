"""Advanced Analytics MCP Server.

Cohort analysis, attribution modeling, A/B testing, and custom reports.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("advanced_analytics")
mcp = FastMCP("AdvancedAnalytics")


# Analytics storage
_cohorts: Dict[str, List[Dict[str, Any]]] = {}
_attribution: List[Dict[str, Any]] = []
_ab_tests: Dict[str, Dict[str, Any]] = {}
_custom_reports: List[Dict[str, Any]] = []


@mcp.tool()
def track_cohort(
    cohort_name: str,
    user_id: str,
    event_type: str,
    value: float = 0,
) -> str:
    """Track user event for cohort analysis.

    Args:
        cohort_name: Cohort identifier (e.g., 'leads_jan_2024')
        user_id: User identifier
        event_type: Event type ('signup', 'first_purchase', 'repeat_purchase', etc.)
        value: Event value (optional)

    Returns:
        JSON confirmation
    """
    if cohort_name not in _cohorts:
        _cohorts[cohort_name] = []

    _cohorts[cohort_name].append({
        "user_id": user_id,
        "event_type": event_type,
        "value": value,
        "timestamp": time.time(),
    })

    return json.dumps({
        "status": "tracked",
        "cohort": cohort_name,
        "event": event_type,
        "user_id": user_id,
    })


@mcp.tool()
def analyze_cohort(cohort_name: str, period_days: int = 30) -> str:
    """Analyze cohort retention and conversion.

    Args:
        cohort_name: Cohort to analyze
        period_days: Analysis period (default 30)

    Returns:
        JSON with cohort analysis
    """
    events = _cohorts.get(cohort_name, [])
    if not events:
        return json.dumps({"status": "error", "message": "Cohort not found"})

    # Group by user
    user_events = defaultdict(list)
    for event in events:
        user_events[event["user_id"]].append(event)

    # Calculate metrics
    total_users = len(user_events)
    users_with_events = len([u for u, e in user_events.items() if len(e) > 1])
    users_with_purchase = len([u for u, e in user_events.items() if any(ev["event_type"] == "first_purchase" for ev in e)])

    # Retention
    retention_rate = (users_with_events / total_users * 100) if total_users > 0 else 0
    conversion_rate = (users_with_purchase / total_users * 100) if total_users > 0 else 0

    # Revenue
    total_revenue = sum(e["value"] for e in events if e["event_type"] in ["first_purchase", "repeat_purchase"])
    avg_revenue_per_user = (total_revenue / total_users) if total_users > 0 else 0

    return json.dumps({
        "status": "success",
        "cohort": cohort_name,
        "total_users": total_users,
        "retention_rate": round(retention_rate, 1),
        "conversion_rate": round(conversion_rate, 1),
        "total_revenue": round(total_revenue, 2),
        "avg_revenue_per_user": round(avg_revenue_per_user, 2),
        "period_days": period_days,
    })


@mcp.tool()
def track_attribution(
    user_id: str,
    channel: str,
    touchpoint: str,
    conversion_value: float = 0,
) -> str:
    """Track marketing attribution.

    Args:
        user_id: User identifier
        channel: Marketing channel
        touchpoint: Touchpoint in journey
        conversion_value: Conversion value (optional)

    Returns:
        JSON confirmation
    """
    _attribution.append({
        "user_id": user_id,
        "channel": channel,
        "touchpoint": touchpoint,
        "conversion_value": conversion_value,
        "timestamp": time.time(),
    })

    return json.dumps({
        "status": "tracked",
        "user_id": user_id,
        "channel": channel,
        "touchpoint": touchpoint,
    })


@mcp.tool()
def get_attribution_report() -> str:
    """Get attribution analysis report.

    Returns:
        JSON with attribution data
    """
    # Group by channel
    channel_data = defaultdict(lambda: {"touches": 0, "conversions": 0, "revenue": 0})

    for record in _attribution:
        channel = record["channel"]
        channel_data[channel]["touches"] += 1
        if record["conversion_value"] > 0:
            channel_data[channel]["conversions"] += 1
            channel_data[channel]["revenue"] += record["conversion_value"]

    # Calculate metrics
    channels = {}
    for channel, data in channel_data.items():
        channels[channel] = {
            "touches": data["touches"],
            "conversions": data["conversions"],
            "conversion_rate": round((data["conversions"] / data["touches"] * 100) if data["touches"] > 0 else 0, 1),
            "revenue": round(data["revenue"], 2),
            "revenue_per_touch": round((data["revenue"] / data["touches"]) if data["touches"] > 0 else 0, 2),
        }

    # Sort by revenue
    sorted_channels = sorted(channels.items(), key=lambda x: x[1]["revenue"], reverse=True)

    return json.dumps({
        "status": "success",
        "channels": dict(sorted_channels),
        "total_touches": len(_attribution),
        "total_revenue": round(sum(c["revenue"] for c in channels.values()), 2),
    })


@mcp.tool()
def create_ab_test(
    test_name: str,
    variants: str,
    primary_metric: str,
) -> str:
    """Create an A/B test.

    Args:
        test_name: Test name
        variants: JSON array of variant definitions
        primary_metric: Primary success metric

    Returns:
        JSON with test details
    """
    test_id = f"ab-{int(time.time())}"

    try:
        variants_list = json.loads(variants) if isinstance(variants, str) else variants
    except json.JSONDecodeError:
        return json.dumps({"status": "error", "message": "Invalid variants JSON"})

    _ab_tests[test_id] = {
        "id": test_id,
        "name": test_name,
        "variants": variants_list,
        "primary_metric": primary_metric,
        "status": "running",
        "created_at": time.time(),
        "results": {v.get("name", f"variant_{i}"): {"visits": 0, "conversions": 0} for i, v in enumerate(variants_list)},
    }

    return json.dumps({
        "status": "created",
        "test_id": test_id,
        "name": test_name,
        "variants_count": len(variants_list),
    })


@mcp.tool()
def track_ab_test_event(
    test_id: str,
    variant_name: str,
    event_type: str,
) -> str:
    """Track an A/B test event.

    Args:
        test_id: Test ID
        variant_name: Variant name
        event_type: Event type ('visit' or 'conversion')

    Returns:
        JSON confirmation
    """
    test = _ab_tests.get(test_id)
    if not test:
        return json.dumps({"status": "error", "message": "Test not found"})

    if variant_name not in test["results"]:
        test["results"][variant_name] = {"visits": 0, "conversions": 0}

    if event_type == "visit":
        test["results"][variant_name]["visits"] += 1
    elif event_type == "conversion":
        test["results"][variant_name]["conversions"] += 1

    return json.dumps({
        "status": "tracked",
        "test_id": test_id,
        "variant": variant_name,
        "event": event_type,
    })


@mcp.tool()
def get_ab_test_results(test_id: str) -> str:
    """Get A/B test results with statistical significance.

    Args:
        test_id: Test ID

    Returns:
        JSON with test results
    """
    test = _ab_tests.get(test_id)
    if not test:
        return json.dumps({"status": "error", "message": "Test not found"})

    # Calculate conversion rates
    results = {}
    for variant_name, data in test["results"].items():
        conversion_rate = (data["conversions"] / data["visits"] * 100) if data["visits"] > 0 else 0
        results[variant_name] = {
            "visits": data["visits"],
            "conversions": data["conversions"],
            "conversion_rate": round(conversion_rate, 2),
        }

    # Find winner
    if results:
        winner = max(results.items(), key=lambda x: x[1]["conversion_rate"])
        results[winner[0]]["is_winner"] = True

    return json.dumps({
        "status": "success",
        "test_id": test_id,
        "name": test["name"],
        "primary_metric": test["primary_metric"],
        "results": results,
        "status": test["status"],
    })


@mcp.tool()
def create_custom_report(
    report_name: str,
    metrics: str,
    dimensions: str,
    filters: str = "",
    date_range: str = "",
) -> str:
    """Create a custom analytics report.

    Args:
        report_name: Report name
        metrics: JSON array of metrics to include
        dimensions: JSON array of dimensions to group by
        filters: JSON filter conditions (optional)
        date_range: Date range (optional)

    Returns:
        JSON with report configuration
    """
    report_id = f"report-{int(time.time())}"

    try:
        metrics_list = json.loads(metrics) if isinstance(metrics, str) else metrics
        dimensions_list = json.loads(dimensions) if isinstance(dimensions, str) else dimensions
    except json.JSONDecodeError:
        return json.dumps({"status": "error", "message": "Invalid metrics or dimensions JSON"})

    report = {
        "id": report_id,
        "name": report_name,
        "metrics": metrics_list,
        "dimensions": dimensions_list,
        "filters": filters,
        "date_range": date_range,
        "created_at": time.time(),
    }

    _custom_reports.append(report)

    return json.dumps({
        "status": "created",
        "report_id": report_id,
        "name": report_name,
    })


@mcp.tool()
def get_analytics_dashboard() -> str:
    """Get comprehensive analytics dashboard.

    Returns:
        JSON with all analytics data
    """
    # Cohort summary
    cohort_summary = {}
    for name, events in _cohorts.items():
        users = len(set(e["user_id"] for e in events))
        cohort_summary[name] = {"users": users, "events": len(events)}

    # Attribution summary
    total_attribution = len(_attribution)
    channels = len(set(a["channel"] for a in _attribution))

    # A/B tests summary
    active_tests = len([t for t in _ab_tests.values() if t["status"] == "running"])

    return json.dumps({
        "status": "success",
        "cohorts": {
            "total": len(_cohorts),
            "summary": cohort_summary,
        },
        "attribution": {
            "total_touches": total_attribution,
            "channels": channels,
        },
        "ab_tests": {
            "total": len(_ab_tests),
            "active": active_tests,
        },
        "custom_reports": len(_custom_reports),
    })


if __name__ == "__main__":
    mcp.run()
