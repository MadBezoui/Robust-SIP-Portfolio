import pandas as pd
import re

with open("Soumission/main_paper.tex", "r") as f:
    text = f.read()

def sub_row(pattern_start, new_row):
    global text
    # pattern_start is like r"1998-08 \(LTCM\)\s*&"
    # replace the entire row up to \\
    pattern = re.compile(pattern_start + r".*?\\\\", re.MULTILINE)
    text = pattern.sub(new_row, text, count=1)

# Table 2: gap verification
df_gap = pd.read_csv("results/gap_verification.csv").set_index("Label")
for idx, r in df_gap.iterrows():
    ls = r['LocalSearchImp']
    if ls == 0: ls_str = "0"
    elif ls < 1e-4: ls_str = f"${ls:.1e}$".replace("e", "\\times 10^{").replace("+0", "").replace("-0", "-") + "}"
    else: ls_str = f"{ls:.6f}"
    
    idx_esc = re.escape(idx)
    new_r = f"{idx} & {r['MaxGradNorm']:.3f} & {r['GridDisp']:.3f} & {r['EmpiricalProduct']:.2f} & {ls_str} \\\\"
    sub_row(r"^" + idx_esc + r"\s*&", new_r)

# Table 4: performance
# Oh wait, Table 4 is currently vertical in the manuscript! I have to change it to horizontal.
t4 = r"""\begin{tabular}{lrrrrr}
\toprule
\textbf{Strategy} & \textbf{Return (\%)} & \textbf{Vol (\%)} & \textbf{Sharpe} & \textbf{Max DD (\%)} & \textbf{Turnover (\%)} \\
\midrule
"""
df_perf = pd.read_csv("results/performance_table.csv").set_index("Strategy")
for c, tex_name in [("1/N", "1/N"), ("MinVar", "TC-MinVar"), ("NominalCVaR", "Nominal CVaR"), ("FiniteRegime", "Finite-Regime CVaR"), ("RobustSIP", "Robust SIP")]:
    r = df_perf.loc[c]
    t4 += f"{tex_name} & {r['Ann_Mean']*100:.2f} & {r['Ann_Vol']*100:.2f} & {r['Sharpe']:.3f} & {r['Max_DD']*100:.2f} & {r['Avg_Turnover']*100:.2f} \\\\\n"
t4 += r"""\bottomrule
\end{tabular}"""

text = re.sub(r"\\begin\{tabular\}\{lrrrrr\}.*?\\end\{tabular\}", t4.replace('\\', '\\\\'), text, count=1, flags=re.DOTALL) # wait, it's lrrrrr in the original?
# Originally Table 4 was \begin{tabular}{lrrrrr} (with 6 columns). Let's use a safe regex for tab:performance
part1, part2 = text.split(r"\label{tab:performance}")
part2 = re.sub(r"\\begin\{tabular\}.*?\\end\{tabular\}", t4.replace('\\', '\\\\'), part2, count=1, flags=re.DOTALL)
text = part1 + r"\label{tab:performance}" + part2

# Table 6: tc sensitivity
df_tc = pd.read_csv("results/tc_sensitivity.csv")
for c, tex_name in [("MinVar", "TC-MinVar"), ("NominalCVaR", "Nominal CVaR"), ("FiniteRegime", "Finite-Regime CVaR"), ("RobustSIP", "Robust SIP")]:
    s_vals = []
    for tc in [0.0, 5.0, 10.0, 20.0, 50.0]:
        row = df_tc[(df_tc['Strategy'] == c) & (df_tc['TC_bps'] == tc)]
        if len(row) > 0: s_vals.append(f"{row.iloc[0]['Sharpe']:.3f}")
        else: s_vals.append("-")
    turn = df_perf.loc[c, 'Avg_Turnover']*100
    new_r = f"{tex_name} & " + " & ".join(s_vals) + f" & {turn:.2f} \\\\"
    sub_row(r"^" + re.escape(tex_name) + r"\s*&", new_r)

# Table 10: bootstrap
df_boot = pd.read_csv("results/bootstrap_inference.csv").set_index("Benchmark")
for c, tex_name in [("NominalCVaR", "Nominal CVaR"), ("1/N", "1/N"), ("MinVar", "TC-MinVar"), ("FiniteRegime", "Finite-Regime CVaR")]:
    r = df_boot.loc[c]
    new_r = f"{tex_name} & {r['Sharpe_Diff']:.4f} & {r['Std_Error']:.4f} & [{r['CI_Lower_95']:.4f}, {r['CI_Upper_95']:.4f}] & {r['P_Value']:.3f} \\\\"
    sub_row(r"^" + re.escape(tex_name) + r"\s*&", new_r)

# Table 11: grid sensitivity
df_grid = pd.read_csv("results/grid_sensitivity.csv").set_index("Grid_Size")
for idx, r in df_grid.iterrows():
    d = r['L1_Distance']
    d_str = "---" if d == 0.0 else f"{d:.4f}"
    new_r = f"{idx}$\\times${idx} & {r['Avg_Runtime']:.2f} & {r['Avg_Active_States']:.1f} & {r['Avg_Worst_CVaR']*100:.2f} & {d_str} \\\\"
    sub_row(r"^" + re.escape(f"{idx}$\\times${idx}") + r"\s*&", new_r)

# Split ESS Table (4.2 in autoreview)
# Table 14 exceeds the usable width. Split it into two tables.
# Wait, I did this in auto_patch.py but didn't handle the label properly. Let's do it cleanly here.
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
    t_ess_2 += f"{idx} & {r['Turnover_Decimal']*100:.2f} & {r['Avg_ESS']:.1f} & {r['Min_ESS']:.1f} & {r['Retained_Frac_Decimal']*100:.1f} \\\\\n"
t_ess_2 += r"""\bottomrule
\end{tabular}
\end{table}"""

part1, part2 = text.split(r"\label{tab:sens_ess}")
# find the full table environment around it
start_idx = part1.rfind(r"\begin{table}")
end_idx = part2.find(r"\end{table}") + len(r"\end{table}")
text = part1[:start_idx] + t_ess_1 + "\n\n" + t_ess_2 + part2[end_idx:]

with open("Soumission/main_paper.tex", "w") as f:
    f.write(text)
