import pandas as pd
import re

with open("Soumission/main_paper.tex", "r") as f:
    text = f.read()

def replace_table(label, new_tabular):
    global text
    # Find the environment containing the label
    # We will search for \label{label} and then replace the \begin{tabular} ... \end{tabular} inside that figure/table environment
    parts = text.split(r"\label{" + label + "}")
    if len(parts) == 2:
        pre = parts[0]
        post = parts[1]
        # find the next tabular in post
        post_sub = re.sub(r"\\begin\{tabular\}.*?\\end\{tabular\}", new_tabular.replace('\\', '\\\\'), post, count=1, flags=re.DOTALL)
        text = pre + r"\label{" + label + "}" + post_sub
    elif len(parts) > 2:
        # if multiple, just replace the first one
        post = parts[1]
        post_sub = re.sub(r"\\begin\{tabular\}.*?\\end\{tabular\}", new_tabular.replace('\\', '\\\\'), post, count=1, flags=re.DOTALL)
        text = pre + r"\label{" + label + "}" + post_sub + "".join([r"\label{" + label + "}" + p for p in parts[2:]])
    else:
        # maybe label is inside tabular? or before? Let's do a block replacement based on the caption?
        pass

# 1. tab:performance
df_perf = pd.read_csv("results/performance_table.csv").set_index("Strategy")
t4 = "\\begin{tabular}{lrrrrr}\n\\toprule\n\\textbf{Strategy} & \\textbf{Return (\\%)} & \\textbf{Vol (\\%)} & \\textbf{Sharpe} & \\textbf{Max DD (\\%)} & \\textbf{Turnover (\\%)} \\\\\n\\midrule\n"
for c, tex_name in [("1/N", "1/N"), ("MinVar", "TC-MinVar"), ("NominalCVaR", "Nominal CVaR"), ("FiniteRegime", "Finite-Regime CVaR"), ("RobustSIP", "Robust SIP")]:
    r = df_perf.loc[c]
    t4 += f"{tex_name} & {r['Ann_Mean']*100:.2f} & {r['Ann_Vol']*100:.2f} & {r['Sharpe']:.3f} & {r['Max_DD']*100:.2f} & {r['Avg_Turnover']*100:.2f} \\\\\n"
t4 += "\\bottomrule\n\\end{tabular}"
replace_table("tab:performance", t4)

# 2. tab:gap_verification
df_gap = pd.read_csv("results/gap_verification.csv").set_index("Label")
t_gap = "\\begin{tabular}{lrrrr}\n\\toprule\n\\textbf{Crisis Period} & \\textbf{Max Gradient Norm} & \\textbf{Grid Dispersion} & \\textbf{Gradient $\\times$ Dispersion} & \\textbf{Local Search Improvement} \\\\\n\\midrule\n"
for idx, row in df_gap.iterrows():
    # Use scientific notation for local search improvement if it's very small
    ls_imp = row['LocalSearchImp']
    if ls_imp == 0.0:
        ls_str = "0"
    elif ls_imp < 1e-4:
        # format as 6.9 \times 10^{-18}
        ls_str = f"${ls_imp:.1e}$".replace("e", "\\times 10^{").replace("+0", "").replace("-0", "-") + "}"
        # fix the format for like 1.4e-17 -> 1.4\times 10^{-17}
        # Actually standard python is 1.4e-17.
        ls_str = ls_str.replace("10^{-", "10^{-").replace("10^{0", "10^{")
    else:
        ls_str = f"{ls_imp:.6f}"
    
    t_gap += f"{idx} & {row['MaxGradNorm']:.3f} & {row['GridDisp']:.3f} & {row['EmpiricalProduct']:.2f} & {ls_str} \\\\\n"
t_gap += "\\bottomrule\n\\end{tabular}"
replace_table("tab:gap_verification", t_gap)

