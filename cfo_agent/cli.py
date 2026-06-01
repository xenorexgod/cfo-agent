from __future__ import annotations

import argparse
import json
from pathlib import Path

from .models import FinanceData
from .reports import REPORTS, render_report
from .zoho_books import build_client_from_env


def load_finance_data(path: Path) -> FinanceData:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return FinanceData.from_dict(payload)


def write_report(output_dir: Path, name: str, content: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{name}.md"
    path.write_text(content, encoding="utf-8")
    return path


def generate(args: argparse.Namespace) -> int:
    data = load_finance_data(Path(args.input))
    selected = [args.report] if args.report else list(REPORTS)
    output_dir = Path(args.output)
    for name in selected:
        content = render_report(name, data)
        path = write_report(output_dir, name, content)
        print(path)
    return 0


def list_reports(_: argparse.Namespace) -> int:
    for name in sorted(REPORTS):
        print(name)
    return 0


def zoho_organizations(_: argparse.Namespace) -> int:
    client = build_client_from_env()
    print(json.dumps(client.list_organizations(), indent=2, sort_keys=True))
    return 0


def zoho_invoices(args: argparse.Namespace) -> int:
    client = build_client_from_env()
    params = {}
    if args.status:
        params["status"] = args.status
    if args.from_date:
        params["date_start"] = args.from_date
    if args.to_date:
        params["date_end"] = args.to_date
    print(json.dumps(client.list_invoices(**params), indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cfo-agent", description="Generate CFO/CFA operating reports.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate", help="Generate one or more CFO reports.")
    generate_parser.add_argument("--input", required=True, help="Path to finance JSON input.")
    generate_parser.add_argument("--output", default="reports", help="Directory for generated Markdown reports.")
    generate_parser.add_argument("--report", choices=sorted(REPORTS), help="Specific report to generate. Defaults to all reports.")
    generate_parser.set_defaults(func=generate)

    list_parser = subparsers.add_parser("list-reports", help="List available report identifiers.")
    list_parser.set_defaults(func=list_reports)

    organizations_parser = subparsers.add_parser("zoho-organizations", help="List Zoho Books organizations using environment credentials.")
    organizations_parser.set_defaults(func=zoho_organizations)

    invoices_parser = subparsers.add_parser("zoho-invoices", help="List Zoho Books invoices for the configured organization.")
    invoices_parser.add_argument("--status", help="Optional Zoho invoice status filter, such as overdue or paid.")
    invoices_parser.add_argument("--from-date", help="Optional invoice start date filter in YYYY-MM-DD format.")
    invoices_parser.add_argument("--to-date", help="Optional invoice end date filter in YYYY-MM-DD format.")
    invoices_parser.set_defaults(func=zoho_invoices)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
