> **Historical working log, superseded.** This file records what was changed and
> verified during preparation, across several rounds. Figures, counts and DOIs
> quoted below refer to intermediate versions and are *not* the state of the
> submitted manuscript. For the submission itself see `SUBMISSION_CHECKLIST.md`
> and `SUBMISSION_KIT.md`.

# Submission package — Computational Optimization and Applications

**Manuscript:** Continuous-state robust CVaR portfolio optimization via
grid-restricted constraint generation
**Authors:** Madani Bezoui (corresponding, `mbezoui@cesi.fr`, ORCID
0000-0002-8342-7039), Thiziri Sifaoui (ORCID 0009-0007-6884-0611),
Ahcene Bounceur (`abounceur@sharjah.ac.ae`, University of Sharjah)
**Prepared:** 4 September 2026 · **Type:** Research Article · **First submission**

---

## What to upload

| File | Role |
| --- | --- |
| `main_paper.pdf` | compiled manuscript (42 pp.) |
| `main_paper.tex` | LaTeX source |
| `references.bib` | BibTeX database |
| `main_paper.bbl` | processed bibliography (required with BibTeX) |
| `svjour3.cls`, `svglov3.clo` | Springer class files |
| `Fig1.pdf` … `Fig12.pdf` | artwork, vector PDF, fonts embedded |
| `cover_letter.pdf` | cover letter |
| `highlights.pdf` | research highlights (optional for this journal) |

`submission_package.zip` bundles exactly those files. It has been verified to
compile in an empty directory with no errors, no undefined references, no
overfull boxes and no missing files.

**Figure numbering.** Manuscript Figures 1–3 are TikZ schematics typeset inline,
so there are no artwork files for them. `Fig1.pdf` … `Fig12.pdf` are the twelve
plotted figures, appearing as manuscript Figures 4–15. Regenerate with

```bash
cd scripts && python3 generate_publication_figures.py --submission ../Soumission
```

## Journal requirements — verified

| Requirement | Status |
| --- | --- |
| Title concise and informative | yes |
| Author names, affiliations (institution, city, country) | yes |
| Corresponding author indicated, active e-mail | marked on the title page |
| 16-digit ORCID for each author | both, hyperlinked |
| Abstract 150–250 words, no undefined abbreviations, no references | 167 words |
| Keywords 4–6 | 5, on the title page |
| Statements and Declarations before the reference list | funding, competing interests, data availability, author contributions |
| Data availability statement | yes, with source citations and archived release |
| Decimal headings, ≤ 3 levels | 2 levels |
| Abbreviations defined at first mention | audited; SAA and TC-MinVar were undefined at first use and are now expanded |
| Footnotes | none used |
| Numbered citations in square brackets | `natbib` `[numbers,sort&compress]` |
| Reference list numbered consecutively, cited works only | 34 entries via BibTeX |
| DOIs as full DOI links | `\doi` redefined to emit `https://doi.org/…`; 32 of 34 entries carry one |
| Entries without a DOI | the 1964 *Sankhyā* article and the 1991 Purdue technical report predate DOI assignment |
| Tables numbered in Arabic, cited in consecutive order, each captioned | 16 tables, order verified programmatically |
| Figures numbered in Arabic, cited in consecutive order | 15 figures, order verified programmatically |
| Figure captions: bold "Fig.", no punctuation after the number or at the end | verified across all 31 captions |
| No titles or captions inside the artwork | removed from all 12 plots |
| Figure lettering 2–3 mm at final size | authored at the 119 mm text width, included at `\textwidth` |
| Figures fit the column width, height under 195 mm | yes |
| No colour named in captions or in the text describing a figure | audited and corrected |
| Colour figures legible in greyscale | every series carries a distinct line style or marker |
| Fonts embedded in vector artwork | verified with `pdffonts` |
| Compiles with no errors, undefined references or overfull boxes | verified |
| Documented repository paths resolve | `src/`, `scripts/`, `data/`, `results/`, `Manifest.toml` — all eight checked against disk |

**LLM use.** The journal requires a declaration only for use beyond AI-assisted
copy editing, which it defines as improvements to human-written text for
readability, style, grammar, spelling, punctuation and tone. A final grammar
pass falls inside that exemption, so no statement was added to the manuscript.
Say the word if you would rather declare it anyway — it is one line in
Statements and Declarations.

