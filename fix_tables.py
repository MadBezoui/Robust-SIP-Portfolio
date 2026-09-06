import re
import pandas as pd

with open("Soumission/main_paper.tex", "r") as f:
    text = f.read()

def replace_table_7(text):
    # Nominal CVaR
    df = pd.read_csv("results/bootstrap_inference.csv").set_index("Benchmark")
    
    # We will search for the lines starting with Nominal CVaR, 1/N, TC-MinVar, Finite-Regime CVaR
    # inside the table and replace them.
    # Actually, we can just replace the entire block between \midrule and \bottomrule in tab:bootstrap
    match = re.search(r"(\\begin\{table\*\}\[h\].*?\\caption\{Paired circular moving-block bootstrap.*?\\midrule\s*)(.*?)(\\bottomrule)", text, re.DOTALL)
    if match:
        pre = match.group(1)
        post = match.group(3)
        rows = []
        for b in ["NominalCVaR", "1/N", "MinVar", "FiniteRegime"]:
            b_tex = {"NominalCVaR":"Nominal CVaR", "1/N":"1/N", "MinVar":"TC-MinVar", "FiniteRegime":"Finite-Regime CVaR"}[b]
            row = df.loc[b]
            r_str = f"{b_tex} & {row['Sharpe_Diff']:.3f} & {row['Std_Error']:.4f} & [{row['CI_Lower_95']:.3f}, {row['CI_Upper_95']:.3f}] & {row['P_Value']:.3f} \\\\\n"
            rows.append(r_str)
        return text[:match.start()] + pre + "".join(rows) + post + text[match.end():]
    return text

def replace_table_6(text):
    df = pd.read_csv("results/tc_sensitivity.csv")
    match = re.search(r"(\\begin\{table\*\}\[h\].*?\\caption\{Transaction cost sensitivity.*?\\midrule\s*\\textbf\{Annualized Return-to-Volatility Ratio\}.*?\\\\)(.*?)(\\midrule\s*\\textbf\{Final Cumulative Wealth.*?\\\\)(.*?)(\\bottomrule)", text, re.DOTALL)
    if match:
        pre1 = match.group(1) + "\n"
        pre2 = match.group(3) + "\n"
        post = match.group(5)
        
        sr_rows = []
        fw_rows = []
        for b in ["1/N", "MinVar", "NominalCVaR", "FiniteRegime", "RobustSIP"]:
            b_tex = {"NominalCVaR":"Nominal CVaR", "1/N":"1/N", "MinVar":"TC-MinVar", "FiniteRegime":"Finite-Regime CVaR", "RobustSIP":"\\textbf{Robust SIP}"}[b]
            sr_vals = df[df["Strategy"]==b]["Sharpe"].values
            fw_vals = df[df["Strategy"]==b]["Final_Wealth"].values
            sr_str = f"{b_tex} & " + " & ".join([f"{x:.3f}" if b!="RobustSIP" else f"\\textbf{{{x:.3f}}}" for x in sr_vals]) + " \\\\\n"
            fw_str = f"{b_tex} & " + " & ".join([f"{x:.2f}" if b!="RobustSIP" else f"\\textbf{{{x:.2f}}}" for x in fw_vals]) + " \\\\\n"
            sr_rows.append(sr_str)
            fw_rows.append(fw_str)
            
        return text[:match.start()] + pre1 + "".join(sr_rows) + pre2 + "".join(fw_rows) + "\n" + post + text[match.end():]
    return text

def replace_table_2(text):
    df = pd.read_csv("results/performance_table.csv")
    match = re.search(r"(\\begin\{table\*\}\[t\].*?\\caption\{Out-of-sample performance.*?\\midrule\s*)(.*?)(\\bottomrule)", text, re.DOTALL)
    if match:
        pre = match.group(1)
        post = match.group(3)
        rows = []
        for b in ["1_N", "MinVar", "NominalCVaR", "FiniteRegime", "RobustSIP"]:
            b_tex = {"NominalCVaR":"Nominal CVaR", "1_N":"1/N", "MinVar":"TC-MinVar", "FiniteRegime":"Finite-Regime CVaR", "RobustSIP":"Robust SIP"}[b]
            row = df[df["Strategy"]==b].iloc[0]
            r_str = f"{b_tex} & {100*row['Ann_Mean']:.2f}\\% & {100*row['Ann_Vol']:.2f}\\% & {row['Sharpe']:.3f} & {100*row['Max_DD']:.2f}\\% & {100*row['Avg_Turnover']:.2f}\\% \\\\\n"
            rows.append(r_str)
        return text[:match.start()] + pre + "".join(rows) + post + text[match.end():]
    return text

text = replace_table_7(text)
text = replace_table_6(text)
text = replace_table_2(text)

with open("Soumission/main_paper.tex", "w") as f:
    f.write(text)
print("Tables restored!")
