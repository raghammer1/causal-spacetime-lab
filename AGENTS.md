# Codex research rules

1. Treat this repository as an educational exploratory numerical physics lab. Distinguish established theory, numerical demonstrations, conjectures and measured evidence explicitly.
2. Never claim a toy simulation proves spacetime is discrete, gravity is emergent, or a black-hole singularity is resolved.
3. Work in an experiment branch for nontrivial changes; keep `main` a reproducible verified baseline, PR-only merges after initial publication.
4. Before experiments, document falsifiable hypothesis, independent controls, expected outcomes and failure conditions.
5. All stochastic experiments require deterministic seeds, parameter sweeps, uncertainty estimates and machine-readable results.
6. Use Python 3.10+, NumPy, Matplotlib, pytest; add dependencies only when justified. Keep a lightweight package and readable API.
7. Every conceptual and numerical claim must either be derived, tested, or labeled as speculation; cite original scientific work where applicable.
8. Never embed personal information, authentication tokens or private repository content. Review changes and secrets before public publishing.
9. Validate `python -m pytest -q` and one end-to-end reproducible CLI experiment prior to commits.
