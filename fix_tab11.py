with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

import re

old_tab = r"""\begin{tabular}{rrrrr}
\toprule
\textbf{Grid Size} & \textbf{Solve Time (s)} & \textbf{Active States} & \textbf{Worst CVaR (\%)} & \textbf{Mean $\ell_1$ distance to $81\times81$} \\
\midrule
$11\times11$ & 0.20 & 3.20 & 4.46 & 0.1213 \\
$21\times21$ & 0.26 & 3.35 & 4.52 & 0.0627 \\
$41\times41$ & 0.47 & 3.75 & 4.53 & 0.0107 \\
$81\times81$ & 0.76 & 3.70 & 4.53 & 0.0000 \\
\bottomrule
\end{tabular}"""

new_tab = r"""\begin{adjustbox}{max width=\textwidth}
\begin{tabular}{rrrrr}
\toprule
\textbf{Grid Size} & \textbf{Solve Time (s)} & \textbf{Active States} & \textbf{Worst CVaR (\%)} & \textbf{Mean $\ell_1$ distance to $81\times81$} \\
\midrule
$11\times11$ & 0.20 & 3.20 & 4.46 & 0.1213 \\
$21\times21$ & 0.26 & 3.35 & 4.52 & 0.0627 \\
$41\times41$ & 0.47 & 3.75 & 4.53 & 0.0107 \\
$81\times81$ & 0.76 & 3.70 & 4.53 & 0.0000 \\
\bottomrule
\end{tabular}
\end{adjustbox}"""

text = text.replace(old_tab, new_tab)

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
