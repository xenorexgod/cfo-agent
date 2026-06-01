from __future__ import annotations

import argparse
import json
from pathlib import Path

from .models import FinanceData
from .reports import REPORTS, render_report


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
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
