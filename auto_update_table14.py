import pandas as pd
import re

df = pd.read_csv('results/ess_full_backtest.csv')

latex_rows = []
for index, row in df.iterrows():
    ess_min = int(row['ESS_Min'])
    ann_ret = row['Ann_Return_Decimal'] * 100
    ann_vol = row['Ann_Vol_Decimal'] * 100
    sharpe = row['Sharpe']
    max_dd = row['Max_DD_Decimal'] * 100
    avg_turn = row['Turnover_Decimal']
    
    latex_row = f"{ess_min} & {ann_ret:.2f} & {ann_vol:.2f} & {sharpe:.2f} & {max_dd:.2f} & {avg_turn:.3f} \\\\"
    latex_rows.append(latex_row)

new_body = "\\midrule\n" + "\n".join(latex_rows) + "\n\\bottomrule"

with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

pattern = re.compile(r"\\begin{tabular}{rrrrrr}\n\\toprule\n\\textbf{ESS Minimum}.*?\\bottomrule", re.DOTALL)
match = pattern.search(text)
if match:
    replacement = r"""\begin{tabular}{rrrrrr}
\toprule
\textbf{ESS Minimum} & \textbf{Ann. Return (\%)} & \textbf{Ann. Volatility (\%)} & \textbf{Sharpe Ratio} & \textbf{Max Drawdown (\%)} & \textbf{Avg Turnover} \\
""" + new_body
    text = text[:match.start()] + replacement + text[match.end():]
    with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
        f.write(text)
    print("Table 14 updated successfully")
else:
    print("Table 14 not found")
