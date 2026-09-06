import pandas as pd
import re

with open("Soumission/main_paper.tex", "r") as f:
    text = f.read()

def replace_table_near_label(label, new_tabular):
    global text
    idx = text.find(r"\label{" + label + "}")
    if idx == -1:
        print("Label not found:", label)
        return
    start_tabular = text.find(r"\begin{tabular}", idx)
    end_tabular = text.find(r"\end{tabular}", start_tabular) + len(r"\end{tabular}")
    text = text[:start_tabular] + new_tabular + text[end_tabular:]

# 1. Table 2
df_gap = pd.read_csv("results/gap_verification.csv").set_index("Label")
t2 = "\\begin{tabular}{lrrrr}\n\\toprule\n\\textbf{Crisis Period} & \\textbf{Max Gradient Norm} & \\textbf{Grid Dispersion} & \\textbf{Gradient $\\times$ Dispersion} & \\textbf{Local Search Improvement} \\\\\n\\midrule\n"
for idx, r in df_gap.iterrows():
    ls = r['LocalSearchImp']
    if ls == 0: ls_str = "0"
    else: ls_str = f"{ls:.2e}"
    t2 += f"{idx} & {r['MaxGradNorm']:.3f} & {r['GridDisp']:.3f} & {r['EmpiricalProduct']:.2f} & {ls_str} \\\\\n"
t2 += "\\bottomrule\n\\end{tabular}"
replace_table_near_label("tab:gap_verification", t2)

# 2. Table 4
df_perf = pd.read_csv("results/performance_table.csv").set_index("Strategy")
t4 = "\\begin{tabular}{lrrrrr}\n\\toprule\n\\textbf{Strategy} & \\textbf{Return (\\%)} & \\textbf{Vol (\\%)} & \\textbf{Sharpe} & \\textbf{Max DD (\\%)} & \\textbf{Turnover (\\%)} \\\\\n\\midrule\n"
for c, tex_name in [("1/N", "1/N"), ("MinVar", "TC-MinVar"), ("NominalCVaR", "Nominal CVaR"), ("FiniteRegime", "Finite-Regime CVaR"), ("RobustSIP", "Robust SIP")]:
    r = df_perf.loc[c]
    t4 += f"{tex_name} & {r['Ann_Mean']*100:.2f} & {r['Ann_Vol']*100:.2f} & {r['Sharpe']:.3f} & {r['Max_DD']*100:.2f} & {r['Avg_Turnover']*100:.2f} \\\\\n"
t4 += "\\bottomrule\n\\end{tabular}"
replace_table_near_label("tab:performance", t4)

# 3. Table 5 (Crisis)
df_cris = pd.read_csv("results/crisis_performance.csv")
t5 = "\\begin{tabular}{llrr}\n\\toprule\n\\textbf{Crisis Period} & \\textbf{Strategy} & \\textbf{Return (\\%)} & \\textbf{Max DD (\\%)} \\\\\n\\midrule\n"
for p in df_cris['Period'].unique():
    for c, tex_name in [("1/N", "1/N"), ("MinVar", "TC-MinVar"), ("NominalCVaR", "Nominal CVaR"), ("FiniteRegime", "Finite-Regime CVaR"), ("RobustSIP", "Robust SIP")]:
        row = df_cris[(df_cris['Period'] == p) & (df_cris['Strategy'] == c)]
        if len(row) > 0:
            r = row.iloc[0]
            t5 += f"{p} & {tex_name} & {r['Return']*100:.2f} & {r['MaxDD']*100:.2f} \\\\\n"
t5 += "\\bottomrule\n\\end{tabular}"
replace_table_near_label("tab:crisis", t5)

# 4. Table 6 (TC Sensitivity)
df_tc = pd.read_csv("results/tc_sensitivity.csv")
t6 = "\\begin{tabular}{lrrrrrrrrrr}\n\\toprule\n& \\multicolumn{5}{c}{\\textbf{Sharpe Ratio (net of TC)}} & \\multicolumn{5}{c}{\\textbf{Final Wealth (\\$, net of TC)}} \\\\\n\\cmidrule(lr){2-6} \\cmidrule(lr){7-11}\n\\textbf{Strategy} & \\textbf{0 bps} & \\textbf{5 bps} & \\textbf{10 bps} & \\textbf{20 bps} & \\textbf{50 bps} & \\textbf{0 bps} & \\textbf{5 bps} & \\textbf{10 bps} & \\textbf{20 bps} & \\textbf{50 bps} \\\\\n\\midrule\n"
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
    t6 += f"{tex_name} & " + " & ".join(s_vals) + " & " + " & ".join(w_vals) + " \\\\\n"
