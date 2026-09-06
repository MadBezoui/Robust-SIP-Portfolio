import pandas as pd
import re

with open("patch_safe.py", "r") as f:
    text = f.read()

# Fix Table 12 replacement
t12_new = r"""# 8. tab:sens_bw (Table 12)
df_bw = pd.read_csv("results/bandwidth_sensitivity.csv").set_index("Multiplier")
t12 = r'''\begin{tabular}{lrr}
\toprule
\textbf{Scalar ($c$)} & \textbf{Active States} & \textbf{OOS CVaR$_{95}$ (\%)} \\
\midrule
'''
for idx, r in df_bw.iterrows():
    t12 += f"{idx} & {r['Avg_Active_States']:.1f} & {r['Avg_Worst_CVaR']*100:.2f} \\\\\n"
t12 += r'''\bottomrule
\end{tabular}'''
replace_table_near_label("tab:sens_bw", t12)
"""

text = re.sub(r"# 8\. tab:sens_bw \(Table 12\).*?(?=# 9\. Split ESS table)", t12_new, text, flags=re.DOTALL)

with open("patch_safe.py", "w") as f:
    f.write(text)
