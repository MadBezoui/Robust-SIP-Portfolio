import re

with open("Soumission/main_paper.tex", "r") as f:
    text = f.read()

heatmap_tex = r"""
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.6\textwidth]{Fig16.pdf}
    \caption{Conditional Expected Shortfall ($\mathrm{ES}_{95}$) differences (\% pts) between Robust SIP and Nominal CVaR across VIX and Drawdown quintiles. Positive values (red) indicate that Robust SIP has higher tail losses in that specific regime.}
    \label{fig:cond_es_heatmap}
\end{figure}
"""

# Insert it at the end of the Conditional tail risk subsection
match = re.search(r"\\subsection\{Conditional tail risk\}(.*?)(?=\\subsection|\\section|\\end\{document\})", text, re.DOTALL)
if match:
    sub_text = match.group(0)
    # append heatmap_tex
    new_sub_text = sub_text + heatmap_tex
    text = text.replace(sub_text, new_sub_text)
    with open("Soumission/main_paper.tex", "w") as f:
        f.write(text)
    print("Added heatmap to tex")
else:
    print("Could not find Conditional tail risk subsection")
