with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

import re

old_text = r"The identical target return constraint $\hat{\mu}^\top w \ge \mu_{\text{target}}$ and weight cap $\bar{w} = 0.15$ are enforced on Robust SIP, Nominal CVaR, and Finite-Regime CVaR."
new_text = r"The identical target-return constraint and weight cap are enforced on TC-MinVar, Nominal CVaR, Finite-Regime CVaR, and Robust SIP."
text = text.replace(old_text, new_text)

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
