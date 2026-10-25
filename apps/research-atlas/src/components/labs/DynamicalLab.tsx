import { useState } from "react";
import type { DataRow } from "../../data/types";
import { sourceUrl } from "../../data/editorial";
import { Stat } from "./Shared";
import {
  ArchivedFrame, EvidenceLoading, EvidenceMeter, evidenceFormat, evidenceNumber,
  useArchivedEvidence,
} from "./QuantumLab";

const dynamicalDatasets = ["dynamical-primary", "dynamical-conditioned", "dynamical-response"];
const cells = [
  { mu: 2, gamma: 0.25 }, { mu: 2, gamma: 1 },
  { mu: 0.1, gamma: 0.25 }, { mu: 0.1, gamma: 1 },
  { mu: -2, gamma: 0.25 }, { mu: -2, gamma: 1 },
];
const gates = [
  { key: "C", title: "Connected", explanation: "At least 80% of the Born graph probability must be connected at each of ages 2, 3 and 4. One attractive connected graph is insufficient." },
  { key: "L", title: "Concentrated response", explanation: "The strongest two targets must capture at least 80% of each source's response on average, with mean cross-site response at least 0.01, at both delays 0.25 and 0.5. Fractional ties prevent arbitrary label choices." },
  { key: "T", title: "Stable", explanation: "Both late graph-law changes must have total variation at most 0.1. A 5% increase in link-flip strength must also retain the locality conditions and at least 80% neighborhood overlap." },
  { key: "D", title: "Dynamically improved", explanation: "Response concentration must improve by at least 0.1 over the paired experiment with links frozen from the start, at both registered delays." },
] as const;

function completeMean(rows: DataRow[], key: string): number | null {
  if (!rows.length) return null;
  const values = rows.map((row) => evidenceNumber(row, key));
  if (values.some((value) => value === null)) return null;
  return values.reduce<number>((sum, value) => sum + (value ?? 0), 0) / values.length;
}
function probability(value: number | null): string {
  return value === null ? "Not available" : `${(value * 100).toFixed(2)}%`;
}

