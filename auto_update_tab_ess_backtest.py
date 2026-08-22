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
    wealth = row['Wealth']
    turnover = row['Turnover_Decimal'] * 100
    avg_ess = row['Avg_ESS']
    min_ess = row['Min_ESS']
    grid_retained = row['Retained_Frac_Decimal'] * 100
    
    latex_row = f"$E_{{\\min}} = {ess_min}$ & {ann_ret:.2f} & {ann_vol:.2f} & {sharpe:.2f} & $-{abs(max_dd):.2f}$ & {wealth:.2f} & {turnover:.2f} & {avg_ess:.1f} & {min_ess:.1f} & {grid_retained:.1f} \\\\"
    latex_rows.append(latex_row)

new_body = "\\midrule\n" + "\n".join(latex_rows) + "\n\\bottomrule"

with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

pattern = re.compile(r"\\begin{tabular}{lrrrrrrrrr}\n\\toprule\n\\textbf{Threshold}.*?\\bottomrule", re.DOTALL)
match = pattern.search(text)
if match:
    replacement = r"""\begin{tabular}{lrrrrrrrrr}
\toprule
\textbf{Threshold} & \textbf{Ann. Ret (\%)} & \textbf{Ann. Vol (\%)} & \textbf{Sharpe} & \textbf{Max DD (\%)} & \textbf{Wealth} & \textbf{Turnover (\%)} & \textbf{Avg ESS} & \textbf{Min ESS} & \textbf{Grid Retained (\%)} \\
""" + new_body
    text = text[:match.start()] + replacement + text[match.end():]
    with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
        f.write(text)
    print("tab:ess_backtest updated successfully")
else:
    print("tab:ess_backtest not found")
