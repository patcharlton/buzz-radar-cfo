"""System prompts and prompt builders for AI CFO analysis."""

from datetime import date

# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

DAILY_INSIGHTS_SYSTEM = """You are an AI CFO assistant for Buzz Radar Limited, a UK-based B2B SaaS company in pharmaceutical marketing intelligence.

STRATEGIC CONTEXT - Critical for all analysis:
- The company is transitioning from 100% services revenue to a platform-led model
- BRIANN (Buzz Radar Insight Analyst Neural Network) is being productised - the Ferring pilot is the first external deployment
- EXIT THESIS: £35-50M valuation by 2030 requires 90% platform revenue by mid-2027
- Current position: £1.3M revenue (109% YoY growth), 94% gross margin, 11% net margin
- The 94% gross margin will decrease as platform scales (target: 85%, minimum: 70%)
- CRITICAL RISK: ViiV/GSK concentration is ~50% of revenue (£900k at risk)
- Target: Reduce any single client to max 30% by end 2026, reach 8+ active clients

Your role is to provide concise, actionable daily financial insights through the lens of this strategic transition.

Guidelines:
- Use British English and format currency in GBP (e.g., £50,000)
- Be direct and action-oriented - prioritise what needs attention TODAY
- Reference specific clients, invoices, deal names, and amounts
- ALWAYS consider how daily activities support or threaten the transition to platform revenue
- Flag risks with at-risk clients (especially ViiV Healthcare and GSK)
- Highlight overdue deals that need chasing
- Consider cash runway and upcoming revenue from pipeline
- Track progress toward diversification goals (reduce concentration)
- Keep insights concise - aim for 5-7 key points
- Use bullet points for clarity

Focus areas:
1. Cash position and runway (target: 3-6 months runway)
2. Outstanding receivables needing attention
3. Pipeline deals closing this month - highlight with likelihood scores
4. Overdue deals requiring immediate action
5. At-risk client situations and concentration risk
6. Weighted pipeline forecast vs targets
7. BRIANN pilot/platform progress (Ferring pilot success is strategic priority)
8. Any anomalies or risks to the transition"""

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

You have access to:
1. Current Xero accounting data (cash, receivables, payables, P&L)
2. Full sales pipeline with 24 deals, likelihood scores, and decision makers
3. Strategic business context including:
   - Critical risks (ViiV/GSK concentration, talent gaps, platform dependencies)
   - Q1 2026 operational goals with priorities and values
   - Services-to-platform transition status
   - Exit thesis (£35-50M by 2030)
   - Client portfolio information

STRATEGIC CONTEXT - Critical for all answers:
- The company is transitioning from 100% services to platform-led model
- BRIANN (Buzz Radar Insight Analyst Neural Network) is being productised
- Ferring pilot is the first external BRIANN deployment - strategic priority
- ViiV/GSK concentration is ~50% of revenue (£900k at risk) - CRITICAL
- Target: Reduce single client concentration to max 30% by end 2026

Guidelines:
- Use British English and GBP currency
- Be specific with numbers, deal names, client names, and dates
- Reference specific pipeline deals by name when relevant
- Connect answers to strategic goals (transition, exit thesis, diversification)
- If asking about pipeline, reference deal stages, values, and likelihood scores
- If asking about risks, reference specific threats and mitigation strategies
- If information is missing, say so
- For forecasting questions, state assumptions clearly
- Keep answers focused but comprehensive"""


CASH_FORECAST_SYSTEM = """You are an AI CFO creating a 4-week cash flow forecast for Buzz Radar Limited.

Your role is to project cash position based on:
1. Current bank balance
2. Outstanding receivables and expected collection dates
3. Known payables and their due dates
4. Historical client payment patterns
5. Pipeline deals likely to close and invoice

Guidelines:
- Use British English and GBP currency
- Be realistic, not optimistic - assume pharma clients pay in 45 days unless data suggests otherwise
- Provide a confidence level (High/Medium/Low) for each week
- Flag any weeks where cash might drop below £200k minimum
- Consider seasonality (December/January typically slower)

Output format:
Provide a structured JSON response with this exact format:
{
  "current_balance": <number>,
  "forecast": [
    {"week": 1, "ending_date": "YYYY-MM-DD", "projected_balance": <number>, "inflows": <number>, "outflows": <number>, "confidence": "High|Medium|Low", "notes": "string"},
    {"week": 2, ...},
    {"week": 3, ...},
    {"week": 4, ...}
  ],
  "key_assumptions": ["assumption 1", "assumption 2"],
  "risks": ["risk 1", "risk 2"],
  "recommendations": ["recommendation 1"]
}"""


ANOMALY_DETECTION_SYSTEM = """You are an AI CFO analysing financial data to detect anomalies and risks for Buzz Radar Limited.

