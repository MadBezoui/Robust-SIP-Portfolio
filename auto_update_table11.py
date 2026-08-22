import pandas as pd
import re

df = pd.read_csv('results/grid_sensitivity.csv')

latex_rows = []
for index, row in df.iterrows():
    grid_size = int(row['Grid_Size'])
    rt = row['Avg_Runtime']
    act = row['Avg_Active_States']
    cvar = row['Avg_Worst_CVaR']
    l1 = row['L1_Distance']
    
    latex_row = f"${grid_size}\\times{grid_size}$ & {rt:.2f} & {act:.2f} & {cvar:.2f} & {l1:.4f} \\\\"
    latex_rows.append(latex_row)

new_body = "\\midrule\n" + "\n".join(latex_rows) + "\n\\bottomrule"

with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

# Using str.replace for safety
start_marker = r"""\begin{tabular}{rrrrr}
\toprule
\textbf{Grid Size}"""
end_marker = r"""\bottomrule
\end{tabular}"""

pattern = re.compile(r"\\begin{tabular}{rrrrr}\n\\toprule\n\\textbf{Grid Size}.*?\\bottomrule", re.DOTALL)
match = pattern.search(text)
if match:
    replacement = r"""\begin{tabular}{rrrrr}
\toprule
\textbf{Grid Size} & \textbf{Solve Time (s)} & \textbf{Active States} & \textbf{Worst CVaR (\%)} & \textbf{Mean $\ell_1$ distance to $81\times81$} \\
""" + new_body
    text = text[:match.start()] + replacement + text[match.end():]
    with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
        f.write(text)
    print("Table 11 updated successfully")
else:
    print("Table 11 not found")
