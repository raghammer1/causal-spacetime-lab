import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, ArrowUpRight, Check } from "lucide-react";
import { sourceUrl } from "../data/editorial";
import { useReadingLevel } from "../components/ReadingLevel";

const readings = {
  explorer: "We learned how relationships can retain information about geometry that was supplied to a model. We did not show that physical space creates itself. The final test failed, and this research programme ends here.",
  engineer: "Reconstruction succeeded under stated sampling or interaction assumptions, while counterexamples exposed information loss. Classical growth and the tested quantum laws failed their advancement conditions. No additional simulation is planned.",
  researcher: "Selected summaries are non-identifying; causal reconstruction remains conditional on a geometric class and volume law. The registered finite unconditioned quantum-locality screen rejects every tested cell. Relational sectors and controlled continuum limits remain unresolved, without positive evidence for further simulation-led pursuit.",
};
const evidence = {
  established: {
    label: "What survives",
    status: "MATHEMATICS & RECORDED EVIDENCE",
    intro: "Useful results remain useful when the physical hypothesis does not advance. These are conditional reconstructions and exact limitations, not a new theory of spacetime.",
    items: [
      { title: "Relationships can retain geometric information", text: "Causal order recovers aspects of supplied time and dimension under the stated sampling laws. Local interval structure adds information that global summaries discard.", experiment: 4 },
      { title: "Some ambiguities are exact", text: "Two random rankings and a uniform two-dimensional causal diamond have the same full-order law. Other exact counterexamples share every selected summary while differing structurally.", experiment: 3 },
      { title: "Quantum correlations reveal supplied interactions", text: "All 72 registered h=1 hidden-chain cases recovered the known bonds. That is a successful reconstruction of a structure already present in the Hamiltonian.", experiment: 6 },
      { title: "Symmetry and response constrain the interpretation", text: "Finite symmetric states retain equal labelled target responses. Exact fragmentation limits and direct-influence identities explain why changing links alone do not establish local geometry.", experiment: 7 },
    ],
  },
  failed: {
    label: "What failed",
    status: "FAILED CLAIMS WITHIN THEIR TESTED SCOPE",
    intro: "A negative result needs the same care as a positive one. The archive preserves adverse outcomes, failed searches, calibration limitations and rejected timing pilots.",
    items: [
      { title: "A reliable geometric certificate from selected statistics", text: "All six Experiment 3 detectors failed the advancement benchmark. Artificial orders passed, while legitimate samples with different boundaries could be rejected.", experiment: 3 },
      { title: "The tested classical growth route", text: "All six fixed-p candidates failed the registered flat local-law benchmark. Published restrictions apply to the stated classical class and convergence notion, not every causal dynamics.", experiment: 5 },
      { title: "Geometry beyond fixed quantum interactions", text: "Random all-to-all models failed required physical-null advantages at n=6 and n=10 despite passing a descriptive proximity screen. Attractive layouts did not establish emergence.", experiment: 6 },
      { title: "Dynamically organised locality in the final finite test", text: "Every size/parameter cell had zero joint successes out of 12 independent preparations. Each simultaneous upper success-probability bound was 0.402190, below the required 0.8.", experiment: 7 },
    ],
  },
  unresolved: {
    label: "What remains open",
    status: "UNRESOLVED · NOT EVIDENCE FOR THIS MODEL",
    intro: "Logical possibilities remain, but they do not justify continuing this programme. Four or five vertices cannot settle continuum physics.",
    items: [
      { title: "Other laws and relational observables", text: "A symmetry-preserving quantum state may have relational graph structure. Conditioning on a graph record answers a different operational question from our unconditioned target-only test.", experiment: 7 },
      { title: "A controlled continuum limit", text: "A justified sequence of states and laws, energy scaling, coarse-graining, nondegenerate geometry and effective propagation bounds would be required. None was established here.", experiment: 7 },
      { title: "Physical spacetime, gravity and black holes", text: "No experiment derived Einstein dynamics, emergent time or an astrophysical black-hole interior. Finite numerical values do not resolve a gravitational singularity.", experiment: 7 },
    ],
  },
};
type EvidenceView = keyof typeof evidence;

