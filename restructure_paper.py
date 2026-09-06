import re

with open("Soumission/main_paper.tex", "r") as f:
    text = f.read()

# 1. Introduction
text = text.replace(r"\section{Introduction and motivation}", r"\section{Introduction}")

# 2. Related work
text = text.replace(r"\section{Related literature and research positioning}", r"\section{Related work}")

# 3. Model
text = text.replace(r"\section{Continuous-state robust CVaR framework}", r"\section{Model}")

# 4. Theory
# Find "\subsection{Semi-infinite programming formulation and theoretical properties}" and change to "\section{Theory}"
text = text.replace(r"\subsection{Semi-infinite programming formulation and theoretical properties}", r"\section{Theory}")

# 5. Algorithms
text = text.replace(r"\section{Grid-restricted adaptive constraint generation}", r"\section{Algorithms}")

# 6. Experimental design
text = text.replace(r"\section{Empirical framework and multi-decade results}", r"\section{Experimental design}")

# 7. Main empirical results
text = text.replace(r"\subsection{Long-term cumulative wealth and risk-adjusted performance}", r"\section{Main empirical results}" + "\n" + r"\subsection{Long-term cumulative wealth and risk-adjusted performance}")

# 8. Computational results
text = text.replace(r"\subsection{Computational scalability, state density, and bootstrap inference}", r"\section{Computational results}")

# 9. Model sensitivity
text = text.replace(r"\section{Model-specification sensitivity}", r"\section{Model sensitivity}")

# 10. Discussion and conclusion
text = text.replace(r"\section{Discussion, limitations, and concluding remarks}", r"\section{Discussion and conclusion}")

# Shorten Table 1:
# We can just change the caption and remove the repeated equations 2 and 3 in the prose
text = re.sub(r"\\begin\{equation\}\\label\{eq:dro_obj\}.*?\\end\{equation\}", "", text, flags=re.DOTALL)

with open("Soumission/main_paper.tex", "w") as f:
    f.write(text)
print("Basic restructuring applied")
