import { useId, type ReactNode } from "react";
import { covers, type EventPoint, type Order } from "../../lib/simulation";
export function LabFrame({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <section className="lab-frame" aria-label={title}>
      <div className="lab-heading">
        <span className="lab-live">
          <i /> LIVE TEACHING MODEL
        </span>
        <h3>{title}</h3>
        <p>{subtitle}</p>
      </div>
      {children}
      <p className="lab-footnote">
        Illustrative browser model • deterministic replay • separate from the
        archived studies • no physical spacetime claim.
      </p>
    </section>
  );
}
export function Seed({
  value,
  onChange,
}: {
  value: number;
  onChange: (n: number) => void;
}) {
  return (
    <label className="lab-field">
      Seed
      <input
        aria-label="Simulation seed"
        type="number"
        min="0"
        max="4294967295"
        value={value}
        onChange={(e) =>
          onChange(
            Math.max(
              0,
              Math.min(4294967295, Math.trunc(Number(e.target.value))),
            ),
          )
        }
      />
    </label>
  );
}
export function Stat({
  label,
  value,
  detail,
}: {
  label: string;
  value: ReactNode;
  detail?: string;
}) {
  return (
    <div className="lab-stat">
      <span>{label}</span>
      <strong>{value}</strong>
      {detail && <small>{detail}</small>}
    </div>
  );
}
export function Toggle({
  value,
  onChange,
  children,
}: {
  value: boolean;
  onChange: (v: boolean) => void;
  children: ReactNode;
}) {
  return (
    <label className="lab-toggle">
      <input
        type="checkbox"
        checked={value}
        onChange={(e) => onChange(e.target.checked)}
      />
      {children}
    </label>
  );
}
export function pct(value: number | null) {
  return value === null ? "Not available" : `${(value * 100).toFixed(1)}%`;
}
export function fmt(value: number | null) {
  return value === null ? "Not available" : value.toFixed(3);
}
export interface XY {
  x: number;
  y: number;
}
export function layout(order: Order): XY[] {
  const depth = Array(order.length).fill(0);
  const indices = order
    .map((_, i) => i)
    .sort((a, b) =>
      order.reduce((s, row) => s + Number(row[a]) - Number(row[b]), 0),
    );
  for (const j of indices)
    for (let i = 0; i < order.length; i++)
      if (order[i][j]) depth[j] = Math.max(depth[j], depth[i] + 1);
  const highest = Math.max(1, ...depth);
  return order.map((_, i) => {
    const peers = indices.filter((j) => depth[j] === depth[i]);
    return {
      x: 50 + ((peers.indexOf(i) + 1) * 500) / (peers.length + 1),
      y: 290 - (depth[i] / highest) * 240,
    };
  });
}
export function Graph({
  order,
  points,
  direct,
  highlighted = [],
  showEdges = true,
  showInherited = false,
  selected,
  onSelect,
  coordinates = false,
  labels = false,
  boundary = "diamond",
  title = "Causal order",
}: {
  order: Order;
  points?: EventPoint[];
  direct?: Order;
  highlighted?: number[];
  showEdges?: boolean;
  showInherited?: boolean;
  selected?: number[];
  onSelect?: (n: number) => void;
  coordinates?: boolean;
  labels?: boolean;
  boundary?: "diamond" | "slab" | "box" | "none";
  title?: string;
}) {
  const gridId = useId();
  const positions = points
    ? points.map((p) => ({ x: 300 + p.x[0] * 460, y: 310 - p.t * 280 }))
    : layout(order);
  const links = direct || covers(order);
  const inHighlight = new Set(highlighted),
    inSelected = new Set(selected);
  return (
    <svg
      className="lab-graph"
      viewBox="0 0 600 350"
      role={onSelect ? "group" : "img"}
      aria-label={title}
    >
      <title>{title}</title>
      <defs>
        <pattern
          id={gridId}
          width="25"
          height="25"
          patternUnits="userSpaceOnUse"
        >
          <path
            d="M 25 0 L 0 0 0 25"
            fill="none"
            stroke="currentColor"
            strokeWidth=".4"
            opacity=".18"
          />
        </pattern>
      </defs>
      <rect width="600" height="350" fill={`url(#${gridId})`} />
      {points && boundary === "diamond" && (
        <path
          d="M300 30 530 170 300 310 70 170Z"
          fill="rgba(150,218,250,.025)"
          stroke="currentColor"
          strokeDasharray="4 6"
          opacity=".4"
        />
      )}
      {points && boundary === "slab" && (
        <path
          d="M185 100 415 100 530 170 415 240 185 240 70 170Z"
          fill="rgba(150,218,250,.035)"
          stroke="currentColor"
          strokeDasharray="4 6"
          opacity=".5"
        />
      )}
      {points && boundary === "box" && (
        <rect
          x="240.2"
          y="30"
          width="119.6"
          height="280"
          fill="rgba(237,187,112,.035)"
          stroke="#edbb70"
          strokeDasharray="4 6"
          opacity=".5"
        />
      )}
      {showEdges &&
        order.flatMap((row, i) =>
          row.flatMap((related, j) =>
            related && (links[i][j] || showInherited)
              ? [
                  <line
                    key={`${i}-${j}`}
                    x1={positions[i].x}
                    y1={positions[i].y}
                    x2={positions[j].x}
                    y2={positions[j].y}
                    stroke={
                      inHighlight.has(i) && inHighlight.has(j)
                        ? "#edbb70"
                        : links[i][j]
                          ? "#96dafa"
                          : "#b49bea"
                    }
                    strokeWidth={
                      inHighlight.has(i) && inHighlight.has(j) ? 2.4 : 0.8
                    }
                    opacity={
                      inHighlight.has(i) && inHighlight.has(j)
                        ? 0.95
                        : links[i][j]
                          ? 0.3
                          : 0.17
                    }
                    strokeDasharray={links[i][j] ? undefined : "3 4"}
                  />,
                ]
              : [],
          ),
        )}
      {positions.map((p, i) => (
        <g
          key={i}
          role={onSelect ? "button" : undefined}
          tabIndex={onSelect ? 0 : undefined}
          aria-label={onSelect ? `Inspect event ${i + 1}` : undefined}
          onClick={() => onSelect?.(i)}
          onKeyDown={(e) => {
            if (onSelect && (e.key === "Enter" || e.key === " ")) {
              e.preventDefault();
              onSelect(i);
            }
          }}
          className={onSelect ? "lab-event" : undefined}
        >
          {onSelect && <circle cx={p.x} cy={p.y} r="11" fill="transparent" />}
          {(inHighlight.has(i) || inSelected.has(i)) && (
            <circle
              cx={p.x}
              cy={p.y}
              r="8"
              fill="none"
              stroke={inSelected.has(i) ? "#e4dfed" : "#edbb70"}
              opacity=".6"
            />
          )}
          <circle
            cx={p.x}
            cy={p.y}
            r={order.length > 80 ? 2.5 : 3.5}
            fill={
              inSelected.has(i)
                ? "#fff"
                : inHighlight.has(i)
                  ? "#edbb70"
                  : "#96dafa"
            }
          />
          {labels && (
            <text x={p.x + 8} y={p.y - 7} fill="currentColor" fontSize="9">
              {i + 1}
            </text>
          )}
        </g>
      ))}
      {coordinates && (
        <>
          <line
            x1="550"
            y1="310"
            x2="550"
            y2="30"
            stroke="currentColor"
            opacity=".4"
          />
          <text x="558" y="40" fill="currentColor" fontSize="10">
            t=1
          </text>
          <text x="558" y="310" fill="currentColor" fontSize="10">
            t=0
          </text>
          <text x="275" y="338" fill="currentColor" fontSize="10">
            space x · c=1
          </text>
        </>
      )}
      {!points && (
        <text x="20" y="333" fill="currentColor" opacity=".65" fontSize="10">
          ABSTRACT ORDER LAYOUT · POSITION IS NOT PHYSICAL SPACE
        </text>
      )}
    </svg>
  );
}
