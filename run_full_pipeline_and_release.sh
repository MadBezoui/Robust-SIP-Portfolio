#!/bin/bash
set -e

echo "Waiting for run_ess_backtest.jl to finish..."
while pgrep -f "run_ess_backtest.jl" > /dev/null; do
    sleep 5
done

echo "Running main_exp.jl..."
cd code
julia --project=. main_exp.jl
cd ..

echo "Updating all tables in LaTeX..."
python3 code/update_all_tables.py
python3 auto_update_table2.py
python3 auto_update_table6.py
python3 auto_update_table11.py
python3 auto_update_tab_ess_backtest.py

echo "Compiling PDF..."
cd submission_CompOptAlg_v2
rm -f *.aux *.bbl *.blg *.log *.out *.toc *.lof *.lot *.fls *.fdb_latexmk
pdflatex main_paper.tex
bibtex main_paper
pdflatex main_paper.tex
pdflatex main_paper.tex
cd ..

echo "Committing and tagging..."
git add .
git commit -m "Final exact reproducibility fixes (run full pipeline, Table 6, 11, ESS, Eq 35) for v1.6.0"
git push origin revision-coap
git tag -f -a v1.6.0-submission-final -m "Final validated release for peer review submission"
git push origin v1.6.0-submission-final -f
gh release create v1.6.0-submission-final -t "v1.6.0: Final Submission for CompOptAlg (Definitive)" -n "Includes all final typography, table formatting, full pipeline re-execution, ESS backtest, and code reproducibility fixes."

echo "Done!"
