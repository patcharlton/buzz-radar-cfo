"""
Financial intelligence metrics API endpoints.

Provides calculated metrics based on historical bank transaction data:
- Runway confidence bands
- Fixed cost floor analysis
- Vendor spend trends
- Cash concentration risk
- Natural language financial queries
"""

from datetime import date, datetime, timedelta
from statistics import mean, stdev
from flask import Blueprint, jsonify, request
from sqlalchemy import func, case, extract, and_, or_

from database import db
from database.models import BankTransaction, MonthlyCashSnapshot

metrics_bp = Blueprint('metrics', __name__)


# =============================================================================
# Helper Functions
# =============================================================================

def get_current_cash_position():
    """Get current cash position from most recent snapshot or calculate from transactions."""
    # Try to get from Xero via dashboard data cache
    try:
        from xero import XeroClient, XeroAuth
        xero_auth = XeroAuth()
        if xero_auth.is_connected():
            xero_client = XeroClient()
            bank_data = xero_client.get_bank_summary()
            return bank_data.get('total_balance', 0)
    except Exception:
        pass

    # Fallback: calculate from most recent snapshot
    latest_snapshot = MonthlyCashSnapshot.query.order_by(
        MonthlyCashSnapshot.snapshot_date.desc()
    ).first()

    if latest_snapshot and latest_snapshot.closing_balance:
        return float(latest_snapshot.closing_balance)

    # Last resort: sum all transactions
    total_in = db.session.query(func.sum(BankTransaction.debit_gbp)).scalar() or 0
    total_out = db.session.query(func.sum(BankTransaction.credit_gbp)).scalar() or 0
    return float(total_in) - float(total_out)


def categorize_expense(description):
    """Categorize expenses based on description patterns."""
    if not description:
        return 'OTHER'

    desc_lower = description.lower()

    categories = {
        'PAYROLL': ['wages', 'hmrc', 'nest pensions', 'paye', 'salary'],
        'SOFTWARE': ['adobe', 'github', 'openai', 'claude', 'asana', 'chatgpt',
                     'microsoft', 'google', 'aws', 'slack', 'notion', 'figma',
                     'anthropic', 'mailchimp', 'hubspot', 'salesforce', 'zoom'],
        'OFFICE': ['lb camden', 'labs camden', 'rent', 'office', 'workspace'],
        'INSURANCE': ['hiscox', 'insurance'],
        'TELECOM': ['ee & t-mobile', 'ee ', 'vodafone', 'three', 'o2', 'mobile'],
        'VEHICLE': ['vwfs', 'vehicle', 'car', 'fuel', 'petrol'],
        'BANKING': ['bank charge', 'interest', 'fee'],
        'PROFESSIONAL': ['accountant', 'legal', 'solicitor', 'consultant'],
        'MARKETING': ['advertising', 'marketing', 'google ads', 'facebook'],
        'TRAVEL': ['travel', 'hotel', 'flight', 'train', 'uber'],
    }

    for category, keywords in categories.items():
        if any(kw in desc_lower for kw in keywords):
            return category

    return 'OTHER'


def normalize_description(description):
    """Normalize description for grouping similar transactions."""
    if not description:
        return 'Unknown'

    # Remove common prefixes and clean up
    desc = description.strip()

    # Remove transaction references (e.g., dates, numbers at end)
    import re
    # Remove trailing dates like "01/12/2024" or "2024-12-01"
    desc = re.sub(r'\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\s*$', '', desc)
    # Remove trailing reference numbers
    desc = re.sub(r'\s*#?\d{6,}\s*$', '', desc)

    return desc.strip() or 'Unknown'


def extract_client_name(description):
    """Extract client name from payment description."""
    if not description:
        return 'Unknown'

    # Common patterns for receivable payments
    if description.startswith('Payment: '):
        return description[9:].strip()
    if description.startswith('From: '):
        return description[6:].strip()
    if ' - Payment' in description:
        return description.split(' - Payment')[0].strip()

    return normalize_description(description)


# =============================================================================
# Widget 1: Cash Runway Confidence Band
# =============================================================================