t6 += "\\bottomrule\n\\end{tabular}"
replace_table_near_label("tab:tc_sensitivity", t6)

# Table 9 (ESS Diagnostics)
df_hist = pd.read_csv("results/active_states_history.csv")
mean_ess = df_hist['Avg_Active_State_ESS']
t9 = "\\begin{tabular}{lr}\n\\toprule\n\\textbf{Statistic} & \\textbf{Value} \\\\\n\\midrule\n"
t9 += "Minimum window-level mean ESS & " + f"{mean_ess.min():.1f}" + " \\\\\n"
t9 += "5th Percentile window-level mean ESS & " + f"{mean_ess.quantile(0.05):.1f}" + " \\\\\n"
t9 += "Median window-level mean ESS & " + f"{mean_ess.median():.1f}" + " \\\\\n"
t9 += "Mean window-level mean ESS & " + f"{mean_ess.mean():.1f}" + " \\\\\n"
t9 += "Maximum window-level mean ESS & " + f"{mean_ess.max():.1f}" + " \\\\\n"
t9 += "\\bottomrule\n\\end{tabular}"
replace_table_near_label("tab:ess_diagnostics", t9)

# Table 10 (Bootstrap)
df_boot = pd.read_csv("results/bootstrap_inference.csv").set_index("Benchmark")
t10 = "\\begin{tabular}{lrrrr}\n\\toprule\n\\textbf{Benchmark} & \\textbf{$\\Delta$ Sharpe} & \\textbf{Std Error} & \\textbf{95\\% CI} & \\textbf{$p$-value} \\\\\n\\midrule\n"
for c, tex_name in [("NominalCVaR", "Nominal CVaR"), ("1/N", "1/N"), ("MinVar", "TC-MinVar"), ("FiniteRegime", "Finite-Regime CVaR")]:
    r = df_boot.loc[c]
    t10 += f"{tex_name} & {r['Sharpe_Diff']:.4f} & {r['Std_Error']:.4f} & [{r['CI_Lower_95']:.4f}, {r['CI_Upper_95']:.4f}] & {r['P_Value']:.3f} \\\\\n"
t10 += "\\bottomrule\n\\end{tabular}"
replace_table_near_label("tab:bootstrap", t10)

# Table 11
df_grid = pd.read_csv("results/grid_sensitivity.csv").set_index("Grid_Size")
t11 = "\\begin{tabular}{lrrrr}\n\\toprule\n\\textbf{Grid Resolution} & \\textbf{Runtime (s)} & \\textbf{Active States} & \\textbf{OOS CVaR$_{95}$ (\\%)} & \\textbf{Dist to Base} \\\\\n\\midrule\n"
for idx, r in df_grid.iterrows():
    d = r['L1_Distance']
    d_str = "---" if d == 0.0 else f"{d:.4f}"
    t11 += f"{idx}$\\times${idx} & {r['Avg_Runtime']:.2f} & {r['Avg_Active_States']:.2f} & {r['Avg_Worst_CVaR']:.2f} & {d_str} \\\\\n"
t11 += "\\bottomrule\n\\end{tabular}"
replace_table_near_label("tab:sens_grid", t11)

# Table 12
df_bw = pd.read_csv("results/bandwidth_sensitivity.csv").set_index("Multiplier")
t12 = "\\begin{tabular}{lrr}\n\\toprule\n\\textbf{Scalar ($c$)} & \\textbf{Active States} & \\textbf{OOS CVaR$_{95}$ (\\%)} \\\\\n\\midrule\n"
for idx, r in df_bw.iterrows():
    t12 += f"{idx} & {r['Avg_Active_States']:.2f} & {r['Avg_Worst_CVaR']:.2f} \\\\\n"
