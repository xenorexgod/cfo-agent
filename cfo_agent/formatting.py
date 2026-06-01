from __future__ import annotations


def money(value: float, suffix: str = "") -> str:
    sign = "-" if value < 0 else ""
    absolute = abs(value)
    if absolute >= 10_000_000:
        text = f"{absolute / 10_000_000:.2f} crore"
    elif absolute >= 100_000:
        text = f"{absolute / 100_000:.2f} lakh"
    else:
        text = f"{absolute:,.0f}"
    return f"{sign}INR {text}{suffix}"


def pct(value: float) -> str:
    return f"{value:.1f}%"


def number(value: float) -> str:
    if value == int(value):
        return f"{int(value):,}"
    return f"{value:,.2f}"


def table(headers: list[str], rows: list[list[object]]) -> str:
    rendered_rows = [[str(cell) for cell in row] for row in rows]
    widths = [len(header) for header in headers]
    for row in rendered_rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def render(row: list[str]) -> str:
        return "| " + " | ".join(cell.ljust(widths[index]) for index, cell in enumerate(row)) + " |"

    separator = "| " + " | ".join("-" * width for width in widths) + " |"
    return "\n".join([render(headers), separator, *[render(row) for row in rendered_rows]])
