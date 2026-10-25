import { createElement } from "react";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import {
  claims,
  concepts,
  experiments,
  SCIENTIFIC_REF,
  sourceUrl,
} from "./data/editorial";
import { ConceptLab, conceptOptions } from "./components/labs/ConceptLab";
import { LevelSwitch, ReadingProvider } from "./components/ReadingLevel";
import Evidence from "./pages/Evidence";
import ExperimentPage from "./pages/Experiment";

// Charts have independent provenance/interaction coverage. Keep this suite focused
// on the scientific narrative and the actual navigation/reading-level bindings.
vi.mock("./components/DataPanel", () => ({ default: () => null }));

const repoRoot = resolve(process.cwd(), "../..");

describe("scientific editorial boundaries", () => {
  it("distinguishes supported reconstruction, scoped falsification and untested physics", () => {
    expect(
      Object.fromEntries(claims.map((claim) => [claim.id, claim.status])),
    ).toEqual({
      "temporal-information": "supported",
      "dimension-information": "supported",
      "one-statistic": "falsified",
      "selected-statistics": "falsified",
      "classical-route": "falsified",
      "quantum-reconstruction": "supported",
      "fixed-quantum-emergence": "falsified",
      "dynamical-locality": "falsified",
      "emergence-impossible": "untested",
      "physical-discreteness": "untested",
      "singularity-resolved": "untested",
    });
    expect(
      claims.find((c) => c.id === "emergence-impossible")?.scope,
    ).toContain("remains open");
    expect(claims.find((c) => c.id === "classical-route")?.assumptions).toMatch(
      /nonnegative.*t₀ or t₁ positive/i,
    );
    expect(claims.find((c) => c.id === "classical-route")?.scope).toMatch(
      /does not cover.*quantum/,
    );
    expect(
      claims.find((c) => c.id === "singularity-resolved")?.scope,
    ).toContain("not itself a curvature singularity");
  });

  it("gives every tested claim direct artifact evidence without weakening the scope", () => {
    for (const claim of claims.filter(
      (c) => c.status === "supported" || c.status === "falsified",
    )) {
      expect(
        claim.sources.some((source) =>
          source.path.startsWith("docs/experiments/"),
        ),
      ).toBe(true);
      expect(claim.assumptions.length).toBeGreaterThan(60);
      expect(claim.scope.length).toBeGreaterThan(60);
      expect(claim.experiments.every((n) => n >= 1 && n <= 7)).toBe(true);
    }
  });

  it("pins repository citations and verifies that every cited local artifact exists", () => {
    expect(SCIENTIFIC_REF).toMatch(/^[a-f0-9]{40}$/);
    expect(SCIENTIFIC_REF).toBe("4e1a667ad2d590ee365a395021f0c9772e63b8d1");
    const allSources = [...experiments, ...claims, ...concepts].flatMap(
      (item) => item.sources,
    );
    for (const source of allSources) {
      const url = new URL(sourceUrl(source.path));
      expect(url.protocol).toBe("https:");
      if (!source.path.startsWith("https://")) {
        expect(existsSync(resolve(repoRoot, source.path)), source.path).toBe(
          true,
        );
        expect(url.pathname).toContain(`/blob/${SCIENTIFIC_REF}/`);
        expect(url.pathname).not.toContain("/blob/main/");
      }
    }
    const primary = "https://doi.org/10.1103/PhysRev.110.965";
    expect(sourceUrl(primary)).toBe(primary);
  });

  it("preserves adverse findings and the correct independent sampling units", () => {
    const time = experiments[0],
      dimensions = experiments[1],
      adversaries = experiments[2],
      local = experiments[3],
      growth = experiments[4],
      quantum = experiments[5],
      dynamical = experiments[6];
    expect(time.measured).toMatch(/4,200.*8,000/);
    expect(time.limitations.join(" ")).toMatch(/post hoc.*not pooled/);
    expect(dimensions.found).toMatch(/200\/200.*98.1%/);
    expect(dimensions.limitations.join(" ")).toMatch(
      /excludes the true integer/,
    );
    expect(adversaries.failed).toMatch(/Zero of 5,400.*361.*post hoc/);
    expect(adversaries.researcher).toMatch(/not a simultaneous 95%/);
    expect(local.researcher).toContain("E[B/A]");
    expect(local.limitations.join(" ")).toContain("postregistration");
    expect(growth.measured).toMatch(/1,056 independent.*17,986 dependent/);
    expect(growth.limitations.join(" ")).toMatch(/48 entries.*pointwise/);
    expect(growth.limitations.join(" ")).toMatch(/falsely rejected.*exclud/);
    expect(growth.assumptions.join(" ")).toMatch(/dependent.*together/);
    expect(quantum.measured).toMatch(/1,818 state records.*873 ground-state/);
    expect(quantum.failed).toMatch(/365\/400.*91.25%/);
    expect(quantum.limitations.join(" ")).toContain("not 1,818 independent");
    expect(quantum.found).toMatch(/n = 6 and 10/);
    expect(dynamical.found).toMatch(/0\/12.*0.402190.*0.8/);
    expect(dynamical.limitations.join(" ")).toMatch(/cannot certify GO.*reject the observed/);
    expect(dynamical.limitations.join(" ")).toContain("does not cause the primary NO-GO");
    expect(dynamical.assumptions.join(" ")).toMatch(/one independent unit.*dependent/);
  });

  it("retains reported headline values rather than inventing an improved outcome", () => {
    const reportPaths = [
      "FINITE_DENSITY_RESULTS",
      "DIMENSION_RECONSTRUCTION_RESULTS",
      "ADVERSARIAL_GEOMETRY_RESULTS",
      "LOCAL_CAUSAL_STRUCTURE_RESULTS",
      "BACKGROUND_FREE_GROWTH_RESULTS",
      "QUANTUM_EMERGENCE_RESULTS",
      "DYNAMICAL_LOCALITY_RESULTS",
    ];
    const facts = [
      ["4,200", "8,000", "7.844"],
      ["1.9980", "3.0161", "3.9914"],
      ["63.17%", "57.33%", "69.00%"],
      ["4.5813", "3.9948", "3.9478"],
      ["1,056", "17,986", "48"],
      ["1,818", "873", "91.25%", ".84316"],
      ["0/12", "0.402190", "144", "238"],
    ];
    reportPaths.forEach((report, i) => {
      const archived = readFileSync(
        resolve(repoRoot, `docs/${report}.md`),
        "utf8",
      );
      const narrative = JSON.stringify(experiments[i]);
      for (const fact of facts[i]) {
        expect(archived, `${report}: ${fact}`).toContain(fact);
        expect(narrative, `narrative: ${fact}`).toContain(fact);
      }
    });
  });

  it("completes seven experiments and closes the programme without a universal no-go", () => {
    expect(experiments.map((experiment) => experiment.id)).toEqual([1, 2, 3, 4, 5, 6, 7]);
    expect(new Set(experiments.map((experiment) => experiment.slug)).size).toBe(7);
    expect(claims).toHaveLength(11);
    expect(experiments[4].next).toMatch(/Historically.*Experiment 6/);
    expect(experiments[5].next).toMatch(/Experiment 7.*final experiment/);
    expect(experiments[6].next).toMatch(/programme is closed.*conclusion B.*no Experiment 8/);
    expect(experiments[6].unresolved).toMatch(/not a universal impossibility theorem/);
    expect(experiments[6].sources).toContainEqual({
      label: "Final synthesis and programme closure",
      path: "docs/FINAL_RESEARCH_SYNTHESIS.md",
    });
    expect(claims.find((claim) => claim.id === "dynamical-locality")?.scope).toMatch(
      /unconditioned screen.*scaling.*remain unresolved.*conclusion B/,
    );
  });
});

