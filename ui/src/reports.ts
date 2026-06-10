import {
  cashRunwayDays,
  cashRunwayMonths,
  dealMetrics,
  diligenceReadinessScore,
  expansionMetrics,
  freeUsableCash,
  overdueReceivables,
  receivablesByBucket,
  receivablesByCentre,
  receivablesTotal,
  riskRating,
} from "./calculations";
import { mdTable, money, num, pct } from "./formatting";
import type { FinanceData } from "./types";

function title(data: FinanceData, t: string): string {
  return `# ${t}\n\n**Company:** ${data.company}  \n**Report date:** ${data.report_date}  \n**Report month:** ${data.report_month}`;
}

export function renderDailyCash(data: FinanceData): string {
  const cash = data.cash;
  const freeCash = freeUsableCash(cash);
  const status = freeCash < cash.fixed_obligations_7d ? "Critical" : "Controlled";
  const recommendation =
    status === "Critical"
      ? "Protect statutory and deposit money, collect priority receivables, and approve only critical payments."
      : "Maintain payment discipline and continue daily cash monitoring.";
  const rows = [
    ["Closing cash", money(cash.closing_cash)],
    ["Less: security deposits held", money(cash.security_deposits_held)],
    ["Less: statutory reserve required", money(cash.statutory_reserve_required)],
    ["**Free usable cash**", `**${money(freeCash)}**`],
    ["7-day fixed obligations", money(cash.fixed_obligations_7d)],
    ["Expected 7-day collections", money(cash.expected_collections_7d)],
  ];
  const runwayRows = [
    ["Gross cash runway", `${cashRunwayMonths(cash.closing_cash, cash.monthly_fixed_obligations).toFixed(2)} months`],
    ["Free usable cash runway", `${cashRunwayDays(freeCash, cash.monthly_fixed_obligations).toFixed(1)} days`],
  ];
  return [
    title(data, "Daily CFO Control Dashboard"),
    `## CFO + CFA View\nLiquidity status is **${status}**. Free usable cash is ${money(freeCash)}, compared with 7-day fixed obligations of ${money(cash.fixed_obligations_7d)}.`,
    "## Executive Cash Summary\n" + mdTable(["Metric", "Amount"], rows),
    "## Runway\n" + mdTable(["Runway type", "Result"], runwayRows),
    "## CFO Recommendation\n" + recommendation,
  ].join("\n\n");
}

export function renderReceivables(data: FinanceData): string {
  const total = receivablesTotal(data.receivables);
  const overdue = overdueReceivables(data.receivables);
  const overduePct = data.monthly_revenue > 0 ? (overdue / data.monthly_revenue) * 100 : 0;
  const bucketRows = Object.entries(receivablesByBucket(data.receivables)).map(([b, a]) => [b, money(a)]);
  const clientRows = [...data.receivables]
    .sort((a, b) => b.days_overdue - a.days_overdue)
    .map((r) => [r.client, r.invoice_number, r.centre, money(r.invoice_amount - r.collected_amount), r.days_overdue, r.owner, r.status]);
  return [
    title(data, "Receivables Aging + Collection Escalation Report"),
    `## CFO + CFA View\nTotal open receivables are ${money(total)}. Overdue receivables are ${money(overdue)}, equal to ${pct(overduePct)} of monthly revenue.`,
    "## Aging Summary\n" + mdTable(["Bucket", "Amount"], bucketRows),
    "## Invoice-Level Follow-Up\n" + mdTable(["Client", "Invoice", "Centre", "Unpaid", "Days overdue", "Owner", "Status"], clientRows),
    "## Escalation Rule\nInvoices above 30 days overdue require founder-visible escalation. Invoices above 60 days require written recovery plan, service hold review, or settlement decision.",
  ].join("\n\n");
}

export function renderCentrePnl(data: FinanceData): string {
  const rows = data.centres.map((c) => [
    c.name,
    money(c.revenue),
    money(c.direct_costs),
    money(c.revenue - c.direct_costs),
    pct((c.occupied_seats / c.seat_capacity) * 100),
    money(c.occupied_seats > 0 ? c.revenue / c.occupied_seats : 0),
    money(c.overdue_receivables),
  ]);
  const flags = data.centres
    .filter((c) => c.revenue - c.direct_costs < 0 || c.overdue_receivables > c.revenue * 0.25)
    .map((c) => c.name);
  const flagText = flags.length ? flags.join(", ") : "No centres currently require founder escalation.";
  return [
    title(data, "Centre-wise P&L + Unit Economics Report"),
    "## CFO + CFA View\nCentre performance should be reviewed at unit level, not only through blended company EBITDA.",
    "## Centre-wise P&L\n" + mdTable(["Centre", "Revenue", "Direct costs", "EBITDA", "Occupancy", "Rev/seat", "Overdue AR"], rows),
    "## Founder Review Flags\n" + flagText,
  ].join("\n\n");
}