@metrics_bp.route('/api/metrics/runway-confidence')
def runway_confidence():
    """
    Calculate runway with confidence bands based on historical cash flow variance.

    Returns best case, expected, and worst case runway estimates.
    """
    try:
        # Get last 12 complete months of snapshots
        twelve_months_ago = date.today().replace(day=1) - timedelta(days=365)

        snapshots = MonthlyCashSnapshot.query.filter(
            MonthlyCashSnapshot.snapshot_date >= twelve_months_ago
        ).order_by(MonthlyCashSnapshot.snapshot_date).all()

        if len(snapshots) < 3:
            return jsonify({
                'success': False,
                'error': 'Insufficient historical data (need at least 3 months)'
            }), 400

        # Calculate monthly net flows (total_in - total_out)
        monthly_flows = []
        for snapshot in snapshots:
            net_flow = float(snapshot.total_in or 0) - float(snapshot.total_out or 0)
            monthly_flows.append(net_flow)

        current_cash = get_current_cash_position()

        # Calculate statistics
        avg_flow = mean(monthly_flows)
        flow_std = stdev(monthly_flows) if len(monthly_flows) > 1 else 0

        # If average flow is positive (profitable)
        if avg_flow >= 0:
            return jsonify({
                'success': True,
                'is_profitable': True,
                'current_cash': round(current_cash, 2),
                'avg_monthly_surplus': round(avg_flow, 2),
                'surplus_volatility': round(flow_std, 2),
                'months_analyzed': len(monthly_flows),
                'calculation_basis': f'{len(monthly_flows)}-month cash flow history'
            })

        # Calculate runway scenarios (using absolute burn)
        avg_burn = abs(avg_flow)
        best_burn = abs(avg_flow + flow_std)   # Lower burn (1 std dev better)
        worst_burn = abs(avg_flow - flow_std)  # Higher burn (1 std dev worse)

        # Handle edge cases
        if best_burn <= 0:
            best_runway = 24  # Cap at 24+ months
        else:
            best_runway = min(current_cash / best_burn, 24)

        expected_runway = current_cash / avg_burn if avg_burn > 0 else 24
        worst_runway = current_cash / worst_burn if worst_burn > 0 else 0

        return jsonify({
            'success': True,
            'is_profitable': False,
            'current_cash': round(current_cash, 2),
            'best_case_months': round(best_runway, 1),
            'expected_months': round(expected_runway, 1),
            'worst_case_months': round(max(worst_runway, 0), 1),
            'avg_monthly_burn': round(avg_burn, 2),
            'burn_volatility': round(flow_std, 2),
            'months_analyzed': len(monthly_flows),
            'calculation_basis': f'{len(monthly_flows)}-month cash flow history'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# Widget 2: Fixed Cost Floor
# =============================================================================

@metrics_bp.route('/api/metrics/fixed-costs')
def fixed_costs():
    """
    Identify and sum recurring monthly expenses (appear in 80%+ of months).

    Returns breakdown of fixed costs by category with zero-revenue runway.
    """
    try:
        # Get 12 months of expense transactions
        twelve_months_ago = date.today() - timedelta(days=365)

        expenses = BankTransaction.query.filter(
            BankTransaction.source_type == 'Spend Money',
            BankTransaction.transaction_date >= twelve_months_ago,
            BankTransaction.credit_gbp > 0
        ).all()

        if not expenses:
            return jsonify({
                'success': False,
                'error': 'No expense transactions found'
            }), 400

        # Count occurrences per description
        monthly_presence = {}  # {description: set of months}
        monthly_amounts = {}   # {description: [amounts]}

        for tx in expenses:
            desc = normalize_description(tx.description)
            month = tx.transaction_date.strftime('%Y-%m')

            if desc not in monthly_presence:
                monthly_presence[desc] = set()
                monthly_amounts[desc] = []

            monthly_presence[desc].add(month)
            monthly_amounts[desc].append(float(tx.credit_gbp or 0))

        # Get total months in dataset
        all_months = set()
        for tx in expenses:
            all_months.add(tx.transaction_date.strftime('%Y-%m'))
        total_months = len(all_months)

        # Fixed cost = appears in 80%+ of months
        fixed_costs_list = []

        for desc, months in monthly_presence.items():
            frequency = len(months) / total_months
            if frequency >= 0.8:
                amounts = monthly_amounts[desc]
                avg_amount = mean(amounts)

                fixed_costs_list.append({
                    'description': desc,
                    'avg_monthly': round(avg_amount, 2),
                    'frequency_pct': round(frequency * 100, 0),
                    'months_present': len(months),
                    'category': categorize_expense(desc)
                })

        # Sort by amount descending
        fixed_costs_list.sort(key=lambda x: x['avg_monthly'], reverse=True)

        total_fixed = sum(fc['avg_monthly'] for fc in fixed_costs_list)

        # Group by category
        by_category = {}
        for fc in fixed_costs_list:
            cat = fc['category']
            if cat not in by_category:
                by_category[cat] = {'total': 0, 'items': []}
            by_category[cat]['total'] += fc['avg_monthly']
            by_category[cat]['items'].append(fc)

        # Sort categories by total
        categories_sorted = sorted(
            [{'category': k, **v} for k, v in by_category.items()],
            key=lambda x: x['total'],
            reverse=True
        )

        # Calculate percentages
        for cat in categories_sorted:
            cat['percent'] = round(cat['total'] / total_fixed * 100, 1) if total_fixed > 0 else 0
            cat['total'] = round(cat['total'], 2)

        current_cash = get_current_cash_position()
        zero_revenue_runway = round(current_cash / total_fixed, 1) if total_fixed > 0 else None

        # Get average total burn for comparison
        avg_total_burn = db.session.query(
            func.avg(MonthlyCashSnapshot.total_out)
        ).scalar() or total_fixed

        return jsonify({
            'success': True,
            'total_monthly_fixed': round(total_fixed, 2),
            'zero_revenue_runway': zero_revenue_runway,
            'current_cash': round(current_cash, 2),
            'as_percent_of_avg_burn': round(total_fixed / float(avg_total_burn) * 100, 1) if avg_total_burn else None,
            'fixed_costs': fixed_costs_list[:20],  # Top 20
            'by_category': categories_sorted,
            'total_months_analyzed': total_months
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# Widget 3: Vendor Spend Trends
# =============================================================================

@metrics_bp.route('/api/metrics/vendor-trends')
def vendor_trends():
    """
    Top vendors by spend with year-over-year comparison.

    Query params:
        year: Compare this year vs prior (default: current year)
        limit: Number of vendors to return (default: 15)
    """
    try:
        year = request.args.get('year', date.today().year, type=int)
        limit = request.args.get('limit', 15, type=int)

        # Define periods (same months for fair comparison)
        current_month = date.today().month
        current_start = date(year, 1, 1)
        current_end = date(year, current_month, 1) - timedelta(days=1)  # End of last complete month

        prior_start = date(year - 1, 1, 1)
        prior_end = date(year - 1, current_month, 1) - timedelta(days=1)

        # Get current year transactions
        current_txs = BankTransaction.query.filter(
            BankTransaction.source_type == 'Spend Money',
            BankTransaction.transaction_date >= current_start,
            BankTransaction.transaction_date <= current_end,
            BankTransaction.credit_gbp > 0
        ).all()

        # Get prior year transactions
        prior_txs = BankTransaction.query.filter(
            BankTransaction.source_type == 'Spend Money',
            BankTransaction.transaction_date >= prior_start,
            BankTransaction.transaction_date <= prior_end,
            BankTransaction.credit_gbp > 0
        ).all()

        # Aggregate by vendor
        current_by_vendor = {}
        for tx in current_txs:
            vendor = normalize_description(tx.description)
            current_by_vendor[vendor] = current_by_vendor.get(vendor, 0) + float(tx.credit_gbp or 0)

        prior_by_vendor = {}
        for tx in prior_txs:
            vendor = normalize_description(tx.description)
            prior_by_vendor[vendor] = prior_by_vendor.get(vendor, 0) + float(tx.credit_gbp or 0)

        # Combine all vendors
        all_vendors = set(current_by_vendor.keys()) | set(prior_by_vendor.keys())

        vendors = []
        for vendor in all_vendors:
            current_spend = current_by_vendor.get(vendor, 0)
            prior_spend = prior_by_vendor.get(vendor, 0)

            if prior_spend > 0:
                change_pct = ((current_spend - prior_spend) / prior_spend) * 100
            else:
                change_pct = None

            vendors.append({
                'vendor': vendor,
                'current_year': round(current_spend, 2),
                'prior_year': round(prior_spend, 2),
                'change_amount': round(current_spend - prior_spend, 2),
                'change_percent': round(change_pct, 1) if change_pct is not None else None,
                'is_new': prior_spend == 0 and current_spend > 0,
                'is_discontinued': current_spend == 0 and prior_spend > 0,
                'category': categorize_expense(vendor)
            })

        # Sort by current year spend
        vendors.sort(key=lambda x: x['current_year'], reverse=True)

        total_current = sum(v['current_year'] for v in vendors)
        total_prior = sum(v['prior_year'] for v in vendors)
        overall_change = ((total_current - total_prior) / total_prior * 100) if total_prior > 0 else None

        return jsonify({
            'success': True,
            'period': f'Jan-{current_end.strftime("%b")} {year} vs Jan-{prior_end.strftime("%b")} {year - 1}',
            'current_year': year,
            'prior_year': year - 1,
            'top_vendors': vendors[:limit],
            'all_vendors_count': len(vendors),
            'total_current': round(total_current, 2),
            'total_prior': round(total_prior, 2),
            'overall_change_pct': round(overall_change, 1) if overall_change is not None else None,
            'new_vendors_count': sum(1 for v in vendors if v['is_new']),
            'discontinued_count': sum(1 for v in vendors if v['is_discontinued'])
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# Widget 4: Cash Concentration Risk
# =============================================================================

@metrics_bp.route('/api/metrics/cash-concentration')
def cash_concentration():
    """
    Analyze revenue concentration across clients.

    Returns concentration risk assessment and client breakdown.
    """
    try:
        # Get receivable payments (money from clients) - last 12 months
        twelve_months_ago = date.today() - timedelta(days=365)

        payments = BankTransaction.query.filter(
            BankTransaction.source_type == 'Receivable Payment',
            BankTransaction.transaction_date >= twelve_months_ago,
            BankTransaction.debit_gbp > 0
        ).all()

        if not payments:
            return jsonify({
                'success': False,
                'error': 'No receivable payments found'
            }), 400

        # Aggregate by client
        client_totals = {}
        for tx in payments:
            client = extract_client_name(tx.description)
            client_totals[client] = client_totals.get(client, 0) + float(tx.debit_gbp or 0)

        # Sort by total
        sorted_clients = sorted(client_totals.items(), key=lambda x: x[1], reverse=True)

        total_received = sum(client_totals.values())

        if total_received == 0:
            return jsonify({
                'success': False,
                'error': 'No revenue recorded'
            }), 400

        # Calculate concentration metrics
        top_1 = sorted_clients[0][1] if len(sorted_clients) >= 1 else 0
        top_3 = sum(c[1] for c in sorted_clients[:3])
        top_5 = sum(c[1] for c in sorted_clients[:5])

        # Build client breakdown
        clients = []
        cumulative = 0
        for client, amount in sorted_clients[:10]:
            cumulative += amount
            clients.append({
                'client': client,
                'amount': round(amount, 2),
                'percent': round(amount / total_received * 100, 1),
                'cumulative_percent': round(cumulative / total_received * 100, 1)
            })

        # Risk assessment
        top_1_pct = top_1 / total_received
        top_3_pct = top_3 / total_received

        if top_1_pct > 0.4:
            concentration_risk = 'HIGH'
            risk_reason = f'Single client represents {round(top_1_pct * 100, 1)}% of revenue'
        elif top_3_pct > 0.7:
            concentration_risk = 'MEDIUM'
            risk_reason = f'Top 3 clients represent {round(top_3_pct * 100, 1)}% of revenue'
        else:
            concentration_risk = 'LOW'
            risk_reason = 'Revenue is well diversified across clients'

        return jsonify({
            'success': True,
            'period': 'Last 12 months',
            'total_received': round(total_received, 2),
            'top_1_percent': round(top_1_pct * 100, 1),
            'top_3_percent': round(top_3_pct * 100, 1),
            'top_5_percent': round(top_5 / total_received * 100, 1),
            'concentration_risk': concentration_risk,
            'risk_reason': risk_reason,
            'clients': clients,
            'client_count': len(client_totals),
            'top_client': {
                'name': sorted_clients[0][0] if sorted_clients else None,
                'amount': round(sorted_clients[0][1], 2) if sorted_clients else 0,
                'percent': round(top_1_pct * 100, 1)
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# Natural Language Financial Query
# =============================================================================

@metrics_bp.route('/api/query/financial', methods=['POST'])
def financial_query():
    """
    Process natural language financial queries.

    Parses the question and returns relevant structured data.
    """
    try:
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({
                'success': False,
                'error': 'Question is required'
            }), 400

        question = data['question'].strip().lower()

        # Extract time period
        period = extract_time_period(question)

        # Determine query type and execute
        result = None

        # Spending queries
        if any(word in question for word in ['spend', 'spent', 'paid', 'cost', 'expense']):
            result = handle_spending_query(question, period)

        # Revenue/payment queries
        elif any(word in question for word in ['received', 'revenue', 'income', 'paid us', 'from client']):
            result = handle_revenue_query(question, period)

        # Vendor/client specific queries
        elif any(word in question for word in ['when did', 'last time', 'last payment', 'how often']):
            result = handle_entity_query(question, period)

        # Top/ranking queries
        elif any(word in question for word in ['top', 'biggest', 'largest', 'highest', 'most']):
            result = handle_ranking_query(question, period)

        # Comparison queries
        elif any(word in question for word in ['compare', 'vs', 'versus', 'difference', 'change']):
            result = handle_comparison_query(question, period)

        # Generic query - return summary data
        else:
            result = handle_generic_query(question, period)

        # Build context for AI
        context = {
            'question': data['question'],
            'query_type': result.get('type', 'generic'),
            'period': period,
            'data_available': {
                'transactions_date_range': '2020-12-01 to present',
                'transaction_count': BankTransaction.query.count()
            }
        }

        return jsonify({
            'success': True,
            'question': data['question'],
            'result': result,
            'context': context
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def extract_time_period(question):
    """Extract time period from natural language."""
    today = date.today()

    question_lower = question.lower()

    # Check for specific patterns
    if 'last quarter' in question_lower:
        # Last complete quarter
        current_quarter = (today.month - 1) // 3
        if current_quarter == 0:
            start = date(today.year - 1, 10, 1)
            end = date(today.year - 1, 12, 31)
        else:
            start = date(today.year, (current_quarter - 1) * 3 + 1, 1)
            end_month = current_quarter * 3
            if end_month == 12:
                end = date(today.year, 12, 31)
            else:
                end = date(today.year, end_month + 1, 1) - timedelta(days=1)
        return {'start': start, 'end': end, 'label': 'last quarter'}

    if 'this quarter' in question_lower:
        current_quarter = (today.month - 1) // 3
        start = date(today.year, current_quarter * 3 + 1, 1)
        return {'start': start, 'end': today, 'label': 'this quarter'}

    if 'last month' in question_lower:
        first_of_month = today.replace(day=1)
        end = first_of_month - timedelta(days=1)
        start = end.replace(day=1)
        return {'start': start, 'end': end, 'label': 'last month'}

    if 'this month' in question_lower:
        start = today.replace(day=1)
        return {'start': start, 'end': today, 'label': 'this month'}

    if 'this year' in question_lower or str(today.year) in question_lower:
        return {'start': date(today.year, 1, 1), 'end': today, 'label': f'{today.year}'}

    if 'last year' in question_lower or str(today.year - 1) in question_lower:
        return {'start': date(today.year - 1, 1, 1), 'end': date(today.year - 1, 12, 31), 'label': f'{today.year - 1}'}

    # Check for specific year mentions
    import re
    year_match = re.search(r'\b(202[0-5])\b', question_lower)
    if year_match:
        year = int(year_match.group(1))
        if year == today.year:
            return {'start': date(year, 1, 1), 'end': today, 'label': str(year)}
        return {'start': date(year, 1, 1), 'end': date(year, 12, 31), 'label': str(year)}

    # Default to last 12 months
    return {'start': today - timedelta(days=365), 'end': today, 'label': 'last 12 months'}


def handle_spending_query(question, period):
    """Handle queries about spending."""
    # Try to extract vendor/category filter
    filter_term = None

    # Common spending categories to look for
    categories = ['consultant', 'software', 'aws', 'google', 'microsoft', 'adobe',
                  'wages', 'payroll', 'rent', 'office', 'travel', 'marketing']

    for cat in categories:
        if cat in question.lower():
            filter_term = cat
            break

    # Query transactions
    query = BankTransaction.query.filter(
        BankTransaction.source_type == 'Spend Money',
        BankTransaction.transaction_date >= period['start'],
        BankTransaction.transaction_date <= period['end'],
        BankTransaction.credit_gbp > 0
    )

    if filter_term:
        query = query.filter(BankTransaction.description.ilike(f'%{filter_term}%'))

    transactions = query.all()

    total = sum(float(tx.credit_gbp or 0) for tx in transactions)

    # Group by vendor
    by_vendor = {}
    for tx in transactions:
        vendor = normalize_description(tx.description)
        by_vendor[vendor] = by_vendor.get(vendor, 0) + float(tx.credit_gbp or 0)

    sorted_vendors = sorted(by_vendor.items(), key=lambda x: x[1], reverse=True)

    return {
        'type': 'spending',
        'period': period['label'],
        'filter': filter_term,
        'total_gbp': round(total, 2),
        'transaction_count': len(transactions),
        'breakdown': [
            {'vendor': v, 'amount': round(a, 2)}
            for v, a in sorted_vendors[:10]
        ],
        'sample_transactions': [
            {
                'date': tx.transaction_date.isoformat(),
                'description': tx.description,
                'amount': float(tx.credit_gbp)
            }
            for tx in transactions[:5]
        ]
    }


def handle_revenue_query(question, period):
    """Handle queries about revenue/income."""
    # Try to extract client filter
    filter_term = None

    # Check for client name mentions (would need actual client list)
    # For now, just do a generic query

    query = BankTransaction.query.filter(
        BankTransaction.source_type == 'Receivable Payment',
        BankTransaction.transaction_date >= period['start'],
        BankTransaction.transaction_date <= period['end'],
        BankTransaction.debit_gbp > 0
    )

    transactions = query.all()

    total = sum(float(tx.debit_gbp or 0) for tx in transactions)

    # Group by client
    by_client = {}
    for tx in transactions:
        client = extract_client_name(tx.description)
        by_client[client] = by_client.get(client, 0) + float(tx.debit_gbp or 0)

    sorted_clients = sorted(by_client.items(), key=lambda x: x[1], reverse=True)

    return {
        'type': 'revenue',
        'period': period['label'],
        'total_gbp': round(total, 2),
        'transaction_count': len(transactions),
        'breakdown': [
            {'client': c, 'amount': round(a, 2)}
            for c, a in sorted_clients[:10]
        ]
    }


def handle_entity_query(question, period):
    """Handle queries about specific vendors/clients."""
    # Find the entity mentioned
    # This is a simplified version - would need more sophisticated NLP

    transactions = BankTransaction.query.filter(
        BankTransaction.transaction_date >= period['start'],
        BankTransaction.transaction_date <= period['end']
    ).order_by(BankTransaction.transaction_date.desc()).limit(100).all()

    # Try to find matching transactions
    keywords = question.lower().split()
    matching = []

    for tx in transactions:
        desc_lower = (tx.description or '').lower()
        if any(kw in desc_lower for kw in keywords if len(kw) > 3):
            matching.append(tx)

    if matching:
        last_tx = matching[0]
        return {
            'type': 'entity',
            'found': True,
            'last_transaction': {
                'date': last_tx.transaction_date.isoformat(),
                'description': last_tx.description,
                'amount_in': float(last_tx.debit_gbp or 0),
                'amount_out': float(last_tx.credit_gbp or 0)
            },
            'transaction_count': len(matching),
            'recent_transactions': [
                {
                    'date': tx.transaction_date.isoformat(),
                    'description': tx.description,
                    'amount_in': float(tx.debit_gbp or 0),
                    'amount_out': float(tx.credit_gbp or 0)
                }
                for tx in matching[:5]
            ]
        }

    return {
        'type': 'entity',
        'found': False,
        'message': 'No matching transactions found'
    }


def handle_ranking_query(question, period):
    """Handle queries about top/biggest items."""
    is_expense = any(word in question.lower() for word in ['expense', 'spend', 'cost', 'vendor'])

    if is_expense:
        transactions = BankTransaction.query.filter(
            BankTransaction.source_type == 'Spend Money',
            BankTransaction.transaction_date >= period['start'],
            BankTransaction.transaction_date <= period['end'],
            BankTransaction.credit_gbp > 0
        ).all()

        by_vendor = {}
        for tx in transactions:
            vendor = normalize_description(tx.description)
            by_vendor[vendor] = by_vendor.get(vendor, 0) + float(tx.credit_gbp or 0)

        sorted_items = sorted(by_vendor.items(), key=lambda x: x[1], reverse=True)

        return {
            'type': 'ranking',
            'category': 'expenses',
            'period': period['label'],
            'top_items': [
                {'name': name, 'amount': round(amount, 2)}
                for name, amount in sorted_items[:10]
            ],
            'total': round(sum(by_vendor.values()), 2)
        }

    else:
        # Assume revenue/client ranking
        transactions = BankTransaction.query.filter(
            BankTransaction.source_type == 'Receivable Payment',
            BankTransaction.transaction_date >= period['start'],
            BankTransaction.transaction_date <= period['end'],
            BankTransaction.debit_gbp > 0
        ).all()

        by_client = {}
        for tx in transactions:
            client = extract_client_name(tx.description)
            by_client[client] = by_client.get(client, 0) + float(tx.debit_gbp or 0)

        sorted_items = sorted(by_client.items(), key=lambda x: x[1], reverse=True)

        return {
            'type': 'ranking',
            'category': 'revenue',
            'period': period['label'],
            'top_items': [
                {'name': name, 'amount': round(amount, 2)}
                for name, amount in sorted_items[:10]
            ],
            'total': round(sum(by_client.values()), 2)
        }


def handle_comparison_query(question, period):
    """Handle year-over-year or period comparison queries."""
    today = date.today()

    # Default to YoY comparison
    current_start = date(today.year, 1, 1)
    current_end = today
    prior_start = date(today.year - 1, 1, 1)
    prior_end = date(today.year - 1, today.month, today.day)

    # Get current period data
    current_out = db.session.query(
        func.sum(BankTransaction.credit_gbp)
    ).filter(
        BankTransaction.source_type == 'Spend Money',
        BankTransaction.transaction_date >= current_start,
        BankTransaction.transaction_date <= current_end
    ).scalar() or 0

    current_in = db.session.query(
        func.sum(BankTransaction.debit_gbp)
    ).filter(
        BankTransaction.source_type == 'Receivable Payment',
        BankTransaction.transaction_date >= current_start,
        BankTransaction.transaction_date <= current_end
    ).scalar() or 0

    # Get prior period data
    prior_out = db.session.query(
        func.sum(BankTransaction.credit_gbp)
    ).filter(
        BankTransaction.source_type == 'Spend Money',
        BankTransaction.transaction_date >= prior_start,
        BankTransaction.transaction_date <= prior_end
    ).scalar() or 0

    prior_in = db.session.query(
        func.sum(BankTransaction.debit_gbp)
    ).filter(
        BankTransaction.source_type == 'Receivable Payment',
        BankTransaction.transaction_date >= prior_start,
        BankTransaction.transaction_date <= prior_end
    ).scalar() or 0

    return {
        'type': 'comparison',
        'current_period': f'{current_start.isoformat()} to {current_end.isoformat()}',
        'prior_period': f'{prior_start.isoformat()} to {prior_end.isoformat()}',
        'spending': {
            'current': round(float(current_out), 2),
            'prior': round(float(prior_out), 2),
            'change_pct': round((float(current_out) - float(prior_out)) / float(prior_out) * 100, 1) if prior_out else None
        },
        'revenue': {
            'current': round(float(current_in), 2),
            'prior': round(float(prior_in), 2),
            'change_pct': round((float(current_in) - float(prior_in)) / float(prior_in) * 100, 1) if prior_in else None
        }
    }


def handle_generic_query(question, period):
    """Handle generic queries with summary data."""
    # Get overall summary for the period
    total_in = db.session.query(
        func.sum(BankTransaction.debit_gbp)
    ).filter(
        BankTransaction.transaction_date >= period['start'],
        BankTransaction.transaction_date <= period['end']
    ).scalar() or 0

    total_out = db.session.query(
        func.sum(BankTransaction.credit_gbp)
    ).filter(
        BankTransaction.transaction_date >= period['start'],
        BankTransaction.transaction_date <= period['end']
    ).scalar() or 0

    tx_count = BankTransaction.query.filter(
        BankTransaction.transaction_date >= period['start'],
        BankTransaction.transaction_date <= period['end']
    ).count()

    return {
        'type': 'summary',
        'period': period['label'],
        'total_money_in': round(float(total_in), 2),
        'total_money_out': round(float(total_out), 2),
        'net_change': round(float(total_in) - float(total_out), 2),
        'transaction_count': tx_count,
        'hint': 'Try asking about specific spending categories, vendors, or time periods for more detailed results.'
    }
