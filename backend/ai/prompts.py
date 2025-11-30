"""System prompts and prompt builders for AI CFO analysis."""

from datetime import date

# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

DAILY_INSIGHTS_SYSTEM = """You are an AI CFO assistant for Buzz Radar Limited, a UK-based B2B SaaS company in pharmaceutical marketing intelligence.

Your role is to provide concise, actionable daily financial insights. You have access to real-time data from Xero accounting software, business context about clients, and sales pipeline information.

Guidelines:
- Use British English and format currency in GBP (e.g., £50,000)
- Be direct and action-oriented - prioritise what needs attention TODAY
- Reference specific clients, invoices, deal names, and amounts
- Flag risks with at-risk clients (especially ViiV Healthcare and GSK)
- Highlight overdue deals that need chasing
- Consider cash runway and upcoming revenue from pipeline
- Keep insights concise - aim for 5-7 key points
- Use bullet points for clarity

Focus areas:
1. Cash position and runway
2. Outstanding receivables needing attention
3. Pipeline deals closing this month - highlight with likelihood scores
4. Overdue deals requiring immediate action
5. At-risk client situations
6. Weighted pipeline forecast vs targets
7. Any anomalies or concerns"""

MONTHLY_ANALYSIS_SYSTEM = """You are an AI CFO providing a monthly strategic financial review for Buzz Radar Limited, a UK-based B2B SaaS company worth approximately £1.3M annual revenue.

Your role is to provide comprehensive analysis connecting financial data to strategic goals, including the company's exit target of £35-50M by 2030.

Guidelines:
- Use British English and GBP currency
- Connect financial metrics to strategic objectives
- Analyse trends and patterns month-over-month
- Provide specific recommendations with reasoning
- Address client concentration risk (ViiV represents ~50% of revenue)
- Consider hiring decisions, investment priorities, and growth opportunities
- Be thorough but structured

Structure your analysis:
1. Executive Summary (2-3 sentences)
2. Cash & Liquidity Analysis
3. Revenue & Client Health
4. Profitability Review
5. Risk Assessment
6. Strategic Recommendations
7. Key Actions for Next Month"""

QA_SYSTEM = """You are an AI CFO assistant for Buzz Radar Limited, answering specific financial questions.

You have access to current Xero accounting data and business context. Provide direct, helpful answers using the data provided.

Guidelines:
- Use British English and GBP currency
- Be specific with numbers and dates
- Reference the actual data provided
- If information is missing, say so
- For forecasting questions, state assumptions clearly
- Keep answers focused on what was asked"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def format_currency(amount):
    """Format amount as GBP currency string."""
    if amount is None:
        return "£0"
    if amount >= 1000000:
        return f"£{amount/1000000:.1f}M"
    if amount >= 1000:
        return f"£{amount/1000:.0f}k"
    return f"£{amount:.0f}"


def format_invoice_list(invoices, max_items=10):
    """Format a list of invoices for the prompt."""
    if not invoices:
        return "No invoices."

    lines = []
    for inv in invoices[:max_items]:
        days = inv.get('days_until_due')
        if days is not None:
            if days < 0:
                status = f"OVERDUE by {abs(days)} days"
            elif days == 0:
                status = "DUE TODAY"
            else:
                status = f"Due in {days} days"
        else:
            status = "No due date"

        lines.append(
            f"- {inv.get('invoice_number', 'N/A')}: {inv.get('contact_name', 'Unknown')} - "
            f"{format_currency(inv.get('amount_due', 0))} ({status})"
        )

    if len(invoices) > max_items:
        lines.append(f"... and {len(invoices) - max_items} more")

    return "\n".join(lines)


def format_at_risk_clients(clients):
    """Format at-risk client information."""
    if not clients:
        return "No clients flagged as at-risk."

    lines = []
    for client in clients:
        lines.append(
            f"- {client.get('name')}: {format_currency(client.get('contract_value', 0))} "
            f"({client.get('notes', 'No notes')})"
        )

    return "\n".join(lines)


def format_thresholds(rules):
    """Format financial thresholds from rules."""
    cash = rules.get('cash_management', rules.get('cash', {}))
    receivables = rules.get('receivables', {})

    return f"""Cash Thresholds:
