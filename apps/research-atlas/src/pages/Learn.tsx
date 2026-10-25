import { useSearchParams, Link } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";
import { concepts, sourceUrl } from "../data/editorial";
import { ConceptLab } from "../components/labs";
import { useReadingLevel } from "../components/ReadingLevel";
export default function Learn() {
  const [params, setParams] = useSearchParams();
  const concept =
    concepts.find((c) => c.id === params.get("concept")) || concepts[0];
  const { level } = useReadingLevel();
  return (
    <div className="container">
      <header className="page-head">
        <p className="eyebrow">THE VISUAL EDUCATION LAB</p>
        <h1>
          Build your <em>intuition.</em>
        </h1>
        <p>
          No physics degree required. Explore the small ideas that make the
          larger questions understandable.
        </p>
      </header>
      <div className="learn-layout">
        <nav className="concept-nav" aria-label="Scientific concepts">
          {concepts.map((c, i) => (
            <button
              key={c.id}
              aria-current={concept.id === c.id ? "page" : undefined}
              onClick={() => setParams({ concept: c.id })}
            >
              <span>{String(i + 1).padStart(2, "0")}</span>
              {c.title}
            </button>
          ))}
        </nav>
        <article className="concept-content" key={concept.id}>
          <p className="eyebrow">A CONCEPT TO EXPLORE</p>
          <h2>{concept.title}</h2>
          <p className="concept-intro">{concept.intro}</p>
          <ConceptLab concept={concept.id} />
          {level !== "explorer" && (
            <p className="technical-explanation">{concept.detail}</p>
          )}
          <details open={level === "researcher" ? true : undefined}>
            <summary>The mathematics & its limits</summary>
            <code className="concept-equation">{concept.equation}</code>
            <p>{concept.detail}</p>
          </details>
          <Link className="button" to={"/experiment/" + concept.experiment}>
            See it in Experiment {concept.experiment}
            <ArrowUpRight size={16} />
          </Link>
          <div className="source-list">
            {concept.sources.map((s) => (
              <a key={s.path} href={sourceUrl(s.path)}>
                {s.label}
                <ArrowUpRight size={14} />
              </a>
            ))}
          </div>
        </article>
      </div>
    </div>
  );
}