export default function Synthesis() {
  const [view, setView] = useState<EvidenceView>("established");
  const { level } = useReadingLevel();
  const selected = evidence[view];
  return (
    <div className="container synthesis-page">
      <header className="page-head">
        <p className="eyebrow">SEVEN EXPERIMENTS / THE FINAL RESEARCH SYNTHESIS</p>
        <h1>A question explored.<br /><em>A programme complete.</em></h1>
        <p>{readings[level]}</p>
      </header>

      <section className="final-decision" aria-labelledby="final-decision-heading">
        <div className="decision-letter" aria-hidden="true">B</div>
        <div>
          <p className="eyebrow">OVERALL CONCLUSION B · PROGRAMME CLOSED</p>
          <h2 id="final-decision-heading">Useful research.<br /><em>Insufficient physical evidence.</em></h2>
          <p>Useful mathematical and computational research, but insufficient evidence
            to pursue the physical hypothesis through more simulations.</p>
          <p>No Experiment 8 is planned. The records remain available so the results,
            assumptions and failures can be inspected independently.</p>
          <a className="text-link" href={sourceUrl("docs/FINAL_RESEARCH_SYNTHESIS.md")}>Read the complete synthesis <ArrowUpRight size={16} /></a>
        </div>
      </section>

      <section className="synthesis-section" aria-labelledby="final-test-heading">
        <div className="section-heading small">
          <div><p className="eyebrow">THE FINAL TEST / EXPERIMENT 07</p>
            <h2 id="final-test-heading">Changing links.<br /><em>No registered locality success.</em></h2></div>
          <span className="tag red">FINITE BENCHMARK: NO-GO</span>
        </div>
        <div className="final-test-grid">
          <div className="final-test-number"><strong>0 / 12</strong><span>joint successes in each of 12 size/parameter cells</span></div>
          <div>
            <p>At N=4 and N=5, evolving quantum links produced correlated graph laws and
              measurement backaction. Those effects did not satisfy the joint requirements
              for connectedness, concentrated response, stability and improvement over frozen links.</p>
            <p>The simultaneous exact upper probability bound was <strong>0.402190</strong>
              {" "}against a required <strong>0.8</strong>. All required controls passed.
              Larger-size geometric scaling remains unresolved; this is not a universal
              impossibility theorem.</p>
            <Link className="text-link" to="/experiment/7">Inspect the final experiment <ArrowRight size={16} /></Link>
          </div>
        </div>
      </section>

      <section className="synthesis-section" aria-labelledby="evidence-ledger-heading">
        <p className="eyebrow">WHAT ALL SEVEN EXPERIMENTS TAUGHT US</p>
        <h2 id="evidence-ledger-heading">Keep the distinctions <em>visible.</em></h2>
        <div className="synthesis-views" role="group" aria-label="Research conclusions">
          {(Object.keys(evidence) as EvidenceView[]).map(key => (
            <button key={key} aria-pressed={view === key} onClick={() => setView(key)}>{evidence[key].label}</button>
          ))}
        </div>
        <div className="synthesis-evidence" aria-live="polite">
          <p className="eyebrow">{selected.status}</p>
          <p className="synthesis-intro">{selected.intro}</p>
          <div className="synthesis-findings">
            {selected.items.map((item, i) => (
              <article key={item.title}>
                <span className="finding-index">{String(i + 1).padStart(2, "0")}</span>
                <div><h3>{item.title}</h3><p>{item.text}</p>
                  <Link className="source-link" to={"/experiment/" + item.experiment}>Experiment {item.experiment} <ArrowUpRight size={13} /></Link></div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="synthesis-section synthesis-record" aria-labelledby="preserved-record-heading">
        <div>
          <p className="eyebrow">THE EVIDENCE STAYS OPEN</p>
          <h2 id="preserved-record-heading">A complete record,<br /><em>including the failures.</em></h2>
          <p>Independent audits checked the decisive quantities. A frozen-source replay
            reproduced all 238 final-experiment scientific artifacts byte for byte.
            Replay verifies reproducibility; it is not an additional independent cohort.</p>
          <a className="text-link" href={sourceUrl("docs/DYNAMICAL_LOCALITY_RESULTS.md")}>Methods, uncertainty and audits <ArrowUpRight size={16} /></a>
        </div>
        <ul className="preserved-list">
          {[
            "Seven experiments, their protocols and raw archives",
            "Exact counterexamples and negative findings",
            "Failed searches, calibration limits and resource decisions",
            "Source hashes, independent checks and reproducible figures",
          ].map(text => <li key={text}><Check size={18} aria-hidden="true" /><span>{text}</span></li>)}
        </ul>
      </section>

      <section className="scope-statement synthesis-stopping-rule">
        <p className="eyebrow">A STOPPING RULE, NOT ANOTHER EXPERIMENT</p>
        <h2>What would justify <em>returning?</em></h2>
        <p>An independently motivated physical principle, a controlled mathematical
          derivation or a discriminating empirical prediction. Another attractive graph,
          fitted classifier or speculative Hamiltonian would not be enough.</p>
        <p>The water analogy remains a useful question. Unlike water’s molecules,
          these proposed microscopic constituents have not gained independent
          physical support from our simulations.</p>
        <div className="synthesis-links">
          <Link className="button" to="/journey">Revisit the full journey <ArrowRight size={16} /></Link>
          <Link className="text-link" to="/data">Explore the preserved data <ArrowUpRight size={16} /></Link>
        </div>
      </section>
    </div>
  );
}
