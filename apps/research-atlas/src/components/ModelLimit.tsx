import { useMemo, useState } from "react";
import { sourceUrl } from "../data/editorial";
import {
  diamondSample,
  emptyOrder,
  intervalHistogram,
  longestChain,
  random,
  twoPlusTwo,
  type Order,
  type Random,
} from "../lib/simulation";
import { Graph, LabFrame, Seed, Stat } from "./labs/Shared";

export const MATCHED_EDGE_PROBABILITY =
  (1 - Math.sqrt(1 - 4 / (3 * Math.sqrt(2)))) / 2;

/** Independent fair labels are essential: forcing equal layer sizes changes the law. */
export function matchedControl(
  count: number,
  rng: Random,
): { order: Order; lower: boolean[] } {
  if (!Number.isInteger(count) || count < 0 || count > 48)
    throw new Error("The teaching control requires an integer 0≤N≤48.");
  const lower = Array.from({ length: count }, () => rng() < 0.5);
  const order = emptyOrder(count);
  for (let a = 0; a < count; a++)
    for (let b = 0; b < count; b++) {
      if (lower[a] && !lower[b]) order[a][b] = rng() < MATCHED_EDGE_PROBABILITY;
    }
  return { order, lower };
}

/** Exact endpoint count; the isolated event is incomparable to both chain endpoints. */
export function threePlusOne(order: Order): number {
  const n = order.length;
  const future = order.map((row) => row.filter(Boolean).length);
  const past = order.map((_, b) =>
    order.reduce((sum, row) => sum + Number(row[b]), 0),
  );
  let total = 0;
  for (let a = 0; a < n; a++)
    for (let c = 0; c < n; c++)
      if (order[a][c]) {
        let middle = 0;
        for (let b = 0; b < n; b++)
          middle += Number(order[a][b] && order[b][c]);
        total += middle * (n - future[a] - past[c] + middle);
      }
  return total;
}