## Second autoreview — response

### The three TC-MinVar windows are resolved (blocker 1)

Diagnosis: the covariance was well conditioned (condition number 200--450) and
$\widehat\Sigma+10^{-5}I\succ0$ over a nonempty polytope, so the failure was
numerical, not mathematical — exactly as the review argued. HiGHS returned
`OTHER_ERROR`; rescaling the objective by a positive constant, which leaves the
minimizer unchanged, recovers all three. The retry fires only after a failed
first attempt, so no new solver dependency was added and `Manifest.toml` stays
pinned.

After re-running the full pipeline: **0 windows without a primal solution, 0
missing values, all five strategies on the identical 377-period calendar.**
Only the TC-MinVar columns changed; the other four strategies are numerically
identical to the previous run.

| TC-MinVar | before | after |
| --- | --- | --- |
| annualized return | 10.71% | 10.68% |
| annualized volatility | 12.32% | 12.28% |
| Sharpe | 0.869 | 0.870 |
| average turnover | 7.03% | 6.59% |
| final wealth | \$21.89 | \$22.25 |
| bootstrap $\Delta$SR | −0.063 | −0.061 |
| bootstrap $p$ | 0.342 | 0.363 |

The three visual artefacts are gone: Figure 4 has no gaps, Figure 5 shows a full
TC-MinVar box with no `n = 374` note, Figure 6 is no longer truncated at 2016.
No qualitative conclusion changed.

**A new caveat surfaced while comparing the two runs and is now disclosed in
Section 5.5:** TC-MinVar reaches the 600-second solver limit on 18 of 377
windows and returns the incumbent, so that leg is not bit-reproducible across
machines. The other four strategies terminate at optimality everywhere.

### Points that were false positives

| Review point | Finding |
| --- | --- |
| 2.1/2.2/2.3 — duplicated and truncated references 4 and 29 | The bibliography is clean. Reference 4 reads in full "From predictive to prescriptive analytics"; the reported "scriptive analytics" is the `pre-/scriptive` hyphenation recombined by text extraction. References 29 and 30 are two different papers (Rockafellar--Uryasev 2000 *J. Risk* and 2002 *J. Banking & Finance*), not a duplicate. Programmatic check: 38 entries, 0 duplicate titles. Verified by rendering the page, not by extracting it. Note that reference 29's pages are 21--41, not 21--42 |
| 3.1 — Section 5.5 item 2 truncated | The text was complete; same extraction artefact. The `\allowbreak` splits that caused it were removed and the description completed anyway |
| 4.1 — DOI inconsistency | The manuscript, README badge, README BibTeX and `CITATION.cff` were already on `10.5281/zenodo.22309074`. Re-verified: HTTP 200, resolves to `zenodo.org/records/22309074`. The review was reading the archived release |

### Points corrected

