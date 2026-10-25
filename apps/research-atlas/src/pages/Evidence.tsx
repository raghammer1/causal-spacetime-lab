import { useSearchParams, Link } from "react-router-dom";
import { ArrowRight, ArrowUpRight } from "lucide-react";
import { claims, sourceUrl } from "../data/editorial";
const statusLabels = {
  supported: "Supported within assumptions",
  falsified: "Falsified within scope",
  open: "Open question",
  untested: "Not tested by this lab",
};
export default function Evidence() {
  const [params, setParams] = useSearchParams();
  const claim = claims.find((c) => c.id === params.get("claim")) || claims[0];
  return (
    <div className="container evidence-page">
      <header className="page-head">
        <p className="eyebrow">THE INTELLECTUAL CENTRE OF THE ATLAS</p>
        <h1>
          What did we
          <br />
          <em>actually disprove?</em>
        </h1>
        <p>
          Scientific progress depends on the size of the claim. Select a
          statement to see the evidence, assumptions and limits that belong to
          it.
        </p>
      </header>
      <div className="evidence-flow" aria-label="Reasoning chain">
        <span>
          Reconstruction<small>Experiments 1–2</small>
        </span>
        <ArrowRight />
        <span>
          Identification limits<small>Experiments 3–4</small>
        </span>
        <ArrowRight />
        <span>
          Classical route rejected<small>Experiment 5</small>
        </span>
        <ArrowRight />
        <span>
          Quantum tests fail advancement<small>Experiments 6–7</small>
        </span>
      </div>
      <div className="evidence-workspace">
        <div className="claim-list" role="group" aria-label="Scientific claims">
          {claims.map((c, i) => (
            <button
              key={c.id}
              className={`claim-node ${c.status} ${c.id === claim.id ? "selected" : ""}`}
              aria-pressed={c.id === claim.id}
              onClick={() => setParams({ claim: c.id })}
            >
              <span className="claim-index">
                {String(i + 1).padStart(2, "0")}
              </span>
              <div>
                <span className={"claim-status " + c.status}>
                  {statusLabels[c.status]}
                </span>
                <h2>{c.title}</h2>
              </div>
              <ArrowUpRight size={17} />
            </button>
          ))}
        </div>
        <article className="claim-detail" aria-live="polite">
          <p className={"claim-status " + claim.status}>
            {statusLabels[claim.status]}
          </p>
          <h2>{claim.precise}</h2>
          <dl>
            <div>
              <dt>The evidence</dt>
              <dd>{claim.evidence}</dd>
            </div>
            <div>
              <dt>Underlying assumptions</dt>
              <dd>{claim.assumptions}</dd>
            </div>
            <div>
              <dt>Why it stops here</dt>
              <dd>{claim.scope}</dd>
            </div>
          </dl>
          <div className="claim-experiments">
            {claim.experiments.map((n) => (
              <Link to={"/experiment/" + n} key={n}>
                Experiment {n}
                <ArrowUpRight size={12} />
              </Link>
            ))}
          </div>
          <div className="source-list">
            {claim.sources.map((s) => (
              <a key={s.path} href={sourceUrl(s.path)}>
                {s.label}
                <ArrowUpRight size={14} />
              </a>
            ))}
          </div>
        </article>
      </div>
      <div className="scope-statement">
        <p className="eyebrow">PROGRAMME CLOSED / CLAIMS REMAIN SCOPED</p>
        <h2>
          Specific tests failed.
          <br />
          <em>An unresolved physical question.</em>
        </h2>
        <p>
          The broad hypothesis of emergent spacetime has not been disproved.
          These studies supply numerical demonstrations, exact limitations on
          selected statistics, a classical growth obstruction and a failed finite
          quantum-locality benchmark. They provide insufficient evidence to
          pursue the physical hypothesis through further simulations.
        </p>
        <Link className="text-link" to="/synthesis">Read the final conclusion <ArrowRight size={16} /></Link>
      </div>
    </div>
  );
}
