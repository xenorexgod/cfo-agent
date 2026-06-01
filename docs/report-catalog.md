# CFO Agent Report Catalog

This catalog maps the uploaded Suits Workspaces CFO/CFA planning pack into executable report generators.

| Report ID | Output | Primary CFO Question |
| --- | --- | --- |
| `daily_cash` | Daily CFO control dashboard | How much cash is truly usable today? |
| `receivables` | Receivables aging and collection escalation | Which collections need escalation? |
| `centre_pnl` | Centre-wise P&L and unit economics | Which centres are profitable, underoccupied, or collection-heavy? |
| `deal_approval` | Client deal approval and pricing report | Should a discounted client deal be approved, renegotiated, or rejected? |
| `vendor_payments` | Vendor payment prioritisation | Which payments should be made first under cash stress? |
| `statutory` | Statutory compliance and reserve report | What tax and compliance cash must be ring-fenced? |
| `investor_update` | Investor monthly update | What can be honestly reported to investors? |
| `valuation` | Valuation and fundraise scenario | What dilution does a raise imply? |
| `expansion` | Expansion governance and debt readiness | Should a new centre or debt-funded expansion be approved? |
| `board_note` | Board note | What resolution or decision should the board consider? |
| `action_tracker` | Management action tracker | What needs owner-led follow-up now? |
| `variance` | Budget vs actual variance report | Where did actuals miss plan? |
| `data_room` | Due diligence readiness report | Is the company investor-data-room ready? |
| `governance` | CFO governance review | Which governance gaps create investor or compliance risk? |
| `executive_summary` | Executive CFO/CFA summary | What is the founder-level view of financial health? |

## Control Logic

- Free usable cash excludes security deposits and statutory reserves.
- Revenue quality separates billed revenue from collected revenue.
- Receivables above 30 days require escalation; above 60 days require founder-visible recovery planning.
- Centre performance flags negative EBITDA and high centre-level receivables.
- Deal approval checks contribution, discount, payback, lock-in, capex, and broker commission.
- Expansion approval checks upfront cash, anchor-client status, and debt service coverage.
- Investor readiness is downgraded by cash stress, overdue collections, undocumented founder loan, related-party gaps, statutory reserve weakness, centre losses, and unsupported expansion.