export default function ModelLimit() {
  const [model, setModel] = useState<"matched" | "minkowski">("matched");
  const [seed, setSeed] = useState(20261025);
  const count = 32;
  const sample = useMemo(
    () =>
      model === "matched"
        ? matchedControl(count, random(seed))
        : { order: diamondSample(2, count, seed).order, lower: null },
    [model, seed],
  );
  const metrics = useMemo(() => {
    const histogram = intervalHistogram(sample.order);
    return {
      n22: twoPlusTwo(sample.order),
      n31: threePlusOne(sample.order),
      height: longestChain(sample.order).length,
      nonempty: histogram.slice(1).reduce((sum, value) => sum + value, 0),
    };
  }, [sample]);
  const subsets = (count * (count - 1) * (count - 2) * (count - 3)) / 24;
  return (
    <LabFrame
      title="One matching number is not a universe"
      subtitle="These two different sampling laws have exactly the same ensemble mean for induced 2+2. Switch the model and inspect the structure that this one number misses."
    >
      <div className="lab-controls">
        <label className="lab-field lab-wide">
          Compare the sampling law
          <select
            aria-label="Model comparison"
            value={model}
            onChange={(e) => setModel(e.target.value as typeof model)}
          >
            <option value="matched">
              Deliberately matched height-two control
            </option>
            <option value="minkowski">
              Uniform d=2 Minkowski diamond reference
            </option>
          </select>
        </label>
        <Seed value={seed} onChange={setSeed} />
        <button onClick={() => setSeed((seed + 1) >>> 0)}>
          Next deterministic sample
        </button>
      </div>
      <div className="lab-stats">
        <Stat
          label="Exact ensemble E[t₂₂] · both laws"
          value="1/24 ≈ 4.1667%"
          detail="Analytic expectation for every N≥4; not a fitted value"
        />
        <Stat
          label="This single sample’s t₂₂"
          value={`${((metrics.n22 / subsets) * 100).toFixed(3)}%`}
          detail={`${metrics.n22} induced 2+2 patterns / ${subsets.toLocaleString("en")} four-event subsets`}
        />
      </div>
      <Graph
        order={sample.order}
        title={
          model === "matched"
            ? "Seeded height-two order with independent fair lower and upper labels"
            : "Order-only drawing of a seeded uniform two-dimensional Minkowski diamond"
        }
      />
      <div className="lab-stats">
        <Stat label="Events" value={count} />
        <Stat
          label="Longest-chain height H"
          value={metrics.height}
          detail={
            model === "matched"
              ? "At most two for every realization"
              : "Measured from this one toy order"
          }
        />
        <Stat
          label="Nonempty open intervals"
          value={metrics.nonempty}
          detail={
            model === "matched"
              ? "Exactly zero under this control law"
              : "Endpoints are excluded"
          }
        />
        <Stat
          label="Induced 3+1 count"
          value={metrics.n31}
          detail={
            model === "matched"
              ? "Exactly zero: a three-chain is impossible"
              : "Exact count in this one toy order"
          }
        />
      </div>
      <p className="lab-insight">
        {model === "matched"
          ? `Each event independently gets a fair lower or upper label. This draw has ${sample.lower?.filter(Boolean).length} lower and ${sample.lower?.filter((v) => !v).length} upper events; equal groups are not enforced. Every possible lower-to-upper edge is independently chosen with q = ${MATCHED_EDGE_PROBABILITY.toFixed(6)}. All open intervals are empty.`
          : "The reference generator supplies known flat geometry and uniform volume sampling, then only its order is drawn here. The graphic positions are not the generating spacetime coordinates. A particular sample’s motif frequency need not equal the analytic expectation."}
      </p>
      <p className="note-box">
        The shared 4.1667% is an <strong>ensemble expectation</strong>. These
        single seeded examples have no empirical confidence interval and are not
        additional research trials. In the archived study, both the matched
        control and the d=2 reference passed their separate eight-entry screens.
        The control’s success demonstrates that the screen is insufficient.
      </p>
      <div className="lab-subsection">
        <h4>The mathematical obstruction is about a sampling law</h4>
        <svg
          className="lab-graph"
          viewBox="0 0 600 185"
          role="img"
          aria-label="Ordinary classical sequential growth approaches almost-semiorder limits with zero induced 2+2 density. A nondegenerate Minkowski diamond has positive 2+2 probability. The targets differ."
        >
          <text x="25" y="29" fill="#96dafa" fontSize="13">
            Studied ordinary CSG
          </text>
          <text x="25" y="53" fill="#a9bccb" fontSize="11">
            specified uniform-suborder limit
          </text>
          <path d="M25 72H272m-10-5 10 5-10 5" stroke="#96dafa" fill="none" />
          <text x="25" y="101" fill="#96dafa" fontSize="13">
            Almost-semiorder restriction
          </text>
          <text x="25" y="125" fill="#edbb70" fontSize="14">
            t₂₂ → 0 and t₃₁ → 0
          </text>
          <line x1="300" y1="18" x2="300" y2="148" stroke="#506474" />
          <text x="325" y="29" fill="#96dafa" fontSize="13">
            Nondegenerate Minkowski target
          </text>
          <text x="325" y="53" fill="#a9bccb" fontSize="11">
            uniform diamond samples, d ≥ 2
          </text>
          <text x="325" y="101" fill="#edbb70" fontSize="14">
            Positive 2+2 probability
          </text>
          <text x="325" y="125" fill="#a9bccb" fontSize="12">
            d = 2: exactly 1/24
          </text>
          <text
            x="300"
            y="171"
            fill="#e3dccc"
            fontSize="12"
            textAnchor="middle"
          >
            These sampling targets are incompatible.
          </text>
        </svg>
        <p>
          The known restriction rules out the investigated classical route to
          this Minkowski sampling target. It does not rule out spacetime
          emerging from different microscopic physics. The deliberately matched
          control above is a separate supplied reference law, not an
          ordinary-CSG candidate.
        </p>
        <details>
          <summary>Why the theorem applies—and where it stops</summary>
          <p>
            Brightwell and Georgiou’s result concerns classical sequential
            growth with nonnegative couplings and t₀ or t₁ positive. Their
            convergence notion uses expected probabilities of every finite
            uniformly sampled labeled suborder, with an atomless ordered
            probability space as the continuum target.
          </p>
          <p>
            The generated orders are approximable by semiorders in expected
            pair-edit distance o(N²). Semiorders exclude induced 2+2 and 3+1; a
            uniform four-event subset touches an edited pair with probability
            tending to zero. The two motif densities must therefore vanish. A
            nondegenerate Minkowski diamond has positive 2+2 probability, so it
            cannot have that limit.
          </p>
          <p>
            For a fixed p &gt; 0, the lab also derives E[t₂₂(N)] ≤
            3(1−p)/[(N−1)p²] → 0. This bound can be loose at finite N and does
            not predict monotonicity over the archived sizes. The result does
            not cover every altered dynamics, quantum mechanism, local scaling
            limit or Lorentzian metric limit.
          </p>
          <p>
            For the matched control, a four-subset has two lower and two upper
            labels with probability 6/16. Exactly two cross-edge matchings
            produce 2+2, giving E[t₂₂] = (6/16)·2q²(1−q)² = 1/24. This equality
            does not imply equality of the full order laws.
          </p>
        </details>
        <div className="source-list">
          <a href={sourceUrl("docs/BACKGROUND_FREE_GROWTH_THEORY.md")}>
            Exact derivations and control law ↗
          </a>
          <a href="https://nicholasgeorgiou.webspace.durham.ac.uk/wp-content/uploads/sites/199/2021/04/contlim.pdf">
            Brightwell–Georgiou: original continuum-limit theorem ↗
          </a>
          <a href={sourceUrl("docs/BACKGROUND_FREE_GROWTH_RESULTS.md")}>
            Archived finite results and adverse controls ↗
          </a>
        </div>
      </div>
    </LabFrame>
  );
}
