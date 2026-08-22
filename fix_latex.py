import re

with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

# Fix Manifest.toml \texttt
text = text.replace("archived \texttt{Manifest.toml}", "archived \\texttt{Manifest.toml}")
text = text.replace("archived \t" + "exttt{Manifest.toml}", "archived \\texttt{Manifest.toml}")
text = text.replace("archived \x09exttt{Manifest.toml}", "archived \\texttt{Manifest.toml}")

# Fix counting convention
text = re.sub(
    r"The exact counting convention should be stated explicitly,.*?$m-1$ exchange updates\.",
    r"We report the number of master-LP solves. Under the one-state initialization and one-new-state-per-update rule, a converged run with $m$ final active states entails $m$ master-LP solves and $m-1$ state-addition updates.",
    text,
    flags=re.IGNORECASE | re.DOTALL
)

# Fix 16.2
text = re.sub(
    r"corresponding to an observed runtime ratio of approximately 16\.2.*?over dense LP discretization",
    r"corresponding to an observed runtime ratio of\n\\[\n72.7093/4.4851\\approx16.21\n\\]\nrelative to the dense $21\\times21$ extensive-form implementation on the representative benchmark window. This ratio is instance- and implementation-specific and is not a general complexity bound,",
    text,
    flags=re.IGNORECASE | re.DOTALL
)

# Fix Table 14 malformed structure
# Currently it is:
# $E_{\min} = 0$ & 11.28 & 13.95 & 0.81 & $-41.69$ & 25.04 & 9.48 & 83.0 & 2.2 & 100.0 \\
# The user wants me to split the rows nicely in the source. This is just source formatting.
# Also user says use `table*` or `sidewaystable` or `\resizebox{\textwidth}{!}` if font remains readable.
# I already have `\resizebox{\textwidth}{!}`.

# Fix Table 1 malformed structure
text = text.replace(r"\begin{table}[htbp]", r"\begin{table*}[htbp]")
text = text.replace(r"\end{table}", r"\end{table*}")

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
