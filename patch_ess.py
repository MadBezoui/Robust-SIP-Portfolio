import pandas as pd
import re

with open("Soumission/main_paper.tex", "r") as f:
    text = f.read()

# Insert the tables after tab:sens_ess
df_ess = pd.read_csv("results/ess_full_backtest.csv").set_index("ESS_Min")
t_ess_1 = r"""\begin{table}[htbp]
\centering
\caption{Sensitivity to Minimum Effective Sample Size ($E_{\min}$): Out-of-sample performance.}
\label{tab:ess_backtest_perf}
\begin{tabular}{lrrrrr}
\toprule
$E_{\min}$ & \textbf{Return (\%)} & \textbf{Vol (\%)} & \textbf{Sharpe} & \textbf{Max DD (\%)} & \textbf{Wealth (\$)} \\
\midrule
"""
for idx, r in df_ess.iterrows():
    t_ess_1 += f"{idx} & {r['Ann_Return_Decimal']*100:.2f} & {r['Ann_Vol_Decimal']*100:.2f} & {r['Sharpe']:.3f} & {r['Max_DD_Decimal']*100:.2f} & {r['Wealth']:.2f} \\\\\n"
t_ess_1 += r"""\bottomrule
\end{tabular}
\end{table}"""

t_ess_2 = r"""\begin{table}[htbp]
\centering
\caption{Sensitivity to Minimum Effective Sample Size ($E_{\min}$): Implementation diagnostics.}
\label{tab:ess_backtest_diag}
\begin{tabular}{lrrrr}
\toprule
$E_{\min}$ & \textbf{Turnover (\%)} & \textbf{Avg ESS} & \textbf{Min ESS} & \textbf{Grid Retained (\%)} \\
\midrule
"""
for idx, r in df_ess.iterrows():
    t_ess_2 += f"{idx} & {r['Turnover_Decimal']*100:.2f} & {r['Avg_ESS']:.2f} & {r['Min_ESS']:.2f} & {r['Retained_Frac_Decimal']*100:.1f} \\\\\n"
t_ess_2 += r"""\bottomrule
\end{tabular}
\end{table}"""

# find end of tab:sens_ess
idx = text.find(r"\label{tab:sens_ess}")
if idx != -1:
    end = text.find(r"\end{table}", idx) + len(r"\end{table}")
    # insert
    text = text[:end] + "\n\n" + t_ess_1 + "\n\n" + t_ess_2 + text[end:]

with open("Soumission/main_paper.tex", "w") as f:
    f.write(text)
