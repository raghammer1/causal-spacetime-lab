import { useMemo, useState } from "react";
import {
  diamondSample,
  estimateDimension,
  fraction,
  layered,
  orderingProbability,
  random,
} from "../../lib/simulation";
import { fmt, Graph, LabFrame, pct, Seed, Stat, Toggle } from "./Shared";
export function DimensionLab() {
  const [seed, setSeed] = useState(20261025),
    [guess, setGuess] = useState<number | null>(null),
    [revealed, setRevealed] = useState(false),
    [adversary, setAdversary] = useState(false),
    [projection, setProjection] = useState(false);
  const dimension = useMemo(
    () => 2 + Math.floor(random(seed + 919)() * 3),
    [seed],
  );
  const sample = useMemo(
    () => diamondSample(dimension, 48, seed),
    [dimension, seed],
  );
  const order = useMemo(
    () =>
      adversary
        ? layered(48, orderingProbability(dimension), seed)
        : sample.order,
    [adversary, dimension, seed, sample],
  );
  const r = fraction(order),
    estimate = estimateDimension(r);
  const reset = (s: number) => {
    setSeed(s);
    setRevealed(false);
    setGuess(null);
    setProjection(false);
  };
  return (
    <LabFrame
      title="Guess the hidden dimension"
      subtitle="The generator knows the geometry. You see only an order. More dimensions give pairs more ways to be causally unrelated."
    >
      <div className="lab-controls">
        <Seed value={seed} onChange={reset} />
        <button onClick={() => reset(seed + 1)}>New mystery sample</button>
        <Toggle
          value={adversary}
          onChange={(v) => {
            setAdversary(v);
            setRevealed(false);
          }}
        >
          Use a fraction-matched artificial order
        </Toggle>
      </div>
      <Graph
        order={order}
        points={
          revealed && projection && !adversary ? sample.points : undefined
        }
        coordinates={revealed && projection && !adversary}
        title="Hidden-dimension causal structure"
      />
      <div className="lab-game">
        <span>Your guess:</span>
        {[2, 3, 4].map((d) => (
          <button
            aria-pressed={guess === d}
            className={guess === d ? "is-active" : ""}
            key={d}
            onClick={() => setGuess(d)}
          >
            {d} dimensions
          </button>
        ))}
        <button
          className="lab-primary"
          disabled={guess === null}
          onClick={() => setRevealed(true)}
        >
          Reveal the model
        </button>
      </div>
      {revealed && (
        <div className="lab-reveal" role="status">
          <h4>
            {adversary
              ? `A two-layer impostor targeting d=${dimension}`
              : `${guess === dimension ? "Correct" : "A useful surprise"}: ${dimension}-dimensional Minkowski sampling`}
          </h4>
          <div className="lab-stats">
            <Stat
              label="Ordering fraction r"
              value={pct(r)}
              detail="Related pairs / all unordered pairs"
            />
            <Stat
              label="Analytical target"
              value={pct(orderingProbability(dimension))}
              detail="Ensemble expectation, not a threshold"
            />
            <Stat
              label="Inferred dimension"
              value={fmt(estimate)}
              detail="Myrheim–Meyer inverse on [1,10]"
            />
          </div>
          <p>
            {adversary
              ? "The fraction was targeted in expectation; a finite realization varies. Every chain still has at most two events. A plausible dimension estimate does not certify geometry."
              : "This is one independent N=48 sample. Pair indicators share events, so a binomial confidence interval over pairs would be invalid. See the archived independent-order bootstrap intervals below."}
          </p>
          {!adversary && (
            <>
              <Toggle value={projection} onChange={setProjection}>
                Reveal a time / first-space-coordinate projection
              </Toggle>
              {projection && (
                <p>
                  Projection only:{" "}
                  {dimension > 2
                    ? `${dimension - 2} spatial coordinate${dimension > 3 ? "s are" : " is"} hidden. Lines follow the full ${dimension}D metric.`
                    : "This 1+1D view shows all generating coordinates."}
                </p>
              )}
            </>
          )}
        </div>
      )}
      <p className="lab-equation">
        E[r] = Γ(d+1)Γ(d/2) / [2Γ(3d/2)] &nbsp; · &nbsp; d=2: 50% &nbsp; d=3:
        22.86% &nbsp; d=4: 10%
      </p>
    </LabFrame>
  );
}
