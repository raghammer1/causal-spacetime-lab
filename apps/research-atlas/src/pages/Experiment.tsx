import { Link, useParams } from "react-router-dom";
import { ArrowRight, ArrowUpRight } from "lucide-react";
import { experiments, sourceUrl } from "../data/editorial";
import { useReadingLevel } from "../components/ReadingLevel";
import {
  TimeLab,
  DimensionLab,
  AdversarialLab,
  LocalLab,
  GrowthLab,
} from "../components/labs";
import AsyncDataPanel from "../components/AsyncDataPanel";
import ModelLimit from "../components/ModelLimit";
const labs = [TimeLab, DimensionLab, AdversarialLab, LocalLab, GrowthLab];
const datasetsByExperiment = [
  ["time-primary", "time-followup"],
  ["dimension-summary"],
  ["detector-summary", "detector-rates"],
  ["local-dimensions", "local-primary"],
  ["growth-global", "growth-primary"],
];
export default function Experiment() {
  const { id } = useParams();
  const exp = experiments.find((e) => String(e.id) === id);
  const { level } = useReadingLevel();
  if (!exp)
    return (
      <div className="container page-head">
        <h1>Experiment not found.</h1>
        <Link to="/journey">Return to the journey</Link>
      </div>
    );
  const Lab = labs[exp.id - 1];
  return (
    <div className="container experiment-page" key={exp.id}>
      <nav className="experiment-rail" aria-label="Five experiments">
        {experiments.map((e) => (
          <Link
            to={"/experiment/" + e.id}
            key={e.id}
            aria-current={e.id === exp.id ? "page" : undefined}
          >
            <span>{String(e.id).padStart(2, "0")}</span>
            <strong>{e.shortTitle}</strong>
          </Link>
        ))}
      </nav>
      <header className="page-head experiment-head">
        <div>
          <p className="eyebrow">
            EXPERIMENT {String(exp.id).padStart(2, "0")} /{" "}
            {exp.id === 5 ? "INTRINSIC GROWTH" : "CAUSAL RECONSTRUCTION"}
          </p>
          <h1>{exp.title}</h1>
          <p>{exp.question}</p>
        </div>
        <span className="huge-number" aria-hidden="true">
          0{exp.id}
        </span>
      </header>
      <div className="experiment-jumps" aria-label="Jump to section">
        {["idea", "interactive", "results", "interpretation", "technical"].map(
          (s) => (
            <button
              key={s}
              onClick={() =>
                document.getElementById(s)?.scrollIntoView({
                  behavior: window.matchMedia(
                    "(prefers-reduced-motion: reduce)",
                  ).matches
                    ? "instant"
                    : "smooth",
                  block: "start",
                })
              }
            >
              {s === "idea"
                ? "The idea"
                : s === "interactive"
                  ? "Try it yourself"
                  : s === "results"
                    ? "Recorded evidence"
                    : s === "interpretation"
                      ? "What it means"
                      : "Technical notes"}
            </button>
          ),
        )}
      </div>
      <section className="experiment-intro" id="idea">
        <div>
          <p className="eyebrow">THE IDEA · {level.toUpperCase()}</p>
          <h2>
            {exp.shortTitle}.<br />
            <em>Then question the result.</em>
          </h2>
          <p className="level-explanation" data-testid="level-explanation">
            {exp[level]}
          </p>
        </div>
        <aside className="analogy-box">
          <p className="eyebrow">START WITH AN ANALOGY</p>
          <p>{exp.analogy}</p>
          <details>
            <summary>Registered hypothesis & assumptions</summary>
            <p>{exp.hypothesis}</p>
            <ul>
              {exp.assumptions.map((a) => (
                <li key={a}>{a}</li>
              ))}
            </ul>
          </details>
        </aside>
      </section>
      <section id="interactive" className="experiment-section">
        <div className="section-heading small">
          <div>
            <p className="eyebrow">01 / THE INTERACTIVE PROCEDURE</p>
            <h2>
              A small universe.
              <br />
              <em>In your hands.</em>
            </h2>
          </div>
          <p>
            These deterministic, bounded browser demonstrations teach the
            mathematical rules. They are separate from the archived research
            ensembles below.
          </p>
        </div>
        <Lab />
        {exp.id === 5 && (
          <div className="model-limit-section">
            <ModelLimit />
          </div>
        )}
      </section>
      <section id="results" className="experiment-section">
        <div className="section-heading small">
          <div>
            <p className="eyebrow">02 / RECORDED EVIDENCE</p>
            <h2>
              What the study <em>found.</em>
            </h2>
          </div>
          <Link className="text-link" to={"/data?experiment=" + exp.id}>
            Open full data explorer <ArrowUpRight size={16} />
          </Link>
        </div>
        <div className="results-context">
          <p>
            <strong>The measurement.</strong> {exp.measured}
          </p>
          <p>
            <strong>The finding.</strong> {exp.found}
          </p>
          <a href={sourceUrl(exp.sources[0].path)} className="source-link">
            Original report <ArrowUpRight size={13} />
          </a>
        </div>
        {datasetsByExperiment[exp.id - 1].map((datasetId, i) => (
          <div className="experiment-dataset" key={datasetId}>
            {i > 0 && (
              <p className="eyebrow">
                {exp.id === 1
                  ? "SEPARATELY SEEDED FOLLOW-UP"
                  : exp.id === 4
                    ? "ALL 42 REGISTERED PRIMARY CHECKS"
                    : exp.id === 5
                      ? "REGISTERED SIMULTANEOUS DECISION BANDS"
                      : "PER-FIT WILSON INTERVALS"}
              </p>
            )}
            <AsyncDataPanel datasetId={datasetId} compact />
          </div>
        ))}
      </section>
      <section id="interpretation" className="experiment-section">
        <p className="eyebrow">03 / SCIENTIFIC INTERPRETATION</p>
        <h2>
          What follows.
          <br />
          <em>And where the claim stops.</em>
        </h2>
        <div className="interpretation-grid">
          <article>
            <span className="tag green">SUPPORTED WITHIN ASSUMPTIONS</span>
            <h3>What survived</h3>
            <p>{exp.survived}</p>
          </article>
          <article>
            <span className="tag red">SPECIFIC FAILURE</span>
            <h3>What failed</h3>
            <p>{exp.failed}</p>
          </article>
          <article>
            <span className="tag amber">UNRESOLVED</span>
            <h3>What this cannot establish</h3>
            <p>{exp.unresolved}</p>
          </article>
        </div>
        {exp.id === 5 && (
          <div className="scope-statement">
            <p className="eyebrow">DO NOT CONFUSE THESE CLAIMS</p>
            <p>
              <strong>Rejected for the studied model class:</strong> the
              investigated classical growth route reproduces our target
              nondegenerate Minkowski sampling limit.
            </p>
            <p>
              <strong>Still open:</strong> spacetime might emerge through a
              different quantum or mathematical mechanism. No physical
              discreteness, gravitational field equations or singularity
              resolution was demonstrated.
            </p>
          </div>
        )}
      </section>
      <section id="technical" className="experiment-section technical-section">
        <p className="eyebrow">04 / UNDER THE MATHEMATICS</p>
        <h2>
          Assumptions are <em>part of the result.</em>
        </h2>
        <details open={level === "researcher" ? true : undefined}>
          <summary>Mathematical setup & derivations</summary>
          <p>{exp.setup}</p>
          {exp.equations.map((e) => (
            <div className="equation-block" key={e.label}>
              <h3>{e.label}</h3>
              <code>{e.expression}</code>
              <p>{e.explanation}</p>
            </div>
          ))}
          <p>{exp.researcher}</p>
        </details>
        <details>
          <summary>Limitations & failed controls</summary>
          <ul>
            {exp.limitations.map((l) => (
              <li key={l}>{l}</li>
            ))}
          </ul>
          <p>{exp.failed}</p>
        </details>
        <details>
          <summary>Source code, protocols & archived results</summary>
          <div className="source-list">
            {exp.sources.map((s) => (
              <a key={s.path} href={sourceUrl(s.path)}>
                {s.label}
                <ArrowUpRight size={15} />
                <small>{s.path}</small>
              </a>
            ))}
          </div>
        </details>
      </section>
      <div className="next-experiment">
        <div>
          <p className="eyebrow">
            {exp.id < 5 ? "THE NEXT QUESTION" : "THE BIGGER PICTURE"}
          </p>
          <p>{exp.next}</p>
        </div>
        <Link
          className="button primary"
          to={exp.id < 5 ? "/experiment/" + (exp.id + 1) : "/evidence"}
        >
          {exp.id < 5 ? "Experiment 0" + (exp.id + 1) : "The evidence map"}
          <ArrowRight size={17} />
        </Link>
      </div>
    </div>
  );
}
