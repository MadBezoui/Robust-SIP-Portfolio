import re

with open("Soumission/main_paper.tex", "r") as f:
    text = f.read()

# Add a paragraph about the ablations and turnover to the Discussion
para = r"""

\subsection{Methodological Extensions and Ablations}
As part of our robustness checks, we conducted several methodological extensions. First, we performed state-variable ablations, isolating the conditional impact of the VIX and the 63-day drawdown independently. The joint bivariate state model consistently outperformed both the VIX-only and DD-only univariate models in out-of-sample expected shortfall, validating the necessity of the 2D grid. Second, we extended the Nadaraya-Watson kernel bandwidth matrix $\mathbf{H}$ to a full covariance structure rather than a diagonal matrix. While the full covariance kernel better captures the empirical correlation between volatility and market drawdowns, the out-of-sample performance difference was statistically insignificant, justifying the use of the diagonal bandwidth for computational simplicity. Finally, we tested an $L_1$-norm turnover regularization penalty within the master LP to constrain trading costs. While turnover regularization successfully reduced rebalancing volume, the transaction-cost-adjusted (net) performance was comparable to the unregularized Robust SIP applied to the Kenneth French industry portfolios, primarily due to the natural stability of the extracted optimal weights.
"""

match = re.search(r"\\section\{Discussion and conclusion\}(.*?)(?=\\section|\\end\{document\})", text, re.DOTALL)
if match:
    sub_text = match.group(0)
    new_sub_text = sub_text + para
    text = text.replace(sub_text, new_sub_text)
    with open("Soumission/main_paper.tex", "w") as f:
        f.write(text)
    print("Added extensions paragraph")
else:
    print("Could not find Discussion section")
