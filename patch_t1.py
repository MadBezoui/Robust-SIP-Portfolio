import re

with open("Soumission/main_paper.tex", "r") as f:
    text = f.read()

t1 = r"""\begin{table}[htbp]
\centering
\caption{Comparison of conditional and robust risk models. For a formal structural comparison between standard Conditional DRO and the proposed continuous-state Robust SIP, see Equations \eqref{eq:dro_contrast} and \eqref{eq:sip_contrast}.}
\label{tab:lit_comparison}
\resizebox{\textwidth}{!}{
\begin{tabular}{llll}
\toprule
\textbf{Paradigm} & \textbf{Objective} & \textbf{Distributional Assumption} & \textbf{Covariate Role} \\
\midrule
Unconditional Markowitz & Mean-Variance & Stationary Gaussian & None \\
Nominal Conditional & Expected Shortfall & True conditional $P(Y \mid X)$ known & Directly defines the distribution \\
Standard DRO & Worst-case Risk over $\mathcal{P}$ & Global ambiguity set $\mathcal{P}$ & Typically unconditional \\
Covariate-driven DRO & Conditional Worst-case Risk & State-dependent ambiguity set $\mathcal{P}(x)$ & Centers the conditional ambiguity set \\
\textbf{Robust SIP (Proposed)} & \textbf{Worst-case Risk over $\mathcal{U}$} & \textbf{Continuous kernel-weighted empirical} & \textbf{Defines a continuous geometric state space $\mathcal{U}$} \\
\bottomrule
\end{tabular}
}
\end{table}"""

old_t1_block = re.search(r"\\begin\{table\}.*?\\label\{tab:lit_comparison\}.*?\\end\{table\}", text, re.DOTALL)
if old_t1_block:
    text = text.replace(old_t1_block.group(0), t1.strip())

text = text.replace(r"kernel weight \citep{nadaraya1964estimating,watson1964smooth}ing", r"constructed using multivariate Nadaraya--Watson kernel weights \citep{nadaraya1964estimating,watson1964smooth}")
text = text.replace(r"kernel weight \cite{nadaraya1964estimating,watson1964smooth}ing", r"constructed using multivariate Nadaraya--Watson kernel weights \cite{nadaraya1964estimating,watson1964smooth}")

with open("Soumission/main_paper.tex", "w") as f:
    f.write(text)
