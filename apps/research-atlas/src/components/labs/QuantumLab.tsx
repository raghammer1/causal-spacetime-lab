import { useEffect, useState, type ReactNode } from "react";
import { loadDataset } from "../../data/loader";
import type { DataRow, Dataset } from "../../data/types";
import { sourceUrl } from "../../data/editorial";
import { Stat } from "./Shared";

const quantumDatasets = ["quantum-summary", "quantum-chain", "quantum-calibration"];

/** A view of saved evidence: no state evolution or scientific fitting runs here. */
export function useArchivedEvidence(ids: readonly string[]) {
  const [datasets, setDatasets] = useState<Dataset[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    Promise.all(ids.map(loadDataset)).then((data) => {
      if (active) { setDatasets(data); setFailed(false); }
    }).catch(() => { if (active) setFailed(true); });
    return () => { active = false; };
  }, [ids, attempt]);
  return { datasets, failed, retry: () => { setFailed(false); setAttempt((n) => n + 1); } };
}

export function ArchivedFrame({ title, subtitle, children }: {
  title: string; subtitle: string; children: ReactNode;
}) {
  return <section className="lab-frame evidence-lab" aria-label={title}>
    <div className="lab-heading">
      <span className="lab-live">ARCHIVED EVIDENCE · INTERACTIVE READING</span>
      <h3>{title}</h3><p>{subtitle}</p>
    </div>
    {children}
    <p className="lab-footnote">Recorded numerical evidence • controls change the view only • no browser quantum simulation • no physical spacetime claim.</p>
  </section>;
}

export function EvidenceLoading({ failed, retry }: { failed: boolean; retry: () => void }) {
  return failed ? <div role="alert" className="lab-reveal">
    <p>The archived evidence could not load.</p><button onClick={retry}>Retry evidence</button>
  </div> : <p role="status">Loading the archived evidence…</p>;
}

export function evidenceNumber(row: DataRow | undefined, key: string): number | null {
  const value = row?.[key];
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}
export function evidenceFormat(value: number | null, digits = 3): string {
  if (value === null) return "Not available";
  if (value !== 0 && Math.abs(value) < 0.0001) return value.toExponential(2);
  return value.toFixed(digits);
}

export function EvidenceMeter({ label, value, detail }: {
  label: string; value: number | null; detail: string;
}) {
  return <div className="evidence-meter">
    <div><strong>{label}</strong><span>{evidenceFormat(value)}</span></div>
    {value !== null && <meter min={0} max={1} value={value} aria-label={label} />}
    <p>{detail}</p>
  </div>;
}