export function renderDealApproval(data: FinanceData): string {
  if (!data.deal) return title(data, "Client Deal Approval + Pricing Report") + "\n\nNo deal data provided.";
  const deal = data.deal;
  const m = dealMetrics(deal);
  let decision = "Renegotiate / Conditional Approval Required";
  if (m.paybackMonths <= deal.lock_in_months / 2 && m.contributionMarginPct >= 25) decision = "Conditional Approval";
  if (m.monthlyContribution <= 0) decision = "Reject / Reprice";
  const rows = [
    ["Seats", num(deal.seats)],
    ["Standard monthly revenue", money(m.standardRevenue)],
    ["Proposed monthly revenue", money(m.proposedRevenue)],
    ["Discount", pct(m.discountPct)],
    ["Monthly contribution", money(m.monthlyContribution)],
    ["Contribution margin", pct(m.contributionMarginPct)],
    ["Initial investment", money(m.initialInvestment)],
    ["Payback period", `${m.paybackMonths.toFixed(1)} months`],
    ["Lock-in", `${deal.lock_in_months} months`],
  ];
  return [
    title(data, "Client Deal Approval + Pricing Report"),
    `## CFO Decision\n**${decision}** for ${deal.client} at ${deal.centre}.`,
    "## Commercial Summary\n" + mdTable(["Metric", "Value"], rows),
    "## Recommended Approval Conditions\nRaise price where possible, extend lock-in or add early-exit protection, recover setup cost, document credit checks, and require founder approval before execution.",
  ].join("\n\n");
}

export function renderVendorPayments(data: FinanceData): string {
  const freeCash = freeUsableCash(data.cash);
  const sorted = [...data.payables].sort((a, b) => {
    if (a.criticality === "Critical" && b.criticality !== "Critical") return -1;
    if (a.criticality !== "Critical" && b.criticality === "Critical") return 1;
    return b.days_overdue - a.days_overdue || b.amount - a.amount;
  });
  const rows = sorted.map((p) => [p.vendor, p.category, p.criticality, money(p.amount), p.days_overdue]);
  const totalPayables = data.payables.reduce((s, p) => s + p.amount, 0);
  return [
    title(data, "Vendor Payment Prioritisation + Cash Control Report"),
    `## CFO + CFA View\nFree usable cash is ${money(freeCash)} against total listed payables of ${money(totalPayables)}. Pay statutory, rent, payroll, and continuity-critical vendors first.`,
    "## Payment Priority Matrix\n" + mdTable(["Vendor", "Category", "Criticality", "Amount", "Days overdue"], rows),
    "## Cash Control Rule\nDo not use security deposits or GST/TDS reserve for discretionary vendor payments or expansion capex.",
  ].join("\n\n");
}

export function renderStatutory(data: FinanceData): string {
  const reserve = data.cash.statutory_reserve_required;
  return [
    title(data, "Statutory Compliance + Cash Reserve Report"),
    `## CFO + CFA View\nStatutory reserve required is ${money(reserve)}. This amount should be ring-fenced from operating liquidity.`,
    "## Control Points\nGST, TDS, PF, ESIC, and ROC dues should be tracked separately with due date, owner, challan status, and payment proof.",
  ].join("\n\n");
}

export function renderInvestorUpdate(data: FinanceData): string {
  const freeCash = freeUsableCash(data.cash);
  const overdue = overdueReceivables(data.receivables);
  return [
    title(data, "Investor Monthly Update"),
    `## Executive Summary\n${data.company} generated ${money(data.monthly_revenue)} billed revenue and ${money(data.monthly_ebitda)} EBITDA in ${data.report_month}. Collected revenue was ${money(data.collected_revenue)}.`,
    `## CFO Disclosure\nFree usable cash is ${money(freeCash)} after excluding security deposits and statutory reserve. Overdue receivables are ${money(overdue)}.`,
    "## Management Focus\nCollections, payment discipline, governance cleanup, and centre-level turnaround remain the immediate priorities before aggressive expansion.",
  ].join("\n\n");
}

export function renderValuation(data: FinanceData): string {
  const preMoney = 200_000_000;
  const raiseAmount = 50_000_000;
  const postMoney = preMoney + raiseAmount;
  const investorOwnership = (raiseAmount / postMoney) * 100;
  const rows = [
    ["Pre-money valuation", money(preMoney)],
    ["Raise amount", money(raiseAmount)],
    ["Post-money valuation", money(postMoney)],
    ["Investor ownership", pct(investorOwnership)],
  ];
  return [
    title(data, "Valuation + Fundraise Scenario Report"),
    "## Scenario\n" + mdTable(["Item", "Value"], rows),
    "## CFO View\nThe valuation story should be supported by clean MIS, receivables control, documented founder loan treatment, and an investor-ready data room before formal diligence.",
  ].join("\n\n");
}

