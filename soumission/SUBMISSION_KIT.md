# Submission kit — Computational Optimization and Applications

**Continuous-state robust CVaR portfolio optimization via grid-restricted
constraint generation**
Madani Bezoui (corresponding), Thiziri Sifaoui, Ahcene Bounceur
Research Article · first submission

---

## 1. What to upload, in Editorial Manager order

| Order | Item type in EM | File |
| --- | --- | --- |
| 1 | Cover Letter | `cover_letter.pdf` |
| 2 | Manuscript (PDF for review) | `main_paper.pdf` |
| 3 | LaTeX source | `main_paper.tex` |
| 4 | Bibliography source | `references.bib` |
| 5 | Processed bibliography | `main_paper.bbl` |
| 6 | Style files | `svjour3.cls`, `svglov3.clo` |
| 7 | Figures | `Fig1.pdf` … `Fig14.pdf` |
| 8 | Highlights (optional) | `highlights.pdf` |

`submission_package.zip` contains exactly these 22 files. The journal requires
"the original source (including all style files and figures) and a PDF version
of the compiled output" — that is what the zip holds. It has been unpacked into
an empty directory and compiled there: 43 pages, no error, no undefined
reference, no duplicate label, no overfull box, nothing missing.

**Figure numbering.** Manuscript Figures 1–3 are TikZ schematics typeset inline,
so no artwork file corresponds to them. `Fig1.pdf` … `Fig14.pdf` are the
fourteen plotted figures, appearing as manuscript Figures 4–17.

## 2. What Editorial Manager asks for that is not in a file

- **Corresponding author:** Madani Bezoui, `mbezoui@cesi.fr`
- **ORCIDs:** Bezoui 0000-0002-8342-7039 · Sifaoui 0009-0007-6884-0611 ·
  Bounceur 0000-0002-0043-7742
- **Suggested reviewers.** Not yet prepared. EM requires an institutional
  e-mail for each. Suggest a mix of countries and institutions, and no one
  connected to the work. Natural pools: the semi-infinite programming community
  (exchange methods, inexact separation oracles) and the conditional /
  distributionally robust optimization community.
- **Excluded reviewers**, if any.
- **Declarations** are already inside the manuscript under "Statements and
  Declarations": funding, competing interests, data availability, author
  contributions.
- **LLM use.** The journal exempts AI-assisted copy editing (readability, style,
  grammar, spelling, punctuation, tone) from declaration. Nothing beyond that
  applies, so no statement is included. If you consider the assistance went
  further, add one sentence to Statements and Declarations before submitting.

## 3. Compliance, verified against the journal guidelines

| Requirement | Status |
| --- | --- |
| Title concise and informative | yes |
| Author names, affiliations with institution, city, country | yes |
| Corresponding author indicated, active e-mail | on the title page |
| 16-digit ORCID for each author | 3 of 3 |
| Abstract 150–250 words, no undefined abbreviation, no reference | 178 words |
| Keywords 4–6, on the title page | 5, page 1 |
| Statements and Declarations, before the reference list | 4 declarations |
| Data availability statement | yes, with source citations and archive DOI |
| Manuscript in LaTeX with Springer class | `svjour3`, `smallcondensed` |
| Decimal headings, at most three levels | 2 levels, 0 subsubsection |
| Abbreviations defined at first mention | audited |
| Footnotes | none |
| Citations as numbers in square brackets | `natbib [numbers,sort&compress]` |
| Reference list = cited works only, numbered consecutively | 35 entries, keys unique |
| DOIs as full DOI links | 30 rendered; the five without are two data-source pages, a 1991 technical report, a 1964 *Sankhyā* article and a NeurIPS paper, none of which carries a DOI |
| Tables in Arabic numerals, cited in consecutive order, each captioned | 21 tables, order verified programmatically |
| Figures in Arabic numerals, cited in consecutive order | 17 figures, order verified programmatically |
| Figure captions: no punctuation after the number or at the end | 38 captions, none ends with a period |
| No colour named in a caption | verified |
| No title or caption inside the artwork | removed from every plot |
| Figure files named `FigN` | 14 files, none missing, none orphaned |
| Fonts embedded in vector artwork | 14 of 14, and in all three PDFs |
| Figures sized to the column width, height under 195 mm | capped at 119 mm wide via `\figwidth`, 45–83 mm high |
| Lettering consistent, 2–3 mm at final size | every figure is typeset at its authoring width, so no figure's lettering is scaled down; tick labels raised to 8 pt |
| Colour figures legible in greyscale | every series carries a distinct line style or marker |
| Compiles with no error, undefined reference, duplicate label or overfull box | verified from an empty directory |

## 4. Numerical integrity

```bash
python3 code/scripts/validate_manuscript.py --tex soumission/main_paper.tex
```

**442 checks, 0 failures.** The script parses every numerical table out of the
`.tex` and compares it cell by cell with `code/results/*.csv`, checks the
cross-table identities, and fails loudly if a table layout is unrecognised or a
strategy row is missing rather than passing silently. Four of the checks are
reproduction identities that would catch a broken experiment rather than a
typo: the shrinkage family at λ=0 must reproduce the Nominal CVaR row and at
λ=1 the state-conditioned row; the return-target experiment at Q50 and the
bandwidth experiment with the diagonal rule must both reproduce the Robust SIP
baseline.

## 5. Nothing in the manuscript is version-pinned

The manuscript, `README.md` and `CITATION.cff` cite the Zenodo **concept DOI**
`10.5281/zenodo.21957758`, which always resolves to the newest version. The
reference entry no longer names a release, and the Data Availability statement
no longer names a Git commit, so publishing a new release requires no edit to
the paper.

## 6. Before you click submit

1. Publish the release so the Data Availability statement resolves — see
   `RELEASE_COMMANDS.md`.
2. Prepare the suggested-reviewer list with institutional e-mail addresses.
3. Confirm all three co-authors have approved this version, as the journal's
   authorship principles require.
