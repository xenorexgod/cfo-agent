from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _number(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    return float(value)


@dataclass(frozen=True)
class CashPosition:
    closing_cash: float
    security_deposits_held: float
    statutory_reserve_required: float
    expected_collections_7d: float = 0.0
    fixed_obligations_7d: float = 0.0
    monthly_fixed_obligations: float = 0.0
    overdraft_available: float = 0.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CashPosition":
        return cls(
            closing_cash=_number(data.get("closing_cash")),
            security_deposits_held=_number(data.get("security_deposits_held")),
            statutory_reserve_required=_number(data.get("statutory_reserve_required")),
            expected_collections_7d=_number(data.get("expected_collections_7d")),
            fixed_obligations_7d=_number(data.get("fixed_obligations_7d")),
            monthly_fixed_obligations=_number(data.get("monthly_fixed_obligations")),
            overdraft_available=_number(data.get("overdraft_available")),
        )


@dataclass(frozen=True)
class Receivable:
    client: str
    invoice_number: str
    centre: str
    invoice_amount: float
    collected_amount: float
    days_overdue: int
    gst_amount: float = 0.0
    owner: str = "Unassigned"
    status: str = "Open"
    dispute: str = "None"

    @property
    def unpaid_amount(self) -> float:
        return max(self.invoice_amount - self.collected_amount, 0.0)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Receivable":
        return cls(
            client=str(data.get("client", "Unknown client")),
            invoice_number=str(data.get("invoice_number", "")),
            centre=str(data.get("centre", "Unassigned")),
            invoice_amount=_number(data.get("invoice_amount")),
            collected_amount=_number(data.get("collected_amount")),
            days_overdue=int(_number(data.get("days_overdue"))),
            gst_amount=_number(data.get("gst_amount")),
            owner=str(data.get("owner", "Unassigned")),
            status=str(data.get("status", "Open")),
            dispute=str(data.get("dispute", "None")),
        )


@dataclass(frozen=True)
class Payable:
    vendor: str
    category: str
    amount: float
    days_overdue: int = 0
    criticality: str = "Normal"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Payable":
        return cls(
            vendor=str(data.get("vendor", "Unknown vendor")),
            category=str(data.get("category", "Uncategorized")),
            amount=_number(data.get("amount")),
            days_overdue=int(_number(data.get("days_overdue"))),
            criticality=str(data.get("criticality", "Normal")),
        )


@dataclass(frozen=True)
class Centre:
    name: str
    revenue: float
    direct_costs: float
    seat_capacity: int
    occupied_seats: int
    capex: float = 0.0
    overdue_receivables: float = 0.0
    break_even_occupancy_pct: float = 0.0

    @property
    def ebitda(self) -> float:
        return self.revenue - self.direct_costs

    @property
    def occupancy_pct(self) -> float:
        if self.seat_capacity <= 0:
            return 0.0
        return self.occupied_seats / self.seat_capacity * 100

    @property
    def revenue_per_occupied_seat(self) -> float:
        if self.occupied_seats <= 0:
            return 0.0
        return self.revenue / self.occupied_seats

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Centre":
        return cls(
            name=str(data.get("name", "Unknown centre")),
            revenue=_number(data.get("revenue")),
            direct_costs=_number(data.get("direct_costs")),
            seat_capacity=int(_number(data.get("seat_capacity"))),
            occupied_seats=int(_number(data.get("occupied_seats"))),
            capex=_number(data.get("capex")),
            overdue_receivables=_number(data.get("overdue_receivables")),
            break_even_occupancy_pct=_number(data.get("break_even_occupancy_pct")),
        )


@dataclass(frozen=True)
class Deal:
    client: str
    centre: str
    seats: int
    standard_price_per_seat: float
    proposed_price_per_seat: float
    monthly_operating_cost: float
    capex: float
    broker_commission: float
    lock_in_months: int
    free_period_days: int = 0
    setup_recovery: float = 0.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Deal":
        return cls(
            client=str(data.get("client", "Unknown client")),
            centre=str(data.get("centre", "Unassigned")),
            seats=int(_number(data.get("seats"))),
            standard_price_per_seat=_number(data.get("standard_price_per_seat")),
            proposed_price_per_seat=_number(data.get("proposed_price_per_seat")),
            monthly_operating_cost=_number(data.get("monthly_operating_cost")),
            capex=_number(data.get("capex")),
            broker_commission=_number(data.get("broker_commission")),
            lock_in_months=int(_number(data.get("lock_in_months"))),
            free_period_days=int(_number(data.get("free_period_days"))),
            setup_recovery=_number(data.get("setup_recovery")),
        )


@dataclass(frozen=True)
class Expansion:
    name: str
    capex: float
    deposits: float
    projected_monthly_ebitda: float
    proposed_debt_emi: float = 0.0
    anchor_clients_signed: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Expansion":
        return cls(
            name=str(data.get("name", "Expansion")),
            capex=_number(data.get("capex")),
            deposits=_number(data.get("deposits")),
            projected_monthly_ebitda=_number(data.get("projected_monthly_ebitda")),
            proposed_debt_emi=_number(data.get("proposed_debt_emi")),
            anchor_clients_signed=int(_number(data.get("anchor_clients_signed"))),
        )


@dataclass(frozen=True)
class FinanceData:
    company: str
    report_date: str
    report_month: str
    cash: CashPosition
    monthly_revenue: float
    collected_revenue: float
    monthly_ebitda: float
    founder_loan: float = 0.0
    related_party_resolutions_pending: bool = False
    receivables: list[Receivable] = field(default_factory=list)
    payables: list[Payable] = field(default_factory=list)
    centres: list[Centre] = field(default_factory=list)
    deal: Deal | None = None
    expansion: Expansion | None = None
    governance_items: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FinanceData":
        return cls(
            company=str(data.get("company", "Company")),
            report_date=str(data.get("report_date", "Data required")),
            report_month=str(data.get("report_month", "Data required")),
            cash=CashPosition.from_dict(data.get("cash", {})),
            monthly_revenue=_number(data.get("monthly_revenue")),
            collected_revenue=_number(data.get("collected_revenue")),
            monthly_ebitda=_number(data.get("monthly_ebitda")),
            founder_loan=_number(data.get("founder_loan")),
            related_party_resolutions_pending=bool(data.get("related_party_resolutions_pending", False)),
            receivables=[Receivable.from_dict(item) for item in data.get("receivables", [])],
            payables=[Payable.from_dict(item) for item in data.get("payables", [])],
            centres=[Centre.from_dict(item) for item in data.get("centres", [])],
            deal=Deal.from_dict(data["deal"]) if data.get("deal") else None,
            expansion=Expansion.from_dict(data["expansion"]) if data.get("expansion") else None,
            governance_items=[str(item) for item in data.get("governance_items", [])],
        )
