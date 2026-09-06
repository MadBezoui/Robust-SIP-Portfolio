import pandas as pd
import re

with open("Soumission/main_paper.tex", "r") as f:
    text = f.read()

# 1. Table 2 (gap_verification)
df_gap = pd.read_csv("results/gap_verification.csv").set_index("Label")
for idx, r in df_gap.iterrows():
    ls = r['LocalSearchImp']
    if ls == 0: ls_str = "0"
    elif ls < 1e-4: ls_str = f"${ls:.1e}$".replace("e", "\\times 10^{").replace("+0", "").replace("-0", "-") + "}"
    else: ls_str = f"{ls:.6f}"
    # e.g., 1998-08 (LTCM) & 0.084 & ...
    old_row = re.escape(idx) + r"\s*&.*?\\\\"
    new_row = f"{idx} & {r['MaxGradNorm']:.3f} & {r['GridDisp']:.3f} & {r['EmpiricalProduct']:.2f} & {ls_str} \\\\"
    text = re.sub(old_row, new_row, text, count=1, flags=re.MULTILINE)

# 2. Table 4 (performance). Let's replace the ENTIRE tab:performance table to be horizontal.
df_perf = pd.read_csv("results/performance_table.csv").set_index("Strategy")
t4 = r"""\begin{tabular}{lrrrrr}
\toprule
\textbf{Strategy} & \textbf{Return (\%)} & \textbf{Vol (\%)} & \textbf{Sharpe} & \textbf{Max DD (\%)} & \textbf{Turnover (\%)} \\
\midrule
"""
for c, tex_name in [("1/N", "1/N"), ("MinVar", "TC-MinVar"), ("NominalCVaR", "Nominal CVaR"), ("FiniteRegime", "Finite-Regime CVaR"), ("RobustSIP", "Robust SIP")]:
    r = df_perf.loc[c]
    t4 += f"{tex_name} & {r['Ann_Mean']*100:.2f} & {r['Ann_Vol']*100:.2f} & {r['Sharpe']:.3f} & {r['Max_DD']*100:.2f} & {r['Avg_Turnover']*100:.2f} \\\\\n"
t4 += r"""\bottomrule
\end{tabular}"""

parts = text.split(r"\label{tab:performance}")
parts[1] = re.sub(r"\\begin\{tabular\}.*?\\end\{tabular\}", t4.replace('\\', '\\\\'), parts[1], count=1, flags=re.DOTALL)
text = r"\label{tab:performance}".join(parts)

# 3. Table 6 (tc sensitivity)
df_tc = pd.read_csv("results/tc_sensitivity.csv")
for c, tex_name in [("MinVar", "TC-MinVar"), ("NominalCVaR", "Nominal CVaR"), ("FiniteRegime", "Finite-Regime CVaR"), ("RobustSIP", "Robust SIP")]:
    s_vals = []
    w_vals = []
    for tc in [0.0, 5.0, 10.0, 20.0, 50.0]:
        row = df_tc[(df_tc['Strategy'] == c) & (df_tc['TC_bps'] == tc)]
        if len(row) > 0:
            s_vals.append(f"{row.iloc[0]['Sharpe']:.3f}")
            w_vals.append(f"{row.iloc[0]['Final_Wealth']:.2f}")
        else:
            s_vals.append("-")
            w_vals.append("-")
    turn = df_perf.loc[c, 'Avg_Turnover']*100
    
    # wait, the tc sensitivity table in manuscript has columns for 0, 5, 10, 20, 50, and wealth 0, 5, 10, 20, 50?
    # let's look at what validate_manuscript.py says. It checks Sharpe for 0, 5, 10, 20, 50 and Wealth for 0, 5, 10, 20, 50.
    # But wait, looking at Table 6 in the manuscript, the columns are: Strategy & 0 & 5 & 10 & 20 & 50 & 0 & 5 & 10 & 20 & 50 \\
    old_row = r"^" + re.escape(tex_name) + r"\s*&.*?\\\\$"
    new_row = f"{tex_name} & " + " & ".join(s_vals) + " & " + " & ".join(w_vals) + r" \\\\"
    text = re.sub(old_row, new_row.replace('\\', '\\\\'), text, count=1, flags=re.MULTILINE)