# 3. tab:tc_sensitivity
df_tc = pd.read_csv("results/tc_sensitivity.csv")
t_tc = "\\begin{tabular}{lrrrrrr}\n\\toprule\n\\textbf{Cost (bps)} & \\textbf{0} & \\textbf{5} & \\textbf{10} & \\textbf{20} & \\textbf{50} & \\textbf{Avg Turnover (\\%)} \\\\\n\\midrule\n"
for c, tex_name in [("1/N", "1/N"), ("MinVar", "TC-MinVar"), ("NominalCVaR", "Nominal CVaR"), ("FiniteRegime", "Finite-Regime CVaR"), ("RobustSIP", "Robust SIP")]:
    if c == "1/N": 
        continue
    # we need Sharpe for 0, 5, 10, 20, 50
    s_vals = []
    w_vals = []
    for tc in [0.0, 5.0, 10.0, 20.0, 50.0]:
        row = df_tc[(df_tc['Strategy'] == c) & (df_tc['TC_bps'] == tc)]
        if len(row) > 0:
            s_vals.append(f"{row.iloc[0]['Sharpe']:.3f}")
        else:
            s_vals.append("-")
    
    turn = df_perf.loc[c, 'Avg_Turnover']*100
    t_tc += f"{tex_name} & " + " & ".join(s_vals) + f" & {turn:.2f} \\\\\n"
t_tc += "\\bottomrule\n\\end{tabular}"
replace_table("tab:tc_sensitivity", t_tc)

# 4. tab:bootstrap (Table 10)
df_boot = pd.read_csv("results/bootstrap_inference.csv").set_index("Benchmark")
t_boot = "\\begin{tabular}{lrrrr}\n\\toprule\n\\textbf{Benchmark} & \\textbf{$\\Delta$ Sharpe} & \\textbf{Std Error} & \\textbf{95\\% CI} & \\textbf{$p$-value} \\\\\n\\midrule\n"
for c, tex_name in [("NominalCVaR", "Nominal CVaR"), ("1/N", "1/N"), ("MinVar", "TC-MinVar"), ("FiniteRegime", "Finite-Regime CVaR")]:
    r = df_boot.loc[c]
    t_boot += f"{tex_name} & {r['Sharpe_Diff']:.4f} & {r['Std_Error']:.4f} & [{r['CI_Lower_95']:.4f}, {r['CI_Upper_95']:.4f}] & {r['P_Value']:.3f} \\\\\n"
t_boot += "\\bottomrule\n\\end{tabular}"
replace_table("tab:bootstrap", t_boot)

# 5. tab:sens_grid (Table 11)
df_grid = pd.read_csv("results/grid_sensitivity.csv").set_index("Grid_Size")
t_grid = "\\begin{tabular}{lrrrr}\n\\toprule\n\\textbf{Grid Resolution} & \\textbf{Runtime (s)} & \\textbf{Active States} & \\textbf{OOS CVaR$_{95}$ (\\%)} & \\textbf{Dist to Base} \\\\\n\\midrule\n"
for idx, row in df_grid.iterrows():
    dist = row['L1_Distance']
    d_str = "---" if dist == 0.0 else f"{dist:.4f}"
    t_grid += f"{idx} & {row['Avg_Runtime']:.2f} & {row['Avg_Active_States']:.1f} & {row['Avg_Worst_CVaR']*100:.2f} & {d_str} \\\\\n"
t_grid += "\\bottomrule\n\\end{tabular}"
replace_table("tab:sens_grid", t_grid)

# Wait, the validation script says:
# - tab:ess_backtest_perf: table not found in the manuscript
# - tab:ess_backtest_diag: table not found in the manuscript
# - Tables 14/15: row count differs from ess_full_backtest.csv
# I need to split the ESS table into TWO tables!

