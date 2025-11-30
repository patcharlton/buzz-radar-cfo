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
        dict: Combined context with keys: business, clients, goals, rules, pipeline
    """
    return {
        'business': load_yaml_file('business_context.yaml'),
        'clients': load_yaml_file('clients.yaml'),
        'goals': load_yaml_file('goals.yaml'),
        'rules': load_yaml_file('rules.yaml'),
        'pipeline': load_yaml_file('pipeline.yaml'),
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
