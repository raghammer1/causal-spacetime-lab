# Interactive Research Atlas

A standalone React + TypeScript application for the completed seven-experiment Causal Spacetime Lab programme. It presents the research journey, bounded teaching demonstrations, eleven scoped evidence-map claims, thirteen visual concept lessons and a provenance-preserving archive explorer. The final conclusion is **B: useful mathematical/computational research, but insufficient evidence to pursue the physical hypothesis through more simulations**. No backend, account, API key or paid service is required.

## Run

Use Node 22.12+ and Python 3.10+. From this directory:

```bash
npm ci
npm run dev
```

Open the printed local URL, including `/causal-spacetime-lab/`. The source uses a hash router so every route and refresh works under the GitHub Pages repository base path.

```bash
npm run data:check       # deterministic archive conversion and Python transform tests
npm test                # numerical, data, editorial and React interaction tests
npm run typecheck
npm run lint
npm run build           # standalone static output in dist/
npx playwright install chromium
npm run test:e2e         # desktop + mobile against the production build
npm run check           # data checks, typecheck, lint, tests, build and browser tests
npm run preview         # inspect the production build locally
```

`npm run data:generate` regenerates frontend data from the untouched scientific archives. It requires no research reruns or third-party Python packages. The reproducible Python baseline is tested separately at the repository root with `python -m pytest -q` and `python -m causal_lab.cli --seed 20261025 --repeats 100 --out results/atlas-baseline`.

## Routes and interactions

| Route after `#` | Experience |
| --- | --- |
| `/` | Water/spacetime macro–micro comparison and a Schwarzschild curvature probe |
| `/journey` | Seven experiments, their hypotheses, measured evidence, failures and final conclusion |
| `/experiment/1` | Seeded Poisson causal diamond, density, hidden coordinates, links and longest chain |
| `/experiment/2` | Uniform d2/d3/d4 dimension guessing, bounded Myrheim–Meyer inversion and adversaries |
| `/experiment/3` | Artificial orders, six detector explanations and archived acceptance intervals |
| `/experiment/4` | Boundary choices, local intervals, overlap and exact information-loss witnesses |
| `/experiment/5` | Seeded percolation with step/play/pause/reset and direct/ancestral edge inspection |
| `/experiment/6` | Quantum correlation, supplied-chain reconstruction and the limits of information-based geometry |
| `/experiment/7` | Quantum-link operational response, the finite NO-GO and unresolved geometric scaling |
| `/synthesis` | Final programme conclusion B, retained mathematical results and conditions for a meaningful restart |
| `/evidence` | Eleven clickable claims with precise status, assumptions and source evidence |
| `/data` | Twenty datasets, exact filters, appropriate log scale, tables and CSV/JSON export |
| `/learn` | Thirteen interactive concepts and mathematical explanations |
| `/sources` | Scientific source library, pinned baseline and source checksums |

The global Explorer / Engineer / Researcher switch changes the scientific explanation. Direct links preserve dataset, experiment, concept or evidence-claim selection in the URL. Native controls, Radix navigation dialog, keyboard graph inspection, a skip link, semantic tables and reduced-motion support are included.

## Scientific integrity

Read [SCIENTIFIC_AUDIT.md](SCIENTIFIC_AUDIT.md) and [SCIENTIFIC_REVIEW.md](SCIENTIFIC_REVIEW.md) for the claim-to-source ledger and the precise no-go scope. Data and editorial citations are pinned to research commit `4e1a667ad2d590ee365a395021f0c9772e63b8d1`, which contains all seven reports and the final synthesis. This is an immutable research commit, not a claim that the experimental PR has merged. SHA256 source locks reject silently changed inputs.

Browser toy examples use their displayed seeds and documented mathematical rules. They are instructional samples, not additional experimental evidence. Python/TypeScript parity fixtures independently check the causal rules, chain length, normalization and dimension reference formula. PRNG streams differ from the Python research streams; matching seed numbers across implementations does not promise matching random samples.

Archived uncertainty keeps its meaning: pointwise whole-order bootstrap intervals, per-fit Wilson intervals, hierarchical three-fit intervals and the Experiment 5 simultaneous screen bands remain separate. Experiment 6's nominal 95% bootstrap covered only 91.25% of calibration means and remains descriptive. Experiment 7 uses simultaneous exact binomial bounds on whole preparations: 0/12 joint successes per cell, upper bound 0.402190 against 0.8. Prefixes, thinnings, targets, times and paired controls are not counted as independent observations. Missing values stay missing, and adverse findings remain visible. The complete raw scientific archives are linked rather than copied into the web payload.

## Architecture and performance

- `src/data/`: generated typed datasets, lightweight catalog, per-dataset lazy loader and sourced editorial content.
- `scripts/`: deterministic stdlib-only conversion, immutable source locks and transformation tests.
- `src/lib/simulation.ts`: bounded deterministic geometry and partial-order algorithms.
- `src/components/labs/`: SVG teaching models with scoped styling.
- `src/components/ScientificChart.tsx`: D3 scales, archived point estimates, independent interval endpoints and explicit reference labels.
- `src/components/DataPanel.tsx`: filtering, scientific disclosures, pagination and complete selected-row export.
- `src/pages/`: lazy route experiences; React Router handles navigation.

Vite builds static files. Tailwind supplies the CSS foundation; custom styles implement the visual system. Framer Motion respects system preferences. Data use lossless column/record packing to reduce transport size and load only when their view opens. Simulations are capped; large studies never run in the browser. Charts require one metric when units differ and ask for narrower filters above 240 defined points. The table and export retain all filtered records.

## Deployment

The public atlas address is https://raghammer1.github.io/causal-spacetime-lab/ .
Experiment 7 is merged. This final frontend update is a separate follow-up PR. Its new content
will reach that address only after review, merge into `main` and successful Pages
CI; building this branch does not change the public site.

`.github/workflows/research-atlas.yml` validates data, source and the production
build on the research branch and PR. Only verified `main` builds deploy. It does
not merge the PR or deploy feature branches. The workflow publishes the built
`dist/` artifact through the `github-pages` environment. If deployment protection
requires approval, that deployment remains pending until a reviewer approves it.

Deployment follows the [official Vite GitHub Pages guide](https://vite.dev/guide/static-deploy.html#github-pages). The public static build contains no credentials or user-specific data.

## Deliberate limits

- These experiments do not demonstrate physical spacetime emergence or discreteness, derive gravity or resolve black-hole singularities.
- The growth no-go is scoped to the stated classical class and finite uniformly sampled-suborder limit, not all possible dynamics or local scaling limits.
- The quantum-link NO-GO concerns the registered finite, unconditioned locality benchmark at N = 4 and 5. Larger-size scaling, graph-adapted instruments and other state families remain unresolved.
- The programme is closed with conclusion B. Logical openness is not positive evidence, and no Experiment 8 or replacement Hamiltonian is proposed.
- Mutual information is total correlation, not operational signalling. Born graph measurements, ensemble expectations and graph-conditioned fresh-matter controls remain distinct.
- Network layouts and projected high-dimensional samples are labeled display devices, not physical spatial coordinates.
- Tiny browser samples have no invented confidence intervals. Inspect recorded ensemble uncertainty in the charts.
- Conditional summaries keep all scalar decisions but link full nested diagnostics in the original sources; CSV exports are the selected frontend table, not the complete raw archive.
- Automated accessibility checks and keyboard testing complement visual inspection; they are not certification of every assistive-technology combination.