- Minimum reserve: {format_currency(cash.get('minimum_balance', cash.get('minimum_reserve', 200000)))}
- Warning level: {format_currency(cash.get('alert_threshold', cash.get('warning_threshold', 250000)))}
- Target reserve: {format_currency(cash.get('comfortable_balance', cash.get('target_reserve', 300000)))}

Receivables Thresholds:
- Warning: {receivables.get('overdue_threshold', receivables.get('warning_days_overdue', 14))} days overdue
- Critical: {receivables.get('critical_threshold', receivables.get('critical_days_overdue', 30))} days overdue"""


def format_pipeline_summary(pipeline_data, rules=None):
    """
    Format a comprehensive pipeline summary for the daily prompt.

    Args:
        pipeline_data: Dict with pipeline information including deals
        rules: Optional rules dict with likelihood weights

    Returns:
        str: Formatted pipeline summary
    """
    from datetime import date

    deals = pipeline_data.get('deals', [])
    if not deals:
        return "No pipeline data available."

    today = date.today()

    # Categorize deals
    committed = []  # Won
    verbal_agreement = []  # High confidence
    procurement = []  # In buying process
    proposals = []  # Being reviewed
    overdue = []  # Past expected close date
    closing_this_month = []

    # Calculate totals
    committed_value = 0
    high_confidence_value = 0
    pipeline_value = 0
    weighted_total = 0

    for deal in deals:
        value = deal.get('deal_value', 0)
        likelihood = deal.get('likelihood', 0)
        stage = deal.get('stage', '')
        expected_close = deal.get('expected_close')
        weight = likelihood / 10.0

        # Check if overdue
        if expected_close and stage != 'Won':
            try:
                close_date = date.fromisoformat(expected_close)
                if close_date < today:
                    days_overdue = (today - close_date).days
                    deal_copy = deal.copy()
                    deal_copy['days_overdue'] = days_overdue
                    overdue.append(deal_copy)
                elif close_date.year == today.year and close_date.month == today.month:
                    closing_this_month.append(deal)
            except ValueError:
                pass

        # Categorize by stage
        if stage == 'Won':
            committed.append(deal)
            committed_value += value
            weighted_total += value
        elif stage == 'Verbal Agreement':
            verbal_agreement.append(deal)
            high_confidence_value += value
            weighted_total += value * weight
        elif stage == 'Procurement':
            procurement.append(deal)
            if likelihood >= 7:
                high_confidence_value += value
            else:
                pipeline_value += value
            weighted_total += value * weight
        elif stage in ['Proposal Being Reviewed', 'Build Proposal']:
            proposals.append(deal)
            pipeline_value += value
            weighted_total += value * weight
        else:
            pipeline_value += value
            weighted_total += value * weight

    # Build output
    lines = []

    # Summary metrics
    lines.append(f"### Pipeline Summary")
    lines.append(f"- Total Pipeline: {format_currency(pipeline_data.get('pipeline_summary', {}).get('total_pipeline_value', sum(d.get('deal_value', 0) for d in deals)))}")
    lines.append(f"- Weighted Pipeline: {format_currency(int(weighted_total))}")
    lines.append(f"- Committed (Won): {format_currency(committed_value)}")
    lines.append(f"- High Confidence (Verbal + Procurement): {format_currency(high_confidence_value)}")
    lines.append(f"- Active Deals: {len(deals)}")
    lines.append("")

    # Deals closing this month
    if closing_this_month:
        lines.append(f"### Deals Closing This Month ({len(closing_this_month)} deals)")
        for deal in sorted(closing_this_month, key=lambda x: x.get('likelihood', 0), reverse=True):
            likelihood = deal.get('likelihood', 0)
            lines.append(
                f"- **{deal.get('name')}** ({deal.get('client')}) - "
                f"{format_currency(deal.get('deal_value', 0))} "
                f"[Likelihood: {likelihood}/10] "
                f"Stage: {deal.get('stage')} | "
                f"Close: {deal.get('expected_close', 'TBD')}"
            )
        lines.append("")

    # CRITICAL: Overdue deals
    if overdue:
        lines.append(f"### OVERDUE DEALS - REQUIRE IMMEDIATE ATTENTION ({len(overdue)} deals)")
        for deal in sorted(overdue, key=lambda x: x.get('days_overdue', 0), reverse=True):
            lines.append(
                f"- **{deal.get('name')}** ({deal.get('client')}) - "
                f"{format_currency(deal.get('deal_value', 0))} "
                f"[{deal.get('days_overdue')} DAYS OVERDUE] "
                f"Stage: {deal.get('stage')} | "
                f"Decision Maker: {deal.get('decision_maker', 'Unknown')}"
            )
        lines.append("")

    # High confidence deals (Verbal Agreement)
    if verbal_agreement:
        lines.append(f"### Verbal Agreements ({len(verbal_agreement)} deals)")
        for deal in verbal_agreement:
            lines.append(
                f"- {deal.get('name')} ({deal.get('client')}) - "
                f"{format_currency(deal.get('deal_value', 0))} "
                f"[Likelihood: {deal.get('likelihood', 0)}/10] | "
                f"Close: {deal.get('expected_close', 'TBD')}"
            )
        lines.append("")

    # Procurement
    if procurement:
        lines.append(f"### In Procurement ({len(procurement)} deals)")
        for deal in procurement:
            lines.append(
                f"- {deal.get('name')} ({deal.get('client')}) - "
                f"{format_currency(deal.get('deal_value', 0))} "
                f"[Likelihood: {deal.get('likelihood', 0)}/10]"
            )
        lines.append("")

    # Proposals being reviewed
    if proposals:
        lines.append(f"### Proposals ({len(proposals)} deals)")
        for deal in sorted(proposals, key=lambda x: x.get('deal_value', 0), reverse=True)[:5]:
            lines.append(
                f"- {deal.get('name')} ({deal.get('client')}) - "
                f"{format_currency(deal.get('deal_value', 0))} "
                f"[Likelihood: {deal.get('likelihood', 0)}/10]"
            )
        if len(proposals) > 5:
            lines.append(f"  ... and {len(proposals) - 5} more proposals")
        lines.append("")

    return "\n".join(lines)


# =============================================================================
# PROMPT BUILDERS
# =============================================================================

def build_daily_prompt(financial_data, context):
    """
    Build the daily insights prompt with financial data and context.

    Args:
        financial_data: Dict with cash_position, receivables, payables, profit_loss
        context: Dict with business, clients, goals, rules, pipeline

    Returns:
        str: Formatted prompt for daily insights
    """
    today = date.today().strftime("%A, %d %B %Y")

    # Extract data
    cash = financial_data.get('cash_position', {})
    receivables = financial_data.get('receivables', {})
    payables = financial_data.get('payables', {})
    pnl = financial_data.get('profit_loss', {})

    # Extract context
    business = context.get('business', {})
    clients_data = context.get('clients', {})
    rules = context.get('rules', {})
    pipeline_data = context.get('pipeline', {})

    # Get at-risk clients (updated for new schema)
    at_risk_clients = []
    for client in clients_data.get('clients', []):
        # Check current contracts for at-risk status
        contracts = client.get('current_contracts', [])
        for contract in contracts:
            if contract.get('status') == 'At Risk':
                at_risk_clients.append({
                    'name': client.get('name'),
                    'contract_value': contract.get('annual_value', 0),
                    'notes': contract.get('notes', ''),
                    'risk_factors': contract.get('risk_factors', [])
                })

    # Get revenue targets for comparison
    revenue_rules = rules.get('revenue', {})
    monthly_target = revenue_rules.get('monthly_target', 125000)
    q4_target = revenue_rules.get('q4_2025_target', 375000)

    # Build prompt
    prompt = f"""Today is {today}.