describe("editorial integration", () => {
  const conceptHeadings: Record<string, string> = {
    causality: "What can influence what?",
    "light-cones": "What can influence what?",
    "proper-time": "A clock made of relationships",
    dimensions: "Guess the hidden dimension",
    diamonds: "A clock made of relationships",
    orders: "A pattern is an induced suborder",
    chains: "A clock made of relationships",
    patterns: "A pattern is an induced suborder",
    closure: "Grow an order. Supply no space.",
    randomness: "Build an impostor universe",
    embedding: "A drawing is not a spacetime",
    continuum: "A limit needs more than a finer picture",
    singularities: "Where the classical description reaches its limit",
  };

  it("maps every educational URL to an implemented demonstration", () => {
    expect(concepts).toHaveLength(13);
    expect(new Set(concepts.map((c) => c.id)).size).toBe(13);
    expect(new Set(concepts.map((c) => c.id))).toEqual(
      new Set(conceptOptions.map(([id]) => id)),
    );
  });

  it.each(concepts)(
    "renders the intended scientific demonstration for $id",
    (concept) => {
      render(createElement(ConceptLab, { concept: concept.id }));
      expect(
        screen.getByRole("heading", { name: conceptHeadings[concept.id] }),
      ).toBeInTheDocument();
      expect(
        screen.getByText(/separate from the archived studies/),
      ).toBeInTheDocument();
    },
  );

  it("changes substantive explanation when the actual experiment reading level changes", () => {
    render(
      createElement(
        ReadingProvider,
        null,
        createElement(LevelSwitch),
        createElement(
          MemoryRouter,
          { initialEntries: ["/experiment/2"] },
          createElement(
            Routes,
            null,
            createElement(Route, {
              path: "/experiment/:id",
              element: createElement(ExperimentPage),
            }),
          ),
        ),
      ),
    );
    const explanation = screen.getByTestId("level-explanation");
    expect(explanation).toHaveTextContent(experiments[1].explorer);
    fireEvent.click(screen.getByRole("button", { name: "engineer" }));
    expect(explanation).toHaveTextContent(experiments[1].engineer);
    expect(explanation).toHaveTextContent("bounded bisection");
    fireEvent.click(screen.getByRole("button", { name: "researcher" }));
    expect(explanation).toHaveTextContent(experiments[1].researcher);
    expect(explanation).toHaveTextContent("Nonlinear inversion");
    expect(
      new Set([
        experiments[1].explorer,
        experiments[1].engineer,
        experiments[1].researcher,
      ]).size,
    ).toBe(3);
  });

  it.each([6, 7])("renders Experiment %i with its own explanation and research limits", (id) => {
    const experiment = experiments[id - 1];
    render(
      createElement(
        ReadingProvider,
        null,
        createElement(LevelSwitch),
        createElement(
          MemoryRouter,
          { initialEntries: [`/experiment/${id}`] },
          createElement(
            Routes,
            null,
            createElement(Route, { path: "/experiment/:id", element: createElement(ExperimentPage) }),
          ),
        ),
      ),
    );
    expect(screen.getByRole("heading", { level: 1, name: experiment.title })).toBeInTheDocument();
    expect(screen.getByTestId("level-explanation")).toHaveTextContent(experiment.explorer);
    fireEvent.click(screen.getByRole("button", { name: "researcher" }));
    expect(screen.getByTestId("level-explanation")).toHaveTextContent(experiment.researcher);
    expect(screen.getByText(experiment.unresolved)).toBeInTheDocument();
    expect(screen.getByText(experiment.next)).toBeInTheDocument();
  });

  it("shows model-specific evidence separately from a universal untested claim", () => {
    render(
      createElement(
        MemoryRouter,
        { initialEntries: ["/evidence?claim=classical-route"] },
        createElement(Evidence),
      ),
    );
    let detail = document.querySelector(".claim-detail") as HTMLElement;
    expect(
      within(detail).getByText("Falsified within scope"),
    ).toBeInTheDocument();
    expect(detail).toHaveTextContent("t₀ or t₁ positive");
    fireEvent.click(
      screen.getByRole("button", {
        name: /All possible emergent-spacetime theories are impossible/,
      }),
    );
    detail = document.querySelector(".claim-detail") as HTMLElement;
    expect(
      within(detail).getByText("Not tested by this lab"),
    ).toBeInTheDocument();
    expect(detail).toHaveTextContent(
      "broader emergence hypothesis remains open",
    );
    expect(
      within(detail).queryByText("Falsified within scope"),
    ).not.toBeInTheDocument();
    expect(
      within(detail).getByRole("link", { name: /Growth conclusion/ }),
    ).toHaveAttribute(
      "href",
      sourceUrl("docs/BACKGROUND_FREE_GROWTH_RESULTS.md"),
    );
  });

  it("links the finite quantum-link failure to evidence without relabeling universal impossibility", () => {
    render(
      createElement(
        MemoryRouter,
        { initialEntries: ["/evidence?claim=dynamical-locality"] },
        createElement(Evidence),
      ),
    );
    const detail = document.querySelector(".claim-detail") as HTMLElement;
    expect(within(detail).getByText("Falsified within scope")).toBeInTheDocument();
    expect(detail).toHaveTextContent("0.402190 < 0.8");
    expect(detail).toHaveTextContent("geometric scaling and broader relational protocols remain unresolved");
    expect(within(detail).getByRole("link", { name: /Programme conclusion B/ })).toHaveAttribute(
      "href",
      sourceUrl("docs/FINAL_RESEARCH_SYNTHESIS.md"),
    );
  });
});
