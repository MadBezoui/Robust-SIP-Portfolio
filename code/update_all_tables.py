import pandas as pd
import re

tex_path = "submission_CompOptAlg_v2/main_paper.tex"
with open(tex_path, "r") as f:
    text = f.read()

def replace_table_rows(text, table_label, new_rows):
    pattern = r"(\\label\{" + table_label + r"\}.*?\\midrule\n)(.*?)(\\bottomrule)"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        print(f"Table {table_label} not found.")
        return text
    return text[:match.start(2)] + new_rows + "\n" + text[match.end(2):]

try:
    df_gap = pd.read_csv("results/gap_verification.csv")
    new_gap_rows = ""
    for _, row in df_gap.iterrows():
        new_gap_rows += f"{row['Label']} & {row['MaxGradNorm']:.3f} & {row['GridDisp']:.3f} & ${row['EmpiricalProduct']:.2e}$ & ${row['LocalSearchImp']:.1e}$ \\\\\n"
    text = replace_table_rows(text, "tab:gap_verification", new_gap_rows)
    print("Updated Table 2.")
except Exception as e: print("Skipping Table 2:", e)

try:
    df_perf = pd.read_csv("results/performance_table.csv")
    new_perf_rows = ""
    for _, row in df_perf.iterrows():
        name = row['Strategy']
        if name == "MinVar": name = "TC-MinVar"
        if name == "NominalCVaR": name = "Nominal CVaR"
        if name == "FiniteRegime": name = "Finite-Regime CVaR"
        if name == "RobustSIP": name = "Robust SIP"
        new_perf_rows += f"{name} & {row['Ann_Mean']*100:.2f}\\% & {row['Ann_Vol']*100:.2f}\\% & {row['Sharpe']:.3f} & {row['Max_DD']*100:.2f}\\% & {row['Avg_Turnover']*100:.2f}\\% \\\\\n"
    text = replace_table_rows(text, "tab:performance", new_perf_rows)
    print("Updated Table 4.")
except Exception as e: print("Skipping Table 4:", e)

try:
    df_boot = pd.read_csv("results/bootstrap_inference.csv")
    new_boot_rows = ""
    for _, row in df_boot.iterrows():
        bench = row['Benchmark']
        if bench == "MinVar": bench = "TC-MinVar"
        if bench == "NominalCVaR": bench = "Nominal CVaR"
        if bench == "FiniteRegime": bench = "Finite-Regime CVaR"
        ci = f"[{row['CI_Lower_95']:.3f}, {row['CI_Upper_95']:.3f}]"
        new_boot_rows += f"{bench} & {row['Sharpe_Diff']:.3f} & {ci} & {row['P_Value']:.3f} \\\\\n"
    text = replace_table_rows(text, "tab:bootstrap", new_boot_rows)
    print("Updated Table 10.")
except Exception as e: print("Skipping Table 10:", e)

try:
    df_block = pd.read_csv("results/block_length_sensitivity.csv")
    new_block_rows = ""
    for _, row in df_block.iterrows():
        new_block_rows += f"{int(row['Block_Length'])} & {row['SE']:.4f} & {row['P_Value']:.3f} \\\\\n"
    text = replace_table_rows(text, "tab:sens_block", new_block_rows)
    print("Updated Table 15.")
except Exception as e: print("Skipping Table 15:", e)

try:
    df_comp = pd.read_csv("results/grid_comparison.csv")
    ad_row = df_comp[df_comp['Method'].str.contains('Adaptive')].iloc[0]
    d21_row = df_comp[df_comp['Method'].str.contains('21x21') & ~df_comp['Method'].str.contains('Adaptive')].iloc[0]
    d41_row = df_comp[df_comp['Method'].str.contains('41x41')].iloc[0]
    new_comp_rows = ""
    new_comp_rows += f"Adaptive exchange, $21\\times21$ grid & Exchange residual \\\\\n"
    new_comp_rows += f"$\\le 10^{{-4}}$ & {ad_row['Active_States']} active state blocks & {ad_row['Runtime_sec']:.2f} s\n"
    new_comp_rows += f"& final grid-oracle value $\\approx {ad_row['Objective_Value']*100:.4f}\\%$ \\\\\n"
    new_comp_rows += f"Dense $21\\times 21$ & {d21_row['Termination_Status']} & {d21_row['Active_States']} & {d21_row['Runtime_sec']:.2f} s & optimum $\\approx {d21_row['Objective_Value']*100:.4f}\\%$ \\\\\n"
    new_comp_rows += f"Dense $41\\times41$ & Time limit reached; no primal incumbent returned\n"
    new_comp_rows += f"& {d41_row['Active_States']} state blocks & {d41_row['Runtime_sec']:.2f} s & Not available \\\\\n"
    text = replace_table_rows(text, "tab:computational", new_comp_rows)
    print("Updated Table 7.")
    
    t_ad = ad_row['Runtime_sec']
    t_d21 = d21_row['Runtime_sec']
    act = ad_row['Active_States']
    ratio = t_d21 / t_ad
    text = re.sub(r"from \d+\.\d+ seconds for the dense", f"from {t_d21:.2f} seconds for the dense", text)
    text = re.sub(r"to \d+\.\d+ seconds for the adaptive", f"to {t_ad:.2f} seconds for the adaptive", text)
    text = re.sub(r"ratio of approximately \d+\.\d+", f"ratio of approximately {ratio:.1f}", text)
    text = re.sub(r"average of \d+\.\d+ active state blocks", f"average of {act:.2f} active state blocks", text)
    print("Updated Text for computational benchmark.")
except Exception as e: print("Skipping Table 7:", e)

with open(tex_path, "w") as f:
    f.write(text)