t12 += "\\bottomrule\n\\end{tabular}"
replace_table_near_label("tab:sens_bw", t12)

# Table 13 (tab:sens_ess) -- Wait, what is Table 13? Let's check what ess_sensitivity.csv has!
df_ess_sens = pd.read_csv("results/ess_sensitivity.csv").set_index("ESS_Min")
t13 = "\\begin{tabular}{lrr}\n\\toprule\n$E_{\\min}$ & \\textbf{Avg Retained States} & \\textbf{OOS CVaR$_{95}$ (\\%)} \\\\\n\\midrule\n"
for idx, r in df_ess_sens.iterrows():
    t13 += f"{idx} & {r['Avg_Retained_States']:.1f} & {r['Avg_Worst_CVaR']:.2f} \\\\\n"
t13 += "\\bottomrule\n\\end{tabular}"
replace_table_near_label("tab:sens_ess", t13)

# Table 14/15: Wait, they were combined in Table 14 previously. The validation script expects tab:ess_backtest_perf and tab:ess_backtest_diag.
# I need to ADD these labels if they don't exist, by splitting the table at the very end of the document.
df_ess = pd.read_csv("results/ess_full_backtest.csv").set_index("ESS_Min")
t_ess_1 = "\\begin{table}[htbp]\n\\centering\n\\caption{Sensitivity to Minimum Effective Sample Size ($E_{\\min}$): Out-of-sample performance.}\n\\label{tab:ess_backtest_perf}\n\\begin{tabular}{lrrrrr}\n\\toprule\n$E_{\\min}$ & \\textbf{Return (\\%)} & \\textbf{Vol (\\%)} & \\textbf{Sharpe} & \\textbf{Max DD (\\%)} & \\textbf{Wealth (\\$)} \\\\\n\\midrule\n"
for idx, r in df_ess.iterrows():
    t_ess_1 += f"{idx} & {r['Ann_Return_Decimal']*100:.2f} & {r['Ann_Vol_Decimal']*100:.2f} & {r['Sharpe']:.3f} & {r['Max_DD_Decimal']*100:.2f} & {r['Wealth']:.2f} \\\\\n"
t_ess_1 += "\\bottomrule\n\\end{tabular}\n\\end{table}"

t_ess_2 = "\\begin{table}[htbp]\n\\centering\n\\caption{Sensitivity to Minimum Effective Sample Size ($E_{\\min}$): Implementation diagnostics.}\n\\label{tab:ess_backtest_diag}\n\\begin{tabular}{lrrrr}\n\\toprule\n$E_{\\min}$ & \\textbf{Turnover (\\%)} & \\textbf{Avg ESS} & \\textbf{Min ESS} & \\textbf{Grid Retained (\\%)} \\\\\n\\midrule\n"
for idx, r in df_ess.iterrows():
    t_ess_2 += f"{idx} & {r['Turnover_Decimal']*100:.2f} & {r['Avg_ESS']:.2f} & {r['Min_ESS']:.2f} & {r['Retained_Frac_Decimal']*100:.1f} \\\\\n"
t_ess_2 += "\\bottomrule\n\\end{tabular}\n\\end{table}"

idx_full_ess = text.find(r"\label{tab:ess_full}") # Wait, what was the label for the full table? In the PDF, it says "Table 14: Sensitivity to Minimum Effective Sample Size (E_min)". Let's look for "tab:ess_full" or similar.
# Let's replace the whole table block if found.
match = re.search(r"\\begin\{table\}.*?Table 14.*?\\end\{table\}", text, flags=re.DOTALL) 
# I will use Python to find the table that has `E_{\min}` and `Wealth` and `Grid Retained`.
if "Grid Retained (\\%)" in text:
    # There is a table that combines them. Let's just append our two tables to the end of the experimental section.
    pass

# Prose fixes
text = text.replace("71.43/3.45\\approx20.70", "71.43/3.45 \\approx 20.7")
if "71.43/3.45 \\approx 20.7" not in text:
    text = text.replace("71.43/3.45", "71.43/3.45 \\approx 20.7")
text = text.replace("an average of only 3.66 active state blocks", "an average of only 3.66 active state blocks (range 1-9 across 377 windows)")

with open("Soumission/main_paper.tex", "w") as f:
    f.write(text)
