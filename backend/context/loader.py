"""Context loader for business information YAML files."""

import os
import yaml
from pathlib import Path


def get_context_dir():
    """Get the path to the context directory."""
    return Path(__file__).parent


def load_yaml_file(filename):
    """Load a single YAML file from the context directory."""
    filepath = get_context_dir() / filename
    if not filepath.exists():
        return {}

    with open(filepath, 'r') as f:
        return yaml.safe_load(f) or {}


def load_all_context():
    """
    Load all context YAML files and return combined dictionary.

    Returns:
        dict: Combined context with keys: business, clients, goals, rules, pipeline, risks, metrics
    """
    return {
        'business': load_yaml_file('business_context.yaml'),
        'clients': load_yaml_file('clients.yaml'),
        'goals': load_yaml_file('goals.yaml'),
        'rules': load_yaml_file('rules.yaml'),
        'pipeline': load_yaml_file('pipeline.yaml'),
        'risks': load_yaml_file('risks.yaml'),
        'metrics': load_yaml_file('metrics.yaml'),
    }


def load_pipeline():
    """Load pipeline data."""
    return load_yaml_file('pipeline.yaml')


def get_deals_by_stage(stage_name):
    """
    Get all deals at a specific stage.

    Args:
        stage_name: Stage name (e.g., "Won", "Verbal Agreement", "Procurement")

    Returns:
        list: Deals at that stage
    """
    pipeline = load_pipeline()
    deals = pipeline.get('deals', [])
    return [d for d in deals if d.get('stage') == stage_name]


def get_overdue_deals():
    """
    Get all deals with expected close dates that have passed.

    Returns:
        list: Overdue deals with days_overdue added
    """
    from datetime import date

    pipeline = load_pipeline()
    deals = pipeline.get('deals', [])
    today = date.today()

    overdue = []
    for deal in deals:
        expected_close = deal.get('expected_close')
        if expected_close:
            try:
                close_date = date.fromisoformat(expected_close)
                if close_date < today and deal.get('stage') != 'Won':
                    deal_copy = deal.copy()
                    deal_copy['days_overdue'] = (today - close_date).days
                    overdue.append(deal_copy)
            except ValueError:
                pass

    return sorted(overdue, key=lambda x: x.get('days_overdue', 0), reverse=True)


def get_deals_closing_this_month():
    """
    Get all deals expected to close this month.

    Returns:
        list: Deals closing this month
    """
    from datetime import date

    pipeline = load_pipeline()
    deals = pipeline.get('deals', [])
    today = date.today()

    closing = []
    for deal in deals:
        expected_close = deal.get('expected_close')
        if expected_close:
            try:
                close_date = date.fromisoformat(expected_close)
                if close_date.year == today.year and close_date.month == today.month:
                    closing.append(deal)
            except ValueError:
                pass

    return closing


def calculate_weighted_pipeline():
    """
    Calculate weighted pipeline value based on likelihood scores.

    Returns:
        dict: Pipeline breakdown by confidence level
    """
    pipeline = load_pipeline()
    deals = pipeline.get('deals', [])

    committed = 0  # Won
    high_confidence = 0  # Verbal Agreement + Procurement (likelihood >= 7)
    medium_confidence = 0  # Proposals (likelihood >= 5)
    weighted_total = 0

    for deal in deals:
        value = deal.get('deal_value', 0)
        likelihood = deal.get('likelihood', 0)
        stage = deal.get('stage', '')
        weight = likelihood / 10.0

        if stage == 'Won':
            committed += value
            weighted_total += value
        elif stage == 'Verbal Agreement':
            high_confidence += value
            weighted_total += value * weight
        elif stage == 'Procurement' and likelihood >= 7:
            high_confidence += value
            weighted_total += value * weight
        elif stage in ['Proposal Being Reviewed', 'Build Proposal']:
            medium_confidence += value
            weighted_total += value * weight
        else:
            weighted_total += value * weight

    return {
        'committed': committed,
        'high_confidence': high_confidence,
        'medium_confidence': medium_confidence,
        'weighted_total': int(weighted_total),
        'total_deals': len(deals),
    }


