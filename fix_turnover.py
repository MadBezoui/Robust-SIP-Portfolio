with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

import re

old_text = r"""To incorporate realistic market frictions, we compute holding-period portfolio turnover taking into account asset price drift over the holding period:
\begin{equation}
    \widetilde w_{i,t} = \frac{w_{i,t-1}(1+R_{i,t})}{\sum_{j=1}^N w_{j,t-1}(1+R_{j,t})}
\end{equation}
where $R_{i,t}$ is the cumulative simple/net return (and $1+R_{i,t}$ is the gross return) of asset $i$ over the 21-day holding period. Holding-period turnover and net return are defined as:
\begin{equation}
    \text{TO}_t = \frac{1}{2} \sum_{i=1}^N | w_{i,t} - \widetilde w_{i,t} |
\end{equation}"""

new_text = r"""To incorporate realistic market frictions, we compute holding-period portfolio turnover taking into account asset price drift over the preceding holding period:
\begin{equation}
    \widetilde w_{i,q} = \frac{w_{i,q-1}(1+R_{i,q-1})}{\sum_{j=1}^N w_{j,q-1}(1+R_{j,q-1})}
\end{equation}
where $R_{i,q-1}$ is the cumulative simple/net return (and $1+R_{i,q-1}$ is the gross return) of asset $i$ over the preceding 21-day holding period $q-1$. Holding-period turnover and net return at period $q$ are defined as:
\begin{equation}
    \text{TO}_q = \frac{1}{2} \sum_{i=1}^N | w_{i,q} - \widetilde w_{i,q} |
\end{equation}"""

text = text.replace(old_text, new_text)

# We also need to change text{TO}_t and R_t in the net return equation?
# \begin{equation}
#     \text{Net Ret}_t = \text{Gross Ret}_t - \text{TC} \times \text{TO}_t
# \end{equation}
old_eq3 = r"""\begin{equation}
    \text{Net Ret}_t = \text{Gross Ret}_t - \text{TC} \times \text{TO}_t
\end{equation}"""
new_eq3 = r"""\begin{equation}
    \text{Net Ret}_q = \text{Gross Ret}_q - \text{TC} \times \text{TO}_q
\end{equation}"""
text = text.replace(old_eq3, new_eq3)

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
