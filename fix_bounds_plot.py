import re

with open("code/generate_publication_figures.py", "r") as f:
    text = f.read()

# Replace iterations with master solves
text = text.replace("Exchange Iteration $k$", "Master solves $k$")
text = text.replace("Exchange Iteration $k$ (State Addition)", "Master solves $k$")

# Replace $10^{-4}$ with 0.01 percentage points
text = text.replace("Residual Gap $\leq 10^{-4}$", "Residual Gap $\leq 0.01$ percentage points")

# Remove malformed symbols if any, maybe $\widehat{\mathcal{U}}$?
text = text.replace("$\widehat{\mathcal{U}}$", "U_hat")

with open("code/generate_publication_figures.py", "w") as f:
    f.write(text)
