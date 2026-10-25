import { useMemo } from "react";
import { motion } from "framer-motion";
export default function Universe({
  micro = false,
  water = false,
}: {
  micro?: boolean;
  water?: boolean;
}) {
  const points = useMemo(
    () =>
      Array.from({ length: 144 }, (_, i) => {
        const u = (i % 12) / 11,
          v = Math.floor(i / 12) / 11;
        const x = 60 + u * 470 + Math.sin(i * 7.31) * 10;
        const y = 55 + v * 330 + Math.cos(i * 2.78) * 10;
        return { x, y };
      }),
    [],
  );
  const mesh = useMemo(
    () =>
      Array.from({ length: 21 }, (_, row) =>
        Array.from({ length: 45 }, (_, col) => {
          const x = 30 + col * 12;
          const depth = row / 20;
          const y =
            110 +
            depth * 270 +
            Math.sin(col * 0.15 + depth * 3.4) * 36 +
            Math.exp(-((col - 23) ** 2) / 95) * Math.sin(depth * Math.PI) * 55;
          return [x, y];
        }),
      ),
    [],
  );
  return (
    <svg
      className="universe"
      viewBox="0 0 600 470"
      role="img"
      aria-label={
        micro
          ? water
            ? "Schematic molecules beneath water’s smooth appearance"
            : "Speculative causal events and relations; not a model of physical spacetime"
          : "Schematic smooth surface representing a continuum description"
      }
    >
      <defs>
        <radialGradient id="field-glow">
          <stop stopColor="#397ca1" stopOpacity=".16" />
          <stop offset="1" stopColor="#397ca1" stopOpacity="0" />
        </radialGradient>
        <linearGradient id="mesh-fade">
          <stop stopColor="#7ac3ed" stopOpacity=".03" />
          <stop offset=".5" stopColor="#9cdaef" stopOpacity=".65" />
          <stop offset="1" stopColor="#7ac3ed" stopOpacity=".06" />
        </linearGradient>
        <filter id="point-glow">
          <feGaussianBlur stdDeviation="2" />
        </filter>
      </defs>
      <ellipse cx="310" cy="265" rx="290" ry="200" fill="url(#field-glow)" />
      <g
        className="diagram-guides"
        fill="none"
        stroke="#91bad1"
        strokeOpacity=".12"
      >
        <path d="M45 420H560M300 30v410" strokeDasharray="3 7" />
        <circle cx="300" cy="255" r="185" strokeDasharray="2 8" />
        <path d="M40 40h16m-8-8v16M550 420h16m-8-8v16" />
      </g>
      <motion.g
        animate={{ opacity: micro ? 0.09 : 1 }}
        transition={{ duration: 0.5 }}
        fill="none"
        stroke="url(#mesh-fade)"
        strokeWidth=".8"
      >
        {mesh.map((row, i) => (
          <polyline key={i} points={row.map((p) => p.join(",")).join(" ")} />
        ))}
        {Array.from({ length: 45 }, (_, i) => (
          <polyline
            key={"c" + i}
            points={mesh.map((row) => row[i].join(",")).join(" ")}
          />
        ))}
      </motion.g>
      <motion.g
        animate={{ opacity: micro ? 1 : 0 }}
        transition={{ duration: 0.5 }}
      >
        {points.map((p, i) => (
          <g key={i}>
            {!water && i < 132 && (
              <path
                d={`M${p.x},${p.y} L${points[i + 12].x},${points[i + 12].y}`}
                stroke="#a7dcf3"
                strokeOpacity=".17"
              />
            )}
            {!water && i < 131 && i % 3 === 0 && (
              <path
                d={`M${p.x},${p.y} L${points[i + 13].x},${points[i + 13].y}`}
                stroke="#a7dcf3"
                strokeOpacity=".24"
              />
            )}
            {water ? (
              <g>
                <path
                  d={`M${p.x - 5},${p.y + 5} ${p.x},${p.y} ${p.x + 6},${p.y + 4}`}
                  stroke="#7bacc4"
                />
                <circle cx={p.x} cy={p.y} r="3.3" fill="#9cdcf5" />
                <circle cx={p.x - 5} cy={p.y + 5} r="1.7" fill="#f0ede4" />
                <circle cx={p.x + 6} cy={p.y + 4} r="1.7" fill="#f0ede4" />
              </g>
            ) : (
              <>
                <circle
                  cx={p.x}
                  cy={p.y}
                  r={i % 7 === 0 ? 3 : 1.8}
                  fill={i % 7 === 0 ? "#edbb70" : "#a8def2"}
                />
                {i % 7 === 0 && (
                  <circle
                    cx={p.x}
                    cy={p.y}
                    r="5"
                    fill="#edbb70"
                    opacity=".3"
                    filter="url(#point-glow)"
                  />
                )}
              </>
            )}
          </g>
        ))}
      </motion.g>
      {!micro && (
        <g fill="#b4e4f5">
          {[mesh[5][15], mesh[9][27], mesh[16][20]].map((p, i) => (
            <g key={i}>
              <circle cx={p[0]} cy={p[1]} r="3" />
              <circle
                cx={p[0]}
                cy={p[1]}
                r="8"
                fill="none"
                stroke="#b4e4f5"
                opacity=".3"
              />
            </g>
          ))}
        </g>
      )}
      <g fill="#7294a8" fontSize="9" fontFamily="monospace">
        <text x="40" y="455">
          {micro ? "DISCRETE DESCRIPTION" : "CONTINUUM DESCRIPTION"}
        </text>
        <text x="480" y="455">
          SCHEMATIC
        </text>
      </g>
    </svg>
  );
}
