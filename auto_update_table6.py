import pandas as pd
import re

df = pd.read_csv('results/tc_sensitivity.csv')

latex_rows = []
for strat in ["1/N", "MinVar", "NominalCVaR", "FiniteRegime", "RobustSIP"]:
    vals = df[df['Strategy'] == strat]['Sharpe'].values
    if strat == "MinVar": name = "TC-MinVar"
    elif strat == "NominalCVaR": name = "Nominal CVaR"
    elif strat == "FiniteRegime": name = "Finite-Regime"
    elif strat == "RobustSIP": name = r"\textbf{Robust SIP}"
    else: name = strat
    
    if strat == "RobustSIP":
        row_str = fr"{name} & \textbf{{{vals[0]:.3f}}} & \textbf{{{vals[1]:.3f}}} & \textbf{{{vals[2]:.3f}}} & \textbf{{{vals[3]:.3f}}} & \textbf{{{vals[4]:.3f}}} \\\\"
    else:
        row_str = fr"{name} & {vals[0]:.3f} & {vals[1]:.3f} & {vals[2]:.3f} & {vals[3]:.3f} & {vals[4]:.3f} \\\\"
    latex_rows.append(row_str)

new_body_sr = "\n".join(latex_rows)

latex_rows_w = []
for strat in ["1/N", "MinVar", "NominalCVaR", "FiniteRegime", "RobustSIP"]:
    vals = df[df['Strategy'] == strat]['Final_Wealth'].values
    if strat == "MinVar": name = "TC-MinVar"
    elif strat == "NominalCVaR": name = "Nominal CVaR"
    elif strat == "FiniteRegime": name = "Finite-Regime"
    elif strat == "RobustSIP": name = r"\textbf{Robust SIP}"
    else: name = strat
    
    if strat == "RobustSIP":
        row_str = fr"{name} & \textbf{{\${vals[0]:.2f}}} & \textbf{{\${vals[1]:.2f}}} & \textbf{{\${vals[2]:.2f}}} & \textbf{{\${vals[3]:.2f}}} & \textbf{{\${vals[4]:.2f}}} \\\\"
    else:
        row_str = fr"{name} & \${vals[0]:.2f} & \${vals[1]:.2f} & \${vals[2]:.2f} & \${vals[3]:.2f} & \${vals[4]:.2f} \\\\"
    latex_rows_w.append(row_str)

new_body_w = "\n".join(latex_rows_w)

with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

# Replace Sharpe Ratio block
pattern_sr = re.compile(r"\\textbf\{Annualized Sharpe Ratio\}.*?(1/N.*?Robust SIP.*?\\\\)", re.DOTALL)
text = pattern_sr.sub(lambda m: r"\textbf{Annualized Sharpe Ratio} & & & & & \\" + "\n" + new_body_sr, text)

# Replace Terminal Wealth block
pattern_w = re.compile(r"\\textbf\{Final Cumulative Wealth.*?1/N.*?Robust SIP.*?\\\\)", re.DOTALL)
text = pattern_w.sub(lambda m: r"\textbf{Final Cumulative Wealth (\$)} & & & & & \\" + "\n" + new_body_w, text)

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
print("Table 6 updated successfully.")
