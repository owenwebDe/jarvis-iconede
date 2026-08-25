"""Predictive Forecasting MCP Server.

AI-powered predictions for revenue, leads, and business metrics.
"""
from __future__ import annotations

import json
import logging
import time
import math
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("predictive_forecast")
mcp = FastMCP("PredictiveForecast")


# Historical data for forecasting
_historical_data: Dict[str, List[Dict[str, Any]]] = {
    "revenue": [],
    "leads": [],
    "conversions": [],
    "campaign_spend": [],
}


@mcp.tool()
def record_historical_metric(
    metric_type: str,
    value: float,
    date: str = "",
) -> str:
    """Record historical metric for forecasting.

    Args:
        metric_type: Type of metric ('revenue', 'leads', 'conversions', 'campaign_spend')
        value: Metric value
        date: Date in YYYY-MM-DD format (optional, defaults to today)

    Returns:
        JSON confirmation
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    if metric_type not in _historical_data:
        _historical_data[metric_type] = []

    _historical_data[metric_type].append({
        "date": date,
        "value": value,
        "timestamp": time.time(),
    })

    return json.dumps({
        "status": "recorded",
        "metric_type": metric_type,
        "value": value,
        "date": date,
    })


@mcp.tool()
def forecast_revenue(days: int = 30) -> str:
    """Forecast revenue for the next N days.

    Args:
        days: Number of days to forecast (default 30)

    Returns:
        JSON with revenue forecast
    """
    historical = _historical_data.get("revenue", [])

    if len(historical) < 7:
        return json.dumps({
            "status": "insufficient_data",
            "message": "Need at least 7 days of historical data",
            "data_points": len(historical),
        })

    # Simple moving average forecast
    recent_values = [d["value"] for d in historical[-30:]]
    avg_daily = sum(recent_values) / len(recent_values)

    # Calculate trend
    if len(recent_values) >= 14:
        first_half = sum(recent_values[:len(recent_values)//2]) / (len(recent_values)//2)
        second_half = sum(recent_values[len(recent_values)//2:]) / (len(recent_values)//2)
        trend = (second_half - first_half) / first_half if first_half > 0 else 0
    else:
        trend = 0

    # Generate forecast
    forecast = []
    current_date = datetime.now()
    projected_value = avg_daily

    for i in range(days):
        current_date += timedelta(days=1)
        projected_value = projected_value * (1 + trend / 30)  # Daily trend adjustment

        forecast.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "projected": round(projected_value, 2),
            "low": round(projected_value * 0.8, 2),
            "high": round(projected_value * 1.2, 2),
        })

    total_forecast = sum(f["projected"] for f in forecast)

    return json.dumps({
        "status": "success",
        "forecast_period_days": days,
        "current_avg_daily": round(avg_daily, 2),
        "trend_percent": round(trend * 100, 1),
        "total_forecast": round(total_forecast, 2),
        "daily_forecast": forecast[:7],  # Show first 7 days
        "confidence": "medium" if len(historical) >= 30 else "low",
    }, indent=2)


@mcp.tool()
def forecast_leads(days: int = 30) -> str:
    """Forecast lead generation for the next N days.

    Args:
        days: Number of days to forecast (default 30)

    Returns:
        JSON with lead forecast
    """
    historical = _historical_data.get("leads", [])

    if len(historical) < 7:
        return json.dumps({
            "status": "insufficient_data",
            "message": "Need at least 7 days of historical data",
        })

    # Simple moving average
    recent_values = [d["value"] for d in historical[-30:]]
    avg_daily = sum(recent_values) / len(recent_values)

    # Seasonality (simplified - weekdays vs weekends)
    weekday_avg = sum(recent_values[:len(recent_values)//2]) / (len(recent_values)//2)
    weekend_factor = 0.6  # Weekends typically lower

    forecast = []
    current_date = datetime.now()

    for i in range(days):
        current_date += timedelta(days=1)
        is_weekend = current_date.weekday() >= 5

        projected = weekday_avg if not is_weekend else weekday_avg * weekend_factor

        forecast.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "projected": round(projected, 0),
            "day_type": "weekend" if is_weekend else "weekday",
        })

    total_forecast = sum(f["projected"] for f in forecast)

    return json.dumps({
        "status": "success",
        "forecast_period_days": days,
        "avg_daily_weekday": round(weekday_avg, 0),
        "total_forecast": round(total_forecast, 0),
        "daily_forecast": forecast[:7],
    }, indent=2)


@mcp.tool()
def forecast_conversion_rate(period_days: int = 30) -> str:
    """Forecast conversion rate trends.

    Args:
        period_days: Period to analyze (default 30)

    Returns:
        JSON with conversion forecast
    """
    leads = _historical_data.get("leads", [])
    conversions = _historical_data.get("conversions", [])

    if len(leads) < 14 or len(conversions) < 14:
        return json.dumps({
            "status": "insufficient_data",
            "message": "Need at least 14 days of data for conversion forecasting",
        })

    # Calculate historical conversion rates
    lead_values = [d["value"] for d in leads[-period_days:]]
    conv_values = [d["value"] for d in conversions[-period_days:]]

    # Match by date (simplified)
    historical_rate = (sum(conv_values) / sum(lead_values) * 100) if sum(lead_values) > 0 else 0

    # Trend
    if len(lead_values) >= 14:
        first_half_rate = (sum(conv_values[:len(conv_values)//2]) / sum(lead_values[:len(lead_values)//2]) * 100) if sum(lead_values[:len(lead_values)//2]) > 0 else 0
        second_half_rate = (sum(conv_values[len(conv_values)//2:]) / sum(lead_values[len(lead_values)//2:]) * 100) if sum(lead_values[len(lead_values)//2:]) > 0 else 0
        trend = second_half_rate - first_half_rate
    else:
        trend = 0

    return json.dumps({
        "status": "success",
        "current_rate": round(historical_rate, 1),
        "trend_percent": round(trend, 1),
        "forecast_next_30_days": {
            "low": round(historical_rate - 2, 1),
            "expected": round(historical_rate + trend, 1),
            "high": round(historical_rate + trend + 3, 1),
        },
        "recommendation": "Improving" if trend > 0 else "Needs optimization" if trend < -1 else "Stable",
    })


@mcp.tool()
def forecast_roi(campaign_name: str = "", period_days: int = 30) -> str:
    """Forecast campaign ROI.

    Args:
        campaign_name: Specific campaign (optional)
        period_days: Period to forecast (default 30)

    Returns:
        JSON with ROI forecast
    """
    spend = _historical_data.get("campaign_spend", [])
    revenue = _historical_data.get("revenue", [])

    if len(spend) < 7 or len(revenue) < 7:
        return json.dumps({
            "status": "insufficient_data",
            "message": "Need at least 7 days of spend and revenue data",
        })

    # Calculate current ROI
    total_spend = sum(d["value"] for d in spend[-period_days:])
    total_revenue = sum(d["value"] for d in revenue[-period_days:])

    roi = ((total_revenue - total_spend) / total_spend * 100) if total_spend > 0 else 0

    # Trend
    recent_spend = sum(d["value"] for d in spend[-7:])
    recent_revenue = sum(d["value"] for d in revenue[-7:])
    recent_roi = ((recent_revenue - recent_spend) / recent_spend * 100) if recent_spend > 0 else 0

    return json.dumps({
        "status": "success",
        "period_days": period_days,
        "current_roi": round(roi, 1),
        "recent_roi_7days": round(recent_roi, 1),
        "trend": "improving" if recent_roi > roi else "declining" if recent_roi < roi else "stable",
        "projected_monthly_roi": round(recent_roi * 30 / 7, 1),
    })


@mcp.tool()
def get_forecast_dashboard() -> str:
    """Get complete forecasting dashboard.

    Returns:
        JSON with all forecasts
    """
    return json.dumps({
        "status": "success",
        "revenue": _get_quick_forecast("revenue"),
        "leads": _get_quick_forecast("leads"),
        "conversions": _get_quick_forecast("conversions"),
        "data_quality": {
            "revenue_days": len(_historical_data.get("revenue", [])),
            "leads_days": len(_historical_data.get("leads", [])),
            "conversions_days": len(_historical_data.get("conversions", [])),
        },
    })


def _get_quick_forecast(metric_type: str) -> Dict[str, Any]:
    """Get quick forecast for a metric."""
    historical = _historical_data.get(metric_type, [])

    if len(historical) < 7:
        return {"status": "insufficient_data"}

    values = [d["value"] for d in historical[-30:]]
    avg = sum(values) / len(values)
    recent_avg = sum(values[-7:]) / 7

    return {
        "status": "success",
        "avg": round(avg, 2),
        "recent_avg": round(recent_avg, 2),
        "trend": "up" if recent_avg > avg else "down" if recent_avg < avg else "stable",
    }


if __name__ == "__main__":
    mcp.run()