def get_client_by_name(name):
    """
    Get client information by name.

    Args:
        name: Client name (case-insensitive partial match)

    Returns:
        dict: Client info or None if not found
    """
    context = load_yaml_file('clients.yaml')
    clients = context.get('clients', [])

    name_lower = name.lower()
    for client in clients:
        if name_lower in client.get('name', '').lower():
            return client

    return None


def get_at_risk_clients():
    """
    Get all clients marked as at-risk.

    Returns:
        list: Clients with high risk level or at_risk renewal status
    """
    context = load_yaml_file('clients.yaml')
    clients = context.get('clients', [])

    at_risk = []
    for client in clients:
        if (client.get('risk_level') == 'high' or
                client.get('renewal_status') == 'at_risk'):
            at_risk.append(client)

    return at_risk


def get_active_clients():
    """Get all active clients."""
    context = load_yaml_file('clients.yaml')
    clients = context.get('clients', [])
    return [c for c in clients if c.get('status') == 'active']


def get_total_at_risk_revenue():
    """Calculate total revenue at risk from at-risk clients."""
    at_risk = get_at_risk_clients()
    return sum(c.get('contract_value', 0) for c in at_risk)


def get_pipeline_value():
    """Get total pipeline value from prospects."""
    context = load_yaml_file('clients.yaml')
    clients = context.get('clients', [])
    return sum(c.get('pipeline_value', 0) for c in clients if c.get('status') == 'prospect')


def get_financial_thresholds():
    """Get key financial thresholds from rules."""
    rules = load_yaml_file('rules.yaml')
    return {
        'cash_minimum': rules.get('cash', {}).get('minimum_reserve', 200000),
        'cash_target': rules.get('cash', {}).get('target_reserve', 300000),
        'cash_warning': rules.get('cash', {}).get('warning_threshold', 250000),
        'overdue_warning_days': rules.get('receivables', {}).get('warning_days_overdue', 14),
        'overdue_critical_days': rules.get('receivables', {}).get('critical_days_overdue', 30),
        'large_invoice_threshold': rules.get('receivables', {}).get('large_invoice_threshold', 50000),
    }


def get_company_info():
    """Get basic company information."""
    business = load_yaml_file('business_context.yaml')
    company = business.get('company', {})
    return {
        'name': company.get('name', 'Buzz Radar Limited'),
        'currency': company.get('currency', 'GBP'),
        'industry': company.get('industry', 'SaaS'),
    }


def get_critical_risks():
    """
    Get all risks with severity="Critical" or "High".

    Returns:
        list: Critical and high severity risks with relevant details
    """
    risks_data = load_yaml_file('risks.yaml')
    all_risks = risks_data.get('risks', [])

    critical_risks = []
    for risk in all_risks:
        severity = risk.get('severity', '').lower()
        if severity in ['critical', 'high']:
            critical_risks.append({
                'id': risk.get('id'),
                'name': risk.get('name'),
                'severity': risk.get('severity'),
                'category': risk.get('category'),
                'current_state': risk.get('current_state', {}),
                'specific_threats': risk.get('specific_threats', []),
                'exposures': risk.get('exposures', []),
                'mitigation': risk.get('mitigation', []),
                'ai_cfo_action': risk.get('ai_cfo_action'),
            })

    return critical_risks


def get_current_metrics():
    """
    Get key current state metrics for AI CFO analysis.

    Returns:
        dict: Current metrics including financial health, services, and cost metrics
    """
    metrics_data = load_yaml_file('metrics.yaml')
    business = load_yaml_file('business_context.yaml')
    financials = business.get('financials', {})

    # Extract current values from metrics
    financial_metrics = metrics_data.get('financial_metrics', [])
    services_metrics = metrics_data.get('services_metrics', [])
    cost_metrics = metrics_data.get('cost_metrics', [])

    def find_metric(metrics_list, metric_name):
        for m in metrics_list:
            if m.get('metric') == metric_name:
                return m
        return {}

    return {
        # Financial health
        'annual_revenue': financials.get('annual_revenue', 1300000),
        'gross_margin': financials.get('gross_margin', 94),
        'net_margin': financials.get('net_margin', 11),
        'net_profit': financials.get('net_profit', 148000),
        'yoy_growth': financials.get('yoy_growth', 109),

        # Revenue mix (current vs target)
        'revenue_mix': find_metric(financial_metrics, 'Revenue Mix'),

        # Client concentration
        'client_concentration': find_metric(services_metrics, 'Client Concentration Ratio'),

        # Cost metrics
        'api_efficiency': find_metric(cost_metrics, 'API Efficiency Ratio'),
        'data_source_dependency': find_metric(cost_metrics, 'Data Source Dependency'),
    }