# 4. Table 10 (bootstrap inference)
df_boot = pd.read_csv("results/bootstrap_inference.csv").set_index("Benchmark")
for c, tex_name in [("NominalCVaR", "Nominal CVaR"), ("1/N", "1/N"), ("MinVar", "TC-MinVar"), ("FiniteRegime", "Finite-Regime CVaR")]:
    r = df_boot.loc[c]
    old_row = r"^" + re.escape(tex_name) + r"\s*&.*?\\\\$"
    new_row = f"{tex_name} & {r['Sharpe_Diff']:.4f} & {r['Std_Error']:.4f} & [{r['CI_Lower_95']:.4f}, {r['CI_Upper_95']:.4f}] & {r['P_Value']:.3f} \\\\"
    text = re.sub(old_row, new_row.replace('\\', '\\\\'), text, count=1, flags=re.MULTILINE)

# 5. Table 11 (grid sensitivity)
df_grid = pd.read_csv("results/grid_sensitivity.csv").set_index("Grid_Size")
for idx, r in df_grid.iterrows():
    d = r['L1_Distance']
    d_str = "---" if d == 0.0 else f"{d:.4f}"
    old_row = r"^" + re.escape(f"{idx}$\\times${idx}") + r"\s*&.*?\\\\$"
    new_row = f"{idx}$\\times${idx} & {r['Avg_Runtime']:.2f} & {r['Avg_Active_States']:.1f} & {r['Avg_Worst_CVaR']*100:.2f} & {d_str} \\\\"
    text = re.sub(old_row, new_row.replace('\\', '\\\\'), text, count=1, flags=re.MULTILINE)

# 6. Split ESS Table
df_ess = pd.read_csv("results/ess_full_backtest.csv").set_index("ESS_Min")
t_ess_1 = r"""\caption{Sensitivity to Minimum Effective Sample Size ($E_{\min}$): Out-of-sample performance.}
\label{tab:ess_backtest_perf}
\begin{tabular}{lrrrrr}
\toprule
$E_{\min}$ & \textbf{Return (\%)} & \textbf{Vol (\%)} & \textbf{Sharpe} & \textbf{Max DD (\%)} & \textbf{Wealth (\$)} \\
\midrule
"""
for idx, r in df_ess.iterrows():
    t_ess_1 += f"{idx} & {r['Ann_Return_Decimal']*100:.2f} & {r['Ann_Vol_Decimal']*100:.2f} & {r['Sharpe']:.3f} & {r['Max_DD_Decimal']*100:.2f} & {r['Wealth']:.2f} \\\\\n"
t_ess_1 += r"""\bottomrule
\end{tabular}"""

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

parts = text.split(r"\label{tab:sens_ess}")
if len(parts) == 2:
    # We replace from \caption{...} before it to \end{tabular} after it
    # Find caption before
    cap_start = parts[0].rfind(r"\caption{")
    tab_end = parts[1].find(r"\end{tabular}") + len(r"\end{tabular}")
    new_text = parts[0][:cap_start] + t_ess_1 + "\n\n" + t_ess_2 + parts[1][tab_end:]
    text = new_text

# Prose fixes
# "mean active states 3.66 not quoted in the manuscript"
# "active-state range 1-9 not quoted in the manuscript"
# "window count 377 not quoted"
# "runtime ratio expression not found"
text = text.replace("71.43/3.45\\approx20.70", "71.43/3.45 \\approx 20.7")
# Let's fix the prose using a generic append if missing.
if "71.43/3.45 \\approx 20.7" not in text:
    text = text.replace("71.43/3.45", "71.43/3.45 \\approx 20.7")

with open("Soumission/main_paper.tex", "w") as f:
    f.write(text)
