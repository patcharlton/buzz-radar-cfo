"""Revenue scenario calculations based on pipeline deals."""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional


@dataclass
class Deal:
    """Represents a pipeline deal."""
    name: str
    client: str
    stage: str
    deal_value: float
    likelihood: int
    expected_close: Optional[str] = None
    best_case: Optional[float] = None
    worst_case: Optional[float] = None


@dataclass
class MonthlyProjection:
    """Revenue projection for a single month."""
    month: str  # YYYY-MM format
    month_label: str  # e.g., "January 2026"
    conservative: float
    base: float
    optimistic: float


@dataclass
class ScenarioResult:
    """Complete scenario analysis result."""
    months: list[MonthlyProjection]
    totals: dict[str, float]
    deals_by_month: dict[str, list[dict]]


def parse_deals(pipeline_deals: list[dict]) -> list[Deal]:
    """Convert raw pipeline dict to Deal objects."""
    deals = []
    for d in pipeline_deals:
        deals.append(Deal(
            name=d.get('name', ''),
            client=d.get('client', ''),
            stage=d.get('stage', ''),
            deal_value=float(d.get('deal_value', 0)),
            likelihood=int(d.get('likelihood', 0)),
            expected_close=d.get('expected_close'),
            best_case=float(d.get('best_case', d.get('deal_value', 0))) if d.get('best_case') else None,
            worst_case=float(d.get('worst_case', 0)) if d.get('worst_case') else None,
        ))
    return deals


def get_month_key(dt: date) -> str:
    """Get YYYY-MM format from date."""
    return dt.strftime('%Y-%m')


def get_month_label(dt: date) -> str:
    """Get human-readable month label."""
    return dt.strftime('%B %Y')


def allocate_deal_to_month(deal: Deal, target_months: list[str]) -> Optional[str]:
    """
    Determine which month a deal should be allocated to.

    Args:
        deal: The deal to allocate
        target_months: List of YYYY-MM month keys we're projecting

    Returns:
        Month key or None if deal doesn't fall in projection period
    """
    if not deal.expected_close:
        # No close date - allocate to first month if Won, otherwise exclude
        if deal.stage == 'Won':
            return target_months[0] if target_months else None
        return None

    try:
        close_date = date.fromisoformat(deal.expected_close)
        month_key = get_month_key(close_date)

        # If deal close date is before first projection month, allocate to first month
        if month_key < target_months[0]:
            return target_months[0]

        # If deal close date is in projection period
        if month_key in target_months:
            return month_key

        # Deal closes after projection period - exclude
        return None

    except ValueError:
        return None


def calculate_scenarios(pipeline: list[dict], months: int = 3) -> dict:
    """
    Calculate revenue scenarios for the next N months.

    Args:
        pipeline: List of deal dictionaries from pipeline.yaml
        months: Number of months to project (default: 3)

    Returns:
        dict: Scenario projections with conservative, base, and optimistic values

    Scenarios:
        - Conservative: Won deals + (Verbal Agreement deals * 0.8)
        - Base: Sum of (deal_value * likelihood/10) for all deals
        - Optimistic: best_case for deals with likelihood >= 5
    """
    deals = parse_deals(pipeline)
    today = date.today()

    # Generate target months
    target_months = []
    month_labels = {}
    current = date(today.year, today.month, 1)

    for i in range(months):
        month_key = get_month_key(current)
        target_months.append(month_key)
        month_labels[month_key] = get_month_label(current)

        # Move to next month
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)

    # Initialize monthly projections
    monthly_data = {
        month: {'conservative': 0.0, 'base': 0.0, 'optimistic': 0.0, 'deals': []}
        for month in target_months
    }

    # Allocate deals to months
    for deal in deals:
        month = allocate_deal_to_month(deal, target_months)
        if not month:
            continue

        deal_info = {
            'name': deal.name,
            'client': deal.client,
            'stage': deal.stage,
            'deal_value': deal.deal_value,
            'likelihood': deal.likelihood,
        }
        monthly_data[month]['deals'].append(deal_info)

        # Conservative: Won + (Verbal Agreement * 0.8)
        if deal.stage == 'Won':
            monthly_data[month]['conservative'] += deal.deal_value
        elif deal.stage == 'Verbal Agreement':
            monthly_data[month]['conservative'] += deal.deal_value * 0.8

        # Base: deal_value * (likelihood / 10)
        weight = deal.likelihood / 10.0
        monthly_data[month]['base'] += deal.deal_value * weight

        # Optimistic: best_case for deals with likelihood >= 5
        if deal.likelihood >= 5:
            best = deal.best_case if deal.best_case else deal.deal_value
            monthly_data[month]['optimistic'] += best
        elif deal.stage == 'Won':
            # Won deals always count in optimistic
            monthly_data[month]['optimistic'] += deal.deal_value

    # Build result
    projections = []
    totals = {'conservative': 0.0, 'base': 0.0, 'optimistic': 0.0}
    deals_by_month = {}

    for month in target_months:
        data = monthly_data[month]
        projections.append({
            'month': month,
            'month_label': month_labels[month],
            'conservative': round(data['conservative'], 2),
            'base': round(data['base'], 2),
            'optimistic': round(data['optimistic'], 2),
        })

        totals['conservative'] += data['conservative']
        totals['base'] += data['base']
        totals['optimistic'] += data['optimistic']

        deals_by_month[month] = data['deals']

    return {
        'months': projections,
        'totals': {
            'conservative': round(totals['conservative'], 2),
            'base': round(totals['base'], 2),
            'optimistic': round(totals['optimistic'], 2),
        },
        'deals_by_month': deals_by_month,
        'projection_period': {
            'start': target_months[0],
            'end': target_months[-1],
            'num_months': months,
        },
    }
