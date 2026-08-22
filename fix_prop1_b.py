with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

import re

old_text = r"""\[
\mu_{\max} = \bar w\sum_{i=1}^{q}\hat\mu_{(i)} + r\hat\mu_{(q+1)},
\].

and $\mu_{\min} = \bar{w} \sum_{i=1}^q \hat{\mu}_{[i]} + \begin{cases} r \hat{\mu}_{[q+1]}, & r > 0 \\ 0, & r = 0 \end{cases}$. The attainable expected-return set is $[\mu_{\min}, \mu_{\max}]$. Then $W\neq\emptyset$ if and only if $\mu_{\mathrm{target}}\leq\mu_{\max}$. Moreover, there exists $w\in S_{\bar w}$ satisfying $\hat\mu^\top w>\mu_{\mathrm{target}}$ if and only if $\mu_{\mathrm{target}}<\mu_{\max}$.
\end{proposition}"""

new_text = r"""\[
\mu_{\max} = \bar w\sum_{i=1}^{q}\hat\mu_{(i)} +
\begin{cases}
r\hat\mu_{(q+1)}, & r>0,\\
0, & r=0.
\end{cases}
\]
and
\[
\mu_{\min} = \bar{w} \sum_{i=1}^q \hat{\mu}_{[i]} +
\begin{cases}
r\hat\mu_{[q+1]}, & r>0,\\
0, & r=0.
\end{cases}
\]
The attainable expected-return set is $[\mu_{\min}, \mu_{\max}]$. Then $W\neq\emptyset$ if and only if $\mu_{\mathrm{target}}\leq\mu_{\max}$. Moreover, there exists $w\in S_{\bar w}$ satisfying $\hat\mu^\top w>\mu_{\mathrm{target}}$ if and only if $\mu_{\mathrm{target}}<\mu_{\max}$.
\end{proposition}"""

text = text.replace(old_text, new_text)

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
