from __future__ import annotations

from collections import defaultdict

from .models import CashPosition, Deal, Expansion, FinanceData, Receivable


def free_usable_cash(cash: CashPosition) -> float:
    return cash.closing_cash - cash.security_deposits_held - cash.statutory_reserve_required


def cash_runway_months(cash_amount: float, monthly_fixed_obligations: float) -> float:
    if monthly_fixed_obligations <= 0:
        return 0.0
    return cash_amount / monthly_fixed_obligations


def cash_runway_days(cash_amount: float, monthly_fixed_obligations: float) -> float:
    return cash_runway_months(cash_amount, monthly_fixed_obligations) * 30


def receivables_total(receivables: list[Receivable]) -> float:
    return sum(item.unpaid_amount for item in receivables)


def overdue_receivables(receivables: list[Receivable]) -> float:
    return sum(item.unpaid_amount for item in receivables if item.days_overdue > 0)


def receivables_by_bucket(receivables: list[Receivable]) -> dict[str, float]:
    buckets = {"Current": 0.0, "1-30": 0.0, "31-60": 0.0, "61-90": 0.0, "90+": 0.0}
    for item in receivables:
        if item.days_overdue <= 0:
            bucket = "Current"
        elif item.days_overdue <= 30:
            bucket = "1-30"
        elif item.days_overdue <= 60:
            bucket = "31-60"
        elif item.days_overdue <= 90:
            bucket = "61-90"
        else:
            bucket = "90+"
        buckets[bucket] += item.unpaid_amount
    return buckets


def receivables_by_centre(receivables: list[Receivable]) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    for item in receivables:
        totals[item.centre] += item.unpaid_amount
    return dict(sorted(totals.items()))


def deal_metrics(deal: Deal) -> dict[str, float]:
    standard_revenue = deal.seats * deal.standard_price_per_seat
    proposed_revenue = deal.seats * deal.proposed_price_per_seat
    revenue_loss = standard_revenue - proposed_revenue
    contribution = proposed_revenue - deal.monthly_operating_cost
    margin = contribution / proposed_revenue * 100 if proposed_revenue else 0.0
    initial_investment = deal.capex + deal.broker_commission - deal.setup_recovery
    payback_months = initial_investment / contribution if contribution > 0 else 0.0
    discount_pct = revenue_loss / standard_revenue * 100 if standard_revenue else 0.0
    return {
        "standard_revenue": standard_revenue,
        "proposed_revenue": proposed_revenue,
        "revenue_loss": revenue_loss,
        "discount_pct": discount_pct,
        "monthly_contribution": contribution,
        "contribution_margin_pct": margin,
        "initial_investment": initial_investment,
        "payback_months": payback_months,
    }


def expansion_metrics(expansion: Expansion, cash: CashPosition, current_ebitda: float) -> dict[str, float]:
    upfront = expansion.capex + expansion.deposits
    free_cash = free_usable_cash(cash)
    dscr = current_ebitda / expansion.proposed_debt_emi if expansion.proposed_debt_emi else 0.0
    return {
        "upfront_cash_required": upfront,
        "upfront_to_closing_cash_multiple": upfront / cash.closing_cash if cash.closing_cash else 0.0,
        "upfront_to_free_cash_multiple": upfront / free_cash if free_cash > 0 else 0.0,
        "dscr": dscr,
    }


def diligence_readiness_score(data: FinanceData) -> int:
    score = 100
    if free_usable_cash(data.cash) < data.cash.fixed_obligations_7d:
        score -= 12
    if overdue_receivables(data.receivables) > data.monthly_revenue * 0.5:
        score -= 12
    if data.founder_loan > 0:
        score -= 8
    if data.related_party_resolutions_pending:
        score -= 8
    if data.cash.statutory_reserve_required <= 0:
        score -= 5
    if any(centre.ebitda < 0 for centre in data.centres):
        score -= 7
    if data.expansion and data.expansion.anchor_clients_signed == 0:
        score -= 5
    return max(score, 0)


def risk_rating(data: FinanceData) -> str:
    free_cash = free_usable_cash(data.cash)
    overdue = overdue_receivables(data.receivables)
    if free_cash < data.cash.fixed_obligations_7d or overdue > data.monthly_revenue * 0.5:
        return "High"
    if free_cash < data.cash.monthly_fixed_obligations * 0.5:
        return "Medium"
    return "Controlled"
