export function money(amount: number): string {
  const abs = Math.abs(amount);
  let formatted: string;
  if (abs >= 10_000_000) formatted = `INR ${(amount / 10_000_000).toFixed(2)} Cr`;
  else if (abs >= 100_000) formatted = `INR ${(amount / 100_000).toFixed(2)} L`;
  else formatted = `INR ${amount.toLocaleString("en-IN")}`;
  return formatted;
}

export function pct(value: number): string {
  return `${value.toFixed(1)}%`;
}

export function num(value: number): string {
  return value.toLocaleString("en-IN");
}

export function mdTable(headers: string[], rows: (string | number)[][]): string {
  const head = `| ${headers.join(" | ")} |`;
  const sep = `| ${headers.map(() => "---").join(" | ")} |`;
  const body = rows.map((r) => `| ${r.join(" | ")} |`).join("\n");
  return [head, sep, body].join("\n");
}
