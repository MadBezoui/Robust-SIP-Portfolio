import re

with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

# Point 21: Correct the block-length conclusion
text = text.replace(
    r"supporting the qualitative conclusion that the inference is not sensitive to the reported range of block lengths.",
    r"Across the examined block lengths, all reported $p$-values exceed 0.05. Thus, the qualitative non-rejection conclusion is unchanged, although the estimated standard errors and $p$-values vary with the block length."
)

# Point 22: Replace editorial instruction about iteration counting
# Text to find: "The exact counting convention should be stated explicitly..."
# Actually, I should just search for something similar or just replace the text if it's there.
# Let's check if it's there:
text = re.sub(
    r"The exact counting convention should be stated explicitly, because an algorithm.*?$m-1$ exchange updates\.",
    r"We report the number of master-LP solves. Under the one-state initialization and one-new-state-per-update rule, a converged run with $m$ final active states entails $m$ master-LP solves and $m-1$ state-addition updates.",
    text,
    flags=re.IGNORECASE | re.DOTALL
)

# Point 23: Clarify transaction-cost initialization
# Add after Equation (42):
text = re.sub(
    r"(\\end\{equation\}\n(?:.*?)%?)\s*Table \\ref\{tab:performance\}",
    r"\1\nAt the first rebalance, the optimized strategies are assumed to trade from an initial $1/N$ allocation. The $1/N$ benchmark therefore incurs zero initial turnover, while the optimized strategies incur the turnover required to move from $1/N$ to their first selected allocation.\n\nTable \\ref{tab:performance}",
    text,
    count=1,
    flags=re.IGNORECASE | re.DOTALL
)
# Note: I need to be careful with Equation 42. Let's just find "transaction costs $\tau$" and add it there if the regex fails.

# Point 28: Table 4 caption and prose
text = text.replace(
    r"Comprehensive out-of-sample performance summary",
    r"Selected out-of-sample performance metrics"
)
text = text.replace(
    r"Table \ref{tab:performance} reports the complete 14-metric performance profile.",
    r"Table \ref{tab:performance} reports five principal out-of-sample performance metrics. The complete performance profile is available in the archived \texttt{results/performance\_table.csv}."
)
text = text.replace(
    r"\textbf{Ann. Return}",
    r"\textbf{Ann. Mean Return}"
)

# Point 29: Software versions
text = re.sub(
    r"Computations were performed on an Apple M1 Pro.*?HiGHS 1\.24\.1\.",
    r"Computations were performed on an Apple M1 Pro with 8 CPU cores and 16 GB RAM. Computations were performed using the exact Julia and package versions recorded in the archived \texttt{Manifest.toml}.",
    text,
    flags=re.IGNORECASE | re.DOTALL
)

# Point 30: Conclusion cites wrong HiGHS reference
# Wait, I didn't see "single-threaded HiGHS 1.24.1 [18]" in the conclusion earlier, let's search for "HiGHS" in conclusion.
text = re.sub(
    r"single-threaded HiGHS 1\.24\.1 \\cite\{.*?\}",
    r"under the reported HiGHS 1.24.1 configuration \\cite{highs2022}",
    text,
    flags=re.IGNORECASE
)
text = re.sub(
    r"single-threaded HiGHS 1\.24\.1",
    r"under the reported HiGHS 1.24.1 configuration",
    text,
    flags=re.IGNORECASE
)

# Point 31: Correct final runtime sentence
text = re.sub(
    r"corresponding to an observed runtime ratio of approximately 16\.2.*?over dense LP discretization\.",
    r"corresponding to an observed runtime ratio of\n\\[\n72.7093/4.4851\\approx16.21\n\\]\nrelative to the dense $21\\times21$ extensive-form implementation on the representative benchmark window. This ratio is instance- and implementation-specific and is not a general complexity bound.",
    text,
    flags=re.IGNORECASE | re.DOTALL
)

# Point 32: ESS thresholding
text = text.replace(
    r"represents a natural regularizer to prevent boundary scenario overfitting.",
    r"provides a support-aware model variant that may mitigate sensitivity to low-support boundary states."
)

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
print("Text patches applied")
