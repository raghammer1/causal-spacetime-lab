# Final seven-experiment atlas verification

Verified 25 October 2026. The frontend presents the completed programme and its
explicit conclusion B. Research inputs and citations are pinned to immutable
commit `4e1a667ad2d590ee365a395021f0c9772e63b8d1`. Experiment 7 PR #8 is now merged;
its post-merge Python CI passed at `c01373596570aecd4de8c83787b0529efe3402bb`.
This separate frontend follow-up starts from that verified main baseline and
deploys only through `main` after review and merge.

| Check | Result |
| --- | --- |
| Complete Python research suite | 1,142 passed; three pre-existing empty-legend warnings |
| End-to-end baseline CLI | Seed 20261025, 100 repeats; completed under ignored `results/atlas-closure-baseline` |
| Deterministic archive conversion | 20 generated datasets match pinned source locks |
| Python data transformation checks | 18 passed |
| Frontend unit and interaction checks | 105 passed across 10 files |
| TypeScript, ESLint and production build | Passed |
| Playwright production-browser checks | 46 passed: desktop, mobile and additional tablet layout checks |
| Automated accessibility | No axe WCAG 2 A/AA or 2.1 AA violations on 14 routes at desktop and mobile widths |
| Data navigation and export | All 20 dataset views load; filters, tables, full-precision exports and immutable source URLs verified |
| Previous frontend observations | All 16,541 observation records in the earlier 13 datasets unchanged; source URLs deliberately repinned |
| Scientific preservation | No changes to research `src/`, root `tests/`, primary archives or frozen protocol/theory/source files |
| Publication review | No credentials or private-machine paths in changed publishable files; local Markdown links resolve |

`npm run check` completed as one end-to-end command. Browser tests use the
production build under the GitHub Pages repository base path. They cover navigation
through all seven experiments to the synthesis, reading levels, closure statements,
quantum model/size controls, dynamical gate counts, the tiny conditional valid mass,
keyboard navigation, reduced motion, mobile menus and document overflow.

The final review corrected three presentation issues: the active gate's text
contrast; a missing explicit warning about Model A's degenerate MDS basis; and
one-sided confidence bounds that had previously been omitted from chart marks.
One-sided bounds now have explicit caps/arrows, labels and inspector text without
an invented second endpoint. Incomplete two-sided intervals remain unavailable,
not reclassified as one-sided evidence. Tests include the actual quantum-chain
lower bounds and existing adverse two-sided intervals.

Quantum summaries retain 60 wholly undefined selected metrics as explicit null
rows with their recorded undefined counts. Bootstrap undercoverage, deterministic
states without ensemble intervals, dependent times/targets and the distinction
between conditional and unconditioned response are disclosed in the UI and exports.
No browser quantum evolution, new research cohort or fitted scientific criterion
was introduced.

Visual review includes [desktop synthesis](docs/screenshots/desktop-synthesis.png),
[mobile synthesis](docs/screenshots/mobile-synthesis.png),
[Experiment 6](docs/screenshots/desktop-experiment-6.png),
[Experiment 7](docs/screenshots/desktop-experiment-7.png), and the updated
[home page](docs/screenshots/desktop-home.png). Screenshots document the current
appearance, rather than acting as golden-image approvals. Large historical
conditional datasets remain lazy chunks; the existing Vite chunk-size advisory
is retained rather than silenced. Automated checks do not certify every device
or assistive technology.

The original verification below is retained as historical context. Its old counts,
source pin and deployment observations describe the initial five-experiment atlas.
Current screenshots at shared filenames reflect the completed seven-experiment UI.

---

# Initial atlas verification — historical Experiments 1–5

Verified 25 October 2026. Scientific baseline: `9bc5984c656271c247354e0079fd900702642064` (the verified main merge of Experiment 5). The application is isolated under `apps/research-atlas`; the only changes outside it are the README entry and the new frontend workflow.