## CURRENT FINANCIAL POSITION

### Cash Position
- Total cash balance: {format_currency(cash.get('total_balance', 0))}
- Bank accounts: {len(cash.get('accounts', []))}

### Receivables (Money Owed To Us)
- Total outstanding: {format_currency(receivables.get('total', 0))}
- Overdue amount: {format_currency(receivables.get('overdue', 0))}
- Outstanding invoices: {receivables.get('count', 0)}
- Overdue invoices: {receivables.get('overdue_count', 0)}

Outstanding Invoices:
{format_invoice_list(receivables.get('invoices', []))}

### Payables (Money We Owe)
- Total outstanding: {format_currency(payables.get('total', 0))}
- Overdue amount: {format_currency(payables.get('overdue', 0))}
- Outstanding bills: {payables.get('count', 0)}

### This Month's P&L
- Revenue: {format_currency(pnl.get('revenue', 0))}
- Expenses: {format_currency(pnl.get('expenses', 0))}
- Net Profit: {format_currency(pnl.get('net_profit', 0))}

## SALES PIPELINE

{format_pipeline_summary(pipeline_data, rules)}

### Revenue Targets
- Monthly Target: {format_currency(monthly_target)}
- Q4 2025 Target: {format_currency(q4_target)}

## BUSINESS CONTEXT

