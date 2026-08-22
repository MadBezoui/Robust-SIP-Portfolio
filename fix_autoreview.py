import re

with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

# 1. Page 2: Delete this sentence from Section 2.1
text = re.sub(r"Delete this sentence from Section 2.1.*?Introduction \.\.\.", "", text, flags=re.IGNORECASE)

# 2. Page 31: Retain this filename
text = re.sub(r"Retain this filename only if it exists.*?every manuscript figure \.\.\.", r"\\texttt{code/generate_publication_figures.py}", text, flags=re.IGNORECASE|re.DOTALL)

# 3. Abstract: paired paired
text = text.replace("paired paired circular moving-block", "paired circular moving-block")

# 4. Section 4.1: Because the portfolio allocation
text = text.replace("Because the portfolio allocation $w^k$ is fixed during separation, After computing", "Because the portfolio allocation $w^k$ is fixed during separation, after computing")

# 5. Section 4.1: precomputation of kernel weights.: sorting
text = text.replace("precomputation of kernel weights.: sorting", "precomputation of kernel weights: sorting")

# 6. Section 3.3 repeats
text = re.sub(r"(The minimizer may be non-unique, but the minimum value is uniquely defined\.\s*){2,}", r"\1", text)

# 7. Section 6.2: remain above 0.18., and
text = text.replace("remain above 0.18., and", "remain above 0.18, and")

# 8. Conclusion: at the reported 5% or 10%
text = text.replace("at the reported 5\\% or 10\\% significance level at conventional significance levels.", "at the conventional 5\\% or 10\\% significance levels.")

# 9. Table 8 over-rounding
text = text.replace("0.032", "0.03189125")

# 10. Figure 11 (kernel_map) caption
text = text.replace("The grid nodes are generated in log-VIX coordinates, and the displayed density includes the Jacobian of the exponential transformation", "The shading represents a direct two-dimensional Gaussian KDE on raw VIX and drawdown")

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