export function QuantumLab() {
  const evidence = useArchivedEvidence(quantumDatasets);
  const [family, setFamily] = useState("chain");
  const [n, setN] = useState(8);
  const [h, setH] = useState(1);
  const [question, setQuestion] = useState<"recovery" | "null">("recovery");
  const rows = evidence.datasets?.[0].rows.filter((r) =>
    r.family === family && r.n === n && r.h === h && r.preparation === "ground" && r.delta === 0 && r.time === 0) ?? [];
  const metric = (name: string) => rows.find((r) => r.metric === name);
  const mean = (name: string) => evidenceNumber(metric(name), "mean");
  const chain = evidence.datasets?.[1].rows.find((r) =>
    r.n === n && r.h === h && r.delta === 0 && r.preparation === "ground" && r.time === 0);
  const calibration = evidence.datasets?.[2].rows.find((row) => row.method === "normal_percentile_bootstrap");
  const coverage = evidenceNumber(calibration, "coverage");
  const calibrationTrials = evidenceNumber(calibration, "trials");
  const nominalCoverage = evidenceNumber(calibration, "nominal_coverage");
  const supplied = family === "chain"
    ? "A chain of interactions is supplied, then its labels are hidden. Recovering its bonds tests reconstruction of known locality."
    : family === "A"
      ? "Every pair has the same supplied coupling. The unique finite ground state is permutation symmetric: it cannot select distinct labeled neighbors."
      : "Every pair has a supplied random coupling. Irregular information patterns can inherit those interactions; asymmetry alone is not emergent geometry.";
  return <ArchivedFrame title="Recovering a pattern is not creating space."
    subtitle="Choose a fixed-interaction model and inspect its recorded ground-state evidence. Mutual information measures shared information; it is not automatically a distance.">
    <div className="lab-controls">
      <label className="lab-field">Interaction model
        <select aria-label="Quantum interaction model" value={family} onChange={(e) => setFamily(e.target.value)}>
          <option value="chain">Hidden chain · supplied locality</option>
          <option value="A">A · uniform all-to-all</option>
          <option value="B">B · random all-to-all</option>
        </select>
      </label>
      <label className="lab-field">Matter qubits
        <select aria-label="Quantum system size" value={n} onChange={(e) => setN(Number(e.target.value))}>
          {[6, 8, 10].map((value) => <option key={value} value={value}>{value}</option>)}
        </select>
      </label>
      <label className="lab-field">Transverse field h
        <select aria-label="Quantum transverse field" value={h} onChange={(e) => setH(Number(e.target.value))}>
          {[0.5, 1, 2].map((value) => <option key={value} value={value}>{value}{value === 1 ? " · registered comparison" : " · secondary check"}</option>)}
        </select>
      </label>
    </div>
    {!evidence.datasets ? <EvidenceLoading failed={evidence.failed} retry={evidence.retry} /> : <>
      <p className="lab-insight" role="status">{supplied}</p>
      <div className="lab-stats">
        <Stat label="Pair-information contrast" value={evidenceFormat(mean("mi_contrast"))} detail="Largest minus smallest pair MI, in bits" />
        <Stat label="Three-dimensional layout mismatch" value={evidenceFormat(mean("stress_d3"))}
          detail={family === "A" ? "Basis-dependent truncated MDS result; see notice below" : "Recorded embedding stress; smaller does not certify geometry"} />
        <Stat label={family === "A" ? "Deterministic ground state" : "Independent coupling realizations"}
          value={evidenceNumber(metric("mi_contrast"), "independent_units") ?? "Not available"}
          detail={family === "A" ? "One state; no ensemble confidence interval" : "Pairs and null replicates are dependent within a realization"} />
      </div>
      {family === "A" && <p className="lab-insight" role="note">Uniform Model A has a degenerate MDS eigenspace. Its truncated three-dimensional stress and shuffle contrasts depend on an arbitrary basis and cannot support structural conclusions.</p>}
      <div className="lab-controls" role="group" aria-label="Quantum evidence question">
        <button aria-pressed={question === "recovery"} className={question === "recovery" ? "is-active" : ""} onClick={() => setQuestion("recovery")}>What was recovered?</button>
        <button aria-pressed={question === "null"} className={question === "null" ? "is-active" : ""} onClick={() => setQuestion("null")}>What do the null controls change?</button>
      </div>
      {question === "recovery" ? <div className="lab-reveal">
        {family === "chain" ? <>
          <div className="evidence-comparison">
            <EvidenceMeter label="Recovered supplied bonds" value={mean("edge_recall_top_n_minus_1")} detail="Fraction of the known chain bonds among the strongest n−1 MI pairs." />
            <EvidenceMeter label="Bond-ranking AUC" value={mean("edge_auc")} detail="AUC=1 places every supplied bond ahead of every nonbond." />
          </div>
          {chain ? <p>Recorded chain-screen successes: <strong>{chain.successes}/{chain.attempted}</strong>.
            Exact lower success-probability bound: <strong>{evidenceFormat(evidenceNumber(chain, "lower"))}</strong>.</p>
            : <p>No registered chain-success bound for this secondary field setting. The recovery metrics remain recorded evidence, not the registered h=1 advancement result.</p>}
          <p>The interaction chain was an input. Successful recovery does not show that a chain formed dynamically.</p>
        </> : <>
          <h4>{family === "A" ? "Equal information leaves no labeled neighborhood." : "A varied pattern still needs an explanation."}</h4>
          {family === "B" && <p>Recorded MI–coupling rank correlation: <strong>{evidenceFormat(mean("spearman_mi_coupling"))}</strong>.
            This compares the information pattern with the magnitudes of the supplied interactions.</p>}
          <p>Recorded triangle-inequality violation fraction: <strong>{evidenceFormat(mean("triangle_violation_fraction"))}</strong>.
            Even zero violations in one construction would not establish a physical metric or spatial dimension.</p>
          <p>Uniform MI, a low-stress drawing, and reconstruction of supplied couplings answer different mathematical questions.</p>
        </>}
      </div> : <div className="lab-reveal">
        <h4>A favorable drawing must survive appropriate nulls.</h4>
        <p>Positive effects below mean the original state has lower layout stress than its null control. Phase scrambling gives valid quantum states; shuffling pair entries need not.</p>
        {family === "A" && <p>Model A's recorded truncated-layout stress and shuffle contrasts are basis-dependent. They cannot support structural conclusions.</p>}
        <div className="evidence-table-wrap">
          <table className="evidence-table"><caption>Recorded paired layout-stress effects</caption>
            <thead><tr><th scope="col">Null control</th><th scope="col">Mean effect</th><th scope="col">Archived nominal lower bound</th><th scope="col">Registered h=1 margin</th></tr></thead>
            <tbody>{[
              ["phase_minus_stress_d3", "Physical phase scramble", "0.01"],
              ["shuffle_minus_stress_d3", "Shuffled pair entries", "0.05"],
            ].map(([name, label, margin]) => <tr key={name}><th scope="row">{label}</th>
              <td>{evidenceFormat(mean(name))}</td><td>{evidenceFormat(evidenceNumber(metric(name), "lower"))}</td><td>{margin}</td></tr>)}</tbody>
          </table>
        </div>
        <p>Missing entries mean this comparison is not available for the selected state. These nominal bootstrap bounds undercovered in calibration; they are not validated confidence guarantees.</p>
        <p>At h=1, model B misses the required phase-null advantage at n=6 and n=10. A favorable comparison at n=8 does not pass the joint advancement benchmark.</p>
      </div>}
      <p className="lab-insight">{coverage !== null && calibrationTrials !== null && nominalCoverage !== null
        ? `Retained calibration failure: nominal ${(nominalCoverage * 100).toFixed(0)}% intervals covered ${Math.round(coverage * calibrationTrials)} of ${calibrationTrials} calibration means (${(coverage * 100).toFixed(2)}%).`
        : "The calibration coverage record is unavailable in this view."} Exact chain-success bounds use a separate binomial calculation. No geometric advancement was established.</p>
      <p className="evidence-source"><a href={evidence.datasets[0].sourceUrl}>Archived quantum measurements</a> · <a href={evidence.datasets[2].sourceUrl}>Calibration record</a> · <a href={sourceUrl("docs/QUANTUM_EMERGENCE_RESULTS.md")}>Definitions and full interpretation</a></p>
    </>}
  </ArchivedFrame>;
}
