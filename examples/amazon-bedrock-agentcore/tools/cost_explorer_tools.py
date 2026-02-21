"""
AWS Cost Explorer Integration Tools
Provides real-time cost data, forecasting, and anomaly detection.

Source: adapted from awslabs/amazon-bedrock-agentcore-samples
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import boto3


def get_cost_and_usage(
    start_date: str,
    end_date: str,
    granularity: str = "DAILY",
    group_by: Optional[List[Dict]] = None,
    filter_expression: Optional[Dict] = None,
) -> str:
    """Retrieve AWS cost and usage data for a specified time period."""
    try:
        ce = boto3.client("ce")
        params = {
            "TimePeriod": {"Start": start_date, "End": end_date},
            "Granularity": granularity,
            "Metrics": ["UnblendedCost", "UsageQuantity"],
        }
        if group_by:
            params["GroupBy"] = group_by
        if filter_expression:
            params["Filter"] = filter_expression

        response = ce.get_cost_and_usage(**params)
        results = {
            "time_period": {"start": start_date, "end": end_date},
            "granularity": granularity,
            "results": [],
            "total_cost": 0.0,
        }

        for result in response.get("ResultsByTime", []):
            period = {
                "start": result["TimePeriod"]["Start"],
                "end": result["TimePeriod"]["End"],
                "groups": [],
            }
            if "Groups" in result:
                for group in result["Groups"]:
                    cost = float(group["Metrics"]["UnblendedCost"]["Amount"])
                    period["groups"].append({
                        "keys": group["Keys"],
                        "cost": round(cost, 2),
                        "unit": group["Metrics"]["UnblendedCost"]["Unit"],
                    })
                    results["total_cost"] += cost
            else:
                cost = float(result["Total"]["UnblendedCost"]["Amount"])
                period["total_cost"] = round(cost, 2)
                period["unit"] = result["Total"]["UnblendedCost"]["Unit"]
                results["total_cost"] += cost
            results["results"].append(period)

        results["total_cost"] = round(results["total_cost"], 2)
        return json.dumps(results, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e), "message": "Failed to retrieve cost data"})


def get_cost_forecast(
    start_date: str,
    end_date: str,
    metric: str = "UNBLENDED_COST",
    granularity: str = "MONTHLY",
) -> str:
    """Get cost forecast for a future time period based on historical data."""
    try:
        ce = boto3.client("ce")
        response = ce.get_cost_forecast(
            TimePeriod={"Start": start_date, "End": end_date},
            Metric=metric,
            Granularity=granularity,
            PredictionIntervalLevel=80,
        )
        results = {
            "time_period": {"start": start_date, "end": end_date},
            "metric": metric,
            "granularity": granularity,
            "total_forecast": round(float(response["Total"]["Amount"]), 2),
            "unit": response["Total"]["Unit"],
            "forecasts": [],
        }
        for f in response.get("ForecastResultsByTime", []):
            results["forecasts"].append({
                "start": f["TimePeriod"]["Start"],
                "end": f["TimePeriod"]["End"],
                "mean_value": round(float(f["MeanValue"]), 2),
                "prediction_interval_lower": round(float(f["PredictionIntervalLowerBound"]), 2),
                "prediction_interval_upper": round(float(f["PredictionIntervalUpperBound"]), 2),
            })
        return json.dumps(results, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e), "message": "Failed to generate forecast"})


def detect_cost_anomalies(lookback_days: int = 7) -> str:
    """Detect cost anomalies using AWS Cost Anomaly Detection."""
    try:
        ce = boto3.client("ce")
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

        response = ce.get_anomalies(
            DateInterval={"StartDate": start_date, "EndDate": end_date},
            MaxResults=100,
        )

        anomalies = []
        for anomaly in response.get("Anomalies", []):
            anomaly_data = {
                "anomaly_id": anomaly["AnomalyId"],
                "anomaly_score": round(anomaly["AnomalyScore"]["CurrentScore"], 2),
                "impact": {
                    "max_impact": round(float(anomaly["Impact"]["MaxImpact"]), 2),
                    "total_impact": round(float(anomaly["Impact"]["TotalImpact"]), 2),
                },
                "start_date": anomaly["AnomalyStartDate"],
                "end_date": anomaly.get("AnomalyEndDate", "Ongoing"),
                "dimension_value": anomaly.get("DimensionValue", "Unknown"),
                "root_causes": [
                    {
                        "service": rc.get("Service", "Unknown"),
                        "region": rc.get("Region", "Unknown"),
                        "usage_type": rc.get("UsageType", "Unknown"),
                    }
                    for rc in anomaly.get("RootCauses", [])
                ],
            }
            anomalies.append(anomaly_data)

        return json.dumps({
            "time_period": {"start": start_date, "end": end_date},
            "anomaly_count": len(anomalies),
            "anomalies": sorted(
                anomalies, key=lambda x: x["impact"]["total_impact"], reverse=True
            ),
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e), "message": "Failed to detect anomalies"})


def get_service_costs(
    service_name: str,
    time_period: str = "LAST_30_DAYS",
    granularity: str = "DAILY",
) -> str:
    """Get detailed cost breakdown for a specific AWS service."""
    try:
        ce = boto3.client("ce")
        days = {"LAST_7_DAYS": 7, "LAST_30_DAYS": 30, "LAST_90_DAYS": 90}.get(time_period, 30)
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        response = ce.get_cost_and_usage(
            TimePeriod={"Start": start_date, "End": end_date},
            Granularity=granularity,
            Metrics=["UnblendedCost", "UsageQuantity"],
            Filter={"Dimensions": {"Key": "SERVICE", "Values": [service_name]}},
            GroupBy=[{"Type": "DIMENSION", "Key": "USAGE_TYPE"}],
        )

        results = {
            "service": service_name,
            "time_period": {"start": start_date, "end": end_date},
            "granularity": granularity,
            "total_cost": 0.0,
            "usage_types": {},
        }

        for result in response.get("ResultsByTime", []):
            for group in result.get("Groups", []):
                usage_type = group["Keys"][0]
                cost = float(group["Metrics"]["UnblendedCost"]["Amount"])
                results["usage_types"][usage_type] = (
                    results["usage_types"].get(usage_type, 0.0) + cost
                )
                results["total_cost"] += cost

        results["total_cost"] = round(results["total_cost"], 2)
        results["usage_types"] = {
            k: round(v, 2)
            for k, v in sorted(results["usage_types"].items(), key=lambda x: x[1], reverse=True)
        }
        return json.dumps(results, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e), "message": f"Failed to get costs for {service_name}"})
