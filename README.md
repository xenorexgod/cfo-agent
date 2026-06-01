# CFO Agent

CFO Agent is a lightweight Python toolkit for producing founder-ready CFO/CFA reports for workspace operating companies. It converts structured operating data into cash-control, MIS, deal approval, investor-readiness, expansion, governance, and board-style reports.

The first report catalog is based on the Suits Workspaces CFO/CFA operating pack supplied for June 2026.

## What It Generates

- Daily CFO control dashboard
- Receivables aging and collection escalation report
- Centre-wise P&L and unit economics report
- Client deal approval and pricing report
- Vendor payment prioritisation and cash control report
- Statutory compliance and cash reserve report
- Investor monthly update
- Valuation and fundraise scenario report
- Expansion debt-readiness report
- Board note and founder decision memo
- Management action tracker
- Budget vs actual variance analysis
- Data room and due diligence readiness report
- Governance review
- Executive CFO summary

## Quick Start

Generate the full sample pack:

```bash
python -m cfo_agent.cli generate --input examples/suits_may_2026.json --output reports
```

Generate one report:

```bash
python -m cfo_agent.cli generate --input examples/suits_may_2026.json --report daily_cash --output reports
```

List available reports:

```bash
python -m cfo_agent.cli list-reports
```

Run tests:

```bash
python -m unittest
```

Generated reports are written to the directory passed with `--output`; the repository keeps source code and examples clean, while report outputs can be regenerated at any time.

## Data Model

The JSON input is intentionally simple and implementation-friendly. It includes company-level cash, revenue, obligations, statutory dues, centre performance, receivables, payables, proposed deal data, expansion data, and governance items.

See `examples/suits_may_2026.json` for a complete example.

## Design Principles

- Treat deposits and statutory reserves as restricted, not free cash.
- Separate billed revenue from collected revenue.
- Flag overdue receivables, payables stress, and weak cash runway early.
- Evaluate centres by EBITDA, occupancy, break-even, and collection quality.
- Require founder approval for expansion, debt, capex, and non-standard deal terms.
- Keep investor-facing material honest about cash stress, governance gaps, and diligence readiness.
