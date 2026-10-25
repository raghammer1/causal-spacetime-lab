import { useMemo, useState } from "react";
import {
  diamondSample,
  fraction,
  growth,
  intervalHistogram,
  intervalOrder,
  layered,
  longestChain,
  relationCount,
  twoPlusTwo,
} from "../../lib/simulation";
import { Graph, LabFrame, pct, Seed, Stat } from "./Shared";
const detectors = [
  [
    "A",
    "Ordering fraction",
    "How many pairs can influence one another? A two-layer network can target this one number while having no long chains.",
  ],
  [
    "B",
    "Chain height",
    "How many events fit in the longest causal chain? This already rejects the easy height-two controls in the archived experiment.",
  ],
  [
    "C",
    "Fraction + height",
    "Combine standardized pair-density and height residuals with an RMS score. Errors can compensate, and two summaries still discard most of an order.",
  ],
  [
    "D",
    "Five-feature RMS",
    "Average standardized residuals across five selected features. A large error can be diluted by small errors elsewhere.",
  ],
  [
    "E",
    "Five-feature maximum",
    "Use the largest standardized residual, preventing that compensation. This changes acceptance, not the information recorded.",
  ],
  [
    "F",
    "Interval abundance",
    "Compare the distribution of event counts between related endpoint pairs. Different orders can still share that complete histogram.",
  ],
];
const families = [
  ["minkowski", "Minkowski d=2"],
  ["layer", "Fraction-matched two-layer"],
  ["dag", "Random DAG + closure"],
  ["height", "Height-targeted toy search"],
  ["multi", "Two-statistic toy search"],
  ["interval", "Unseen interval order"],
  ["rank", "Rank-two law-equivalent control"],
];
export function AdversarialLab() {
  const [family, setFamily] = useState("layer"),
    [seed, setSeed] = useState(20261025),
    [detector, setDetector] = useState(0);
  const reference = useMemo(() => diamondSample(2, 32, seed).order, [seed]);
  const order = useMemo(() => {
    if (family === "minkowski" || family === "rank")
      return diamondSample(2, 32, seed + 1).order;
    if (family === "layer") return layered(32, 0.5, seed);
    if (family === "interval") return intervalOrder(32, seed);
    if (family === "dag") return growth(32, 0.08, seed).order;
    const height = longestChain(reference).length,
      target = fraction(reference)!;
    let best = growth(32, 0.02, seed).order,
      score = Infinity;
    for (let k = 0; k < 24; k++) {
      const candidate = growth(32, 0.01 + k / 100, seed + k).order;
      const error =
        Math.abs(longestChain(candidate).length - height) +
        (family === "multi" ? 30 * Math.abs(fraction(candidate)! - target) : 0);
      if (error < score) {
        score = error;
        best = candidate;
      }
    }
    return best;
  }, [family, reference, seed]);
  const bins = intervalHistogram(order);
  return (
    <LabFrame
      title="Build an impostor universe"
      subtitle="Choose a generator, then ask what each detector can actually see. A matched summary is evidence about that summary alone."
    >
      <div className="lab-controls">
        <label className="lab-field lab-wide">
          Candidate family
          <select
            aria-label="Adversarial family"
            value={family}
            onChange={(e) => setFamily(e.target.value)}
          >
            {families.map(([id, label]) => (
              <option key={id} value={id}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <Seed value={seed} onChange={setSeed} />
        <button onClick={() => setSeed(seed + 1)}>Resample</button>
      </div>
      <div className="lab-compare">
        <div>
          <h4>Known geometric sample</h4>
          <Graph order={reference} title="Minkowski reference order" />
          <p>
            r = {pct(fraction(reference))} · height{" "}
            {longestChain(reference).length}
          </p>
        </div>
        <div>
          <h4>Selected candidate</h4>
          <Graph order={order} title="Selected adversarial order" />
          <p>
            r = {pct(fraction(order))} · height {longestChain(order).length}
          </p>
        </div>
      </div>
      <div className="lab-detectors" aria-label="Detector explanations">
        {detectors.map(([letter, label], i) => (
          <button
            key={letter}
            aria-pressed={detector === i}
            className={detector === i ? "is-active" : ""}
            onClick={() => setDetector(i)}
          >
            <b>{letter}</b>
            <span>{label}</span>
          </button>
        ))}
      </div>
      <div className="lab-reveal">
        <h4>{detectors[detector][1]}</h4>
        <p>{detectors[detector][2]}</p>
        <div className="lab-stats">
          <Stat label="Related pairs" value={relationCount(order)} />
          <Stat label="Chain height" value={longestChain(order).length} />
          <Stat label="Induced 2+2" value={twoPlusTwo(order)} />
          <Stat label="Empty intervals / links" value={bins[0] || 0} />
        </div>
      </div>
      <p className="lab-insight">
        {family === "rank"
          ? "The rank construction has exactly the same d=2 order law as uniform-null-coordinate sampling, which this panel uses as a distribution-equivalent generator. No order-only detector can separate those distributions. This is a positive equivalence control."
          : family === "height" || family === "multi"
            ? "This miniature search compares 24 seeded percolation candidates to one displayed reference. It illustrates selection over summaries; it is not the registered protected-height or five-feature search, and its outcomes are not archived detector acceptance rates."
            : "These small orders show structure, not detector acceptance decisions. The calibrated, held-out acceptance rates and confidence intervals are recorded below. All six registered detectors failed the advancement benchmark."}
      </p>
    </LabFrame>
  );
}
