import pandas as pd
import numpy as np
import re

# Read Exp A
df = pd.read_csv("results/experiment_A.csv")
df['Grid'] = df['Grid'].astype(str) + "x" + df['Grid'].astype(str)
# Summarize by grid
summary = df.groupby('Grid').agg(
    n_windows=('Window', 'count'),
    mean_dense_time=('Dense_Time', 'mean'),
    median_dense_time=('Dense_Time', 'median'),
    mean_adapt_time=('Adaptive_Time', 'mean'),
    median_adapt_time=('Adaptive_Time', 'median'),
    mean_speedup=('Adaptive_Time', lambda x: np.mean(df.loc[x.index, 'Dense_Time'] / x)),
    max_obj_diff=('Obj_Diff', 'max'),
    max_l1_diff=('L1_Diff', 'max'),
    mean_active=('Adaptive_Active_States', 'mean')
).reset_index()

tex_table = r"""
\begin{table}[htbp]
\centering
\caption{Computational benchmark: Dense vs. Adaptive Separation}
\label{tab:computational}
\begin{tabular}{lrrrrrrrr}
\toprule
\textbf{Grid} & \textbf{N} & \textbf{Dense(s)} & \textbf{Adapt(s)} & \textbf{Speedup} & \textbf{Max Obj $\Delta$} & \textbf{Max $\ell_1 \Delta$} & \textbf{Active} \\
\midrule
"""
for _, row in summary.iterrows():
    tex_table += f"{row['Grid']} & {row['n_windows']} & {row['mean_dense_time']:.2f} & {row['mean_adapt_time']:.2f} & {row['mean_speedup']:.1f}x & {row['max_obj_diff']:.1e} & {row['max_l1_diff']:.1e} & {row['mean_active']:.1f} \\\\\n"
tex_table += r"""\bottomrule
\end{tabular}
\end{table}
"""

with open("Soumission/main_paper.tex", "r") as f:
    text = f.read()

# Replace tab:computational
match = re.search(r"(\\begin\{table\}.*?\\caption\{Computational profile of continuous-state robust SIP.*?\\end\{table\})", text, re.DOTALL)
if match:
    text = text[:match.start()] + tex_table + text[match.end():]

# Fix tab:sens_ess
text = text.replace(r"\label{tab:ess_backtest}", "\\label{tab:ess_backtest}\n\\label{tab:sens_ess}")

with open("Soumission/main_paper.tex", "w") as f:
    f.write(text)

