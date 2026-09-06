import pandas as pd
import re
import os

tex_path = "Soumission/main_paper.tex"
with open(tex_path, "r") as f:
    content = f.read()

# Update Table 2: Performance
try:
    df_perf = pd.read_csv("results/performance_table.csv")
    for _, row in df_perf.iterrows():
        strat = row['Strategy']
        if strat == "1_N": s_tex = "1/N"
        elif strat == "MinVar": s_tex = "TC-MinVar"
        elif strat == "NominalCVaR": s_tex = "Nominal CVaR"
        elif strat == "FiniteRegime": s_tex = "Finite-Regime CVaR"
        elif strat == "RobustSIP": s_tex = "Robust SIP"
        else: continue
        
        # We need to replace the line starting with s_tex
        pattern = re.compile(r"^(" + re.escape(s_tex) + r"\s*&.*?)\\\\$", re.MULTILINE)
        replacement = f"{s_tex} & {100*row['Ann_Mean']:.2f}\\% & {100*row['Ann_Vol']:.2f}\\% & {row['Sharpe']:.3f} & {100*row['Max_DD']:.2f}\\% & {100*row['Avg_Turnover']:.2f}\\% \\\\"
        content = pattern.sub(replacement, content)
except Exception as e:
    print(f"Skipping Table 2 update: {e}")

# Save
with open(tex_path, "w") as f:
    f.write(content)

print("Manuscript patched successfully.")