export function renderExpansion(data: FinanceData): string {
  if (!data.expansion) return title(data, "Expansion Governance + Debt Readiness Report") + "\n\nNo expansion data provided.";
  const expansion = data.expansion;
  const m = expansionMetrics(expansion, data.cash, data.monthly_ebitda);
  let decision = "Conditional Approval Review";
  if (m.dscr < 1.2) decision = "Pause / Renegotiate";
  if (expansion.anchor_clients_signed === 0) decision = "Pause / Do Not Commit Yet";
  const rows = [
    ["Capex", money(expansion.capex)],
    ["Deposits", money(expansion.deposits)],
    ["Total upfront cash", money(m.upfrontCashRequired)],
    ["Upfront / closing cash", `${m.upfrontToClosingCashMultiple.toFixed(1)}x`],
    ["Upfront / free cash", `${m.upfrontToFreeCashMultiple.toFixed(1)}x`],
    ["Debt service coverage ratio", `${m.dscr.toFixed(2)}x`],
    ["Anchor clients signed", num(expansion.anchor_clients_signed)],
  ];
  return [
    title(data, "Expansion Governance + Debt Readiness Report"),
    `## CFO Decision\n**${decision}** for ${expansion.name}.`,
    "## Expansion Cash Requirement\n" + mdTable(["Metric", "Value"], rows),
    "## Approval Conditions\nFunding confirmation, signed anchor clients, lease risk review, capex payback model, centre-wise break-even model, and founder approval.",
  ].join("\n\n");
}

export function renderBoardNote(data: FinanceData): string {
  return [
    title(data, "Board Note"),
    "## Decision Requested\nApprove a stabilization-first plan: protect statutory reserves, prioritize collections, document founder loan, close related-party governance gaps, and pause unprotected expansion commitments.",
    "## Current Risk Rating\n" + riskRating(data),
    "## Recommended Board Resolution\nManagement is authorized to execute critical operating payments and collection escalation, while any new centre capex, debt, or long-lock-in lease requires separate board approval.",
  ].join("\n\n");
}

export function renderActionTracker(data: FinanceData): string {
  const rows = [
    ["Collect overdue receivables", "Finance owner", "7 days", "High"],
    ["Ring-fence GST/TDS reserve", "Founder + finance", "Immediate", "High"],
    ["Document founder loan", "Founder + CA/CS", "This week", "High"],
    ["Review Centre C turnaround", "Founder + operations", "7 days", "High"],
    ["Prepare investor data room index", "Finance controller", "This week", "Medium"],
  ];
  return title(data, "Management Action Tracker + Follow-Up Report") + "\n\n" + mdTable(["Action", "Owner", "Due", "Priority"], rows);
}

export function renderVariance(data: FinanceData): string {
  const targetRevenue = data.monthly_revenue * 1.08;
  const targetEbitda = data.monthly_ebitda + 200_000;
  const rows = [
    ["Revenue", money(targetRevenue), money(data.monthly_revenue), money(data.monthly_revenue - targetRevenue)],
    ["EBITDA", money(targetEbitda), money(data.monthly_ebitda), money(data.monthly_ebitda - targetEbitda)],
  ];
  return [
    title(data, "Budget vs Actual + Variance Analysis Report"),
    "## Revenue & Profitability\n" + mdTable(["Metric", "Budget", "Actual", "Variance"], rows),
    "## CFO View\nPositive EBITDA is useful, but cash conversion and overdue collections determine operating strength.",
  ].join("\n\n");
}

export function renderDataRoom(data: FinanceData): string {
  const score = diligenceReadinessScore(data);
  const status = score < 80 ? "Share After Review" : "Investor Ready";
  const rows = [
    ["MIS and financials", "Required"],
    ["Receivables/payables aging", "Required"],
    ["GST/TDS challans", "Required"],
    ["Founder loan documentation", "Required"],
    ["Related-party resolutions", "Required"],
    ["Lease and capex files", "Required"],
  ];
  return [
    title(data, "Data Room + Due Diligence Readiness Report"),
    `## CFO Readiness View\nCurrent readiness score is **${score}/100**. Recommended status: **${status}**.`,
    "## Data Room Index\n" + mdTable(["Folder", "Status"], rows),
    "## Critical Red Flags\nFounder loan, related-party resolutions, collections gap, statutory reserve protection, and centre-level performance should be addressed before formal investor diligence.",
  ].join("\n\n");
}