### At-Risk Clients (Require Attention)
{format_at_risk_clients(at_risk_clients)}

### Financial Thresholds
{format_thresholds(rules)}

## REQUEST
Based on this data, provide your daily CFO insights. Focus on:
1. What needs immediate attention today?
2. Any cash flow concerns?
3. Which invoices should be chased?
4. **CRITICAL: Which overdue deals need chasing TODAY?** (Name specific deals, decision makers, and days overdue)
5. Pipeline deals closing this month - likelihood of hitting targets?
6. At-risk client situations requiring attention
7. Key actions to prioritise today

Be specific with client names, deal names, decision makers, and amounts. Highlight any deals that have been overdue for more than 14 days as CRITICAL."""

    return prompt


def build_monthly_prompt(financial_data, context):
    """
    Build the monthly analysis prompt.

    Args:
        financial_data: Dict with financial metrics
        context: Dict with business context

    Returns:
        str: Formatted prompt for monthly analysis
    """
    today = date.today()
    month_name = today.strftime("%B %Y")

    # Extract data
    cash = financial_data.get('cash_position', {})
    receivables = financial_data.get('receivables', {})
    payables = financial_data.get('payables', {})
    pnl = financial_data.get('profit_loss', {})

    # Extract context
    business = context.get('business', {})
    clients_data = context.get('clients', {})
    goals = context.get('goals', {})
    rules = context.get('rules', {})

    company = business.get('company', {})
    strategy = business.get('strategy', {})
    financial_goals = goals.get('financial_goals', {})

    # Calculate metrics
    total_active_revenue = clients_data.get('summary', {}).get('total_active_revenue', 1200000)
    at_risk_revenue = clients_data.get('summary', {}).get('at_risk_revenue', 0)
    pipeline = clients_data.get('summary', {}).get('pipeline_value', 0)

    # Get all clients for analysis
    all_clients = clients_data.get('clients', [])
    active_clients = [c for c in all_clients if c.get('status') == 'active']

    prompt = f"""# Monthly Financial Review: {month_name}

## COMPANY OVERVIEW
- Company: {company.get('name', 'Buzz Radar Limited')}
- Annual Revenue: {format_currency(company.get('annual_revenue', 1300000))}
- Exit Target: {format_currency(strategy.get('target_valuation_min', 35000000))} - {format_currency(strategy.get('target_valuation_max', 50000000))} by {strategy.get('target_year', 2030)}

## CURRENT FINANCIAL POSITION

### Cash
- Balance: {format_currency(cash.get('total_balance', 0))}
- Target Reserve: {format_currency(rules.get('cash', {}).get('target_reserve', 300000))}

### This Month's Performance
- Revenue: {format_currency(pnl.get('revenue', 0))}
- Expenses: {format_currency(pnl.get('expenses', 0))}
- Net Profit: {format_currency(pnl.get('net_profit', 0))}

### Receivables
- Outstanding: {format_currency(receivables.get('total', 0))}
- Overdue: {format_currency(receivables.get('overdue', 0))}

### Payables
- Outstanding: {format_currency(payables.get('total', 0))}

## CLIENT PORTFOLIO

### Active Clients ({len(active_clients)})
"""

    for client in active_clients:
        prompt += f"- {client.get('name')}: {format_currency(client.get('contract_value', 0))} "
        prompt += f"(Risk: {client.get('risk_level', 'unknown')}, Renewal: {client.get('renewal_status', 'unknown')})\n"

    prompt += f"""
