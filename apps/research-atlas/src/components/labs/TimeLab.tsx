import { useMemo, useState } from "react";
import {
  emptyOrder,
  fraction,
  longestChain,
  timeSample,
} from "../../lib/simulation";
import { fmt, Graph, LabFrame, pct, Seed, Stat, Toggle } from "./Shared";
export function TimeLab() {
  const [density, setDensity] = useState(64),
    [seed, setSeed] = useState(20261025),
    [coordinates, setCoordinates] = useState(true),
    [edges, setEdges] = useState(true),
    [chainOn, setChainOn] = useState(true),
    [control, setControl] = useState("diamond");
  const sample = useMemo(() => timeSample(density, seed), [density, seed]);
  const order = useMemo(
    () =>
      control === "total"
        ? sample.order.map((r, i) => r.map((_, j) => i < j))
        : control === "antichain"
          ? emptyOrder(sample.points.length)
          : sample.order,
    [control, sample],
  );
  const chain = useMemo(() => longestChain(order), [order]),
    estimate = chain.length / Math.sqrt(2 * density);
  return (
    <LabFrame
      title="A clock made of relationships"
      subtitle="Each event is a point. A chain is a sequence in which every event can influence the next. Count the longest one."
    >
      <div className="lab-controls">
        <label className="lab-field lab-range">
          Density ρ <strong>{density}</strong>
          <input
            aria-label="Sampling density"
            type="range"
            min="8"
            max="160"
            step="8"
            value={density}
            onChange={(e) => setDensity(+e.target.value)}
          />
        </label>
        <Seed value={seed} onChange={setSeed} />
        <button onClick={() => setSeed(seed + 1)}>New sprinkle</button>
        <label className="lab-field">
          Model
          <select
            aria-label="Time model"
            value={control}
            onChange={(e) => setControl(e.target.value)}
          >
            <option value="diamond">Minkowski diamond</option>
            <option value="total">Total-order control</option>
            <option value="antichain">Antichain control</option>
          </select>
        </label>
      </div>
      <div className="lab-options">
        <Toggle value={coordinates} onChange={setCoordinates}>
          Show generating coordinates
        </Toggle>
        <Toggle value={edges} onChange={setEdges}>
          Show causal links
        </Toggle>
        <Toggle value={chainOn} onChange={setChainOn}>
          Highlight longest chain
        </Toggle>
      </div>
      <Graph
        order={order}
        points={
          coordinates && control === "diamond" ? sample.points : undefined
        }
        coordinates={coordinates && control === "diamond"}
        showEdges={edges}
        highlighted={chainOn ? chain : []}
        title="Sampled causal diamond and longest chain"
      />
      <div className="lab-stats">
        <Stat
          label="Interior events"
          value={order.length}
          detail={`Poisson mean λ = ρ/2 = ${density / 2}`}
        />
        <Stat
          label="Longest chain L"
          value={chain.length}
          detail="Endpoints are not counted"
        />
        <Stat
          label="Reconstructed duration"
          value={fmt(estimate)}
          detail="T̂ = L / √(2ρ)"
        />
        <Stat
          label="Reference duration"
          value={control === "diamond" ? "1.000" : "Not physical"}
          detail={`Comparable pairs: ${pct(fraction(order))}`}
        />
      </div>
      <p className="lab-insight">
        {control === "diamond"
          ? "The order-only algorithm receives the relation matrix, not coordinates. Hiding coordinates changes only the drawing. At finite density, this asymptotic clock is biased; one sprinkle cannot establish the ensemble trend or a confidence interval."
          : "Applying the geometric formula to an arbitrary order still returns a number. That number is not a physical elapsed time: these controls violate the sampling assumptions."}
      </p>
    </LabFrame>
  );
}