| Check | Result |
| --- | --- |
| Existing Python suite, `.venv/bin/python -m pytest -q` | 813 passed |
| Reproducible baseline CLI, seed 20261025, 100 repeats | Completed; deterministic CSV/plots under ignored `results/atlas-baseline` |
| Frontend `npm test` | 82 passed, across numerical, React, editorial, chart and data tests |
| `npm run data:check` | 13 Python checks; deterministic generated artifacts match source locks |
| TypeScript | Passed |
| ESLint | Passed |
| `npm run build` | Passed; static production bundle |
| Playwright, desktop and 390px mobile | 34 passed |
| axe WCAG 2 A/AA and 2.1 AA scans | No violations on all 11 routes at both viewport sizes |
| Layout | No document-level horizontal overflow on all routes and all 13 dataset tables |
| Dependencies | npm audit reported zero vulnerabilities |
| Scientific archive preservation | `git diff 9bc5984 -- src tests docs pyproject.toml AGENTS.md` empty |
| Public-source review | No credentials, personal email addresses or private-machine paths in publishable application sources |

Tests use the production build at the repository base path, not the development server. Hash navigation, reading-level changes, causal rules, deterministic replay, the growth cap, keyboard graph inspection, mobile dialog focus, reduced motion, uncertainty endpoint preservation, valid empty states, dataset filters, full-precision CSV/JSON export and immutable source links are exercised. Export checks read the downloaded files and validate their rows and provenance.

The misleading height-two model is independently checked by exhaustively weighting all four-event iid layer/edge configurations: its exact 2+2 probability is 1/24 despite height ≤ 2 and zero 3+1. Python fixtures independently validate geometry, longest-chain normalization and the dimension reference formula. Small illustrative browser samples do not receive fabricated confidence intervals.

Visual QA inspected desktop/mobile home and the growth/evidence experiences. Reviewed screenshots are in [docs/screenshots](docs/screenshots/): [desktop home](docs/screenshots/desktop-home.png), [mobile home](docs/screenshots/mobile-home.png), [evidence map](docs/screenshots/desktop-evidence.png), [growth experiment](docs/screenshots/desktop-growth.png). Screenshots are generated artifacts, not pixel-perfect golden tests; no screenshot approval assertion hides layout failures.

## Findings corrected during review

- Misaligned education concept IDs rendered the wrong demo; all 13 dispatches now have tests.
- A mixed-metric selection could plot incomparable units; charts require one metric while tables/exports retain all rows.
- Decorative experiment numerals had insufficient contrast; desktop contrast was increased and mobile decoration removed.
- Chart point selection could persist after filtering; filter changes now clear the inspector.
- Detector C’s explanation was corrected to the registered RMS combination, including compensation.
- Overlap demonstrations now require shared interval interiors or report no qualifying overlap.
- Artificial time controls no longer show physical coordinate axes.
- Data are loaded per dataset and losslessly packed; the complete growth archive is not downloaded for the time lesson.
- New later-experiment documentation does not invalidate this pinned first-five data snapshot; modified selected data still fail verification.

## Deployment state and limits

GitHub Pages is configured for GitHub Actions at https://raghammer1.github.io/causal-spacetime-lab/ . The feature branch is not deployed. After PR review and merge, the frontend workflow validates `main`, uploads the built static artifact, and deploys it. There was no existing Pages content to replace. No automatic merge is configured.

The largest lazily loaded conditional dataset is approximately 1.8 MB uncompressed (333 KB gzip); Vite reports a chunk-size advisory for the two complete conditional tables. These are data chunks loaded only on request, not the initial application bundle. Full raw research archives remain linked. The UI caps plots at 240 defined rows and directs larger views to filters/tables/exports. The browser growth demo caps at 48 events.

Automated accessibility testing and keyboard checks do not certify every browser, device or assistive technology. The checked screenshots and test matrix document the actual verification performed.