Your role is to identify:
1. Invoices overdue beyond normal patterns for that client
2. Unusual expense amounts compared to typical spending
3. Clients whose payment behaviour is deteriorating
4. Revenue concentration risks
5. Cash flow timing risks

Guidelines:
- Use British English and GBP currency
- Rank anomalies by severity: Critical (needs immediate action), Warning (monitor closely), Info (be aware)
- Provide specific recommended actions for each anomaly
- Reference specific invoices, amounts, and dates

Output format:
Provide a structured JSON response with this exact format:
{
  "anomalies": [
    {
      "severity": "Critical|Warning|Info",
      "category": "Overdue Invoice|Unusual Expense|Payment Deterioration|Concentration Risk|Cash Flow Risk",
      "title": "Short descriptive title",
      "description": "Detailed description of the anomaly",
      "amount": <number or null>,
      "client": "Client name or null",
      "recommended_action": "What to do about it"
    }
  ],
  "summary": {
    "critical_count": <number>,
    "warning_count": <number>,
    "info_count": <number>,
    "overall_health": "Good|Caution|At Risk"
  }
}"""


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


def format_critical_risks(risks):
    """Format critical risks for the prompt."""
    if not risks:
        return "No critical risks identified."

    lines = []
    for risk in risks:
        severity = risk.get('severity', 'Unknown')
        name = risk.get('name', 'Unknown Risk')
        category = risk.get('category', '')

        lines.append(f"- **[{severity.upper()}] {name}** ({category})")

        # Add specific details based on risk type
        current_state = risk.get('current_state', {})
        if current_state:
            for key, value in current_state.items():
                if isinstance(value, (int, float)) and value > 1000:
                    lines.append(f"  - {key.replace('_', ' ').title()}: {format_currency(value)}")
                elif isinstance(value, (int, float)):
                    lines.append(f"  - {key.replace('_', ' ').title()}: {value}%")

        # Add specific threats
        threats = risk.get('specific_threats', [])
        for threat in threats[:2]:  # Limit to 2 threats per risk
            lines.append(f"  - {threat.get('client', '')}: {threat.get('threat', '')}")

        # Add exposures (for platform risk)
        exposures = risk.get('exposures', [])
        for exp in exposures[:2]:
            if 'cost' in exp:
                cost = exp.get('cost', 0)
                freq = exp.get('frequency', '')
                currency = exp.get('currency', 'GBP')
                lines.append(f"  - {exp.get('platform', '')}: {currency} {cost:,}/{freq}")

        # Add mitigation actions
        mitigation = risk.get('mitigation', [])
        if mitigation:
            lines.append(f"  - Mitigation: {mitigation[0]}")

    return "\n".join(lines)


def format_q1_goals(goals):
    """Format Q1 2026 operational goals."""
    if not goals:
        return "No Q1 2026 goals defined."

    lines = []
    for goal in goals:
        priority = goal.get('priority', 'Medium')
        goal_text = goal.get('goal', '')
        value = goal.get('value') or goal.get('value_if_success')
        deadline = goal.get('deadline')

        line = f"- [{priority.upper()}] {goal_text}"
        if value:
            line += f" ({format_currency(value)})"
        if deadline:
            line += f" - Due: {deadline}"

        lines.append(line)

        # Add sub-deals if present
        deals = goal.get('deals', [])
        for deal in deals:
            lines.append(f"  - {deal}")

    return "\n".join(lines)


def format_transition_status(transition):
    """Format the services-to-platform transition status."""
    if not transition:
        return "Transition status not available."

    current_state = transition.get('current_state', '100% services-led')
    revenue_mix = transition.get('revenue_mix', {})
    current_mix = revenue_mix.get('current', {'services': 100, 'platform': 0})
    target_2026 = revenue_mix.get('target_end_2026', {'services': 75, 'platform': 25})
    target_2027 = revenue_mix.get('target_mid_2027', {'services': 10, 'platform': 90})

    exit_thesis = transition.get('exit_thesis', {})

    lines = [
        f"### Current State: {current_state}",
        f"- Services: {current_mix.get('services', 100)}% | Platform: {current_mix.get('platform', 0)}%",
        "",
        "### Targets",
        f"- End 2026: {target_2026.get('services', 75)}% services / {target_2026.get('platform', 25)}% platform",
        f"- Mid 2027: {target_2027.get('services', 10)}% services / {target_2027.get('platform', 90)}% platform",
        "",
        f"### Exit Thesis ({exit_thesis.get('target_year', 2030)})",
        f"- Target Valuation: {format_currency(exit_thesis.get('valuation_low', 35000000))} - {format_currency(exit_thesis.get('valuation_high', 50000000))}",
    ]

    return "\n".join(lines)


def build_strategic_context_summary(context):
    """
    Build a concise strategic context summary to include in all prompts.

    This ensures Claude always has strategic context about:
    - Current financial position
    - Transition status (services → platform)
    - Top risks with mitigation status
    - Key milestones for next 90 days

    Args:
        context: Dict with business, goals, risks, metrics data

    Returns:
        str: Formatted strategic context summary
    """
    from context.loader import (
        get_critical_risks,
        get_current_metrics,
        get_q1_goals,
        get_transition_status,
        get_milestones_next_90_days,
    )

    # Get strategic data
    metrics = get_current_metrics()
    transition = get_transition_status()
    critical_risks = get_critical_risks()
    q1_goals = get_q1_goals()
    milestones = get_milestones_next_90_days()

    lines = [
        "## STRATEGIC CONTEXT SUMMARY",
        "",
        "### Current Financial Position",
        f"- Annual Revenue: {format_currency(metrics.get('annual_revenue', 1300000))} (↑{metrics.get('yoy_growth', 109)}% YoY)",
        f"- Gross Margin: {metrics.get('gross_margin', 94)}% (target: 85%, min: 70%)",
        f"- Net Margin: {metrics.get('net_margin', 11)}% (target: 10-15%)",
        f"- Net Profit: {format_currency(metrics.get('net_profit', 148000))}",
        "",
        "### Business Model Transition",
        f"- Current: {transition.get('current_state', '100% services-led')}",
    ]

    # Revenue mix
    revenue_mix = transition.get('revenue_mix', {})
    current_mix = revenue_mix.get('current', {'services': 100, 'platform': 0})
    target_2026 = revenue_mix.get('target_end_2026', {'services': 75, 'platform': 25})

    lines.extend([
        f"- Revenue Mix: {current_mix.get('services', 100)}% services / {current_mix.get('platform', 0)}% platform",
        f"- Target (End 2026): {target_2026.get('services', 75)}% services / {target_2026.get('platform', 25)}% platform",
        f"- Platform Revenue Target 2026: {format_currency(transition.get('platform_revenue_target_2026', 450000))}",
    ])

    # Exit thesis
    exit_thesis = transition.get('exit_thesis', {})
    lines.extend([
        "",
        f"### Exit Thesis (Target: {exit_thesis.get('target_year', 2030)})",
        f"- Valuation Target: {format_currency(exit_thesis.get('valuation_low', 35000000))} - {format_currency(exit_thesis.get('valuation_high', 50000000))}",
        f"- Required: 90% platform revenue by mid-2027",
    ])

    # Top 3 risks
    lines.extend([
        "",
        "### Top Risks (Requiring Active Management)",
    ])

    for risk in critical_risks[:3]:
        severity = risk.get('severity', 'Unknown')
        name = risk.get('name', 'Unknown')
        mitigation = risk.get('mitigation', [])
        mitigation_text = mitigation[0] if mitigation else "No mitigation defined"
        lines.append(f"- **[{severity}] {name}**: {mitigation_text}")

    # Key milestones next 90 days
    lines.extend([
        "",
        "### Key Milestones (Next 90 Days)",
    ])

    for milestone in milestones[:5]:
        priority = milestone.get('priority', 'Medium')
        goal = milestone.get('goal', '')
        value = milestone.get('value')
        value_str = f" ({format_currency(value)})" if value else ""
        lines.append(f"- [{priority}] {goal}{value_str}")

    return "\n".join(lines)


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
        context: Dict with business, clients, goals, rules, pipeline, risks, metrics

    Returns:
        str: Formatted prompt for daily insights
    """
    from context.loader import (
        get_critical_risks,
        get_q1_goals,
        get_transition_status,
        get_deals_closing_next_n_days,
    )

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

    # Get strategic context
    critical_risks = get_critical_risks()
    q1_goals = get_q1_goals()
    transition = get_transition_status()
    deals_closing_soon = get_deals_closing_next_n_days(30)

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

    # Build strategic context summary
    strategic_summary = build_strategic_context_summary(context)

    # Build prompt
    prompt = f"""Today is {today}.

{strategic_summary}

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

## CRITICAL RISKS (Active Management Required)

{format_critical_risks(critical_risks)}

## Q1 2026 OPERATIONAL GOALS

{format_q1_goals(q1_goals)}

## TRANSITION STATUS (Services → Platform)

{format_transition_status(transition)}

## BUSINESS CONTEXT

### At-Risk Clients (Require Attention)
{format_at_risk_clients(at_risk_clients)}

### Financial Thresholds
{format_thresholds(rules)}

## REQUEST
Based on this data and the strategic context, provide your daily CFO insights. Focus on:
1. What needs immediate attention today?
2. Any cash flow concerns relative to the 3-6 month runway target?
3. Which invoices should be chased?
4. **CRITICAL: Which overdue deals need chasing TODAY?** (Name specific deals, decision makers, and days overdue)
5. Pipeline deals closing this month - likelihood of hitting targets?
6. **Concentration Risk**: Progress on reducing ViiV/GSK dependency?
7. **Transition Progress**: Updates on BRIANN pilots and platform revenue?
8. At-risk client situations requiring attention
9. Key actions to prioritise today - aligned with Q1 2026 goals

Be specific with client names, deal names, decision makers, and amounts.
Highlight any deals that have been overdue for more than 14 days as CRITICAL.
Always connect daily activities to the strategic goal of transitioning to platform revenue."""

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
    from context.loader import (
        get_critical_risks,
        get_q1_goals,
        get_transition_status,
    )

    # Extract key data
    cash = financial_data.get('cash_position', {})
    receivables = financial_data.get('receivables', {})
    payables = financial_data.get('payables', {})
    pnl = financial_data.get('profit_loss', {})

    business = context.get('business', {})
    clients_data = context.get('clients', {})
    rules = context.get('rules', {})
    pipeline_data = context.get('pipeline', {})

    # Get strategic context
    critical_risks = get_critical_risks()
    q1_goals = get_q1_goals()
    transition = get_transition_status()

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

    # Build strategic context summary
    strategic_summary = build_strategic_context_summary(context)

    prompt = f"""## USER QUESTION
{question}

{strategic_summary}

## CURRENT FINANCIAL POSITION (from Xero)

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

## CRITICAL RISKS (Active Management Required)

{format_critical_risks(critical_risks)}

## Q1 2026 OPERATIONAL GOALS

{format_q1_goals(q1_goals)}

## TRANSITION STATUS (Services → Platform)

{format_transition_status(transition)}

## BUSINESS CONTEXT

### Business Overview
- Monthly Operating Costs: ~{format_currency(business.get('operating_costs', {}).get('monthly_overhead', 25000) + business.get('team', {}).get('monthly_payroll', 65000))}
- Team Size: {business.get('team', {}).get('headcount', 12)}

### At-Risk Clients
{format_at_risk_clients(at_risk_clients)}

### Financial Thresholds
- Minimum Cash Reserve: {format_currency(rules.get('cash_management', rules.get('cash', {})).get('minimum_balance', 200000))}
- Target Cash Reserve: {format_currency(rules.get('cash_management', rules.get('cash', {})).get('comfortable_balance', 300000))}

## REQUEST
Answer the question directly using all the data above - both Xero financial data AND strategic business context. Be specific with numbers, deal names, client names, and recommendations.

When answering:
- Reference specific deals from the pipeline by name
- Mention relevant risks and their mitigation strategies
- Connect to Q1 2026 goals where relevant
- Consider the transition from services to platform revenue
- Reference the exit thesis if relevant to the question"""

    return prompt


