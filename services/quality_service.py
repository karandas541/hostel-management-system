"""Actionable recommendations based on observed feedback ratings."""

from analytics.satisfaction_analysis import get_satisfaction_analysis
from utils.authorization import require_role


def get_quality_recommendations(actor=None):
    require_role(actor, "admin")
    recommendations = []
    for category, score in get_satisfaction_analysis(actor=actor).items():
        if score is None:
            status = "No feedback yet"
            recommendation = f"Collect feedback for {category} before setting an improvement target."
        elif score < 3.0:
            status = "Critical Improvement"
            recommendation = f"{category} needs immediate attention."
        elif score < 4.0:
            status = "Needs Improvement"
            recommendation = f"Improve {category} to increase student satisfaction."
        else:
            status = "Good Performance"
            recommendation = f"{category} is performing well. Continue monitoring."
        recommendations.append({
            "category": category,
            "score": score,
            "status": status,
            "recommendation": recommendation,
        })
    return recommendations
