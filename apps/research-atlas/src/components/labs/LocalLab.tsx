import { useMemo, useState } from "react";
import {
  components,
  cycleWitness,
  diamondSample,
  estimateDimension,
  fraction,
  induced,
  interval,
  intervalHistogram,
  longestChain,
  minkowskiOrder,
  random,
  relationCount,
  twoPlusTwo,
  type EventPoint,
} from "../../lib/simulation";
import { fmt, Graph, LabFrame, Seed, Stat, Toggle } from "./Shared";
export function LocalLab() {
  const [seed, setSeed] = useState(20261025),
    [region, setRegion] = useState<"diamond" | "slab" | "box">("slab"),
    [pairIndex, setPairIndex] = useState(0),
    [overlap, setOverlap] = useState(false),
    [witness, setWitness] = useState<"global" | "extended">("global"),
    [disconnected, setDisconnected] = useState(false);
  const sample = useMemo(() => {
    if (region === "diamond") return diamondSample(2, 64, seed);
    const rng = random(seed),
      points: EventPoint[] = [];
    if (region === "box") {
      for (let i = 0; i < 64; i++)
        points.push({ t: rng(), x: [0.26 * rng() - 0.13] });
    } else
      while (points.length < 64) {
        const u = rng(),
          v = rng(),
          t = (u + v) / 2;
        if (t >= 0.25 && t <= 0.75) points.push({ t, x: [(u - v) / 2] });
      }
    return { points, order: minkowskiOrder(points) };
  }, [seed, region]);
  const pairs = useMemo(
    () =>
      sample.order
        .flatMap((row, a) =>
          row.flatMap((v, b) =>
            v ? [{ a, b, inside: interval(sample.order, a, b) }] : [],
          ),
        )
        .filter((p) => p.inside.length >= 2)
        .sort(
          (a, b) =>
            Math.abs(a.inside.length - 12) - Math.abs(b.inside.length - 12),
        )
        .slice(0, 32),
    [sample],
  );
  const pair = pairs[Math.min(pairIndex, pairs.length - 1)],
    other = pairs.find(
      (p) =>
        (p.a !== pair?.a || p.b !== pair?.b) &&
        p.inside.some((i) => pair?.inside.includes(i)),
    ),
    inside = pair?.inside || [],
    shared = inside.filter((i) => other?.inside.includes(i));
  const example = useMemo(
      () => cycleWitness(witness, disconnected),
      [witness, disconnected],
    ),
    interior =
      witness === "global"
        ? induced(
            example,
            Array.from({ length: 8 }, (_, i) => i + 1),
          )
        : example;
  return (
    <LabFrame
      title="Look inside a causal interval"
      subtitle="The outside boundary can distort a global statistic. An internal interval can recover a cleaner sampling law—under the right assumptions."
    >
      <div className="lab-controls">
        <label className="lab-field">
          Sampling region
          <select
            aria-label="Sampling region"
            value={region}
            onChange={(e) => {
              setRegion(e.target.value as typeof region);
              setPairIndex(0);
            }}
          >
            <option value="diamond">Flat causal diamond</option>
            <option value="slab">Causally convex slab</option>
            <option value="box">Spatial box (not causally convex)</option>
          </select>
        </label>
        <Seed
          value={seed}
          onChange={(n) => {
            setSeed(n);
            setPairIndex(0);
          }}
        />
        <label className="lab-field">
          Selected endpoints
          <select
            aria-label="Selected causal interval"
            value={Math.min(pairIndex, Math.max(0, pairs.length - 1))}
            onChange={(e) => setPairIndex(+e.target.value)}
          >
            {pairs.map((p, i) => (
              <option key={i} value={i}>
                {p.a + 1} → {p.b + 1} ({p.inside.length} inside)
              </option>
            ))}
          </select>
        </label>
        <Toggle value={overlap} onChange={setOverlap}>
          Compare an overlapping interval
        </Toggle>
      </div>
      <Graph
        order={sample.order}
        points={sample.points}
        boundary={region}
        highlighted={overlap ? shared : inside}
        selected={
          pair
            ? overlap && other
              ? [pair.a, pair.b, other.a, other.b]
              : [pair.a, pair.b]
            : []
        }
        title="Internal causal interval within the selected sampling boundary"
      />
      <div className="lab-stats">
        <Stat
          label="Global inferred dimension"
          value={fmt(estimateDimension(fraction(sample.order)))}
          detail="One N=64 toy sample; true d=2"
        />
        <Stat
          label="Selected interval events"
          value={inside.length}
          detail="Endpoints excluded"
        />
        <Stat
          label="Selected-interval MM estimate"
          value={fmt(
            estimateDimension(fraction(induced(sample.order, inside))),
          )}
          detail="Not the registered pooled m=2 estimator"
        />
        <Stat
          label={overlap ? "Shared interior events" : "Internal components"}
          value={
            overlap
              ? other
                ? shared.length
                : "Not available"
              : components(induced(sample.order, inside))
          }
        />
      </div>
      {overlap && !other && (
        <p className="lab-insight">
          No second displayed interval shares an interior event with this
          selection. Choose different endpoints or a new seed.
        </p>
      )}
      <p className="lab-insight">
        {region === "box"
          ? "A spatial box can clip the complete geometric interval between its endpoints. This toy uses a deliberately narrow box, x ∈ [−0.13, 0.13], t ∈ [0, 1], to make clipping visible; its width differs from the archive. Conditioning on an observed event count does not repair the missing region; the flat-diamond local law need not apply."
          : "Uniform independent sampling in a causally convex flat region gives a flat-diamond internal order law conditional on fixed endpoints and interior count. This toy chooses intervals by count for display; its single estimate is noisy. Overlapping intervals share events and are not independent trials."}
      </p>
      <div className="lab-subsection">
        <h4>Same summaries. Different orders.</h4>
        <div className="lab-controls">
          <label className="lab-field lab-wide">
            Exact counterexample
            <select
              aria-label="Exact counterexample"
              value={witness}
              onChange={(e) => setWitness(e.target.value as typeof witness)}
            >
              <option value="global">
                Old global summaries: local structure separates them
              </option>
              <option value="extended">
                Extended summaries: a stronger identification limit
              </option>
            </select>
          </label>
          <Toggle value={disconnected} onChange={setDisconnected}>
            Show the disconnected interior
          </Toggle>
        </div>
        <Graph
          order={example}
          labels
          title="Exact equal-summary counterexample"
        />
        <div className="lab-stats">
          <Stat
            label="Events / relations"
            value={`${example.length} / ${relationCount(example)}`}
          />
          <Stat label="Height" value={longestChain(example).length} />
          <Stat label="Induced 2+2 count" value={twoPlusTwo(example)} />
          <Stat label="Interior components" value={components(interior)} />
        </div>
        <p>
          Full interval histogram:{" "}
          {intervalHistogram(example)
            .map((v, i) => (v ? `a${i}=${v}` : ""))
            .filter(Boolean)
            .join(", ")}
          .
        </p>
        <p>
          {witness === "global"
            ? "These ten-event orders share event count, relation count, height and the entire interval histogram. Switching the interior changes the induced 2+2 count from 12 to 16 and its connectivity. Local information distinguishes them."
            : "These twelve-event orders share the extended measured summaries, including all induced four-event pattern counts, degree profiles, interval statistics and the 2+2 count (42). Yet one comparability graph is connected and the other has two components. They are nonisomorphic even up to duality."}
        </p>
      </div>
    </LabFrame>
  );
}
