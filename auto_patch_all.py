import pandas as pd
import re

with open("Soumission/main_paper.tex", "r") as f:
    text = f.read()

# 1. Fix Table 4 (tab:performance) to be HORIZONTAL and match CSV
df_perf = pd.read_csv("results/performance_table.csv").set_index("Strategy")
t4_tex = r"""\begin{tabular}{lrrrrr}
\toprule
\textbf{Strategy} & \textbf{Return (\%)} & \textbf{Vol (\%)} & \textbf{Sharpe} & \textbf{Max DD (\%)} & \textbf{Turnover (\%)} \\
\midrule
"""
for c, tex_name in [("1/N", "1/N"), ("MinVar", "TC-MinVar"), ("NominalCVaR", "Nominal CVaR"), ("FiniteRegime", "Finite-Regime CVaR"), ("RobustSIP", "Robust SIP")]:
    r = df_perf.loc[c]
    t4_tex += f"{tex_name} & {r['Ann_Mean']*100:.2f} & {r['Ann_Vol']*100:.2f} & {r['Sharpe']:.3f} & {r['Max_DD']*100:.2f} & {r['Avg_Turnover']*100:.2f} \\\\\n"
t4_tex += r"\bottomrule" + "\n" + r"\end{tabular}"

# Replace tab:performance content
text = re.sub(r"\\begin\{tabular\}.*?\\end\{tabular\}", t4_tex, text, count=1, flags=re.DOTALL) 
# wait, replacing the first tabular is dangerous. Let's find tab:performance.