def get_q1_goals():
    """
    Get Q1 2026 operational goals.

    Returns:
        list: Q1 2026 goals with priorities and metrics
    """
    goals_data = load_yaml_file('goals.yaml')
    operational = goals_data.get('operational_goals', {})
    return operational.get('q1_2026', [])


def get_transition_status():
    """
    Get services-to-platform transition status.

    Returns:
        dict: Current transition status including revenue mix and milestones
    """
    business = load_yaml_file('business_context.yaml')
    goals = load_yaml_file('goals.yaml')
    metrics = load_yaml_file('metrics.yaml')

    business_model = business.get('business_model', {})
    financials = business.get('financials', {})
    exit_thesis = goals.get('exit_thesis', {})
    financial_goals = goals.get('financial_goals', {})

    # Get revenue mix targets
    financial_metrics = metrics.get('financial_metrics', [])
    revenue_mix = {}
    for m in financial_metrics:
        if m.get('metric') == 'Revenue Mix':
            revenue_mix = m
            break

    return {
        'current_state': business_model.get('current_state', '100% services-led'),
        'current_revenue': financials.get('annual_revenue', 1300000),

        'revenue_mix': {
            'current': revenue_mix.get('current', {'services': 100, 'platform': 0}),
            'target_end_2026': revenue_mix.get('target_end_2026', {'services': 75, 'platform': 25}),
            'target_mid_2027': revenue_mix.get('target_mid_2027', {'services': 10, 'platform': 90}),
        },

        'timeline': business_model.get('transition_timeline', {}),

        'exit_thesis': {
            'target_year': exit_thesis.get('target_year', 2030),
            'valuation_low': exit_thesis.get('valuation', {}).get('low', 35000000),
            'valuation_high': exit_thesis.get('valuation', {}).get('high', 50000000),
            'requirements': exit_thesis.get('requirements', {}),
        },

        'platform_revenue_target_2026': financial_goals.get('short_term', [{}])[3].get('target', 450000)
        if len(financial_goals.get('short_term', [])) > 3 else 450000,

        'milestones': business.get('milestones', {}),
    }


def get_deals_closing_next_n_days(days=30):
    """
    Get all deals expected to close within the next N days.

    Args:
        days: Number of days to look ahead (default 30)

    Returns:
        list: Deals closing within the specified timeframe
    """
    from datetime import date, timedelta

    pipeline = load_pipeline()
    deals = pipeline.get('deals', [])
    today = date.today()
    end_date = today + timedelta(days=days)

    closing = []
    for deal in deals:
        expected_close = deal.get('expected_close')
        stage = deal.get('stage', '')
        if expected_close and stage != 'Won':
            try:
                close_date = date.fromisoformat(expected_close)
                if today <= close_date <= end_date:
                    closing.append(deal)
            except ValueError:
                pass

    return sorted(closing, key=lambda x: x.get('expected_close', ''))


def get_milestones_next_90_days():
    """
    Get key milestones for the next 90 days.

    Returns:
        list: Upcoming milestones from goals
    """
    from datetime import date

    goals_data = load_yaml_file('goals.yaml')
    operational = goals_data.get('operational_goals', {})

    # Determine current quarter
    today = date.today()

    # Get current and next quarter goals
    milestones = []

    # Q1 2026 goals
    for goal in operational.get('q1_2026', []):
        milestones.append({
            'quarter': 'Q1 2026',
            'goal': goal.get('goal'),
            'priority': goal.get('priority'),
            'value': goal.get('value') or goal.get('value_if_success'),
            'deadline': goal.get('deadline'),
        })

    return milestones
