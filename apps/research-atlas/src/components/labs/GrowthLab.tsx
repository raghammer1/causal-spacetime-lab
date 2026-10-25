import { useEffect, useMemo, useState } from "react";
import {
  fraction,
  growth,
  induced,
  longestChain,
  relationCount,
  twoPlusTwo,
} from "../../lib/simulation";
import { Graph, LabFrame, pct, Seed, Stat, Toggle } from "./Shared";
export function GrowthLab() {
  const [seed, setSeed] = useState(20261025),
    [probability, setProbability] = useState(0.1),
    [count, setCount] = useState(1),
    [playing, setPlaying] = useState(false),
    [inherited, setInherited] = useState(true),
    [selected, setSelected] = useState(0);
  const history = useMemo(
    () => growth(48, probability, seed),
    [probability, seed],
  );
  const indices = useMemo(
    () => Array.from({ length: count }, (_, i) => i),
    [count],
  );
  const order = useMemo(
      () => induced(history.order, indices),
      [history, indices],
    ),
    direct = useMemo(
      () => induced(history.direct, indices),
      [history, indices],
    );
  const observed = Math.min(selected, count - 1),
    directPast = direct.flatMap((row, i) => (row[observed] ? [i + 1] : [])),
    inheritedPast = order.flatMap((row, i) =>
      row[observed] && !direct[i][observed] ? [i + 1] : [],
    );
  useEffect(() => {
    if (!playing) return;
    const timer = window.setInterval(() => {
      setCount((n) => {
        if (n >= 48) {
          setPlaying(false);
          return n;
        }
        return n + 1;
      });
    }, 700);
    return () => window.clearInterval(timer);
  }, [playing]);
  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    const stop = () => {
      if (query.matches) setPlaying(false);
    };
    query.addEventListener("change", stop);
    return () => query.removeEventListener("change", stop);
  }, []);
  const reset = () => {
    setCount(1);
    setSelected(0);
    setPlaying(false);
  };
  const motifTotal =
    count < 4 ? 0 : (count * (count - 1) * (count - 2) * (count - 3)) / 24;
  return (
    <LabFrame
      title="Grow an order. Supply no space."
      subtitle="At each birth, select each earlier event independently with probability p. Inherit every ancestor of the selected events."
    >
      <div className="lab-controls">
        <label className="lab-field">
          Selection probability p
          <select
            aria-label="Growth probability"
            value={probability}
            onChange={(e) => {
              setProbability(+e.target.value);
              reset();
            }}
          >
            {[0.005, 0.01, 0.02, 0.05, 0.1, 0.3].map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </label>
        <Seed
          value={seed}
          onChange={(n) => {
            setSeed(n);
            reset();
          }}
        />
        <button
          className="lab-primary"
          disabled={count === 48}
          onClick={() => {
            setPlaying(false);
            setCount((n) => Math.min(48, n + 1));
          }}
        >
          + One event
        </button>
        <button
          disabled={count === 48 && !playing}
          aria-pressed={playing}
          onClick={() => setPlaying(!playing)}
        >
          {playing ? "Pause growth" : "Auto-play growth"}
        </button>
        <button onClick={reset}>Reset history</button>
      </div>
      <div className="lab-options">
        <Toggle value={inherited} onChange={setInherited}>
          Show inherited relations
        </Toggle>
        <span>
          <i className="lab-key-direct" /> Direct selection{" "}
          <i className="lab-key-inherited" /> Inherited by transitivity
        </span>
      </div>
      <Graph
        order={order}
        direct={direct}
        showInherited={inherited}
        selected={[observed]}
        onSelect={setSelected}
        labels
        title="Growing causal order: solid selections and dashed inherited relationships"
      />
      <div className="lab-stats">
        <Stat label="Events born" value={`${count} / 48`} />
        <Stat
          label="Causal relations"
          value={relationCount(order)}
          detail={`${relationCount(direct)} primitive selections`}
        />
        <Stat label="Chain height" value={longestChain(order).length} />
        <Stat
          label="Induced 2+2 frequency"
          value={
            motifTotal ? pct(twoPlusTwo(order) / motifTotal) : "Not available"
          }
          detail="Exact count in this single small order"
        />
      </div>
      <div className="lab-reveal">
        <label className="lab-field">
          Inspect a birth
          <select
            aria-label="Inspect growth event"
            value={observed}
            onChange={(e) => setSelected(+e.target.value)}
          >
            {indices.map((i) => (
              <option key={i} value={i}>
                Event {i + 1}
              </option>
            ))}
          </select>
        </label>
        <p>
          Event {observed + 1} selected{" "}
          <strong>
            {directPast.length ? directPast.join(", ") : "no earlier events"}
          </strong>
          . Additional inherited ancestors:{" "}
          <strong>
            {inheritedPast.length ? inheritedPast.join(", ") : "none"}
          </strong>
          .
        </p>
        <p>
          Ordering fraction: {pct(fraction(order))}. The birth labels and
          drawing positions are display conventions; they do not assign physical
          space or elapsed time.
        </p>
      </div>
      <p className="lab-insight">
        The d=2 Minkowski ensemble has induced 2+2 expectation 1/24 ≈ 4.17%.
        Crossing that value in one finite history is not passing the registered
        finite signature or establishing a continuum limit. Compare independent
        archived histories below.
      </p>
    </LabFrame>
  );
}
