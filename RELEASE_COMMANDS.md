# Release commands — your side

The manuscript, `README.md` and `CITATION.cff` all cite the **concept DOI**
`10.5281/zenodo.21957758`. It resolves to whatever the newest Zenodo version is,
so **none of them needs editing when you publish a release**. The bibliography
entry no longer names a release and the Data Availability statement no longer
names a Git commit, so there is nothing version-specific left in the paper.
Bump only `version:` and `date-released:` in `CITATION.cff`.

## 1. Check before tagging

```bash
python3 code/scripts/validate_manuscript.py --tex soumission/main_paper.tex
```

Must print `0 failed` (currently 442 checks). It parses every numerical table
out of the `.tex` and compares it cell by cell with `code/results/*.csv`, and it
fails loudly if a table layout is not recognised or a strategy row is missing,
rather than passing vacuously.

## 2. Commit and push

```bash
git add -A
git commit -m "Referee revision: scalability study, return-target and bandwidth sensitivities, regularized conditional comparator"
git push origin main
```

## 3. Tag and release — this is what triggers Zenodo

Zenodo's GitHub integration fires on the **release published** webhook only. A
plain push does not trigger it, and neither does pushing a tag on its own.
Zenodo archives GitHub's source zipball of the tag, so only committed content is
archived; assets attached to the release are ignored.

```bash
git tag -a v1.9.0 -m "Referee revision for Computational Optimization and Applications"
git push origin v1.9.0
gh release create v1.9.0 --title "v1.9.0" \
   --notes "Manuscript prepared for submission to Computational Optimization and Applications. Code, data and numerical outputs behind the submitted version."
```

Keep "prepared for submission" wording in the release notes — earlier notes said
"(*Computational Optimization and Applications*, 2026)", which reads as if the
paper were already published.

## 4. After Zenodo has ingested

Nothing to change in the manuscript. Optionally bump in `CITATION.cff`:

```yaml
version: 1.9.0
date-released: 2026-09-07
```

The version-specific DOI Zenodo mints is only needed if you ever want to pin an
exact snapshot in a reply to referees.

## 5. Regenerating results

Baseline pipeline:

```bash
cd code/scripts
julia 01_run_backtest.jl          # ~3 h; 18 MinVar windows hit the 600 s limit
julia 02_evaluate_performance.jl
julia 03_statistical_inference.jl
julia 04_experiment_A_matched_dense_vs_adaptive.jl   # matched dense vs exchange, 3 grids
julia gap_verification.jl         # 1001x1001 dense reference grid
```

Revision experiments, each on the identical 377-window calendar:

```bash
cd code/scripts
julia run_referee_benchmarks.jl   # hull-restricted SIP and state-conditioned CVaR
julia run_domain_sensitivity.jl   # state-domain expansion margin, delta in {0,5,10,20}%
julia run_target_sensitivity.jl   # expected-return target: non-binding, Q25, Q50, Q75
julia run_shrinkage_benchmark.jl  # regularized conditional CVaR, lambda in {0,.25,.5,.75,1}
julia run_bandwidth_geometry.jl   # diagonal versus full-covariance bandwidth
python3 run_riskfree_sensitivity.py                  # Sharpe at rf = 0, 2, 4 percent
```

Then figures and the cross-check:

```bash
cd code/scripts
python3 generate_publication_figures.py --submission ../../soumission
python3 validate_manuscript.py --tex ../../soumission/main_paper.tex
```

Runtimes: the three Julia revision experiments that re-solve the robust SIP
(`run_target_sensitivity.jl`, `run_domain_sensitivity.jl`,
`run_bandwidth_geometry.jl`) each cost roughly one full backtest pass per
specification. `run_shrinkage_benchmark.jl` is much cheaper, being plain LPs
with no exchange loop.

## 6. Rebuilding the manuscript

```bash
cd soumission
pdflatex -interaction=nonstopmode main_paper.tex
bibtex main_paper
pdflatex -interaction=nonstopmode main_paper.tex
pdflatex -interaction=nonstopmode main_paper.tex
```

Check the log afterwards; all four counts must be zero:

```bash
cd soumission && for k in '^!' 'undefined' 'multiply' 'Overfull \\hbox'; do \
  printf '%-18s %s\n' "$k" "$(grep -ci "$k" main_paper.log)"; done
```

Note that `\resizebox` and `adjustbox` shrink a wide table rather than
overflowing, so a zero overfull count does not prove a table is legible. Two
tables use `adjustbox`; look at the rendered page after changing either.

## 7. Repackaging for Editorial Manager

```bash
cd soumission
rm -f submission_package.zip
zip -q submission_package.zip cover_letter.pdf main_paper.pdf main_paper.tex \
  references.bib main_paper.bbl svjour3.cls svglov3.clo highlights.pdf Fig{1,2,3,4,5,6,7,8,9,10,11,12,13,14}.pdf
```

Then unpack it into an empty directory and compile there before uploading.
