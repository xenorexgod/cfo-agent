from __future__ import annotations

from collections.abc import Callable

from .calculations import (
    cash_runway_days,
    cash_runway_months,
    deal_metrics,
    diligence_readiness_score,
    expansion_metrics,
    free_usable_cash,
    overdue_receivables,
    receivables_by_bucket,
    receivables_by_centre,
    receivables_total,
    risk_rating,
)
from .formatting import money, number, pct, table
from .models import FinanceData

ReportRenderer = Callable[[FinanceData], str]


def _title(data: FinanceData, title: str) -> str:
    return f"# {title}\n\n**Company:** {data.company}\n**Report date:** {data.report_date}\n**Report month:** {data.report_month}\n"


def render_daily_cash(data: FinanceData) -> str:
    cash = data.cash
    free_cash = free_usable_cash(cash)
    rows = [
        ["Closing cash", money(cash.closing_cash)],
        ["Less: security deposits held", money(cash.security_deposits_held)],
        ["Less: statutory reserve required", money(cash.statutory_reserve_required)],
        ["Free usable cash", money(free_cash)],
        ["7-day fixed obligations", money(cash.fixed_obligations_7d)],
        ["Expected 7-day collections", money(cash.expected_collections_7d)],
    ]
    status = "Critical" if free_cash < cash.fixed_obligations_7d else "Controlled"
    recommendation = (
        "Protect statutory and deposit money, collect priority receivables, and approve only critical payments."
        if status == "Critical"
        else "Maintain payment discipline and continue daily cash monitoring."
    )
    return "\n\n".join(
        [
            _title(data, "Daily CFO Control Dashboard"),
            "## CFO + CFA View\n"
            f"Liquidity status is **{status}**. Free usable cash is {money(free_cash)}, compared with "
            f"7-day fixed obligations of {money(cash.fixed_obligations_7d)}.",
            "## Executive Cash Summary\n" + table(["Metric", "Amount"], rows),
            "## Runway\n"
            + table(
                ["Runway type", "Result"],
                [
                    ["Gross cash runway", f"{cash_runway_months(cash.closing_cash, cash.monthly_fixed_obligations):.2f} months"],
                    ["Free usable cash runway", f"{cash_runway_days(free_cash, cash.monthly_fixed_obligations):.1f} days"],
                ],
            ),
            "## CFO Recommendation\n" + recommendation,
        ]
    )


def render_receivables(data: FinanceData) -> str:
    total = receivables_total(data.receivables)
    overdue = overdue_receivables(data.receivables)
    overdue_pct = overdue / data.monthly_revenue * 100 if data.monthly_revenue else 0.0
    bucket_rows = [[bucket, money(amount)] for bucket, amount in receivables_by_bucket(data.receivables).items()]
    client_rows = [
        [item.client, item.invoice_number, item.centre, money(item.unpaid_amount), item.days_overdue, item.owner, item.status]
        for item in sorted(data.receivables, key=lambda item: item.days_overdue, reverse=True)
    ]
    return "\n\n".join(
        [
            _title(data, "Receivables Aging + Collection Escalation Report"),
            "## CFO + CFA View\n"
            f"Total open receivables are {money(total)}. Overdue receivables are {money(overdue)}, "
            f"equal to {pct(overdue_pct)} of monthly revenue.",
            "## Aging Summary\n" + table(["Bucket", "Amount"], bucket_rows),
            "## Invoice-Level Follow-Up\n"
            + table(["Client", "Invoice", "Centre", "Unpaid", "Days overdue", "Owner", "Status"], client_rows),
            "## Escalation Rule\nInvoices above 30 days overdue require founder-visible escalation. Invoices above 60 days require written recovery plan, service hold review, or settlement decision.",
        ]
    )


