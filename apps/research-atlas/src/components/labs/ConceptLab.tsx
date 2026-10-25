import { useState } from "react";
import {
  closure,
  emptyOrder,
  longestChain,
  type Order,
} from "../../lib/simulation";
import { Graph, LabFrame, Stat, Toggle } from "./Shared";
import { GrowthLab } from "./GrowthLab";
import { TimeLab } from "./TimeLab";
import { DimensionLab } from "./DimensionLab";
import { LocalLab } from "./LocalLab";
import { AdversarialLab } from "./AdversarialLab";
export const conceptOptions = [
  ["causality", "Events and causal relationships"],
  ["light-cones", "Light cones"],
  ["proper-time", "Proper time"],
  ["dimensions", "Spacetime dimensionality"],
  ["diamonds", "Causal diamonds"],
  ["orders", "Partial orders"],
  ["chains", "Longest chains"],
  ["patterns", "Induced 2+2 and 3+1"],
  ["closure", "Transitive closure"],
  ["randomness", "Randomness can mimic geometry"],
  ["embedding", "Embedding versus physical spacetime"],
  ["continuum", "Continuum limits"],
  ["singularities", "Black-hole singularities"],
];
function LightCone() {
  const [time, setTime] = useState(0.7),
    [space, setSpace] = useState(0.3);
  const squared = time * time - space * space,
    classification =
      Math.abs(squared) < 0.000001
        ? "Lightlike"
        : squared > 0
          ? "Timelike"
          : "Spacelike";
  return (
    <LabFrame
      title="What can influence what?"
      subtitle="Set c=1: light travels one spatial unit per unit of time. Move the test event across the light cone."
    >
      <div className="lab-controls">
        <label className="lab-field lab-range">
          Time separation Δt: {time.toFixed(2)}
          <input
            type="range"
            aria-label="Time separation"
            min="0"
            max="1"
            step=".05"
            value={time}
            onChange={(e) => setTime(+e.target.value)}
          />
        </label>
        <label className="lab-field lab-range">
          Space separation Δx: {space.toFixed(2)}
          <input
            type="range"
            aria-label="Space separation"
            min="-1"
            max="1"
            step=".05"
            value={space}
            onChange={(e) => setSpace(+e.target.value)}
          />
        </label>
      </div>
      <svg
        className="lab-graph"
        viewBox="0 0 600 340"
        role="img"
        aria-label={`Light cone; test event is ${classification.toLowerCase()} separated`}
      >
        <path d="M300 300 80 40 520 40Z" fill="rgba(150,218,250,.09)" />
        <path
          d="M80 40 300 300 520 40"
          fill="none"
          stroke="#96dafa"
          strokeDasharray="5 5"
        />
        <path d="M50 300H550M300 320V20" fill="none" stroke="#506474" />
        <text x="310" y="28" fill="#a9bccb">
          time ↑
        </text>
        <text x="515" y="325" fill="#a9bccb">
          space →
        </text>
        <text x="250" y="65" fill="#96dafa">
          causal future
        </text>
        <circle cx="300" cy="300" r="5" fill="#96dafa" />
        <line
          x1="300"
          y1="300"
          x2={300 + space * 220}
          y2={300 - time * 260}
          stroke="#edbb70"
          strokeWidth="2"
        />
        <circle
          cx={300 + space * 220}
          cy={300 - time * 260}
          r="7"
          fill="#edbb70"
        />
      </svg>
      <div className="lab-stats">
        <Stat label="Separation" value={classification} />
        <Stat label="Δs² = Δt² − Δx²" value={squared.toFixed(3)} />
        <Stat
          label="Inertial proper time"
          value={
            squared >= 0 ? Math.sqrt(squared).toFixed(3) : "No timelike path"
          }
        />
      </div>
      <p className="lab-insight">
        Inside the cone, a slower-than-light signal can connect the events.
        Outside it, the separation is spacelike. The strict order in these toy
        studies excludes exact null ties; those ties have probability zero under
        ideal continuous sampling.
      </p>
    </LabFrame>
  );
}
function PatternLab({ initial = false }: { initial?: boolean }) {
  const [three, setThree] = useState(initial),
    [cross, setCross] = useState(false),
    [closed, setClosed] = useState(true);
  const direct = emptyOrder(4);
  if (three) {
    direct[0][1] = true;
    direct[1][2] = true;
  } else {
    direct[0][1] = true;
    direct[2][3] = true;
  }
  if (cross) direct[0][3] = true;
  const order = closure(direct);
  return (
    <LabFrame
      title="A pattern is an induced suborder"
      subtitle="Keep every causal relation among the selected four events. Extra relations change the pattern."
    >
      <div className="lab-controls">
        <Toggle value={three} onChange={setThree}>
          Use 3+1 instead of 2+2
        </Toggle>
        <Toggle value={cross} onChange={setCross}>
          Add a cross relation
        </Toggle>
        <Toggle value={closed} onChange={setClosed}>
          Reveal transitive consequences
        </Toggle>
      </div>
      <Graph
        order={order}
        direct={direct}
        showInherited={closed}
        labels
        title="Four-event induced pattern and its transitive closure"
      />
      <div className="lab-stats">
        <Stat
          label="Pattern"
          value={cross ? "Neither target motif" : three ? "3+1" : "2+2"}
        />
        <Stat label="Height" value={longestChain(order).length} />
      </div>
      <p className="lab-insight">
        {three
          ? "A 3+1 has a three-event chain and one event unrelated to all three. The first event precedes the third by transitivity, even when its edge is hidden."
          : "A 2+2 has exactly two disjoint two-event chains and no other relations. A cross relation removes this induced 2+2."}{" "}
        These are exact combinatorial examples, not stochastic measurements.
      </p>
    </LabFrame>
  );
}
function ContinuumLab() {
  const [count, setCount] = useState(12),
    [route, setRoute] = useState(false);
  return (
    <LabFrame
      title="A limit needs more than a finer picture"
      subtitle="Increasing the number of events is a sequence of models. A continuum claim requires convergence of specified, label-invariant observables."
    >
      <div className="lab-controls">
        <label className="lab-field lab-range">
          Drawing resolution: {count}
          <input
            aria-label="Drawing resolution"
            type="range"
            min="4"
            max="40"
            value={count}
            onChange={(e) => setCount(+e.target.value)}
          />
        </label>
        <Toggle value={route} onChange={setRoute}>
          Show the classical-growth obstruction
        </Toggle>
      </div>
      <svg
        className="lab-graph"
        viewBox="0 0 600 300"
        role="img"
        aria-label="Schematic sequence and continuum target"
      >
        <path
          d="M50 230Q300 -90 550 230"
          fill="none"
          stroke="#96dafa"
          strokeWidth="1"
          opacity=".4"
        />
        {Array.from({ length: count }, (_, i) => {
          const t = i / (count - 1);
          return (
            <circle
              key={i}
              cx={50 + 500 * t}
              cy={230 - 640 * t * (1 - t)}
              r="3"
              fill={route ? "#edbb70" : "#96dafa"}
            />
          );
        })}
        <text x="70" y="280" fill="#a9bccb">
          More dots can imitate a curve. That alone proves no sampling limit.
        </text>
      </svg>
      <p className="lab-insight">
        {route
          ? "For the ordinary classical sequential-growth class studied here, existing almost-semiorder restrictions obstruct the required nondegenerate Minkowski sampling limit. The archived fixed-p finite failures are separate numerical evidence. A different microscopic mechanism may change the assumptions."
          : "A picture can become visually smooth while its causal pattern law stays wrong. Specify a sampling limit, sampling measure, invariants and dynamics before interpreting a finer drawing as spacetime. This diagram is schematic, not experimental data."}
      </p>
    </LabFrame>
  );
}
function SingularityLab() {
  const [radius, setRadius] = useState(2),
    [view, setView] = useState(false);
  const curvature = radius > 0 ? 12 / radius ** 6 : Infinity;
  return (
    <LabFrame
      title="Where the classical description reaches its limit"
      subtitle="In the ideal Schwarzschild solution, the event horizon and the central singularity are different places. Use units where the horizon radius is 1."
    >
      <div className="lab-controls">
        <label className="lab-field lab-range">
          Radius r / rₛ: {radius.toFixed(2)}
          <input
            aria-label="Radius relative to event horizon"
            type="range"
            min=".1"
            max="3"
            step=".05"
            value={radius}
            onChange={(e) => setRadius(+e.target.value)}
          />
        </label>
        <Toggle value={view} onChange={setView}>
          Compare the water analogy
        </Toggle>
      </div>
      <svg
        className="lab-graph"
        viewBox="0 0 600 320"
        role="img"
        aria-label="Schematic horizon and central singularity"
      >
        <circle
          cx="300"
          cy="150"
          r="88"
          fill="rgba(150,218,250,.035)"
          stroke="#96dafa"
          strokeDasharray="5 6"
        />
        <circle cx="300" cy="150" r="5" fill="#df8e85" />
        <circle cx={300 + radius * 88} cy="150" r="6" fill="#edbb70" />
        <text x="216" y="260" fill="#96dafa">
          event horizon: r = rₛ
        </text>
        <text x="225" y="80" fill="#df8e85">
          ideal singularity: r → 0
        </text>
        <line
          x1="300"
          y1="150"
          x2={300 + radius * 88}
          y2="150"
          stroke="#edbb70"
          opacity=".5"
        />
      </svg>
      <div className="lab-stats">
        <Stat
          label="Schwarzschild curvature scalar K·rₛ⁴"
          value={curvature.toLocaleString(undefined, {
            maximumFractionDigits: 2,
          })}
          detail="K = 12 rₛ² / r⁶; finite at the horizon"
        />
        <Stat
          label="Location"
          value={
            radius > 1
              ? "Outside horizon"
              : radius < 1
                ? "Inside horizon"
                : "At horizon"
          }
        />
      </div>
      <p className="lab-insight">
        {view
          ? "Water has experimentally established microscopic constituents. A microscopic spacetime description is a hypothesis. Failure of a continuum description can motivate deeper theories, but the analogy neither identifies the microscopic physics nor resolves a gravitational singularity."
          : "The ideal classical curvature diverges as r approaches zero; the horizon is not a curvature singularity. These flat causal-order experiments contain no black-hole dynamics and do not resolve this divergence. The plotted radius is a schematic coordinate, not an observer trajectory."}
      </p>
      <p className="lab-footnote">
        Mathematical reference:{" "}
        <a
          href="https://www.damtp.cam.ac.uk/user/tong/gr/grhtml/S6.html"
          target="_blank"
          rel="noreferrer"
        >
          David Tong, General Relativity, §6.1 (Kretschmann scalar)
        </a>
        . With rₛ=2GM/c², K=48G²M²/(c⁴r⁶)=12rₛ²/r⁶.
      </p>
    </LabFrame>
  );
}
function EmbeddingLab() {
  const [swap, setSwap] = useState(false);
  const order: Order = [
    [false, true, true, true],
    [false, false, false, true],
    [false, false, false, true],
    [false, false, false, false],
  ];
  return (
    <LabFrame
      title="A drawing is not a spacetime"
      subtitle="The order says which events precede which. Rearranging the drawing preserves those relations."
    >
      <button onClick={() => setSwap(!swap)}>Change display coordinates</button>
      <Graph
        order={order}
        points={
          swap
            ? [
                { t: 0.1, x: [0] },
                { t: 0.45, x: [-0.2] },
                { t: 0.55, x: [0.15] },
                { t: 0.9, x: [0] },
              ]
            : undefined
        }
        title="Same diamond order in two drawing layouts"
        labels
      />
      <p className="lab-insight">
        Both views encode the same four-event order. A mathematical embedding
        must preserve relations under a specified metric; a faithful sampling
        model also requires volume information. A physical spacetime
        interpretation additionally requires dynamics and empirical evidence.
        This drawing alone supplies neither.
      </p>
    </LabFrame>
  );
}
export function ConceptLab({ concept }: { concept?: string }) {
  const [choice, setChoice] = useState("light-cones");
  const selected =
    conceptOptions.find(
      ([id, name]) =>
        id === concept || name.toLowerCase() === concept?.toLowerCase(),
    )?.[0] || choice;
  const body =
    selected === "proper-time" ||
    selected === "chains" ||
    selected === "diamonds" ? (
      <TimeLab />
    ) : selected === "dimensions" ? (
      <DimensionLab />
    ) : selected === "patterns" || selected === "orders" ? (
      <PatternLab />
    ) : selected === "closure" ? (
      <GrowthLab />
    ) : selected === "randomness" ? (
      <AdversarialLab />
    ) : selected === "continuum" ? (
      <ContinuumLab />
    ) : selected === "singularities" ? (
      <SingularityLab />
    ) : selected === "embedding" ? (
      <EmbeddingLab />
    ) : selected === "local" ? (
      <LocalLab />
    ) : (
      <LightCone />
    );
  return (
    <div className="lab-concepts">
      {!concept && (
        <label className="lab-field lab-concept-select">
          Explore a concept
          <select
            aria-label="Educational concept"
            value={choice}
            onChange={(e) => setChoice(e.target.value)}
          >
            {conceptOptions.map(([id, name]) => (
              <option key={id} value={id}>
                {name}
              </option>
            ))}
          </select>
        </label>
      )}
      {body}
    </div>
  );
}