# Find the old tab:sens_ess and replace it with TWO tables
df_ess = pd.read_csv("results/ess_full_backtest.csv").set_index("ESS_Min")
t_ess_perf = "\\begin{table}[htbp]\n\\centering\n\\caption{Sensitivity to Minimum Effective Sample Size ($E_{\\min}$): Out-of-sample performance.}\n\\label{tab:ess_backtest_perf}\n\\begin{tabular}{lrrrrr}\n\\toprule\n$E_{\\min}$ & \\textbf{Return (\\%)} & \\textbf{Vol (\\%)} & \\textbf{Sharpe} & \\textbf{Max DD (\\%)} & \\textbf{Wealth (\\$)} \\\\\n\\midrule\n"
for idx, row in df_ess.iterrows():
    t_ess_perf += f"{idx} & {row['Ann_Return_Decimal']*100:.2f} & {row['Ann_Vol_Decimal']*100:.2f} & {row['Sharpe']:.3f} & {row['Max_DD_Decimal']*100:.2f} & {row['Wealth']:.2f} \\\\\n"
t_ess_perf += "\\bottomrule\n\\end{tabular}\n\\end{table}\n"

t_ess_diag = "\\begin{table}[htbp]\n\\centering\n\\caption{Sensitivity to Minimum Effective Sample Size ($E_{\\min}$): Implementation diagnostics.}\n\\label{tab:ess_backtest_diag}\n\\begin{tabular}{lrrrr}\n\\toprule\n$E_{\\min}$ & \\textbf{Turnover (\\%)} & \\textbf{Avg ESS} & \\textbf{Min ESS} & \\textbf{Grid Retained (\\%)} \\\\\n\\midrule\n"
for idx, row in df_ess.iterrows():
    t_ess_diag += f"{idx} & {row['Turnover_Decimal']*100:.2f} & {row['Avg_ESS']:.1f} & {row['Min_ESS']:.1f} & {row['Retained_Frac_Decimal']*100:.1f} \\\\\n"
t_ess_diag += "\\bottomrule\n\\end{tabular}\n\\end{table}\n"

# Replace the single old tab:sens_ess block completely
old_ess_block = re.search(r"\\begin\{table\}.*?\\label\{tab:sens_ess\}.*?\\end\{table\}", text, re.DOTALL)
if old_ess_block:
    text = text.replace(old_ess_block.group(0), t_ess_perf + "\n" + t_ess_diag)
else:
    print("Could not find tab:sens_ess")

# Also Table 1 is unreadable:
# Let's fix Table 1 (tab:models).
# "use one row per model, reduce prose, avoid repeating Observed covariates"
t1 = r"""
\begin{table}[htbp]
\centering
\caption{Taxonomy of portfolio optimization paradigms. Robust SIP avoids forming a single global ambiguity set, replacing it with a conditional empirical distribution constrained by state-specific geometries.}
\label{tab:models}
\resizebox{\textwidth}{!}{
\begin{tabular}{llll}
\toprule
\textbf{Paradigm} & \textbf{Objective} & \textbf{Distributional Assumption} & \textbf{Covariate Role} \\
\midrule
Unconditional Markowitz & Mean-Variance & Stationary Gaussian & None \\
Nominal Conditional & Expected Shortfall & True conditional $P(Y \mid X)$ known & Directly defines the distribution \\
Standard DRO & Worst-case Risk over $\mathcal{P}$ & Global ambiguity set $\mathcal{P}$ (e.g., Wasserstein) & Typically unconditional \\
Covariate-driven DRO & Conditional Worst-case Risk & State-dependent ambiguity set $\mathcal{P}(x)$ & Centers the conditional ambiguity set \\
\textbf{Robust SIP (Proposed)} & \textbf{Worst-case Risk over $\mathcal{U}$} & \textbf{Continuous kernel-weighted empirical} & \textbf{Defines a continuous geometric state space $\mathcal{U}$} \\
\bottomrule
\end{tabular}
}
\end{table}
"""
old_t1_block = re.search(r"\\begin\{table\}.*?\\label\{tab:models\}.*?\\end\{table\}", text, re.DOTALL)
if old_t1_block:
    text = text.replace(old_t1_block.group(0), t1)

with open("Soumission/main_paper.tex", "w") as f:
    f.write(text)

print("Tables updated.")
