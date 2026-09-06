import re
with open("Soumission/main_paper.tex", "r") as f:
    text = f.read()

# wait, just checking one final thing about Table 4: did the 0.11% come back because of missing 100 multiplier?
# The table 4 is "Annualized Mean Return (\%) & 12.24 & 10.75 & 10.76 & 11.15 & 11.28 \\"
# So it's 12.24, not 0.12. It's completely fine.
