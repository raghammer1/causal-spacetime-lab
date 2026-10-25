import { Link } from "react-router-dom";
import { ArrowRight, ArrowDown, ArrowUpRight } from "lucide-react";
import { experiments, sourceUrl } from "../data/editorial";
import { useReadingLevel } from "../components/ReadingLevel";
export default function Journey() {
  const { level } = useReadingLevel();
  return (
    <div className="container">
      <header className="page-head">
        <p className="eyebrow">SEVEN EXPERIMENTS / A COMPLETED PROGRAMME</p>
        <h1>
          A journey from
          <br />
          reconstruction to <em>limits.</em>
        </h1>
        <p>
          We began by asking what causal order can reveal. Each result made the
          next question sharper. The seventh experiment closes this line of
          computational research; the archive keeps the entire journey visible.
        </p>
      </header>
      <div className="journey-timeline">
        {experiments.map((exp) => (
          <article className="journey-stop" key={exp.id}>
            <div className="timeline-marker">
              <span>{String(exp.id).padStart(2, "0")}</span>
            </div>
            <div className="journey-body">
              <div className="journey-title">
                <span className="eyebrow">
                  EXPERIMENT {exp.id} /{" "}
                  {exp.id < 3
                    ? "RECONSTRUCTION"
                    : exp.id < 5
                      ? "IDENTIFIABILITY"
                      : exp.id === 5 ? "CLASSICAL GROWTH"
                        : exp.id === 6 ? "QUANTUM INFORMATION" : "DYNAMICAL LOCALITY"}
                </span>
                <Link className="text-link" to={"/experiment/" + exp.id}>
                  Open experiment <ArrowUpRight size={16} />
                </Link>
              </div>
              <h2>{exp.shortTitle}</h2>
              <p className="question">{exp.question}</p>
              <p>{exp[level]}</p>
              <dl className="journey-facts">
                <div>
                  <dt>Hypothesis</dt>
                  <dd>{exp.hypothesis}</dd>
                </div>
                <div>
                  <dt>What we simulated</dt>
                  <dd>{exp.setup}</dd>
                </div>
                <div>
                  <dt>What we measured</dt>
                  <dd>{exp.measured}</dd>
                </div>
                <div>
                  <dt>What we found</dt>
                  <dd>{exp.found}</dd>
                </div>
              </dl>
              <details>
                <summary>Assumptions, claims that survived & limits</summary>
                <ul>
                  {exp.assumptions.map((a) => (
                    <li key={a}>{a}</li>
                  ))}
                </ul>
                <p>
                  <strong>Survived:</strong> {exp.survived}
                </p>
                <p>
                  <strong>Failed:</strong> {exp.failed}
                </p>
                <p>
                  <strong>Unresolved:</strong> {exp.unresolved}
                </p>
                <a
                  className="source-link"
                  href={sourceUrl(exp.sources[0].path)}
                >
                  Read the original results <ArrowUpRight size={13} />
                </a>
              </details>
              <div className="next-question">
                {exp.id < 7 ? <ArrowDown size={20} /> : <ArrowRight size={20} />}
                <p>{exp.next}</p>
              </div>
            </div>
          </article>
        ))}
      </div>
      <section className="journey-ending">
        <span className="tag amber">
          PROGRAMME CLOSED · CONCLUSION B
        </span>
        <h2>
          We have reached a stopping point.
          <br />
          <em>We did not settle the universe.</em>
        </h2>
        <p>
          Causal reconstruction and quantum correlations yielded useful
          mathematical results. The classical and quantum models did not
          establish emergent physical spacetime. The final finite locality
          benchmark failed, and there is insufficient evidence to continue
          through more simulations.
        </p>
        <Link className="button primary" to="/synthesis">
          Read the final synthesis <ArrowRight size={17} />
        </Link>
      </section>
    </div>
  );
}