def render_centre_pnl(data: FinanceData) -> str:
    rows = [
        [
            centre.name,
            money(centre.revenue),
            money(centre.direct_costs),
            money(centre.ebitda),
            pct(centre.occupancy_pct),
            money(centre.revenue_per_occupied_seat),
            money(centre.overdue_receivables),
        ]
        for centre in data.centres
    ]
    flags = [centre.name for centre in data.centres if centre.ebitda < 0 or centre.overdue_receivables > centre.revenue * 0.25]
    flag_text = ", ".join(flags) if flags else "No centres currently require founder escalation."
    return "\n\n".join(
        [
            _title(data, "Centre-wise P&L + Unit Economics Report"),
            "## CFO + CFA View\nCentre performance should be reviewed at unit level, not only through blended company EBITDA.",
            "## Centre-wise P&L\n"
            + table(["Centre", "Revenue", "Direct costs", "EBITDA", "Occupancy", "Rev/seat", "Overdue AR"], rows),
            "## Founder Review Flags\n" + flag_text,
        ]
    )


def render_deal_approval(data: FinanceData) -> str:
    if not data.deal:
        return _title(data, "Client Deal Approval + Pricing Report") + "\nNo deal data provided."
    deal = data.deal
    metrics = deal_metrics(deal)
    decision = "Renegotiate / Conditional Approval Required"
    if metrics["payback_months"] <= deal.lock_in_months / 2 and metrics["contribution_margin_pct"] >= 25:
        decision = "Conditional Approval"
    if metrics["monthly_contribution"] <= 0:
        decision = "Reject / Reprice"
    return "\n\n".join(
        [
            _title(data, "Client Deal Approval + Pricing Report"),
            f"## CFO Decision\n**{decision}** for {deal.client} at {deal.centre}.",
            "## Commercial Summary\n"
            + table(
                ["Metric", "Value"],
                [
                    ["Seats", number(deal.seats)],
                    ["Standard monthly revenue", money(metrics["standard_revenue"])],
                    ["Proposed monthly revenue", money(metrics["proposed_revenue"])],
                    ["Discount", pct(metrics["discount_pct"])],
                    ["Monthly contribution", money(metrics["monthly_contribution"])],
                    ["Contribution margin", pct(metrics["contribution_margin_pct"])],
                    ["Initial investment", money(metrics["initial_investment"])],
                    ["Payback period", f"{metrics['payback_months']:.1f} months"],
                    ["Lock-in", f"{deal.lock_in_months} months"],
                ],
            ),
            "## Recommended Approval Conditions\nRaise price where possible, extend lock-in or add early-exit protection, recover setup cost, document credit checks, and require founder approval before execution.",
        ]
    )


def render_vendor_payments(data: FinanceData) -> str:
    free_cash = free_usable_cash(data.cash)
    sorted_payables = sorted(data.payables, key=lambda item: (item.criticality != "Critical", -item.days_overdue, -item.amount))
    rows = [[item.vendor, item.category, item.criticality, money(item.amount), item.days_overdue] for item in sorted_payables]
    total_payables = sum(item.amount for item in data.payables)
    return "\n\n".join(
        [
            _title(data, "Vendor Payment Prioritisation + Cash Control Report"),
            "## CFO + CFA View\n"
            f"Free usable cash is {money(free_cash)} against total listed payables of {money(total_payables)}. Pay statutory, rent, payroll, and continuity-critical vendors first.",
            "## Payment Priority Matrix\n" + table(["Vendor", "Category", "Criticality", "Amount", "Days overdue"], rows),
            "## Cash Control Rule\nDo not use security deposits or GST/TDS reserve for discretionary vendor payments or expansion capex.",
        ]
    )


def render_statutory(data: FinanceData) -> str:
    reserve = data.cash.statutory_reserve_required
    return "\n\n".join(
        [
            _title(data, "Statutory Compliance + Cash Reserve Report"),
            "## CFO + CFA View\n"
            f"Statutory reserve required is {money(reserve)}. This amount should be ring-fenced from operating liquidity.",
            "## Control Points\nGST, TDS, PF, ESIC, and ROC dues should be tracked separately with due date, owner, challan status, and payment proof.",
        ]
    )


