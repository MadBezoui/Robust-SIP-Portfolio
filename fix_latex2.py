import re

with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

# A. Drawdown indexing
text = text.replace(r"D_t = 1 - \frac{P_t}{\max_{s \in [t-L, t]} P_s}", r"D_t = 1 - \frac{P_t}{\max_{s=t-62,\dots,t} P_s}")

# B. Abstract
text = text.replace("the CBOE Volatility Index, $\log V_t$ (log-VIX)", "the logarithm of the CBOE Volatility Index, $\log V_t$ (log-VIX)")
# wait, the abstract:
text = text.replace("the CBOE Volatility Index (VIX) and trailing market drawdown", "the logarithm of the CBOE Volatility Index (log-VIX) and trailing market drawdown")

# C. Duplicate CVaR-minimizer statement
text = re.sub(r"(The minimizer may be non-unique, but the minimum value.*?\.\n\s*){2,}", r"\1", text)

# D. Proposition 1 assumption
text = text.replace(r"\mu =", r"\mu = \bar{w} \sum_{i=1}^q \widehat{\mu}_{[i]} + \begin{cases} r\widehat{\mu}_{[q+1]}, & r > 0 \\ 0, & r = 0 \end{cases}")
# Actually wait, let me just replace the exact code string
text = text.replace(r"(r > 0 ? r\widehat{\mu}_{[q+1]} : 0)", r"\begin{cases} r\widehat{\mu}_{[q+1]}, & r > 0 \\ 0, & r = 0 \end{cases}")
if r"0 < \bar{w} \le 1" not in text:
    text = text.replace(r"For any target return level $\eta$,", r"For any target return level $\eta$ and uniform bound $0 < \bar{w} \le 1$,")

# E. Initialization-sensitivity claim
text = re.sub(r"The algorithm exhibited robustness to initialization.*?20 out of 20 tested rolling windows\.", "", text, flags=re.IGNORECASE|re.DOTALL)

# Insert missing Equation (35) - wait, where was it supposed to go? In the previous autoreview, it said "Proposition 3 contains its actual \epsilon-optimality inequality."
# Let's see if 0 \le G(w^k) - v^\star \le \varepsilon is there.
if r"0 \le G(w^k) - v^\star \le \varepsilon" not in text and r"0 \leq G(w^k) - v^\star \leq \varepsilon" not in text:
    text = text.replace("an $\varepsilon$-optimal solution.", "an $\varepsilon$-optimal solution, satisfying $0 \le G(w^k) - v^\star \le \varepsilon$.")

# Use \mathcal{A}_k instead of \widehat{\mathcal{U}}_k in the exact-separation theorem.
text = text.replace(r"If $\theta_k^* \in \widehat{\mathcal{U}}_k$, then $w^k$ is optimal", r"If $\theta_k^* \in \mathcal{A}_k$, then $w^k$ is optimal")

# Correct bootstrap p-value formula
old_pval = r"frac{1}{B} \sum_{r=1}^B \mathbf{1}"
if old_pval in text:
    pass
# I will just write a regex for the p-value formula.
text = re.sub(
    r"\\widehat\{p\}\s*=\s*.*?\\right\\}",
    r"\\widehat p = \\frac{1 + \\sum_{r=1}^{B} \\mathbf 1 \\left\\{ \\left| \\Delta\\mathrm{SR}^{*r} - \\overline{\\Delta\\mathrm{SR}^{*}} \\right| \\geq \\left| \\widehat{\\Delta\\mathrm{SR}} \\right| \\right\\}}{B+1}",
    text,
    flags=re.DOTALL
)

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
