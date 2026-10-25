import { useId, useState } from "react";
import { scaleLinear, scaleLog, scalePoint } from "d3-scale";
import { line } from "d3-shape";
import type { ChartSpec, DataRow } from "../data/types";
import { formatNumber, humanize } from "../lib/data-utils";
const palette = [
  "#9bdcf5",
  "#edbb70",
  "#98c3a5",
  "#ce9cb4",
  "#a9b2f0",
  "#d6c9a6",
  "#8fb9c8",
  "#d68c7e",
];
export default function ScientificChart({
  rows,
  spec,
  log = false,
  logX = false,
  extraReferences = [],
}: {
  rows: DataRow[];
  spec: ChartSpec;
  log?: boolean;
  logX?: boolean;
  extraReferences?: { value: number; label: string }[];
}) {
  const id = useId();
  const [inspect, setInspect] = useState<DataRow | null>(null);
  const valid = rows.filter(
    (r) =>
      typeof r[spec.y] === "number" &&
      Number.isFinite(r[spec.y]) &&
      r[spec.x] !== null,
  );
  if (!valid.length)
    return (
      <div className="empty-state">
        No defined estimates for these filters. Missing measurements are not
        zeros.
      </div>
    );
  if (valid.length > 240)
    return (
      <div className="empty-state">
        {valid.length.toLocaleString()} defined records. Narrow the filters to
        240 or fewer records to plot them clearly. The table and exports include
        every filtered row.
      </div>
    );
  const W = 850,
    H = 360,
    left = 74,
    right = 28,
    top = 34,
    bottom = 85;
  const numeric = valid.every((r) => typeof r[spec.x] === "number");
  const xs = valid.map((r) => Number(r[spec.x]));
  const labels = [...new Set(valid.map((r) => String(r[spec.x])))];
  const useLogX = logX && numeric && xs.every((v) => v > 0);
  const xNumeric = (useLogX ? scaleLog() : scaleLinear())
    .domain([Math.min(...xs), Math.max(...xs)])
    .range([left, W - right]);
  if (numeric && Math.min(...xs) === Math.max(...xs))
    xNumeric.domain(useLogX ? [xs[0] / 2, xs[0] * 2] : [xs[0] - 1, xs[0] + 1]);
  const xCat = scalePoint<string>()
    .domain(labels)
    .range([left + 24, W - right - 24])
    .padding(0.2);
  const x = (r: DataRow) =>
    numeric ? xNumeric(Number(r[spec.x])) : xCat(String(r[spec.x]))!;
  const refs = [
    ...(spec.reference !== undefined
      ? [
          {
            value: spec.reference,
            label: spec.referenceLabel || "Analytical reference",
          },
        ]
      : []),
    ...extraReferences,
  ];
  const ys = valid
    .flatMap((r) => [
      r[spec.y],
      spec.low ? r[spec.low] : null,
      spec.high ? r[spec.high] : null,
    ])
    .filter((v): v is number => typeof v === "number" && Number.isFinite(v));
  const allY = [...ys, ...refs.map((r) => r.value)];
  const lo = Math.min(...allY),
    hi = Math.max(...allY),
    pad = (hi - lo || Math.max(Math.abs(hi), 1)) * 0.15;
  const useLog = log && allY.every((v) => v > 0);
  const y = useLog
    ? scaleLog()
        .domain([lo / 1.5, hi * 1.5])
        .range([H - bottom, top])
    : scaleLinear()
        .domain([lo - pad, hi + pad])
        .nice()
        .range([H - bottom, top]);
  const series = [
    ...new Set(
      valid.map((r) =>
        spec.series ? String(r[spec.series]) : "Recorded mean",
      ),
    ),
  ];
  const ticks = useLog
    ? y
        .ticks(4)
        .filter((_, i, a) => a.length < 9 || i % Math.ceil(a.length / 7) === 0)
    : y.ticks(5);
  return (
    <div className="scientific-chart">
      <div className="chart-axis-title">
        {spec.label} <span>· {spec.unit}</span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} role="group" aria-labelledby={id}>
        <title id={id}>
          {spec.label} by {humanize(spec.x)}. {valid.length} archived estimates;
          vertical bars show the source intervals described below.
        </title>
        {ticks.map((t) => (
          <g key={t}>
            <line
              x1={left}
              x2={W - right}
              y1={y(t)}
              y2={y(t)}
              stroke="#26333f"
              strokeDasharray="3 5"
            />
            <text
              x={left - 12}
              y={y(t) + 4}
              textAnchor="end"
              fill="#b3bfca"
              fontSize="11"
            >
              {formatNumber(t, 3)}
            </text>
          </g>
        ))}
        {(numeric
          ? new Set(xs).size <= 10
            ? [...new Set(xs)].sort((a, b) => a - b)
            : xNumeric.ticks(6)
          : labels
        ).map((t) => (
          <g key={String(t)}>
            <text
              transform={`translate(${numeric ? xNumeric(Number(t)) : xCat(String(t))},${H - bottom + 22})${numeric ? "" : " rotate(-22)"}`}
              textAnchor={numeric ? "middle" : "end"}
              fill="#b3bfca"
              fontSize="10"
            >
              {numeric ? formatNumber(Number(t), 1) : humanize(String(t))}
            </text>
          </g>
        ))}
        {refs.map((r, i) => (
          <g key={r.label}>
            <line
              x1={left}
              x2={W - right}
              y1={y(r.value)}
              y2={y(r.value)}
              stroke="#f0c586"
              opacity=".6"
              strokeDasharray="5 5"
            />
            <text
              x={W - right}
              y={y(r.value) - 6 - i * 2}
              textAnchor="end"
              fill="#f0c586"
              fontSize="10"
            >
              {r.label}
            </text>
          </g>
        ))}
        {series.map((s, i) => {
          const rs = valid.filter(
            (r) =>
              (spec.series ? String(r[spec.series]) : "Recorded mean") === s,
          );
          const canJoin =
            numeric && new Set(rs.map((r) => r[spec.x])).size === rs.length;
          return (
            <g
              key={s}
              fill={palette[i % palette.length]}
              stroke={palette[i % palette.length]}
            >
              {canJoin && (
                <path
                  d={
                    line<DataRow>()
                      .x(x)
                      .y((r) => y(Number(r[spec.y])))(
                      [...rs].sort(
                        (a, b) => Number(a[spec.x]) - Number(b[spec.x]),
                      ),
                    ) || ""
                  }
                  fill="none"
                  strokeWidth="1.5"
                  opacity=".6"
                />
              )}
              {rs.map((r, j) => {
                const a = spec.low ? r[spec.low] : null,
                  b = spec.high ? r[spec.high] : null;
                return (
                  <g key={j}>
                    {typeof a === "number" && typeof b === "number" && (
                      <path
                        d={`M${x(r)},${y(a)}V${y(b)}M${x(r) - 4},${y(a)}h8M${x(r) - 4},${y(b)}h8`}
                        fill="none"
                        strokeWidth="1.4"
                      />
                    )}
                    <circle
                      cx={x(r)}
                      cy={y(Number(r[spec.y]))}
                      r="4"
                      tabIndex={0}
                      role="button"
                      aria-label={`${s}, ${humanize(spec.x)} ${r[spec.x]}: ${formatNumber(r[spec.y])}${typeof a === "number" ? `, interval ${formatNumber(a)} to ${formatNumber(b)}` : ""}`}
                      onFocus={() => setInspect(r)}
                      onMouseEnter={() => setInspect(r)}
                      onClick={() => setInspect(r)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          setInspect(r);
                        }
                      }}
                    >
                      <title>
                        {s} · {spec.x}={r[spec.x]} · {formatNumber(r[spec.y])} [
                        {formatNumber(a)}, {formatNumber(b)}]
                      </title>
                    </circle>
                  </g>
                );
              })}
            </g>
          );
        })}
        <text
          x={(left + W - right) / 2}
          y={H - 9}
          textAnchor="middle"
          fill="#c1cbd3"
          fontSize="11"
        >
          {humanize(spec.x)}
          {useLogX ? " · logarithmic x scale" : ""}
          {useLog ? " · logarithmic y scale" : ""}
        </text>
      </svg>
      <div className="chart-legend">
        {series.map((s, i) => (
          <span key={s}>
            <i style={{ background: palette[i % palette.length] }} />
            {spec.series ? humanize(spec.series) + " = " : ""}
            {humanize(s)}
          </span>
        ))}
      </div>
      {inspect && (
        <div className="point-inspector" role="status">
          <strong>Selected record</strong>{" "}
          {[
            "family",
            "dimension",
            "dimension_label",
            "metric",
            "parameter",
            "target",
            "fit",
            "method",
          ]
            .filter((k) => inspect[k] !== undefined && inspect[k] !== null)
            .map((k) => (
              <span key={k}>
                {" "}
                · {humanize(k)}: {formatNumber(inspect[k])}
              </span>
            ))}{" "}
          · {humanize(spec.x)}: {formatNumber(inspect[spec.x])} ·{" "}
          {formatNumber(inspect[spec.y])} {spec.unit}{" "}
          {spec.low && spec.high && (
            <>
              · interval [{formatNumber(inspect[spec.low])},{" "}
              {formatNumber(inspect[spec.high])}]
            </>
          )}
        </div>
      )}
      <p className="microcopy">
        {rows.length - valid.length > 0
          ? `${rows.length - valid.length} undefined estimates remain in the table and export. `
          : ""}
        Each point is an archived summary. Lines connect values within a series;
        they are guides, not fitted models. Focus or select a point to inspect
        it.
      </p>
    </div>
  );
}
