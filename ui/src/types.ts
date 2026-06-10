export interface CashPosition {
  closing_cash: number;
  security_deposits_held: number;
  statutory_reserve_required: number;
  expected_collections_7d: number;
  fixed_obligations_7d: number;
  monthly_fixed_obligations: number;
  overdraft_available: number;
}

export interface Receivable {
  client: string;
  invoice_number: string;
  centre: string;
  invoice_amount: number;
  collected_amount: number;
  gst_amount: number;
  days_overdue: number;
  owner: string;
  status: string;
  dispute?: boolean;
}

export interface Payable {
  vendor: string;
  category: string;
  amount: number;
  days_overdue: number;
  criticality: "Critical" | "Strategic" | "Normal";
}

export interface Centre {
  name: string;
  revenue: number;
  direct_costs: number;
  seat_capacity: number;
  occupied_seats: number;
  capex: number;
  overdue_receivables: number;
  break_even_occupancy_pct: number;
}

export interface Deal {
  client: string;
  centre: string;
  seats: number;
  standard_price_per_seat: number;
  proposed_price_per_seat: number;
  monthly_operating_cost: number;
  capex: number;
  broker_commission: number;
  lock_in_months: number;
  free_period_days: number;
  setup_recovery: number;
}

export interface Expansion {
  name: string;
  capex: number;
  deposits: number;
  projected_monthly_ebitda: number;
  proposed_debt_emi: number;
  anchor_clients_signed: number;
}

export interface FinanceData {
  company: string;
  report_date: string;
  report_month: string;
  monthly_revenue: number;
  collected_revenue: number;
  monthly_ebitda: number;
  founder_loan: number;
  related_party_resolutions_pending: boolean;
  cash: CashPosition;
  receivables: Receivable[];
  payables: Payable[];
  centres: Centre[];
  deal?: Deal;
  expansion?: Expansion;
  governance_items?: string[];
}
