import { useMemo, useState } from "react";
import { ArrowUpRight, Download, RotateCcw } from "lucide-react";
import type { ChartSpec, Dataset } from "../data/types";
import {
  filterRows,
  formatNumber,
  humanize,
  downloadFile,
  toCsv,
} from "../lib/data-utils";
import ScientificChart from "./ScientificChart";
const filterKeys = [
  "model",
  "duration",
  "family",
  "dimension_label",
  "dimension",
  "reference_dimension",
  "count",
  "parameter",
  "target",
  "fit",
  "stage",
  "metric",
  "scope",
  "method",
];
export default function DataPanel({
  dataset,
  initialFilters,
  compact = false,
}: {
  dataset: Dataset;
  initialFilters?: Record<string, string>;
  compact?: boolean;
}) {
  const initial = Object.fromEntries(
    Object.entries(dataset.defaultFilters).map(([k, v]) => [k, String(v)]),
  );
  const [filters, setFilters] = useState<Record<string, string>>({
    ...initial,
    ...initialFilters,
  });
  const [search, setSearch] = useState("");
  const [log, setLog] = useState(false);
  const [logX, setLogX] = useState(dataset.chart.x === "density");
  const [page, setPage] = useState(0);
  const [view, setView] = useState<"chart" | "table">(
    dataset.id === "detector-advancement" ? "table" : "chart",
  );
  const [allCols, setAllCols] = useState(false);
  const options = useMemo(
    () =>
      filterKeys
        .filter((k) => dataset.columns.includes(k))
        .map((key) => ({
          key,
          values: [
            ...new Set(
              dataset.rows.map((r) => r[key]).filter((v) => v !== null),
            ),
          ].sort((a, b) =>
            typeof a === "number" && typeof b === "number"
              ? a - b
              : String(a).localeCompare(String(b)),
          ),
        }))
        .filter((o) => o.values.length > 1 && o.values.length <= 90),
    [dataset],
  );
  const rows = useMemo(
    () => filterRows(dataset.rows, filters, search),
    [dataset, filters, search],
  );
  const spec: ChartSpec = { ...dataset.chart };
  if (dataset.id.startsWith("time-") && filters.duration) {
    spec.reference = Number(filters.duration);
    spec.referenceLabel = `Known duration T = ${filters.duration}`;
  }
  if (dataset.id === "growth-global" && filters.metric !== "t22") {
    delete spec.reference;
    delete spec.referenceLabel;
    spec.label = humanize(filters.metric || "Selected metric");
    spec.unit =
      filters.metric === "height"
        ? "events"
        : filters.metric === "global_dimension"
          ? "reference-equivalent dimensions"
          : "see metric definition";
  }
  if (dataset.id === "local-global")
    spec.label = humanize(filters.metric || "Selected metric");
  const refs =
    dataset.id === "dimension-summary" && filters.family === "genuine"
      ? [2, 3, 4]
          .filter(
            (d) =>
              !filters.dimension_label || filters.dimension_label === String(d),
          )
          .map((d) => ({ value: d, label: `Generating d = ${d}` }))
      : [];
  const cols = allCols
    ? dataset.columns
    : [
        ...new Set(
          [
            spec.x,
            ...options.map((o) => o.key),
            spec.y,
            spec.low,
            spec.high,
            "status",
            "repeats",
            "n",
            "history_count",
            "parent_count",
          ].filter((k): k is string =>
            Boolean(k && dataset.columns.includes(k)),
          ),
        ),
      ];
  const canLogX =
    rows.length > 0 &&
    rows.every((r) => typeof r[spec.x] === "number" && Number(r[spec.x]) > 0);
  const needsMetric =
    [
      "local-global",
      "growth-global",
      "local-conditional",
      "growth-conditional",
    ].includes(dataset.id) && !filters.metric;
  const canLog =
    rows.some((r) => typeof r[spec.y] === "number") &&
    rows.every((r) =>
      [spec.y, spec.low, spec.high].every(
        (k) =>
          !k || r[k] === null || (typeof r[k] === "number" && Number(r[k]) > 0),
      ),
    ) &&
    (spec.reference === undefined || spec.reference > 0);
  function exportData(kind: "csv" | "json") {
    downloadFile(
      `${dataset.id}-filtered.${kind}`,
      kind === "csv"
        ? toCsv(rows, dataset.columns)
        : JSON.stringify({ ...dataset, filters, rows }, null, 2),
      kind === "csv" ? "text/csv;charset=utf-8" : "application/json",
    );
  }
  return (
    <section
      className={`data-panel ${compact ? "compact" : ""}`}
      aria-label={dataset.title}
    >
      <div className="data-heading">
        <div>
          <span className="tag">
            RECORDED EVIDENCE · EXPERIMENT {dataset.experiment}
          </span>
          <h3>{dataset.title}</h3>
          <p>{dataset.description}</p>
        </div>
        <a className="source-link" href={dataset.sourceUrl}>
          Exact source <ArrowUpRight size={13} />
        </a>
      </div>
      <div className="data-filters">
        {options.map(({ key, values }) => (
          <label key={key}>
            {humanize(key)}
            <select
              aria-label={humanize(key)}
              value={filters[key] || ""}
              onChange={(e) => {
                setFilters({ ...filters, [key]: e.target.value });
                setPage(0);
                setLog(false);
              }}
            >
              <option value="">All</option>
              {values.map((v) => (
                <option key={String(v)} value={String(v)}>
                  {humanize(String(v))}
                </option>
              ))}
            </select>
          </label>
        ))}
        <button
          className="icon-button"
          aria-label="Reset data filters"
          title="Reset data filters"
          onClick={() => {
            setFilters(initial);
            setSearch("");
            setPage(0);
            setLog(false);
          }}
        >
          <RotateCcw size={17} />
        </button>
      </div>
      <div className="data-toolbar">
        <div className="segmented" role="group" aria-label="Data display">
          <button
            disabled={dataset.id === "detector-advancement"}
            aria-pressed={view === "chart"}
            onClick={() => setView("chart")}
          >
            Chart
          </button>
          <button
            aria-pressed={view === "table"}
            onClick={() => setView("table")}
          >
            Numerical table
          </button>
        </div>
        <span className="record-count" aria-live="polite">
          {rows.length.toLocaleString()} /{" "}
          {dataset.rows.length.toLocaleString()} records
        </span>
        <div className="export-buttons">
          <button
            aria-label="Export filtered CSV"
            onClick={() => exportData("csv")}
          >
            <Download size={14} />
            CSV
          </button>
          <button
            aria-label="Export filtered JSON with provenance"
            onClick={() => exportData("json")}
          >
            JSON
          </button>
        </div>
      </div>
      {rows.length === 0 ? (
        <div className="empty-state">
          No archived rows match these filters. Reset the filters or choose
          another combination.
        </div>
      ) : view === "chart" ? (
        <>
          <div className="chart-options">
            {canLogX && (
              <label>
                <input
                  type="checkbox"
                  checked={logX}
                  onChange={(e) => setLogX(e.target.checked)}
                />{" "}
                Logarithmic x axis
              </label>
            )}
            <label>
              <input
                type="checkbox"
                checked={log && canLog}
                disabled={!canLog}
                onChange={(e) => setLog(e.target.checked)}
              />{" "}
              Logarithmic y axis
            </label>
            {!canLog && (
              <span>Requires positive values and interval bounds.</span>
            )}
          </div>
          <>
            {needsMetric ? (
              <div className="empty-state">
                Select one metric to plot. Different metrics measure different
                quantities; the table and exports can still show them together.
              </div>
            ) : (
              <ScientificChart
                key={JSON.stringify(filters) + search}
                rows={rows}
                spec={spec}
                log={log && canLog}
                logX={logX && canLogX}
                extraReferences={refs}
              />
            )}
          </>
        </>
      ) : (
        <>
          <div className="table-options">
            <label>
              Find a record
              <input
                type="search"
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(0);
                }}
                placeholder="Search filtered data…"
              />
            </label>
            <label className="check-label">
              <input
                type="checkbox"
                checked={allCols}
                onChange={(e) => setAllCols(e.target.checked)}
              />{" "}
              All source columns
            </label>
          </div>
          <div
            className="table-scroll"
            tabIndex={0}
            role="region"
            aria-label="Scrollable numerical results"
          >
            <table>
              <caption className="sr-only">
                {dataset.title}; {dataset.uncertainty}
              </caption>
              <thead>
                <tr>
                  {cols.map((c) => (
                    <th scope="col" key={c}>
                      {humanize(c)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.slice(page * 20, page * 20 + 20).map((row, i) => (
                  <tr key={i}>
                    {cols.map((c) => (
                      <td key={c} title={String(row[c] ?? "Not available")}>
                        {formatNumber(row[c], 6)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pagination">
            <button disabled={page === 0} onClick={() => setPage(page - 1)}>
              Previous
            </button>
            <span>
              Page {page + 1} of {Math.max(1, Math.ceil(rows.length / 20))}
            </span>
            <button
              disabled={(page + 1) * 20 >= rows.length}
              onClick={() => setPage(page + 1)}
            >
              Next
            </button>
          </div>
        </>
      )}
      <div className="chart-disclosure">
        <p>
          <strong>Uncertainty</strong> {dataset.uncertainty}
        </p>
        <p>
          <strong>Independent sampling unit</strong> {dataset.sampleUnit}
        </p>
        <details>
          <summary>Assumptions, definitions & provenance</summary>
          <p>{dataset.assumptions}</p>
          <p>
            <strong>Selection:</strong> {dataset.selection}
          </p>
          <p>
            r: related pairs / unordered pairs. H: events in a longest chain.
            t22 / t31: fraction of four-event subsets inducing the stated
            pattern. TV: total variation distance, not a signed residual.
            “Equivalent” means within a registered practical margin; it does not
            establish exact equality. CI describes uncertainty in a summary, not
            the spread of individual orders.
          </p>
          <p>
            All columns in this frontend selection and their missing values are
            retained in exports; the exact source contains the full nested
            diagnostics. Repeated prefixes, overlapping intervals, paired
            controls and thinnings are not independent samples.
          </p>
          <a href={dataset.sourceUrl}>{dataset.sourcePath}</a>
          <p className="checksum">SHA-256: {dataset.sha256}</p>
        </details>
      </div>
    </section>
  );
}