### Revenue Concentration
- Total Active Revenue: {format_currency(total_active_revenue)}
- At-Risk Revenue: {format_currency(at_risk_revenue)} ({at_risk_revenue/total_active_revenue*100:.0f}% of active)
- Pipeline Value: {format_currency(pipeline)}

## GOALS & TARGETS
- Revenue Target (This Year): {format_currency(financial_goals.get('current_year', {}).get('revenue_target', 1500000))}
- Profit Margin Target: {financial_goals.get('current_year', {}).get('profit_margin_target', 20)}%
- Cash Reserve Target: {format_currency(financial_goals.get('current_year', {}).get('cash_reserve_target', 300000))}

## STRATEGIC PRIORITIES
"""

    for goal in goals.get('strategic_goals', {}).get('this_quarter', []):
        prompt += f"- [{goal.get('priority', 'medium').upper()}] {goal.get('goal')}\n"

    prompt += """

## REQUEST
Provide a comprehensive monthly CFO analysis covering:
1. Executive summary of financial health
2. Cash and liquidity position vs targets
3. Revenue quality and client risk assessment
4. Progress toward goals
5. Key risks and mitigation strategies
6. Specific recommendations for next month
7. Any strategic concerns regarding the exit timeline"""

    return prompt


def build_qa_prompt(question, financial_data, context):
    """
    Build a prompt for answering a specific question.

    Args:
        question: The user's question
        financial_data: Dict with financial data
        context: Dict with business context including pipeline

    Returns:
        str: Formatted prompt for Q&A
    """
    # Extract key data
    cash = financial_data.get('cash_position', {})
    receivables = financial_data.get('receivables', {})
    payables = financial_data.get('payables', {})
    pnl = financial_data.get('profit_loss', {})

    business = context.get('business', {})
    clients_data = context.get('clients', {})
    rules = context.get('rules', {})
    pipeline_data = context.get('pipeline', {})

    # Get at-risk clients (updated for new schema)
    at_risk_clients = []
    for client in clients_data.get('clients', []):
        contracts = client.get('current_contracts', [])
        for contract in contracts:
            if contract.get('status') == 'At Risk':
                at_risk_clients.append({
                    'name': client.get('name'),
                    'contract_value': contract.get('annual_value', 0),
                    'notes': contract.get('notes', ''),
                })

    prompt = f"""## USER QUESTION
{question}

## AVAILABLE DATA

### Cash Position
- Total Balance: {format_currency(cash.get('total_balance', 0))}

### Receivables
- Total Outstanding: {format_currency(receivables.get('total', 0))}
- Overdue: {format_currency(receivables.get('overdue', 0))} ({receivables.get('overdue_count', 0)} invoices)
- Total Invoices: {receivables.get('count', 0)}

Outstanding Invoices:
{format_invoice_list(receivables.get('invoices', []), max_items=15)}

### Payables
- Total Outstanding: {format_currency(payables.get('total', 0))}
- Overdue: {format_currency(payables.get('overdue', 0))}

### This Month's P&L
- Revenue: {format_currency(pnl.get('revenue', 0))}
- Expenses: {format_currency(pnl.get('expenses', 0))}
- Net Profit: {format_currency(pnl.get('net_profit', 0))}

## SALES PIPELINE

{format_pipeline_summary(pipeline_data, rules)}

### Business Context
- Monthly Operating Costs: ~{format_currency(business.get('operating_costs', {}).get('monthly_overhead', 25000) + business.get('team', {}).get('monthly_payroll', 65000))}
- Team Size: {business.get('team', {}).get('headcount', 12)}

### At-Risk Clients
{format_at_risk_clients(at_risk_clients)}

### Financial Thresholds
- Minimum Cash Reserve: {format_currency(rules.get('cash_management', rules.get('cash', {})).get('minimum_balance', 200000))}
- Target Cash Reserve: {format_currency(rules.get('cash_management', rules.get('cash', {})).get('comfortable_balance', 300000))}

## REQUEST
Answer the question directly using the data above. Be specific with numbers, deal names, client names, and recommendations. If the question is about pipeline, use the pipeline data provided."""

    return prompt
