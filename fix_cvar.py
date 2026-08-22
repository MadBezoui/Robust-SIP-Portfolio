with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

import re

pattern = r"For fixed \$\(w,\\theta\)\$, every minimizer.*?the minimum value \$\\Phi_\\tau\(w, \\theta\)\$ is uniquely defined\."

new_text = r"""For fixed $(w,\theta)$, the set of minimizers consists of weighted empirical $(1-\tau)$-quantiles of the loss distribution $\widehat{\mathbb P}_\theta$. This set may be non-singleton, but the minimum value $\Phi_\tau(w,\theta)$ is uniquely defined."""

text = re.sub(pattern, lambda m: new_text, text, flags=re.DOTALL)

text = text.replace(r"z^*(\theta)", r"z^\star(w,\theta)")

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
