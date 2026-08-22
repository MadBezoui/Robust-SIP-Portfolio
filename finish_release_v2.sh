#!/bin/bash
echo "Waiting for run_ess_backtest.jl to finish..."
while pgrep -f "run_ess_backtest.jl" > /dev/null; do
    sleep 5
done
echo "ESS backtest finished! Updating Table 14..."
python3 auto_update_table14.py

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
git commit -m "Final exact reproducibility fixes (Table 11, Table 14, Eq 35, ESS backtest) for v1.6.0"
git push origin revision-coap
git tag -f -a v1.6.0-submission-final -m "Final validated release for peer review submission"
git push origin v1.6.0-submission-final -f
gh release create v1.6.0-submission-final -t "v1.6.0: Final Submission for CompOptAlg (Definitive)" -n "Includes all final typography, table formatting, ESS backtest, and code reproducibility fixes."

echo "Done!"