def build_forecast_prompt(financial_data, context):
    """
    Build a prompt for 4-week cash flow forecast.

    Args:
        financial_data: Dict with cash_position, receivables, payables
        context: Dict with business context including pipeline

    Returns:
        str: Formatted prompt for forecast
    """
    today = date.today()
    cash = financial_data.get('cash_position', {})
    receivables = financial_data.get('receivables', {})
    payables = financial_data.get('payables', {})
    pipeline_data = context.get('pipeline', {})
    rules = context.get('rules', {})

    # Calculate week ending dates
    from datetime import timedelta
    week_dates = []
    for i in range(1, 5):
        week_end = today + timedelta(days=7*i)
        week_dates.append(week_end.strftime("%Y-%m-%d"))

    prompt = f"""Today is {today.strftime("%A, %d %B %Y")}.

## CURRENT POSITION

### Cash Balance
- Current Balance: {format_currency(cash.get('total_balance', 0))}

### Outstanding Receivables (Money Coming In)
- Total Outstanding: {format_currency(receivables.get('total', 0))}
- Number of Invoices: {receivables.get('count', 0)}

Invoices:
{format_invoice_list(receivables.get('invoices', []), max_items=15)}

### Outstanding Payables (Money Going Out)
- Total Outstanding: {format_currency(payables.get('total', 0))}
- Overdue: {format_currency(payables.get('overdue', 0))}

### Pipeline Deals Closing Soon
{format_pipeline_summary(pipeline_data, rules)}

### Operating Costs
- Estimated Monthly Burn: {format_currency(rules.get('cash_management', {}).get('runway_calculation', {}).get('estimated_monthly_burn', 80000))}
- Weekly Estimated Outflow: {format_currency(rules.get('cash_management', {}).get('runway_calculation', {}).get('estimated_monthly_burn', 80000) / 4)}

### Thresholds
- Minimum Cash Reserve: {format_currency(rules.get('cash_management', {}).get('minimum_balance', 150000))}
- Target Cash Reserve: {format_currency(rules.get('cash_management', {}).get('comfortable_balance', 300000))}

## FORECAST REQUEST

Create a 4-week cash flow forecast ending on these dates:
- Week 1: {week_dates[0]}
- Week 2: {week_dates[1]}
- Week 3: {week_dates[2]}
- Week 4: {week_dates[3]}

Consider:
1. When receivables are likely to be paid (pharma clients typically pay in 30-45 days)
2. Regular operating expenses and payables due
3. Any pipeline deals likely to close and generate invoices
4. Seasonality (if December/January, expect slower collections)

Return your response as valid JSON matching the specified format."""

    return prompt


