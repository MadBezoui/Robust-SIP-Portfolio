import re

with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

# Fix Table 14
text = text.replace("Minimum window-level mean active-state ESS", "Min ESS")

# Fix Table 15
text = text.replace("Block Length $b$, in 21-trading-day holding periods", "Block Length")

# Let's also check Table 1
text = text.replace("Present model & Continuous state index set & One fixed kernel-weighted\nempirical distribution for each state & Single allocation robust across all\nindexed states & Continuous state index & Finite grid-restricted LP solved\nby constraint generation",
"Present model & Continuous state index set & One fixed kernel-weighted\nempirical distribution for each state & Single allocation robust across all\nindexed states & Continuous state index & Finite grid-restricted LP\nsolved by constraint generation")

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
