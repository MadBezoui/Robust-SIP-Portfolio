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

# 2. Update Table 4 (performance)
try:
    df_perf = pd.read_csv("results/performance_table.csv")
    new_perf_rows = ""
    for _, row in df_perf.iterrows():
        name = row['Strategy']
        if name == "MinVar": name = "TC-MinVar"
        if name == "NominalCVaR": name = "Nominal CVaR"
        if name == "FiniteRegime": name = "Finite-Regime CVaR"
        if name == "RobustSIP": name = "Robust SIP"
        # Ann_Mean is a fraction (e.g. 0.122 -> 12.24)
        new_perf_rows += f"{name} & {row['Ann_Mean']*100:.2f}\\% & {row['Ann_Vol']*100:.2f}\\% & {row['Sharpe']:.3f} & {row['Max_DD']*100:.2f}\\% & {row['Avg_Turnover']*100:.2f}\\% \\\\\n"
    text = replace_table_rows(text, "tab:performance", new_perf_rows)
    print("Updated Table 4.")
except Exception as e:
    print("Skipping Table 4:", e)

with open(tex_path, "w") as f:
    f.write(text)
# 3. Update Table 10 (bootstrap)
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
except Exception as e:
    print("Skipping Table 10:", e)

# 4. Update Table 15 (sens_block)
try:
    df_block = pd.read_csv("results/block_length_sensitivity.csv")
    new_block_rows = ""
    for _, row in df_block.iterrows():
        new_block_rows += f"{int(row['Block_Length'])} & {row['SE']:.4f} & {row['P_Value']:.3f} \\\\\n"
    text = replace_table_rows(text, "tab:sens_block", new_block_rows)
    print("Updated Table 15.")
except Exception as e:
    print("Skipping Table 15:", e)

with open(tex_path, "w") as f:
    f.write(text)
