"""Business Intelligence MCP Server.

Real-time business metrics, KPI tracking, and analytics for
IconEdge Technologies.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("business_intel")
mcp = FastMCP("BusinessIntelligence")

# Metrics storage (in production, use SQLite)
_metrics: Dict[str, List[Dict[str, Any]]] = {
    "leads": [],
    "campaigns": [],
    "outreach": [],
    "revenue": [],
    "agents": [],
}

_kpis: Dict[str, Dict[str, Any]] = {
    "lead_conversion_rate": {"value": 0, "target": 20, "unit": "%"},
    "campaign_roas": {"value": 0, "target": 3.0, "unit": "x"},
    "response_rate": {"value": 0, "target": 15, "unit": "%"},
    "agent_success_rate": {"value": 0, "target": 90, "unit": "%"},
    "avg_lead_score": {"value": 0, "target": 70, "unit": "points"},
    "daily_leads": {"value": 0, "target": 20, "unit": "leads"},
    "daily_outreach": {"value": 0, "target": 50, "unit": "messages"},
}


def _record_metric(category: str, metric_type: str, value: float, metadata: Dict[str, Any] = None):
    """Record a metric data point."""
    if category not in _metrics:
        _metrics[category] = []

    _metrics[category].append({
        "type": metric_type,
        "value": value,
        "metadata": metadata or {},
        "timestamp": time.time(),
    })

    # Keep last 1000 per category
    if len(_metrics[category]) > 1000:
        _metrics[category] = _metrics[category][-1000:]


@mcp.tool()
def record_lead_metric(
    metric_type: str,
    value: float,
    source: str = "",
    details: str = "",
) -> str:
    """Record a lead-related metric.

    Args:
        metric_type: Type of metric ('new_lead', 'qualified', 'converted', 'lost')
        value: Metric value (usually count or score)
        source: Source of the lead (e.g., 'web_search', 'linkedin')
        details: Additional details

    Returns:
        JSON confirmation
    """
    _record_metric("leads", metric_type, value, {"source": source, "details": details})

    # Update KPIs
    if metric_type == "new_lead":
        _kpis["daily_leads"]["value"] += 1
    elif metric_type == "converted":
        _kpis["lead_conversion_rate"]["value"] = _calculate_conversion_rate()

    return json.dumps({
        "status": "recorded",
        "metric": metric_type,
        "value": value,
        "kpi_update": {
            "daily_leads": _kpis["daily_leads"]["value"],
            "conversion_rate": _kpis["lead_conversion_rate"]["value"],
        },
    })


@mcp.tool()
def record_campaign_metric(
    campaign_name: str,
    metric_type: str,
    value: float,
    spend: float = 0,
) -> str:
    """Record a campaign performance metric.

    Args:
        campaign_name: Name of the campaign
        metric_type: Type of metric ('impressions', 'clicks', 'conversions', 'revenue')
        value: Metric value
        spend: Amount spent (optional)

    Returns:
        JSON confirmation
    """
    _record_metric("campaigns", metric_type, value, {
        "campaign": campaign_name,
        "spend": spend,
    })

    # Update ROAS if revenue
    if metric_type == "revenue" and spend > 0:
        _kpis["campaign_roas"]["value"] = value / spend

    return json.dumps({
        "status": "recorded",
        "campaign": campaign_name,
        "metric": metric_type,
        "value": value,
        "roas": _kpis["campaign_roas"]["value"],
    })


@mcp.tool()
def record_outreach_metric(
    metric_type: str,
    value: float,
    channel: str = "",
    campaign: str = "",
) -> str:
    """Record an outreach metric.

    Args:
        metric_type: Type of metric ('sent', 'delivered', 'opened', 'replied', 'converted')
        value: Metric value
        channel: Communication channel ('email', 'whatsapp', 'linkedin')
        campaign: Campaign name (optional)

    Returns:
        JSON confirmation
    """
    _record_metric("outreach", metric_type, value, {
        "channel": channel,
        "campaign": campaign,
    })

    # Update response rate
    if metric_type == "replied":
        _kpis["response_rate"]["value"] = _calculate_response_rate()

    return json.dumps({
        "status": "recorded",
        "metric": metric_type,
        "value": value,
        "channel": channel,
        "response_rate": _kpis["response_rate"]["value"],
    })


@mcp.tool()
def record_agent_metric(
    agent_name: str,
    metric_type: str,
    value: float,
    task_type: str = "",
) -> str:
    """Record an agent performance metric.

    Args:
        agent_name: Name of the agent
        metric_type: Type of metric ('task_completed', 'task_failed', 'duration')
        value: Metric value
        task_type: Type of task (optional)

    Returns:
        JSON confirmation
    """
    _record_metric("agents", metric_type, value, {
        "agent": agent_name,
        "task_type": task_type,
    })

    # Update agent success rate
    _kpis["agent_success_rate"]["value"] = _calculate_agent_success_rate()

    return json.dumps({
        "status": "recorded",
        "agent": agent_name,
        "metric": metric_type,
        "value": value,
        "agent_success_rate": _kpis["agent_success_rate"]["value"],
    })


@mcp.tool()
def get_dashboard() -> str:
    """Get the full business intelligence dashboard.

    Returns:
        JSON with all KPIs, trends, and insights
    """
    # Calculate trends
    trends = _calculate_trends()

    # Get recent activity
    recent_activity = _get_recent_activity()

    # Calculate targets progress
    targets = {}
    for kpi_name, kpi_data in _kpis.items():
        progress = (kpi_data["value"] / kpi_data["target"] * 100) if kpi_data["target"] > 0 else 0
        targets[kpi_name] = {
            "current": kpi_data["value"],
            "target": kpi_data["target"],
            "progress": f"{min(progress, 100):.0f}%",
            "status": "on_track" if progress >= 80 else "behind",
            "unit": kpi_data["unit"],
        }

    # Generate insights
    insights = _generate_insights()

    return json.dumps({
        "status": "success",
        "kpis": targets,
        "trends": trends,
        "recent_activity": recent_activity,
        "insights": insights,
        "last_updated": datetime.now().isoformat(),
    }, indent=2)


@mcp.tool()
def get_kpi_summary() -> str:
    """Get a quick KPI summary.

    Returns:
        JSON with key performance indicators
    """
    summary = {}
    for kpi_name, kpi_data in _kpis.items():
        progress = (kpi_data["value"] / kpi_data["target"] * 100) if kpi_data["target"] > 0 else 0
        summary[kpi_name] = {
            "value": kpi_data["value"],
            "target": kpi_data["target"],
            "status": "✅" if progress >= 80 else "⚠️" if progress >= 50 else "❌",
        }

    return json.dumps({
        "status": "success",
        "kpis": summary,
    }, indent=2)


@mcp.tool()
def get_trend_analysis(
    metric_type: str,
    period_days: int = 7,
) -> str:
    """Get trend analysis for a specific metric.

    Args:
        metric_type: Type of metric to analyze
        period_days: Number of days to analyze (default 7)

    Returns:
        JSON with trend data and analysis
    """
    # Get metrics for period
    cutoff = time.time() - (period_days * 86400)
    period_metrics = []

    for category_metrics in _metrics.values():
        for m in category_metrics:
            if m["timestamp"] >= cutoff and m["type"] == metric_type:
                period_metrics.append(m)

    # Calculate trend
    if len(period_metrics) >= 2:
        first_half = sum(m["value"] for m in period_metrics[:len(period_metrics)//2])
        second_half = sum(m["value"] for m in period_metrics[len(period_metrics)//2:])

        if first_half > 0:
            change_percent = ((second_half - first_half) / first_half) * 100
        else:
            change_percent = 100 if second_half > 0 else 0

        trend = "up" if change_percent > 0 else "down" if change_percent < 0 else "stable"
    else:
        change_percent = 0
        trend = "insufficient_data"

    return json.dumps({
        "status": "success",
        "metric_type": metric_type,
        "period_days": period_days,
        "total_data_points": len(period_metrics),
        "trend": trend,
        "change_percent": round(change_percent, 1),
        "total_value": sum(m["value"] for m in period_metrics),
    })


@mcp.tool()
def get_funnel_analysis() -> str:
    """Get lead conversion funnel analysis.

    Returns:
        JSON with funnel metrics
    """
    # Get counts by stage
    funnel = {
        "leads": _count_metrics("leads", "new_lead"),
        "qualified": _count_metrics("leads", "qualified"),
        "contacted": _count_metrics("outreach", "sent"),
        "responded": _count_metrics("outreach", "replied"),
        "converted": _count_metrics("leads", "converted"),
    }

    # Calculate conversion rates
    conversion_rates = {}
    stages = list(funnel.keys())
    for i in range(1, len(stages)):
        if funnel[stages[i-1]] > 0:
            rate = (funnel[stages[i]] / funnel[stages[i-1]]) * 100
        else:
            rate = 0
        conversion_rates[f"{stages[i-1]}_to_{stages[i]}"] = round(rate, 1)

    # Overall conversion
    overall = (funnel["converted"] / funnel["leads"] * 100) if funnel["leads"] > 0 else 0

    return json.dumps({
        "status": "success",
        "funnel": funnel,
        "conversion_rates": conversion_rates,
        "overall_conversion": round(overall, 1),
    }, indent=2)


def _calculate_conversion_rate() -> float:
    """Calculate lead conversion rate."""
    converted = _count_metrics("leads", "converted")
    total = _count_metrics("leads", "new_lead")
    return (converted / total * 100) if total > 0 else 0


def _calculate_response_rate() -> float:
    """Calculate outreach response rate."""
    replied = _count_metrics("outreach", "replied")
    sent = _count_metrics("outreach", "sent")
    return (replied / sent * 100) if sent > 0 else 0


def _calculate_agent_success_rate() -> float:
    """Calculate agent success rate."""
    completed = _count_metrics("agents", "task_completed")
    failed = _count_metrics("agents", "task_failed")
    total = completed + failed
    return (completed / total * 100) if total > 0 else 0


def _count_metrics(category: str, metric_type: str) -> int:
    """Count metrics of a specific type."""
    return sum(1 for m in _metrics.get(category, []) if m["type"] == metric_type)


def _calculate_trends() -> Dict[str, Any]:
    """Calculate trends for key metrics."""
    return {
        "leads_trend": "up" if _kpis["daily_leads"]["value"] > 15 else "stable",
        "conversion_trend": "improving" if _kpis["lead_conversion_rate"]["value"] > 10 else "needs_attention",
        "roas_trend": "healthy" if _kpis["campaign_roas"]["value"] > 2.5 else "optimize",
    }


def _get_recent_activity() -> List[Dict[str, Any]]:
    """Get recent activity across all categories."""
    recent = []
    cutoff = time.time() - 3600  # Last hour

    for category, metrics in _metrics.items():
        for m in metrics[-5:]:  # Last 5 per category
            if m["timestamp"] >= cutoff:
                recent.append({
                    "category": category,
                    "type": m["type"],
                    "value": m["value"],
                    "time": datetime.fromtimestamp(m["timestamp"]).strftime("%H:%M"),
                })

    return sorted(recent, key=lambda x: x["time"], reverse=True)[:10]


def _generate_insights() -> List[str]:
    """Generate actionable insights from metrics."""
    insights = []

    if _kpis["daily_leads"]["value"] < _kpis["daily_leads"]["target"]:
        insights.append("📊 Lead generation below target. Consider increasing research intensity.")

    if _kpis["campaign_roas"]["value"] < 2.0:
        insights.append("💰 Campaign ROAS below 2x. Review targeting and creative.")

    if _kpis["response_rate"]["value"] < 10:
        insights.append("📧 Response rate low. Test new outreach angles.")

    if _kpis["agent_success_rate"]["value"] < 85:
        insights.append("🤖 Agent success rate needs attention. Check for system issues.")

    if not insights:
        insights.append("✅ All KPIs on track. Keep up the great work!")

    return insights


if __name__ == "__main__":
    mcp.run()
