import re

with open("Soumission/main_paper.tex", "r") as f:
    text = f.read()

# Rename Table 5 (Crisis)
old_cap = r"\caption{Realized out-of-sample returns and maximum drawdowns across historical crisis periods}"
new_cap = r"\caption{Approximate crisis-period performance using complete 21-day holding periods classified by holding-period end date}"
text = text.replace(old_cap, new_cap)

# Add conditional tail risk
conditional_text = r"""
\subsection{Conditional tail risk}
To answer the central empirical question---whether robustification across the state domain reduces realized tail losses conditional on stressful market states---we group out-of-sample daily returns according to lagged state variables and evaluate the 5\% Conditional Value-at-Risk and maximum drawdown for each state group. As reported in Table \ref{tab:cond_risk}, Robust SIP achieves a CVaR of 1.03\% in the Low VIX group, 1.63\% in the Medium VIX group, 2.16\% in the High VIX group, and 4.99\% in the Extreme VIX group. In comparison, Nominal CVaR achieves 1.00\%, 1.46\%, 1.92\%, and 4.74\% respectively. Thus, Robust SIP does not outperform nominal CVaR in the reported stress groups. Similar conclusions apply to the maximum drawdown metric.
\begin{table}[htbp]
\centering
\caption{Out-of-sample conditional tail risk}
\label{tab:cond_risk}
\begin{tabular}{llrrr}
\toprule
\textbf{State Group} & \textbf{Strategy} & \textbf{CVaR$_{0.95}$ (\%)} & \textbf{Max Drawdown (\%)} & \textbf{Observations} \\
\midrule
Low VIX & 1/N & 1.12 & -6.37 & 2619 \\
& Nominal CVaR & 1.00 & -5.54 & 2619 \\
& Robust SIP & 1.03 & -5.67 & 2619 \\
\midrule
Medium VIX & 1/N & 1.81 & -36.58 & 2609 \\
& Nominal CVaR & 1.46 & -31.11 & 2609 \\
& Robust SIP & 1.63 & -34.28 & 2609 \\
\midrule
High VIX & 1/N & 2.54 & -47.02 & 1900 \\
& Nominal CVaR & 1.92 & -32.61 & 1900 \\
& Robust SIP & 2.16 & -38.77 & 1900 \\
\midrule
Extreme VIX & 1/N & 6.10 & -91.82 & 792 \\
& Nominal CVaR & 4.74 & -84.04 & 792 \\
& Robust SIP & 4.99 & -88.04 & 792 \\
\bottomrule
\end{tabular}
\end{table}
"""

if "Conditional tail risk" not in text:
    # insert before "Crisis performance"
    text = text.replace(r"\subsection{Crisis performance}", conditional_text + "\n" + r"\subsection{Crisis performance}")

# The user requested 4 Research Questions in the Introduction
rq_text = r"""
In this context, we formulate the following research questions:
\begin{enumerate}
    \item \textbf{RQ1}: How does a continuous-state robust formulation compare structurally and empirically to standard unconditional and discrete-regime robust portfolio models?
    \item \textbf{RQ2}: Can adaptive constraint generation effectively scale continuous-state portfolio robustification, overcoming the computational limits of dense enumeration?
    \item \textbf{RQ3}: Does state-domain continuous robustification improve out-of-sample risk-adjusted returns and downside protection across non-stationary market environments?
    \item \textbf{RQ4}: What is the role of model regularization---such as bandwidth scaling and empirical support thresholding---in mitigating boundary scenario overfitting within continuous robust sets?
\end{enumerate}
"""
if "RQ1" not in text:
    text = text.replace(r"In this paper, we propose a continuous-state robust portfolio", rq_text + "\n" + r"In this paper, we propose a continuous-state robust portfolio")

with open("Soumission/main_paper.tex", "w") as f:
    f.write(text)
