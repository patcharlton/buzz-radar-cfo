"""Gap analysis between projections and targets."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class GapAnalysis:
    """Result of gap analysis."""
    target: float
    base_projection: float
    gap: float
    gap_percentage: float
    status: str  # 'on_track', 'at_risk', 'behind'
    deals_to_close: list[dict]


def calculate_gap(base_projection: float, target: float) -> dict:
    """
    Calculate the gap between base projection and target.

    Args:
        base_projection: The weighted pipeline projection
        target: The revenue target

    Returns:
        dict: Gap analysis with status and recommendations
    """
    gap = target - base_projection
    gap_percentage = (gap / target * 100) if target > 0 else 0

    # Determine status
    if gap <= 0:
        status = 'on_track'
        status_label = 'On Track'
        status_color = 'green'
    elif gap_percentage <= 15:
        status = 'at_risk'
        status_label = 'At Risk'
        status_color = 'amber'
    else:
        status = 'behind'
        status_label = 'Behind Target'
        status_color = 'red'

    return {
        'target': target,
        'base_projection': round(base_projection, 2),
        'gap': round(gap, 2),
        'gap_percentage': round(gap_percentage, 1),
        'status': status,
        'status_label': status_label,
        'status_color': status_color,
        'surplus': round(-gap, 2) if gap < 0 else 0,
    }


def find_deals_to_close_gap(gap: float, pipeline: list[dict]) -> list[dict]:
    """
    Find deals that could close the revenue gap.

    Prioritises deals by:
    1. High likelihood (8-10) first
    2. Then by value (larger deals preferred)
    3. Excludes Won deals

    Args:
        gap: The revenue gap to close
        pipeline: List of deal dictionaries

    Returns:
        list: Recommended deals to focus on closing
    """
    if gap <= 0:
        return []

    # Filter to actionable deals (not Won, likelihood > 0)
    actionable = [
        d for d in pipeline
        if d.get('stage') != 'Won' and d.get('likelihood', 0) > 0
    ]

    # Score deals: high likelihood + high value = high priority
    scored_deals = []
    for deal in actionable:
        likelihood = deal.get('likelihood', 0)
        value = deal.get('deal_value', 0)

        # Score: likelihood weight (0-1) * value
        # Higher likelihood deals are prioritised
        score = (likelihood / 10) * value

        scored_deals.append({
            'name': deal.get('name'),
            'client': deal.get('client'),
            'deal_value': value,
            'likelihood': likelihood,
            'stage': deal.get('stage'),
            'expected_close': deal.get('expected_close'),
            'decision_maker': deal.get('decision_maker'),
            'score': score,
            'weighted_value': round(value * likelihood / 10, 2),
        })

    # Sort by score descending
    scored_deals.sort(key=lambda x: x['score'], reverse=True)

    # Select deals to close gap
    selected = []
    cumulative = 0

    for deal in scored_deals:
        if cumulative >= gap:
            break

        selected.append({
            **deal,
            'impact': f"Adds {deal['weighted_value']:,.0f} to projection",
        })
        cumulative += deal['weighted_value']

    return selected


def get_gap_recommendations(gap_analysis: dict, deals_to_close: list[dict]) -> list[str]:
    """
    Generate actionable recommendations based on gap analysis.

    Args:
        gap_analysis: Result from calculate_gap
        deals_to_close: Recommended deals from find_deals_to_close_gap

    Returns:
        list: Prioritised recommendations
    """
    recommendations = []
    status = gap_analysis.get('status')
    gap = gap_analysis.get('gap', 0)

    if status == 'on_track':
        surplus = gap_analysis.get('surplus', 0)
        recommendations.append(
            f"Pipeline is healthy with {surplus:,.0f} surplus above target."
        )
        recommendations.append(
            "Focus on converting high-likelihood deals to lock in the quarter."
        )

    elif status == 'at_risk':
        recommendations.append(
            f"Gap of {gap:,.0f} to target - needs attention."
        )

        if deals_to_close:
            top_deal = deals_to_close[0]
            recommendations.append(
                f"Priority: Close {top_deal['name']} ({top_deal['client']}) - "
                f"{top_deal['deal_value']:,.0f} at {top_deal['likelihood']}/10 likelihood."
            )

        recommendations.append(
            "Review deals in 'Proposal Being Reviewed' stage for quick wins."
        )

    else:  # behind
        recommendations.append(
            f"Significant gap of {gap:,.0f} ({gap_analysis.get('gap_percentage')}%) to target."
        )

        if len(deals_to_close) >= 2:
            total_needed = sum(d['weighted_value'] for d in deals_to_close[:3])
            recommendations.append(
                f"Need to close multiple deals: {', '.join(d['name'] for d in deals_to_close[:3])} "
                f"would add {total_needed:,.0f} to projection."
            )

        recommendations.append(
            "Consider accelerating pipeline by moving deals forward in stages."
        )
        recommendations.append(
            "Evaluate if target is realistic given current pipeline."
        )

    return recommendations


def analyse_gap(base_projection: float, target: float, pipeline: list[dict]) -> dict:
    """
    Complete gap analysis with recommendations.

    Args:
        base_projection: Weighted pipeline projection
        target: Revenue target
        pipeline: List of deal dictionaries

    Returns:
        dict: Complete gap analysis with deals and recommendations
    """
    gap_analysis = calculate_gap(base_projection, target)
    gap = gap_analysis.get('gap', 0)

    deals_to_close = find_deals_to_close_gap(gap, pipeline) if gap > 0 else []
    recommendations = get_gap_recommendations(gap_analysis, deals_to_close)

    return {
        **gap_analysis,
        'deals_to_close': deals_to_close,
        'recommendations': recommendations,
        'deals_count': len(deals_to_close),
    }
