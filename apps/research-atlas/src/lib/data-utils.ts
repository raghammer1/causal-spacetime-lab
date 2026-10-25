import type { DataRow, DataValue } from "../data/types";
export function formatNumber(value: DataValue | undefined, digits = 4): string {
  if (
    value === null ||
    value === undefined ||
    (typeof value === "number" && !Number.isFinite(value))
  )
    return "Not available";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "string") return value;
  if (value !== 0 && Math.abs(value) < 0.001) return value.toExponential(3);
  return new Intl.NumberFormat("en", { maximumFractionDigits: digits }).format(
    value,
  );
}
export function filterRows(
  rows: DataRow[],
  filters: Record<string, string>,
  search = "",
): DataRow[] {
  const needle = search.trim().toLowerCase();
  return rows.filter(
    (row) =>
      Object.entries(filters).every(
        ([key, value]) => value === "" || String(row[key]) === value,
      ) &&
      (!needle ||
        Object.values(row).some((v) =>
          String(v).toLowerCase().includes(needle),
        )),
  );
}
export function toCsv(rows: DataRow[], columns: string[]): string {
  const escape = (v: DataValue | undefined) =>
    `"${(v === null || v === undefined ? "" : String(v)).replaceAll('"', '""')}"`;
  return [
    columns.map(escape).join(","),
    ...rows.map((row) => columns.map((key) => escape(row[key])).join(",")),
  ].join("\r\n");
}
export const humanize = (text: string) =>
  text.replaceAll("_", " ").replaceAll("ci95", "95% CI");
export function downloadFile(name: string, content: string, type: string) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 500);
}
