with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

import re

old_str = r"""\[
\rho_k = \frac12
\sqrt{\Delta_{v,k}^2+\Delta_{d,k}^2},
\].

Where $\Delta_{v,k}$ and $\Delta_{d,k}$ are the corresponding grid spacings."""

new_str = r"""\[
\rho_k
=
\frac12\sqrt{\Delta_{v,k}^2+\Delta_{d,k}^2},
\]
where $\Delta_{v,k}$ and $\Delta_{d,k}$ are the corresponding grid spacings."""

text = text.replace(old_str, new_str)

old_str2 = r"""\[
0\le G_k(w)-\widehat G_k(w)\le L_{\Phi,k}\rho_k.
\]."""
new_str2 = r"""\[
0\le G_k(w)-\widehat G_k(w)\le L_{\Phi,k}\rho_k.
\]"""
text = text.replace(old_str2, new_str2)

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