export function renderGovernance(data: FinanceData): string {
  const items = data.governance_items?.length ? data.governance_items : ["No governance items provided"];
  const rows = items.map((item) => [item, "Open"]);
  const rating = riskRating(data) === "High" ? "AMBER / RED" : "AMBER";
  return [
    title(data, "CFO Governance Review"),
    `## Overall Governance Rating\n${rating}`,
    "## Open Governance Items\n" + mdTable(["Item", "Status"], rows),
  ].join("\n\n");
}

export function renderExecutiveSummary(data: FinanceData): string {
  const freeCash = freeUsableCash(data.cash);
  const overdue = overdueReceivables(data.receivables);
  const centreAr = receivablesByCentre(data.receivables);
  const worstCentre = Object.keys(centreAr).length
    ? Object.entries(centreAr).reduce((a, b) => (b[1] > a[1] ? b : a))[0]
    : "Data required";
  const rows = [
    ["Billed revenue", money(data.monthly_revenue)],
    ["Collected revenue", money(data.collected_revenue)],
    ["Overdue receivables", money(overdue)],
    ["Highest AR centre", worstCentre],
    ["Diligence readiness", `${diligenceReadinessScore(data)}/100`],
  ];
  return [
    title(data, "Executive CFO + CFA Summary"),
    `## CFO + CFA View\n${data.company} is showing accounting profitability but cash stress. Monthly EBITDA is ${money(data.monthly_ebitda)}, but free usable cash is only ${money(freeCash)} after excluding deposits and statutory reserve.`,
    "## Key Numbers\n" + mdTable(["Metric", "Value"], rows),
    "## Recommendation\nStabilize before expansion. Focus on cash recovery, payables prioritisation, statutory reserve protection, governance cleanup, and centre turnaround.",
  ].join("\n\n");
}

export type ReportId =
  | "executive_summary"
  | "daily_cash"
  | "receivables"
  | "centre_pnl"
  | "deal_approval"
  | "vendor_payments"
  | "statutory"
  | "investor_update"
  | "valuation"
  | "expansion"
  | "board_note"
  | "action_tracker"
  | "variance"
  | "data_room"
  | "governance";

export interface ReportMeta {
  id: ReportId;
  label: string;
  description: string;
  category: "operations" | "strategy" | "governance" | "overview";
}

export const REPORTS: ReportMeta[] = [
  { id: "executive_summary", label: "Executive Summary", description: "C-suite overview with key metrics and stabilization recommendation", category: "overview" },
  { id: "daily_cash", label: "Daily Cash Control", description: "Free usable cash, 7-day obligations, and runway analysis", category: "operations" },
  { id: "receivables", label: "Receivables Aging", description: "Collections aging buckets and invoice-level escalation", category: "operations" },
  { id: "centre_pnl", label: "Centre P&L", description: "Unit-level profitability, occupancy, and overdue AR by centre", category: "operations" },
  { id: "vendor_payments", label: "Vendor Payments", description: "Payment prioritization matrix by criticality", category: "operations" },
  { id: "statutory", label: "Statutory Reserve", description: "Tax and compliance reserve ring-fencing", category: "governance" },
  { id: "variance", label: "Variance Analysis", description: "Budget vs actual revenue and EBITDA comparison", category: "operations" },
  { id: "deal_approval", label: "Deal Approval", description: "New client pricing, contribution margin, and payback analysis", category: "strategy" },
  { id: "expansion", label: "Expansion Readiness", description: "New centre debt coverage and cash requirement analysis", category: "strategy" },
  { id: "valuation", label: "Valuation Scenario", description: "Fundraise dilution model and pre/post-money scenario", category: "strategy" },
  { id: "investor_update", label: "Investor Update", description: "Monthly investor communication with CFO disclosure", category: "strategy" },
  { id: "board_note", label: "Board Note", description: "Board decision request with risk rating and resolution language", category: "governance" },
  { id: "action_tracker", label: "Action Tracker", description: "Owner-assigned execution checklist with priorities", category: "governance" },
  { id: "data_room", label: "Data Room", description: "Due diligence readiness score and document index", category: "governance" },
  { id: "governance", label: "Governance Review", description: "Open governance items and overall governance rating", category: "governance" },
];

export const RENDERERS: Record<ReportId, (data: FinanceData) => string> = {
  executive_summary: renderExecutiveSummary,
  daily_cash: renderDailyCash,
  receivables: renderReceivables,
  centre_pnl: renderCentrePnl,
  deal_approval: renderDealApproval,
  vendor_payments: renderVendorPayments,
  statutory: renderStatutory,
  investor_update: renderInvestorUpdate,
  valuation: renderValuation,
  expansion: renderExpansion,
  board_note: renderBoardNote,
  action_tracker: renderActionTracker,
  variance: renderVariance,
  data_room: renderDataRoom,
  governance: renderGovernance,
};
