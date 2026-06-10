import type { CashPosition, Deal, Expansion, FinanceData, Receivable } from "./types";

export function freeUsableCash(cash: CashPosition): number {
  return cash.closing_cash - cash.security_deposits_held - cash.statutory_reserve_required;
}

export function cashRunwayMonths(cashAmount: number, monthlyFixed: number): number {
  if (monthlyFixed <= 0) return 0;
  return cashAmount / monthlyFixed;
}

export function cashRunwayDays(cashAmount: number, monthlyFixed: number): number {
  return cashRunwayMonths(cashAmount, monthlyFixed) * 30;
}

export function receivablesTotal(receivables: Receivable[]): number {
  return receivables.reduce((s, r) => s + (r.invoice_amount - r.collected_amount), 0);
}

export function overdueReceivables(receivables: Receivable[]): number {
  return receivables
    .filter((r) => r.days_overdue > 0)
    .reduce((s, r) => s + (r.invoice_amount - r.collected_amount), 0);
}

export function receivablesByBucket(receivables: Receivable[]): Record<string, number> {
  const buckets: Record<string, number> = { Current: 0, "1-30": 0, "31-60": 0, "61-90": 0, "90+": 0 };
  for (const r of receivables) {
    const unpaid = r.invoice_amount - r.collected_amount;
    if (r.days_overdue <= 0) buckets["Current"] += unpaid;
    else if (r.days_overdue <= 30) buckets["1-30"] += unpaid;
    else if (r.days_overdue <= 60) buckets["31-60"] += unpaid;
    else if (r.days_overdue <= 90) buckets["61-90"] += unpaid;
    else buckets["90+"] += unpaid;
  }
  return buckets;
}

export function receivablesByCentre(receivables: Receivable[]): Record<string, number> {
  const totals: Record<string, number> = {};
  for (const r of receivables) {
    totals[r.centre] = (totals[r.centre] || 0) + (r.invoice_amount - r.collected_amount);
  }
  return Object.fromEntries(Object.entries(totals).sort(([a], [b]) => a.localeCompare(b)));
}

export function dealMetrics(deal: Deal) {
  const standardRevenue = deal.seats * deal.standard_price_per_seat;
  const proposedRevenue = deal.seats * deal.proposed_price_per_seat;
  const revenueLoss = standardRevenue - proposedRevenue;
  const contribution = proposedRevenue - deal.monthly_operating_cost;
  const margin = proposedRevenue > 0 ? (contribution / proposedRevenue) * 100 : 0;
  const initialInvestment = deal.capex + deal.broker_commission - deal.setup_recovery;
  const paybackMonths = contribution > 0 ? initialInvestment / contribution : 0;
  const discountPct = standardRevenue > 0 ? (revenueLoss / standardRevenue) * 100 : 0;
  return { standardRevenue, proposedRevenue, revenueLoss, discountPct, monthlyContribution: contribution, contributionMarginPct: margin, initialInvestment, paybackMonths };
}

export function expansionMetrics(expansion: Expansion, cash: CashPosition, currentEbitda: number) {
  const upfront = expansion.capex + expansion.deposits;
  const freeCash = freeUsableCash(cash);
  const dscr = expansion.proposed_debt_emi > 0 ? currentEbitda / expansion.proposed_debt_emi : 0;
  return {
    upfrontCashRequired: upfront,
    upfrontToClosingCashMultiple: cash.closing_cash > 0 ? upfront / cash.closing_cash : 0,
    upfrontToFreeCashMultiple: freeCash > 0 ? upfront / freeCash : 0,
    dscr,
  };
}

export function diligenceReadinessScore(data: FinanceData): number {
  let score = 100;
  if (freeUsableCash(data.cash) < data.cash.fixed_obligations_7d) score -= 12;
  if (overdueReceivables(data.receivables) > data.monthly_revenue * 0.5) score -= 12;
  if (data.founder_loan > 0) score -= 8;
  if (data.related_party_resolutions_pending) score -= 8;
  if (data.cash.statutory_reserve_required <= 0) score -= 5;
  if (data.centres.some((c) => c.revenue - c.direct_costs < 0)) score -= 7;
  if (data.expansion && data.expansion.anchor_clients_signed === 0) score -= 5;
  return Math.max(score, 0);
}

export function riskRating(data: FinanceData): string {
  const freeCash = freeUsableCash(data.cash);
  const overdue = overdueReceivables(data.receivables);
  if (freeCash < data.cash.fixed_obligations_7d || overdue > data.monthly_revenue * 0.5) return "High";
  if (freeCash < data.cash.monthly_fixed_obligations * 0.5) return "Medium";
  return "Controlled";
}