export function DynamicalLab() {
  const evidence = useArchivedEvidence(dynamicalDatasets);
  const [n, setN] = useState(5);
  const [cell, setCell] = useState(0);
  const [gate, setGate] = useState<string>("C");
  const [preparation, setPreparation] = useState("E");
  const [delay, setDelay] = useState(0.25);
  const decision = evidence.datasets?.[0].rows.find((row) => row.N === n && row.cell === cell);
  const comparison = (law: string) => evidence.datasets?.[1].rows.find((row) =>
    row.N === n && row.cell === cell && row.preparation === preparation && row.delay === delay && row.law === law);
  const born = comparison("Born");
  const degree = comparison("degree");
  const responses = evidence.datasets?.[2].rows.filter((row) =>
    row.N === n && row.cell === cell && row.preparation === preparation && row.delay === delay) ?? [];
  const currentGate = gates.find((item) => item.key === gate)!;
  const validMass = evidenceNumber(born, "valid_graph_F_probability_mean");
  const bounds = evidenceNumber(decision, "upper");
  const parameters = cells[cell];
  return <ArchivedFrame title="Which condition fails when links can change?"
    subtitle="Explore the frozen six-setting study. Every gate was specified before the primary experiment. Graph drawings do not enter this decision.">
    <div className="lab-controls">
      <label className="lab-field">Matter vertices
        <select aria-label="Dynamical system size" value={n} onChange={(e) => setN(Number(e.target.value))}>
          <option value={4}>4 vertices · 10 total qubits</option>
          <option value={5}>5 vertices · 15 total qubits</option>
        </select>
      </label>
      <label className="lab-field">Registered parameter setting
        <select aria-label="Dynamical parameter setting" value={cell} onChange={(e) => setCell(Number(e.target.value))}>
          {cells.map((setting, index) => <option value={index} key={index}>Cell {index} · μ={setting.mu}, Γ={setting.gamma}</option>)}
        </select>
      </label>
    </div>
    {!evidence.datasets ? <EvidenceLoading failed={evidence.failed} retry={evidence.retry} /> : <>
      <div className="lab-reveal">
        <h4>Registered decision · independent E preparations</h4>
        <p>Cell {cell}: μ={parameters.mu}, Γ={parameters.gamma}; h=g=U=1. Each entire exchangeable preparation is one statistical unit. Its targets, times and measured graphs do not increase the sample size.</p>
        <div className="lab-stats" role="status">
          <Stat label="Joint successes" value={`${decision?.successes ?? "—"} / ${decision?.attempted ?? "—"}`} detail="The same preparation must satisfy C, L, T and D" />
          <Stat label="Simultaneous upper probability bound" value={probability(bounds)} detail="Exact binomial bound, family size 12, total α=0.05" />
          <Stat label="Required advancement probability" value="80%" detail="Fixed before primary data; not a slider to tune" />
        </div>
        <p className="lab-insight"><strong>{decision?.assessment === "fails" ? "The registered joint screen is rejected." : "Read the archived cell assessment."}</strong> At this workload, even 12/12 successes could not certify advancement. The observed 0/12 can reject the specified 80% target. Continuum behavior remains unresolved.</p>
      </div>
      <div className="evidence-gate-list" role="group" aria-label="Inspect a registered condition">
        {gates.map((item) => <button key={item.key} className={`evidence-gate${gate === item.key ? " is-active" : ""}`}
          aria-pressed={gate === item.key} onClick={() => setGate(item.key)}>
          <span>{item.key}</span><strong>{item.title}</strong>
          <span>{decision?.[item.key] ?? "—"} / {decision?.attempted ?? "—"} successes</span>
        </button>)}
      </div>
      <div className="lab-reveal" aria-live="polite"><h4>{currentGate.key} · {currentGate.title}</h4><p>{currentGate.explanation}</p>
        <p>Individual gate counts are descriptive. Passing one gate does not pass the joint screen.</p>
      </div>
      <div className="lab-heading"><h3>What changes when a graph record is available?</h3>
        <p>The actual evolving system and fresh-matter frozen-graph controls are different experiments. Compare their archived responses without replacing one with the other.</p>
      </div>
      <div className="lab-controls">
        <label className="lab-field">Preparation for response comparison
          <select aria-label="Dynamical response preparation" value={preparation} onChange={(e) => setPreparation(e.target.value)}>
            <option value="E">E · exchangeable preparations</option>
            <option value="Splus">Splus · symmetric link superposition</option>
            <option value="Sempty">Sempty · initially absent links</option>
          </select>
        </label>
        <label className="lab-field">Response delay after age 2
          <select aria-label="Dynamical response delay" value={delay} onChange={(e) => setDelay(Number(e.target.value))}>
            <option value={0.25}>0.25 simulation-time units</option><option value={0.5}>0.5 simulation-time units</option>
          </select>
        </label>
      </div>
      <p className="lab-insight">{preparation === "E"
        ? "This panel shows arithmetic means over the 12 independent E preparations. These are descriptive means, not new confidence intervals."
        : "This panel shows one deterministic symmetric preparation. It has no independent ensemble confidence interval. The registered gate counts above still refer to E preparations."}</p>
      <div className="evidence-lab-grid">
        <div className="lab-reveal">
          <h4>Actual evolving quantum links</h4>
          <EvidenceMeter label="Full-system response concentration F" value={completeMean(responses, "F")}
            detail="The original aged state, unobserved links and full Hamiltonian. No graph outcome is selected." />
          <p>Mean cross-site response: <strong>{evidenceFormat(completeMean(responses, "response_mean"))}</strong>.
            Paired initially frozen F: <strong>{evidenceFormat(completeMean(responses, "frozen_F"))}</strong>.</p>
          <p>Uniform target responses give F=2/(N−1)={evidenceFormat(2 / (n - 1))}. F measures concentration, not the recovery of known spatial neighbors.</p>
        </div>
        <div className="lab-reveal">
          <h4>Fresh matter on frozen graph controls</h4>
          <EvidenceMeter label="No graph record: F of the mixed-state response"
            value={evidenceNumber(born, "F_of_unobserved_mixture_response_mean")}
            detail="Average target states first, then calculate distinguishability and F." />
          <EvidenceMeter label="Average graph-resolved response, then F"
            value={evidenceNumber(born, "F_of_average_conditional_response_mean")}
            detail="Calculate each graph's response first, then average responses with the Born weights." />
          <EvidenceMeter label="Graph-adapted F, conditional on being defined"
            value={evidenceNumber(born, "mean_graph_conditioned_F_given_valid_mean")}
            detail="Choose the strongest targets within each graph before averaging F. Undefined graph mass is reported below." />
        </div>
      </div>
      <div className="lab-stats">
        <Stat label="Born mass with defined graph-adapted F" value={probability(validMass)} detail="Graphs with zero-response sources can make F undefined" />
        <Stat label="Connected Born mass" value={probability(evidenceNumber(born, "connected_probability_mean"))} detail="Connected does not imply geometric" />
        <Stat label="Degree-null graph-adapted F" value={evidenceFormat(evidenceNumber(degree, "mean_graph_conditioned_F_given_valid_mean"))} detail="Separate conditioning under the degree-matched graph law" />
      </div>
      <p className="lab-insight">A high conditional F may describe a tiny portion of the Born law, disconnected components, or structure reproduced by the degree null. Access to a graph record changes the operational question. These controls reset matter and freeze links; they do not demonstrate persistent relational locality in the evolving quantum state.</p>
      <p className="evidence-source"><a href={evidence.datasets[0].sourceUrl}>Registered gate counts</a> · <a href={evidence.datasets[2].sourceUrl}>Recorded quantum responses</a> · <a href={evidence.datasets[1].sourceUrl}>Conditional-control summary</a> · <a href={sourceUrl("docs/DYNAMICAL_LOCALITY_RESULTS.md")}>Scope and full report</a></p>
    </>}
  </ArchivedFrame>;
}