def render_investor_update(data: FinanceData) -> str:
    free_cash = free_usable_cash(data.cash)
    overdue = overdue_receivables(data.receivables)
    return "\n\n".join(
        [
            _title(data, "Investor Monthly Update"),
            "## Executive Summary\n"
            f"{data.company} generated {money(data.monthly_revenue)} billed revenue and {money(data.monthly_ebitda)} EBITDA in {data.report_month}. "
            f"Collected revenue was {money(data.collected_revenue)}.",
            "## CFO Disclosure\n"
            f"Free usable cash is {money(free_cash)} after excluding security deposits and statutory reserve. Overdue receivables are {money(overdue)}.",
            "## Management Focus\nCollections, payment discipline, governance cleanup, and centre-level turnaround remain the immediate priorities before aggressive expansion.",
        ]
    )


def render_valuation(data: FinanceData) -> str:
    pre_money = 200_000_000
    raise_amount = 50_000_000
    post_money = pre_money + raise_amount
    investor_ownership = raise_amount / post_money * 100
    return "\n\n".join(
        [
            _title(data, "Valuation + Fundraise Scenario Report"),
            "## Scenario\n" + table(["Item", "Value"], [["Pre-money valuation", money(pre_money)], ["Raise amount", money(raise_amount)], ["Post-money valuation", money(post_money)], ["Investor ownership", pct(investor_ownership)]]),
            "## CFO View\nThe valuation story should be supported by clean MIS, receivables control, documented founder loan treatment, and an investor-ready data room before formal diligence.",
        ]
    )


def render_expansion(data: FinanceData) -> str:
    if not data.expansion:
        return _title(data, "Expansion Governance + Debt Readiness Report") + "\nNo expansion data provided."
    expansion = data.expansion
    metrics = expansion_metrics(expansion, data.cash, data.monthly_ebitda)
    decision = "Pause / Renegotiate" if metrics["dscr"] and metrics["dscr"] < 1.2 else "Conditional Approval Review"
    if expansion.anchor_clients_signed == 0:
        decision = "Pause / Do Not Commit Yet"
    return "\n\n".join(
        [
            _title(data, "Expansion Governance + Debt Readiness Report"),
            f"## CFO Decision\n**{decision}** for {expansion.name}.",
            "## Expansion Cash Requirement\n"
            + table(
                ["Metric", "Value"],
                [
                    ["Capex", money(expansion.capex)],
                    ["Deposits", money(expansion.deposits)],
                    ["Total upfront cash", money(metrics["upfront_cash_required"])],
                    ["Upfront / closing cash", f"{metrics['upfront_to_closing_cash_multiple']:.1f}x"],
                    ["Upfront / free cash", f"{metrics['upfront_to_free_cash_multiple']:.1f}x"],
                    ["Debt service coverage ratio", f"{metrics['dscr']:.2f}x"],
                    ["Anchor clients signed", number(expansion.anchor_clients_signed)],
                ],
            ),
            "## Approval Conditions\nFunding confirmation, signed anchor clients, lease risk review, capex payback model, centre-wise break-even model, and founder approval.",
        ]
    )


def render_board_note(data: FinanceData) -> str:
    return "\n\n".join(
        [
            _title(data, "Board Note"),
            "## Decision Requested\nApprove a stabilization-first plan: protect statutory reserves, prioritize collections, document founder loan, close related-party governance gaps, and pause unprotected expansion commitments.",
            "## Current Risk Rating\n" + risk_rating(data),
            "## Recommended Board Resolution\nManagement is authorized to execute critical operating payments and collection escalation, while any new centre capex, debt, or long-lock-in lease requires separate board approval.",
        ]
    )


def render_action_tracker(data: FinanceData) -> str:
    rows = [
        ["Collect overdue receivables", "Finance owner", "7 days", "High"],
        ["Ring-fence GST/TDS reserve", "Founder + finance", "Immediate", "High"],
        ["Document founder loan", "Founder + CA/CS", "This week", "High"],
        ["Review Centre C turnaround", "Founder + operations", "7 days", "High"],
        ["Prepare investor data room index", "Finance controller", "This week", "Medium"],
    ]
    return _title(data, "Management Action Tracker + Follow-Up Report") + "\n\n" + table(["Action", "Owner", "Due", "Priority"], rows)