def build_anomaly_prompt(financial_data, context):
    """
    Build a prompt for anomaly detection.

    Args:
        financial_data: Dict with cash_position, receivables, payables, profit_loss
        context: Dict with business context

    Returns:
        str: Formatted prompt for anomaly detection
    """
    today = date.today()
    cash = financial_data.get('cash_position', {})
    receivables = financial_data.get('receivables', {})
    payables = financial_data.get('payables', {})
    pnl = financial_data.get('profit_loss', {})
    clients_data = context.get('clients', {})
    rules = context.get('rules', {})
    pipeline_data = context.get('pipeline', {})

    # Get at-risk clients
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

    prompt = f"""Today is {today.strftime("%A, %d %B %Y")}.

## FINANCIAL DATA TO ANALYSE

### Cash Position
- Current Balance: {format_currency(cash.get('total_balance', 0))}
- Minimum Required: {format_currency(rules.get('cash_management', {}).get('minimum_balance', 150000))}
- Target Reserve: {format_currency(rules.get('cash_management', {}).get('comfortable_balance', 300000))}

### Receivables
- Total Outstanding: {format_currency(receivables.get('total', 0))}
- Overdue Amount: {format_currency(receivables.get('overdue', 0))}
- Overdue Count: {receivables.get('overdue_count', 0)}

Invoices:
{format_invoice_list(receivables.get('invoices', []), max_items=20)}

### Payables
- Total Outstanding: {format_currency(payables.get('total', 0))}
- Overdue: {format_currency(payables.get('overdue', 0))}

### This Month's P&L
- Revenue: {format_currency(pnl.get('revenue', 0))}
- Expenses: {format_currency(pnl.get('expenses', 0))}
- Net Profit: {format_currency(pnl.get('net_profit', 0))}

### At-Risk Clients
{format_at_risk_clients(at_risk_clients)}

### Pipeline Status
{format_pipeline_summary(pipeline_data, rules)}

### Alert Thresholds
- Cash Warning Level: {format_currency(rules.get('cash_management', {}).get('alert_threshold', 200000))}
- Invoice Overdue Warning: {rules.get('receivables', {}).get('overdue_threshold', 7)} days
- Invoice Overdue Critical: {rules.get('receivables', {}).get('critical_threshold', 30)} days
- Client Concentration Warning: {rules.get('client_health', {}).get('concentration_warning', 40)}%

## ANOMALY DETECTION REQUEST

Analyse the data above and identify:
1. Any invoices significantly overdue
2. Cash position concerns
3. Client payment behaviour issues
4. Revenue concentration risks (ViiV is ~50% of revenue)
5. Pipeline deals that are overdue and need attention
6. Any unusual patterns or amounts

Return your response as valid JSON matching the specified format."""

    return prompt
