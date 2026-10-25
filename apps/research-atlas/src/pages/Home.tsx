import { useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  ArrowDown,
  ArrowUpRight,
  Orbit,
  Waves,
} from "lucide-react";
import Universe from "../components/Universe";
import { useReadingLevel } from "../components/ReadingLevel";
const chapters = [
  ["01", "Reconstruct time", "From causal relationships to elapsed time."],
  ["02", "Recover dimensions", "A dimension hidden in the order of events."],
  [
    "03",
    "Challenge the detectors",
    "Can artificial universes fool the mathematics?",
  ],
  ["04", "Look closer", "Local structure reveals what global measures miss."],
  [
    "05",
    "Grow without geometry",
    "A classical route reaches a mathematical limit.",
  ],
];
export default function Home() {
  const [micro, setMicro] = useState(false);
  const [water, setWater] = useState(false);
  const [radius, setRadius] = useState(1);
  const { level } = useReadingLevel();
  return (
    <>
      <section className="hero container">
        <div className="hero-copy">
          <p className="eyebrow">
            <span className="amber-line" /> THE INTERACTIVE RESEARCH ATLAS
          </p>
          <h1>
            What if
            <br />
            spacetime is
            <br />
            <em>like water?</em>
          </h1>
          <p className="hero-subtitle">
            Exploring whether space, time and geometry emerge from something
            deeper.
          </p>
          <p className="hero-description">
            Water looks continuous. Look closer, and a different world appears.
            Could smooth spacetime also be a description of something
            underneath?
          </p>
          <div className="hero-actions">
            <Link className="button primary" to="/journey">
              Follow the research <ArrowRight size={17} />
            </Link>
            <Link className="text-link" to="/experiment/1">
              Enter the lab <ArrowUpRight size={15} />
            </Link>
          </div>
          <div className="hero-footnote">
            <span>05 EXPERIMENTS</span>
            <span>OPEN DATA</span>
            <span>ONE UNRESOLVED QUESTION</span>
          </div>
        </div>
        <div className="hero-visual">
          <div className="visual-topline">
            <span>01 / A CHANGE OF SCALE</span>
            <span className="live-tag">INTERACTIVE</span>
          </div>
          <Universe micro={micro} water={water} />
          <div className="scale-controls">
            <div
              className="segmented"
              role="group"
              aria-label="Analogy material"
            >
              <button aria-pressed={!water} onClick={() => setWater(false)}>
                <Orbit size={14} /> Spacetime
              </button>
              <button aria-pressed={water} onClick={() => setWater(true)}>
                <Waves size={14} /> Water
              </button>
            </div>
            <div className="segmented" role="group" aria-label="View scale">
              <button aria-pressed={!micro} onClick={() => setMicro(false)}>
                Macro
              </button>
              <button aria-pressed={micro} onClick={() => setMicro(true)}>
                Micro
              </button>
            </div>
          </div>
          <div className="visual-caption">
            <span className={micro && !water ? "tag amber" : "tag"}>
              {water
                ? "ESTABLISHED PHYSICS"
                : micro
                  ? "SPECULATIVE DEPICTION"
                  : "ESTABLISHED DESCRIPTION"}
            </span>
            <p>
              {water
                ? micro
                  ? "Molecules and their interactions underlie water’s collective fluid behaviour. Molecular positions here are schematic."
                  : "At large scales, fluid equations describe water as a continuous material. That useful description has limits."
                : micro
                  ? "One possible idea: microscopic events connected by causal relationships. We have not shown that physical spacetime is made this way."
                  : "General Relativity describes spacetime with smooth geometry. This illustrative surface is a visual analogy, not a solution of Einstein’s equations."}
            </p>
          </div>
        </div>
      </section>
      <section className="research-status container">
        <div className="status-label">
          <span className="status-dot amber-dot" /> RESEARCH STATUS
        </div>
        <p>
          Our experiments have <strong>not demonstrated</strong> that physical
          spacetime is emergent.
        </p>
        <Link to="/evidence">
          What did we establish? <ArrowUpRight size={17} />
        </Link>
      </section>
      <section className="section container">
        <div className="section-heading">
          <div>
            <p className="eyebrow">A QUESTION THAT BECAME FIVE EXPERIMENTS</p>
            <h2>
              Follow the evidence.
              <br />
              <em>Even when it changes the story.</em>
            </h2>
          </div>
          <p>
            First we reconstructed time and dimension. Then we challenged our
            own methods. Finally, we asked whether geometry could arise without
            being supplied.
          </p>
        </div>
        <div className="chapter-list">
          {chapters.map(([n, t, d], i) => (
            <Link to={"/experiment/" + (i + 1)} className="chapter-row" key={n}>
              <span className="chapter-number">{n}</span>
              <div className="chapter-spark" aria-hidden="true">
                <svg viewBox="0 0 96 50">
                  {Array.from({ length: 9 }, (_, j) => (
                    <g key={j}>
                      <path
                        d={`M${8 + j * 10},${38 - Math.sin(j * (i + 1)) * 10} L${18 + j * 9},${10 + Math.cos(j + i) * 7}`}
                        stroke="currentColor"
                        opacity=".4"
                      />
                      <circle
                        cx={8 + j * 10}
                        cy={38 - Math.sin(j * (i + 1)) * 10}
                        r="2"
                        fill="currentColor"
                      />
                    </g>
                  ))}
                </svg>
              </div>
              <h3>{t}</h3>
              <p>{d}</p>
              <ArrowUpRight size={20} />
            </Link>
          ))}
        </div>
      </section>
      <section className="origin-section">
        <div className="container origin-grid">
          <div>
            <p className="eyebrow">WHY ASK THE QUESTION?</p>
            <h2>
              When a description
              <br />
              <em>reaches its limits.</em>
            </h2>
            <p>
              {level === "explorer"
                ? "In classical black-hole models, some freely falling paths end after finite proper time. The classical spacetime description is incomplete. That motivates deeper theories. It does not tell us what the deeper theory is."
                : level === "engineer"
                  ? "The Schwarzschild curvature invariant grows as r⁻⁶. The event horizon is regular in suitable coordinates; the r=0 curvature divergence belongs to this idealized classical solution. Our causal-order studies do not simulate gravitational collapse."
                  : "For a Schwarzschild black hole, K = Rₐᵦᵧδ Rᵃᵦᵧδ = 48G²M²/(c⁴r⁶). The horizon at rₛ = 2GM/c² is not a curvature singularity. Geodesic incompleteness is the more general singularity criterion; these experiments test neither it nor quantum resolution."}
            </p>
            <Link className="text-link" to="/learn?concept=singularities">
              Understand singularities <ArrowUpRight size={15} />
            </Link>
          </div>
          <div className="horizon-demo">
            <div className="visual-topline">
              <span>CLASSICAL SCHWARZSCHILD MODEL</span>
            </div>
            <svg
              viewBox="0 0 470 230"
              role="img"
              aria-label={`Probe at ${radius.toFixed(2)} horizon radii; horizon has finite curvature`}
            >
              <defs>
                <radialGradient id="hole">
                  <stop stopColor="#02050a" offset=".5" />
                  <stop stopColor="#edbb70" stopOpacity=".1" offset=".72" />
                  <stop stopColor="#edbb70" stopOpacity="0" offset="1" />
                </radialGradient>
              </defs>
              <circle cx="235" cy="115" r="106" fill="url(#hole)" />
              <ellipse
                cx="235"
                cy="115"
                rx="165"
                ry="40"
                fill="none"
                stroke="#98cfe9"
                opacity=".2"
              />
              <circle
                cx="235"
                cy="115"
                r="58"
                fill="#03070c"
                stroke="#edbb70"
                strokeDasharray="3 5"
              />
              <path d="M235 115H425" stroke="#6c8799" />
              <circle cx={235 + radius * 58} cy="115" r="5" fill="#a4d9f1" />
              <text x="32" y="30" fill="#99aaba" fontSize="10">
                HORIZON ≠ SINGULARITY
              </text>
              <text
                x="235"
                y="198"
                fill="#edbb70"
                fontSize="11"
                textAnchor="middle"
              >
                event horizon · r / rₛ = 1
              </text>
              <text
                x="235"
                y="119"
                fill="#a2b1bb"
                fontSize="9"
                textAnchor="middle"
              >
                r = 0
              </text>
            </svg>
            <label className="range-label" htmlFor="radius">
              Move the probe <span>r / rₛ = {radius.toFixed(2)}</span>
            </label>
            <input
              id="radius"
              type="range"
              min="0.15"
              max="3"
              step="0.05"
              value={radius}
              onChange={(e) => setRadius(Number(e.target.value))}
            />
            <p className="microcopy">
              Curvature relative to the horizon:{" "}
              <strong>
                {(radius ** -6).toLocaleString("en", {
                  maximumFractionDigits: 2,
                })}
                ×
              </strong>
              . Finite at the horizon; unbounded as r → 0 in this classical
              model. The slider never reaches r = 0.
            </p>
            <a
              className="source-link"
              href="https://www.einstein-online.info/en/spotlight/singularities/"
            >
              Background: Einstein Online <ArrowUpRight size={12} />
            </a>
          </div>
        </div>
      </section>
      <section className="container closing-question">
        <p className="eyebrow">THE MOST IMPORTANT DISTINCTION</p>
        <h2>
          One route closed.
          <br />
          <em>The larger question is open.</em>
        </h2>
        <p>
          The investigated classical growth models failed our target. That does
          not rule out every possible mechanism for emergent spacetime.
        </p>
        <Link className="button" to="/evidence">
          Explore the falsification map <ArrowRight size={17} />
        </Link>
        <ArrowDown className="closing-arrow" size={28} />
      </section>
    </>
  );
}
