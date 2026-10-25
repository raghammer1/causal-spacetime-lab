#!/usr/bin/env bash
# Run from this repository root on a machine authenticated to GitHub CLI.
# This script intentionally refuses to overwrite an existing GitHub repository.
set -euo pipefail
REPO='raghammer1/causal-spacetime-lab'
cd "$(dirname "$0")/.."
if ! command -v gh >/dev/null; then
  echo 'GitHub CLI is missing. Install with: brew install gh'; exit 1
fi
if ! gh auth status >/dev/null 2>&1; then
  echo 'GitHub CLI is not authenticated. Run: gh auth login'; exit 1
fi
if gh repo view "$REPO" >/dev/null 2>&1; then
  echo "GitHub repo $REPO already exists; refusing to overwrite anything."; exit 1
fi
if [ ! -d .git ]; then
  git init -b main
fi
if git remote get-url origin >/dev/null 2>&1; then
  echo 'Origin remote already exists; inspect it manually before publishing.'; exit 1
fi
if [ -n "$(git log -1 --format=%h 2>/dev/null || true)" ]; then
  echo 'A local git history exists; inspect before publishing.'; exit 1
fi
printf 'About to create PUBLIC GitHub repository %s from this directory.\n' "$REPO"
printf 'Inspect README.md, notebooks and all files for private information first.\n'
read -r -p 'Continue? [y/N] ' answer
if [[ "$answer" != y && "$answer" != Y ]]; then
  echo 'Cancelled'; exit 1
fi
git add .
if git diff --cached --name-only | grep -E '(^|/)(\.env|.*\.pem|.*\.key|results/)' >/dev/null; then
  echo 'Potentially sensitive or generated files staged. Aborting.'; exit 1
fi
printf '\nFiles to publish:\n'
git diff --cached --name-only
git commit -m 'Initial reproducible causal spacetime experiments'
gh repo create "$REPO" --public --source=. --remote=origin --push
gh repo view "$REPO" --web
