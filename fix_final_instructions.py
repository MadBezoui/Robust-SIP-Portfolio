import re

with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

# 1. Replace the "Retain this filename..." instruction
text = re.sub(
    r"Retain this filename only if it exists.*?submission release\.:",
    r"\\textbf{Figure Generation Module} (\\texttt{code/generate\\_publication\\_figures.py}):",
    text,
    flags=re.IGNORECASE | re.DOTALL
)

# 2. Replace the software citation instruction
text = re.sub(
    r"The final bibliography should include formal software.*?dual-simplex implementation\.",
    r"The computational pipeline was implemented in the Julia programming language \\cite{bezanson2017julia}, with optimization models formulated using JuMP \\cite{dunning2017jump} and solved via the HiGHS solver \\cite{highs2022}.",
    text,
    flags=re.IGNORECASE | re.DOTALL
)

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
print("Fixes applied.")
