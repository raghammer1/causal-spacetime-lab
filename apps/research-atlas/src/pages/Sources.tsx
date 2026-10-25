import { ArrowUpRight } from "lucide-react";
import { experiments, sourceUrl, SCIENTIFIC_REF } from "../data/editorial";
import { provenance } from "../data/catalog";
export default function Sources() {
  return (
    <div className="container">
      <header className="page-head">
        <p className="eyebrow">OPEN RESEARCH / REPRODUCIBLE EVIDENCE</p>
        <h1>
          Trace every <em>claim.</em>
        </h1>
        <p>
          The atlas reads archived research. It does not regenerate the large
          studies or replace their protocols. Each dataset is pinned to a
          verified repository commit.
        </p>
      </header>
      <div className="provenance-banner">
        <span className="tag green">PINNED RESEARCH ARCHIVE · EXPERIMENTS 1–7</span>
        <a
          href={
            "https://github.com/raghammer1/causal-spacetime-lab/commit/" +
            SCIENTIFIC_REF
          }
        >
          {SCIENTIFIC_REF}
          <ArrowUpRight size={15} />
        </a>
        <p>
          Browser demonstrations use deterministic seeds for replay. Their
          small, illustrative outputs are separate from recorded ensemble
          measurements.
        </p>
      </div>
      <section className="source-standards">
        <h2>How to read this atlas</h2>
        <dl className="journey-facts">
          <div>
            <dt>Known mathematics</dt>
            <dd>
              Established results and their assumptions, with primary references
              in the linked derivations.
            </dd>
          </div>
          <div>
            <dt>Numerical observations</dt>
            <dd>
              Finite recorded samples, with their sampling units, source
              definitions and uncertainty intervals.
            </dd>
          </div>
          <div>
            <dt>Exact deductions</dt>
            <dd>
              Mathematical counterexamples and identities that delimit what
              selected statistics can establish.
            </dd>
          </div>
          <div>
            <dt>Open hypotheses</dt>
            <dd>
              Ideas about physical spacetime that these models have not
              demonstrated or ruled out.
            </dd>
          </div>
        </dl>
      </section>
      <section className="sources-experiment">
        <p className="eyebrow">PROGRAMME CLOSURE</p>
        <h2>The complete research conclusion</h2>
        <div className="source-list">
          <a href={sourceUrl("docs/FINAL_RESEARCH_SYNTHESIS.md")}>Seven-experiment synthesis <ArrowUpRight size={15} /></a>
          <a href={sourceUrl("docs/DYNAMICAL_LOCALITY_RESULTS.md")}>Final experiment: results, audits and limitations <ArrowUpRight size={15} /></a>
        </div>
      </section>
      {experiments.map((e) => (
        <section className="sources-experiment" key={e.id}>
          <p className="eyebrow">EXPERIMENT 0{e.id}</p>
          <h2>{e.shortTitle}</h2>
          <div className="source-list">
            {e.sources.map((s) => (
              <a href={sourceUrl(s.path)} key={s.path}>
                {s.label}
                <ArrowUpRight size={15} />
                <small>{s.path}</small>
              </a>
            ))}
          </div>
        </section>
      ))}
      <section className="sources-experiment">
        <h2>Dataset integrity</h2>
        <p>
          Conversion validates the source checksums and preserves archived
          values. JSON exports include provenance. CSV exports preserve the
          source field names and full precision; missing values are empty cells.
        </p>
        <details>
          <summary>{provenance.sources.length} source checksums</summary>
          {provenance.sources.map((s) => (
            <div className="source-checksum" key={s.path}>
              <a href={s.url}>{s.path}</a>
              <code>{s.sha256}</code>
            </div>
          ))}
        </details>
      </section>
    </div>
  );
}
