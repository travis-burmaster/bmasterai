"""
AWS Budgets Integration Tools
Provides budget tracking, burn rate, and overrun forecasting.

Source: adapted from awslabs/amazon-bedrock-agentcore-samples
"""

import json
from datetime import datetime, timedelta

import boto3


def _account_id() -> str:
    return boto3.client("sts").get_caller_identity()["Account"]


def get_all_budgets() -> str:
    """List all AWS budgets and their current utilization status."""
    try:
        client = boto3.client("budgets")
        response = client.describe_budgets(AccountId=_account_id())

        budgets_list = []
        for budget in response.get("Budgets", []):
            limit = float(budget["BudgetLimit"]["Amount"])
            actual = float(
                budget.get("CalculatedSpend", {}).get("ActualSpend", {}).get("Amount", 0)
            )
            forecasted = float(
                budget.get("CalculatedSpend", {}).get("ForecastedSpend", {}).get("Amount", 0)
            )
            utilization = (actual / limit * 100) if limit > 0 else 0

            budgets_list.append({
                "name": budget["BudgetName"],
                "limit": round(limit, 2),
                "actual_spend": round(actual, 2),
                "forecasted_spend": round(forecasted, 2),
                "utilization_percent": round(utilization, 2),
                "remaining": round(limit - actual, 2),
                "unit": budget["BudgetLimit"]["Unit"],
                "status": "OK" if utilization < 80 else "WARNING" if utilization < 100 else "EXCEEDED",
            })

        budgets_list.sort(key=lambda x: x["utilization_percent"], reverse=True)

        return json.dumps({
            "total_budgets": len(budgets_list),
            "budgets": budgets_list,
            "summary": {
                "ok":       sum(1 for b in budgets_list if b["status"] == "OK"),
                "warning":  sum(1 for b in budgets_list if b["status"] == "WARNING"),
                "exceeded": sum(1 for b in budgets_list if b["status"] == "EXCEEDED"),
            },
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e), "message": "Failed to list budgets"})


def get_budget_status(budget_name: str) -> str:
    """Get current status and utilization of a specific budget."""
    try:
        client = boto3.client("budgets")
        response = client.describe_budget(AccountId=_account_id(), BudgetName=budget_name)
        budget = response["Budget"]

        limit = float(budget["BudgetLimit"]["Amount"])
        actual = float(
            budget.get("CalculatedSpend", {}).get("ActualSpend", {}).get("Amount", 0)
        )
        forecasted = float(
            budget.get("CalculatedSpend", {}).get("ForecastedSpend", {}).get("Amount", 0)
        )
        utilization = (actual / limit * 100) if limit > 0 else 0
        forecast_util = (forecasted / limit * 100) if limit > 0 else 0

        return json.dumps({
            "budget_name": budget_name,
            "budget_limit": round(limit, 2),
            "actual_spend": round(actual, 2),
            "forecasted_spend": round(forecasted, 2),
            "utilization_percent": round(utilization, 2),
            "forecast_utilization_percent": round(forecast_util, 2),
            "remaining_budget": round(limit - actual, 2),
            "unit": budget["BudgetLimit"]["Unit"],
            "status": "OK" if utilization < 80 else "WARNING" if utilization < 100 else "EXCEEDED",
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e), "message": f"Failed to get budget: {budget_name}"})


def calculate_burn_rate(time_period: str = "LAST_7_DAYS") -> str:
    """Calculate daily/weekly/monthly spending burn rate and trend."""
    try:
        ce = boto3.client("ce")
        days = {"LAST_7_DAYS": 7, "LAST_30_DAYS": 30, "LAST_90_DAYS": 90}.get(time_period, 7)
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        response = ce.get_cost_and_usage(
            TimePeriod={"Start": start_date, "End": end_date},
            Granularity="DAILY",
            Metrics=["UnblendedCost"],
        )

        daily_costs = [
            float(r["Total"]["UnblendedCost"]["Amount"])
            for r in response.get("ResultsByTime", [])
        ]
        total = sum(daily_costs)
        avg_daily = total / len(daily_costs) if daily_costs else 0

        mid = len(daily_costs) // 2
        first_avg = sum(daily_costs[:mid]) / mid if mid else 0
        second_avg = sum(daily_costs[mid:]) / (len(daily_costs) - mid) if mid else 0
        trend_pct = ((second_avg - first_avg) / first_avg * 100) if first_avg > 0 else 0

        return json.dumps({
            "time_period": {"start": start_date, "end": end_date, "days": days},
            "total_cost": round(total, 2),
            "burn_rate": {
                "daily_average":      round(avg_daily, 2),
                "weekly_average":     round(avg_daily * 7, 2),
                "monthly_projection": round(avg_daily * 30, 2),
            },
            "trend": {
                "percent_change": round(trend_pct, 2),
                "direction": "INCREASING" if trend_pct > 5 else "DECREASING" if trend_pct < -5 else "STABLE",
            },
            "daily_costs": [round(c, 2) for c in daily_costs],
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e), "message": "Failed to calculate burn rate"})