def render_variance(data: FinanceData) -> str:
    target_revenue = data.monthly_revenue * 1.08
    target_ebitda = data.monthly_ebitda + 200_000
    return "\n\n".join(
        [
            _title(data, "Budget vs Actual + Variance Analysis Report"),
            "## Revenue & Profitability\n"
            + table(["Metric", "Budget", "Actual", "Variance"], [["Revenue", money(target_revenue), money(data.monthly_revenue), money(data.monthly_revenue - target_revenue)], ["EBITDA", money(target_ebitda), money(data.monthly_ebitda), money(data.monthly_ebitda - target_ebitda)]]),
            "## CFO View\nPositive EBITDA is useful, but cash conversion and overdue collections determine operating strength.",
        ]
    )


def render_data_room(data: FinanceData) -> str:
    score = diligence_readiness_score(data)
    status = "Share After Review" if score < 80 else "Investor Ready"
    rows = [["MIS and financials", "Required"], ["Receivables/payables aging", "Required"], ["GST/TDS challans", "Required"], ["Founder loan documentation", "Required"], ["Related-party resolutions", "Required"], ["Lease and capex files", "Required"]]
    return "\n\n".join(
        [
            _title(data, "Data Room + Due Diligence Readiness Report"),
            f"## CFO Readiness View\nCurrent readiness score is **{score}/100**. Recommended status: **{status}**.",
            "## Data Room Index\n" + table(["Folder", "Status"], rows),
            "## Critical Red Flags\nFounder loan, related-party resolutions, collections gap, statutory reserve protection, and centre-level performance should be addressed before formal investor diligence.",
        ]
    )


def render_governance(data: FinanceData) -> str:
    items = data.governance_items or ["No governance items provided"]
    rows = [[item, "Open"] for item in items]
    return "\n\n".join(
        [
            _title(data, "CFO Governance Review"),
            "## Overall Governance Rating\nAMBER / RED" if risk_rating(data) == "High" else "## Overall Governance Rating\nAMBER",
            "## Open Governance Items\n" + table(["Item", "Status"], rows),
        ]
    )


def render_executive_summary(data: FinanceData) -> str:
    free_cash = free_usable_cash(data.cash)
    overdue = overdue_receivables(data.receivables)
    centre_ar = receivables_by_centre(data.receivables)
    worst_centre = max(centre_ar.items(), key=lambda item: item[1])[0] if centre_ar else "Data required"
    return "\n\n".join(
        [
            _title(data, "Executive CFO + CFA Summary"),
            "## CFO + CFA View\n"
            f"{data.company} is showing accounting profitability but cash stress. Monthly EBITDA is {money(data.monthly_ebitda)}, "
            f"but free usable cash is only {money(free_cash)} after excluding deposits and statutory reserve.",
            "## Key Numbers\n"
            + table(
                ["Metric", "Value"],
                [["Billed revenue", money(data.monthly_revenue)], ["Collected revenue", money(data.collected_revenue)], ["Overdue receivables", money(overdue)], ["Highest AR centre", worst_centre], ["Diligence readiness", f"{diligence_readiness_score(data)}/100"]],
            ),
            "## Recommendation\nStabilize before expansion. Focus on cash recovery, payables prioritisation, statutory reserve protection, governance cleanup, and centre turnaround.",
        ]
    )


REPORTS: dict[str, ReportRenderer] = {
    "daily_cash": render_daily_cash,
    "receivables": render_receivables,
    "centre_pnl": render_centre_pnl,
    "deal_approval": render_deal_approval,
    "vendor_payments": render_vendor_payments,
    "statutory": render_statutory,
    "investor_update": render_investor_update,
    "valuation": render_valuation,
    "expansion": render_expansion,
    "board_note": render_board_note,
    "action_tracker": render_action_tracker,
    "variance": render_variance,
    "data_room": render_data_room,
    "governance": render_governance,
    "executive_summary": render_executive_summary,
}


def render_report(name: str, data: FinanceData) -> str:
    try:
        return REPORTS[name](data).rstrip() + "\n"
    except KeyError as exc:
        available = ", ".join(sorted(REPORTS))
        raise ValueError(f"Unknown report '{name}'. Available reports: {available}") from exc
