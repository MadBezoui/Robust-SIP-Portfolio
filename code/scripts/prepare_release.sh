#!/usr/bin/env bash
# Pre-flight check before tagging the release that Zenodo will archive.
#
# HOW ZENODO UPDATES
#   Zenodo's GitHub integration fires on the "release published" webhook only.
#   Pushing commits does not trigger it, and pushing a tag on its own does not
#   either -- you must publish a GitHub Release.  Zenodo then archives GitHub's
#   source zipball of that tag, i.e. exactly the committed tree.  Files attached
#   to the release as assets are NOT archived, so everything that must end up in
#   the Zenodo record has to be committed and pushed first.
#
#   The integration is already enabled for this repository: v1.2.0 through
#   v1.6.0 were archived automatically.  Concept DOI 10.5281/zenodo.21957758
#   always resolves to the newest version, and that is the DOI the manuscript
#   cites -- so the citation becomes correct as soon as the release is
#   published, with no further edit to the PDF.
#
# Usage:  bash scripts/prepare_release.sh

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
TAG="v1.7.1"
status=0

ok()   { printf '  ok       %s\n' "$*"; }
fail() { printf '  MISSING  %s\n' "$*"; status=1; }

echo "== 1. Every path the manuscript documents exists =="
for f in \
  src/RobustSIP.jl \
  scripts/01_run_backtest.jl \
  scripts/02_evaluate_performance.jl \
  scripts/03_statistical_inference.jl \
  scripts/generate_publication_figures.py \
  scripts/validate_manuscript.py \
  Project.toml \
  Manifest.toml \
  data/aligned_market_data.csv \
  results/performance_table.csv \
  results/tc_sensitivity.csv \
  results/crisis_performance.csv \
  results/bootstrap_inference.csv \
  results/block_length_sensitivity.csv \
  results/ess_full_backtest.csv \
  results/ess_sensitivity.csv \
  results/grid_sensitivity.csv \
  results/bandwidth_sensitivity.csv \
  results/gap_verification.csv \
  results/active_states_history.csv \
  CITATION.cff \
  LICENSE ; do
  [ -f "$f" ] && ok "$f" || fail "$f"
done

echo
echo "== 2. Nothing needed is left uncommitted =="
dirty=$(git status --porcelain -- src scripts data results Soumission \
        Project.toml Manifest.toml CITATION.cff LICENSE main_exp.jl 2>/dev/null || true)
if [ -n "$dirty" ]; then
  echo "  still to 'git add' + 'git commit':"
  printf '%s\n' "$dirty" | sed 's/^/    /'
  status=1
else
  ok "working tree clean for everything that goes into the archive"
fi

echo
echo "== 3. Manuscript tables reproduce from the archived CSVs =="
( cd scripts && python3 validate_manuscript.py ) || status=1

echo
if [ "$status" -ne 0 ]; then
  echo "NOT READY -- resolve the items above first."
  exit 1
fi

cat <<EOF
READY. Run, from $ROOT:

  git add -A
  git commit -m "Submission bundle: regenerated figures, table cross-checks, v1.7.1"
  git push origin main

  # Zenodo reacts to the published release, not to the push:
  git tag -a $TAG -m "Submission bundle for Computational Optimization and Applications"
  git push origin $TAG
  gh release create $TAG --title "$TAG" \\
     --notes "Code, data and numerical outputs underlying the submitted manuscript."

To cite the immutable snapshot rather than the concept DOI, take the version
DOI that Zenodo returns and replace it in Soumission/references.bib (doi and
url of bezoui2026robust) and in CITATION.cff, then rebuild the PDF.
EOF