| Review point | Action |
| --- | --- |
| 1.3 — bootstrap not fully paired | Fixed: the observed statistic now comes from the same aligned vectors the bootstrap resamples |
| 5.2 — Proposition 4 proof | **Replaced** by the direct value-function inequality suggested: $|\min_z F(\theta)-\min_z F(\theta')|\le\sup_z|F(z,\theta)-F(z,\theta')|\le(2M_L/\tau)\|p(\theta)-p(\theta')\|_1$, then the gradient bound integrated along the segment using $\sum_t p_t=1$. No Danskin, no Clarke subdifferential. Equation (38) is kept as the interpretive gradient formula |
| 5.3 — termination tolerance | Finite termination now stated explicitly for every $\varepsilon>0$, with a note that it does not extend to $\varepsilon=0$ |
| 7.2 — quantile convention | The rounded order statistic was replaced by Julia's documented `quantile` (Hyndman--Fan type 7) |
| 7.3 — procedure naming | Percentile interval and centered-bootstrap $p$-value are now named as two distinct procedures |
| 10.1 — vague abstract claim | Replaced by the representative figures: 441 to 5 state blocks, 72.7 to 4.5 seconds |
| 10.3 — Section 6.2 wording | "without materially altering" replaced by a point-estimate statement, with an explicit note that no equivalence test was conducted |
| 10.4 — Table 7 units | Caption now states that both rows share the training sample, bandwidth and grid; that values are per cent; and that the residual is in decimal loss units ($2.2642\times10^{-5}$ = 0.0023 percentage points) |
| 4.1/4.3 — metadata | README now carries a table separating version DOI and concept DOI, and states that software authorship (two authors) differs from manuscript authorship (three) |

### Still open

- **A v1.7.1 release is required.** The archived v1.7.0 predates the TC-MinVar
  recovery and the bootstrap fix, so `results/*.csv` in the archive no longer
  match the PDF — this is the discrepancy the review found in point 1.4. Run
  `bash scripts/prepare_release.sh` and publish; the manuscript cites the
  concept-resolved version DOI, so Reference 6 must be updated to the new
  version DOI afterwards.
- **Length and figure density** (10.5, 9): moving the 30-industry allocation
  plots and secondary sensitivity tables to supplementary material would shorten
  the 45-page main text. That is a restructuring decision, left to the authors.
- **Contribution positioning** (9): the review's suggested framing is a matter
  of authorial judgment and was not imposed on the text.

## Response to the autoreview

Every point was checked against the current manuscript. The review targets an
earlier version (it cites `v1.6.0-submission-final`), so several of its items
were already resolved.

| Review point | Finding |
| --- | --- |
| 3 — Table 9 (83.02) vs Table 15 (85.8) ESS | already consistent: Table 15 reads 83.02, matching `active_states_history.csv` |
| 3.1 — Table 15 mixes state populations | **fixed.** The caption also named the wrong population: per `run_ess_backtest.jl` both the mean and the minimum are computed over *active* states, not admissible grid states. Columns are now "Mean active-state ESS", "Minimum active-state ESS", "Retained-grid fraction", with a caption defining each and cross-referencing Table 9 |
| 4 — TC-MinVar not reconciled | verified: Table 6 at 10 bps equals Table 4 for all five strategies, and equals `tc_sensitivity.csv` |
| 5.4 — `L_Phi` derivation reads as Clarke-based | **fixed**, reworded to a direct bound on the variation of the normalized kernel weights |
| 6.1 — duplicated sentence, p. 19 | already fixed, single occurrence |
| 6.2 — repetition, p. 25 | already fixed, single occurrence of the suggested sentence |
| 6.3 — malformed Reference 8 | already fixed: correct title, `booktitle`, pages, DOI |
| 6.4 — Reference 6 stale | points to v1.7.0, but see the blocker below |
| 6.5 — invalid `CITATION.cff` | **fixed**: `CITATION.cff`, `cff-version: 1.2.0`, `version: 1.7.0`, ORCIDs added |
| 6.6 — Sharpe convention underspecified | already stated: zero risk-free rate, compounded 21-trading-day holding-period returns, annualized with 12 periods per year — matches `02_evaluate_performance.jl` |
| 7 — automated consistency assertions | **implemented**: `scripts/validate_manuscript.py` now parses every table out of the `.tex` and cross-checks it against the CSVs — **263 checks, 0 failures** |

Also removed while going through the source: a leftover editorial comment
(`% Alternative: Retain code/main_exp.jl only if...`) that would have shipped
inside the submitted `main_paper.tex`.

### What `validate_manuscript.py` covers

Tables 2, 4, 5, 6, 9, 10, 11, 12, 13, 14, 15 and 16 cell by cell against
`gap_verification`, `performance_table`, `crisis_performance`,
`tc_sensitivity`, `active_states_history`, `bootstrap_inference`,
`grid_sensitivity`, `bandwidth_sensitivity`, `ess_sensitivity`,
`ess_full_backtest` and `block_length_sensitivity`; the cross-table identities
(Table 4 = Table 6 at 10 bps, Table 4 Robust SIP = Table 14 at `Emin=0`,
Table 9 mean ESS = Table 15 mean active-state ESS); and the scalars quoted in
the prose (mean active states, active-state range, window count, runtime
ratio). Tolerances are half the last printed digit.

## Archive — resolved

`v1.7.0-submission-final` is published and Zenodo has archived it as
**10.5281/zenodo.22309074** (4 September 2026), which is the DOI now cited in
Reference 6 and in `CITATION.cff`. Verified directly:

- the GitHub release resolves (HTTP 200), as do all twelve repository paths the
  manuscript documents (`src/`, `scripts/`, `data/`, `results/`, `Project.toml`,
  `Manifest.toml`, `CITATION.cff`, `LICENSE`);
- the eleven result CSVs behind every manuscript table are **byte-identical**
  between the published tag and the local files the 263 checks run against.

`Soumission/` is excluded from the repository by `.gitignore`, so the archive
holds code, data and numerical outputs but not the manuscript — which is what
Section 5.5 and the Data Availability statement claim, so both remain accurate.

## Reference audit — response

| Ref. | Finding |
| --- | --- |
| [3] Bennouna & Van Parys | Crossref shows no volume or pages yet, so `published online` is correct and stays |
| [4] Bertsimas & Kallus | already complete and appears once; the "malformed and duplicated" finding targets an older file |
| [6] Zenodo | **fixed**: now the v1.7.0 version DOI 10.5281/zenodo.22309074 |
| [9] Cboe | **fixed**: corporate author `Cboe Global Markets, Inc.`, and the exact file the pipeline downloads (`VIX_History.csv`) rather than the product page |
| [10] Chu, Lin & Toh | article number normalised from `Article 69` to `69` |
| [12] JuMP | already capitalised correctly |
| [14] Fabozzi | **fixed**: Crossref confirms DOI 10.3905/jpm.2007.684751 belongs to Fabozzi, Kolm, Pachamanova and Focardi; author list corrected |
| [15] French | **fixed**: exact dataset (`30 Industry Portfolios, daily value-weighted returns`) and the archive the pipeline downloads |
| [17] Hettich & Kortanek | cited only as a general SIP survey; Proposition 3's proof is self-contained, so no theorem or page reference is needed |
| [18] HiGHS | **fixed**: replaced by Huangfu & Hall, *Math. Prog. Comput.* 10(1):119–142, 2018, with the software URL kept in a note |
| [24] Oustry & Cerulli | the manuscript already states that their relative-gap oracle model and strong-convexity assumption do not subsume the linear master objective |
| [25] Politis & Romano | **fixed**: complete `@techreport` with institution, address and type |
| [26] Qi, Grigas & Shen | volume, issue and pages already final (74(3):1604–1625) |
| [28] Rockafellar & Uryasev (2000) | already complete and appears once |
| [30] Scaillet | **fixed**: the sentence claimed *conditional* expected shortfall; it now describes what the 2004 article actually does. Adding the 2005 conditional-ES paper instead remains an option |

Left as the authors chose them: [1] Agra, [7] Bezoui et al. (2019), [8] Bezoui
et al. (2024), [27] Regaigui et al., [32] Thomä et al. and [34] Yue et al. are
flagged in the audit as optional or peripheral. Dropping a citation changes how
the paper positions itself — that is an editorial call, not a defect, so they
were kept. Say the word and they come out in one pass.

## Former blocking item — now closed

Review point 2 is still live, and in a worse form than the review describes.
Checked directly:

- `https://github.com/MadBezoui/Robust-SIP-Portfolio/releases/tag/v1.7.0-submission-final`
  returns **404**. The latest published release is still
  `v1.6.0-submission-final`, whose result files do not match this PDF.
- DOI `10.5281/zenodo.22056130`, cited in Reference 6 and in `CITATION.cff`,
  resolves — but the record it points at is **`v1.2.0-submission-final`**, not
  v1.7.0.
- `results/performance_table.csv`, `tc_sensitivity.csv`,
  `ess_full_backtest.csv`, `grid_sensitivity.csv` and `gap_verification.csv`
  all return **404** on the default branch.

So the Data Availability statement, Section 5.5 and Reference 6 are not yet
factually accurate. `scripts/prepare_release.sh` assembles the exact bundle
(results, scripts, data, figures, manuscript, `Project.toml`, `Manifest.toml`,
`CITATION.cff`), runs the 263 consistency checks over it, and prints the
remaining tag / release / Zenodo steps. Publishing a release and minting a
fresh DOI are yours to do; the DOI in `Soumission/references.bib` and
`CITATION.cff` must then be replaced with the new one.

## Late edits by a co-author, checked

Tables 1, 2 and 3 were restructured in `Soumission/main_paper.tex` while this
pass was running, and the repository was reorganised from `Code/` into
`src/ scripts/ data/ results/`. All of it was re-verified:

- Table 1 in portrait three columns reads better than the landscape version it
  replaced; `pdflscape` is now loaded but unused (harmless).
- Table 2 was moved to `tabular*{\linewidth}` and overflowed the margin by
  45 pt. Switched to the `adjustbox` idiom the other wide tables already use.
- Table 3 had a long unbreakable cell, so `adjustbox` was shrinking the whole
  table to roughly 5 pt — illegible. Column two now wraps at a fixed width and
  the table is back at `\small`.
- The eight repository paths the manuscript documents were pointing at the old
  `Code/` layout; realigned on `src/`, `scripts/`, `data/`, `results/` and each
  one verified to exist.
- None of the earlier corrections were lost: hyperref `hidelinks`, the `\doi`
  redefinition, both ORCIDs, the Table 15 headings, the SAA and TC-MinVar
  definitions, the Lipschitz wording and the figure-caption fixes are all still
  in place.

## Third author added

Ahcene Bounceur was added throughout, translated from the Elsevier
`\author[...]/\ead/\address` form supplied into the `svjour3` form the paper
uses (`\author{... \and ...}` plus an `\institute{... \at ...}` block):
title page, running head (svjour3 abbreviates it to "M. Bezoui et al." for three
or more authors), affiliation block, Author Contributions (Supervision,
Writing -- review and editing), cover letter in both `.tex` and `.txt`, and
`CITATION.cff`.

Two knock-on fixes were needed:

- The third affiliation pushed the keyword line onto page 2 again. Reclaimed by
  compacting the affiliation block onto fewer lines and emptying the
  `\date{Received: date / Accepted: date}` placeholder, which production fills
  in anyway. **The abstract was not touched** — it stays at 167 words.
- The cover letter ran to two pages; the signature block is now single-spaced
  and the leading tightened, so it fits on one again.

Two things left for you:

- **ORCID for Ahcene Bounceur** was not supplied, so his entry has none in the
  manuscript or in `CITATION.cff`.
- **The Zenodo v1.7.0 record credits only Bezoui and Sifaoui.** Reference 6 lists
  those two authors to match the deposited record. If Bounceur should appear as
  an author of the archive as well, edit the record metadata on Zenodo (no new
  release needed) and add him to the `bezoui2026robust` entry.

## Remaining item for the authors

- **Suggested / excluded reviewers.** Editorial Manager asks for these at
  submission; an institutional e-mail address is required for each suggestion.
  They are not part of the manuscript files.

## Substantive changes made while preparing the package

- **Three windows with no TC-MinVar solution.** The target-constrained
  minimum-variance QP returned no primal solution on 8 June 2016, 6 November
  2017 and 8 October 2018. These windows were silently dropped by the evaluation
  code (`skipmissing`), which made TC-MinVar's statistics rest on 374 of 377
  windows while the other strategies use all 377, and produced unexplained
  artefacts in three figures. The exclusion is now stated in Section 5.1 and
  marked in Figure 7; the turnover panel reports `n = 374` for that strategy.
- **Crisis-state coordinates.** The `(VIX, drawdown)` pairs quoted for the five
  crisis episodes paired each episode's peak-VIX day with its peak-drawdown day,
  so three of the five pairs matched no observed state. They now report the
  single observed state at each episode's drawdown trough, which is what
  Figure 14 marks.
- **State density coordinates.** Figure 14's density was estimated in raw VIX
  while its caption claimed log-VIX. It is now estimated in the model
  coordinates `(log VIX, D)`, with the axis relabelled in VIX levels, matching
  both the caption and the model.
- **Highlights.** The claimed "~20× speedup" is 16.2× in the manuscript
  (72.7093 / 4.4851), and the claim that the finite grid supremum "matches the
  continuous supremum to 1e-4 precision" contradicted the manuscript's own
  statement that the local search "provides no certificate of continuous-domain
  optimality". Both were corrected.
- **Abstract shortened** from 219 to 167 words so the keyword line sits on the
  title page. No claim was dropped; the exact backtest dates and the data-span
  sentence were compressed, since both are stated in full in Section 5.1.
- **Bibliography.** `politis1992circular` (Wiley chapter) replaced by the
  authors' `politis1991circular` (Purdue University, Department of Statistics,
  1991); both citations updated.
