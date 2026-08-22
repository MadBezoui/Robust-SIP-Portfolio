with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

import re

old_eq = r"""    \begin{equation}
        0 \le G(w^k)-v^\star = \sup_{\theta\in\mathcal U}\Phi_\tau(w^k,\theta)-v^\star \le \varepsilon.
    \end{equation}"""

new_eq = r"""    \begin{equation}
    \begin{split}
        0 &\le G(w^k)-v^\star \\
        &= \sup_{\theta\in\mathcal U}\Phi_\tau(w^k,\theta)-v^\star \le \varepsilon.
    \end{split}
    \end{equation}"""

text = text.replace(old_eq, new_eq)
with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
