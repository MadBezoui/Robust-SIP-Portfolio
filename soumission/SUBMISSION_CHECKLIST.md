# Submission checklist — Computational Optimization and Applications

**Continuous-state robust CVaR portfolio optimization via grid-restricted
constraint generation**

Research Article · first submission · manuscript verified 8 September 2026

Submit `submission_package.zip` (22 files). It was unpacked into an empty
directory and compiled there: **43 pages, no error, no undefined reference, no
duplicate label, no overfull box, nothing missing.**

---

## 1. Upload, in Editorial Manager order

| # | EM item type | File |
| --- | --- | --- |
| 1 | Cover Letter | `cover_letter.pdf` |
| 2 | Manuscript | `main_paper.pdf` |
| 3 | LaTeX source | `main_paper.tex` |
| 4 | Bibliography source | `references.bib` |
| 5 | Processed bibliography | `main_paper.bbl` |
| 6 | Style files | `svjour3.cls`, `svglov3.clo` |
| 7 | Figures | `Fig1.pdf` … `Fig14.pdf` |
| 8 | Highlights (optional) | `highlights.pdf` |

Manuscript Figures 1–3 are TikZ schematics typeset inline, so no artwork file
corresponds to them. `Fig1.pdf` … `Fig14.pdf` are the fourteen plotted figures
and appear as manuscript Figures 4–17.

## 2. Type into Editorial Manager

- **Title:** Continuous-state robust CVaR portfolio optimization via
  grid-restricted constraint generation
- **Corresponding author:** Madani Bezoui — `mbezoui@cesi.fr` —
  CESI LINEACT, UR 7527, Nancy, France — ORCID 0000-0002-8342-7039
- **Thiziri Sifaoui** — Department of Mathematics and Computer Science,
  University of Amine Elokkal El Hadj Moussa Eg Akhamouk, Tamanghasset, Algeria;
  LAROMAD, Faculty of Sciences, UMMTO, Tizi Ouzou, Algeria —
  ORCID 0009-0007-6884-0611
- **Ahcene Bounceur** — College of Computing and Informatics, University of
  Sharjah, United Arab Emirates — `abounceur@sharjah.ac.ae` —
  ORCID 0000-0002-0043-7742
- **Abstract and keywords:** copy from the manuscript (178 words, 5 keywords).
- **Declarations:** already inside the manuscript under *Statements and
  Declarations* — funding, competing interests, data availability, author
  contributions. EM may also ask you to tick them in the interface.

## 3. What you must supply that is not in any file

- [ ] **Suggested reviewers.** EM requires a name, affiliation and an
      **institutional** e-mail for each. Choose people with no connection to the
      work, spread across countries and institutions. Two natural pools: the
      semi-infinite programming community (exchange methods, inexact separation
      oracles) and the conditional / distributionally robust optimization
      community.
- [ ] **Excluded reviewers**, if any.
- [ ] **Co-author approval.** The journal's authorship principles require that
      all three authors have approved this exact version.
- [ ] **Publish the Zenodo release** so the Data Availability statement
      resolves — see `../RELEASE_COMMANDS.md`. The manuscript cites the concept
      DOI `10.5281/zenodo.21957758`, which always resolves to the newest
      version, so **nothing in the paper needs editing afterwards**.

## 4. Verified against the journal guidelines

The guidelines impose **no page limit and no word limit** on the body. The only
quantitative requirements are those below.

| Requirement | Status |
| --- | --- |
| Abstract 150–250 words | 178 |
| Keywords 4–6, on the title page | 5, page 1 |
| Decimal headings, at most three levels | 2 levels, no subsubsection |
| Statements and Declarations before the reference list | 4 declarations |
| Data availability statement | yes, with source citations and archive DOI |
| Citations as numbers in square brackets | `natbib [numbers,sort&compress]` |
| Reference list = cited works only | 35 entries, keys unique |
| DOIs rendered as full DOI links | 30 of 35; the 5 without are two data-source pages, a 1991 technical report, a 1964 *Sankhyā* article and a NeurIPS paper, none of which carries a DOI |
| Tables cited in consecutive numerical order, each captioned | 21 tables, verified programmatically |
| Figures cited in consecutive numerical order | 17 figures, verified programmatically |
| Captions: no punctuation after the number or at the end | 38 captions, 0 ending in punctuation |
| No colour named in a caption | 0 |
| No title or caption inside the artwork | removed from every plot |
| Figure files named `FigN` | 14, none missing, none orphaned |
| Figure width ≤ 119 mm, height ≤ 195 mm | 0 figures exceed either |
| Lettering 2–3 mm at final size | every figure is typeset at its authoring width, so no lettering is scaled down; tick labels at 8 pt |
| Colour figures legible in greyscale | every series carries a distinct line style or marker |
| Fonts embedded | 0 unembedded fonts across all 17 PDFs |
| Compiles clean from an empty directory | verified |

## 5. Numerical integrity

```bash
python3 code/scripts/validate_manuscript.py --tex soumission/main_paper.tex
```

**442 checks, 0 failures.** Every numerical table in the `.tex` is compared cell
by cell with `code/results/*.csv`. The script fails loudly if a table layout is
unrecognised or a strategy row is missing, rather than passing silently. Four
checks are reproduction identities that would catch a broken experiment rather
than a typo: the shrinkage family at λ=0 must reproduce the Nominal CVaR row and
at λ=1 the state-conditioned row; the return-target experiment at Q50 and the
bandwidth experiment with the diagonal rule must both reproduce the Robust SIP
baseline.

## 6. Two things to know before you answer referees

- **AI assistance.** The journal exempts AI-assisted copy editing (readability,
  style, grammar, spelling, punctuation, tone) from declaration, so no statement
  is included. If you judge the assistance went further, it is one sentence to
  add to *Statements and Declarations*.
- **Reproducibility caveat, already disclosed in the manuscript.** TC-MinVar
  reaches the 600-second solver limit on 18 of 377 windows and returns the
  incumbent, so that one leg is not bit-reproducible across machines. The other
  four strategies terminate at optimality everywhere.

## 7. If you rebuild before submitting

```bash
cd soumission
pdflatex -interaction=nonstopmode main_paper.tex
bibtex main_paper
pdflatex -interaction=nonstopmode main_paper.tex
pdflatex -interaction=nonstopmode main_paper.tex
```

All four counts must be zero:

```bash
cd soumission && for k in '^!' 'undefined' 'multiply' 'Overfull \\hbox'; do \
  printf '%-18s %s\n' "$k" "$(grep -ci "$k" main_paper.log)"; done
```

The cover letter carries `\today`, so rebuilding it restamps the date. Two
tables use `adjustbox`, which shrinks rather than overflows — a zero overfull
count does not prove they are legible, so look at the rendered pages if you
change them.
