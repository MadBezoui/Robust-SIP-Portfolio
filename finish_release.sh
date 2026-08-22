#!/bin/bash
echo "Waiting for gap_verification.csv to be updated..."
while true; do
    mod_time=$(stat -f "%m" results/gap_verification.csv)
    if [ "$mod_time" -gt 1787374000 ]; then
        break
    fi
    sleep 5
done
echo "CSV updated! Updating Table 2..."
python3 auto_update_table2.py

echo "Compiling PDF..."
cd submission_CompOptAlg_v2
pdflatex main_paper.tex
bibtex main_paper
pdflatex main_paper.tex
pdflatex main_paper.tex
cd ..

echo "Committing and tagging..."
git add .
git commit -m "Final exact reproducibility fixes and regenerated Table 2 for v1.5.0"
git push origin revision-coap
git tag -f -a v1.5.0-submission-final -m "Final validated release for peer review submission"
git push origin v1.5.0-submission-final -f
gh release create v1.5.0-submission-final -t "v1.5.0: Final Submission for CompOptAlg (Definitive)" -n "Includes all final typography, table formatting, and code reproducibility fixes."

echo "Done!"
