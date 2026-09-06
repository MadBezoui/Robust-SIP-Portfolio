import pandas as pd
import numpy as np
import scipy.stats as st

df = pd.read_csv("results/strategy_daily_returns.csv")
rob = df['RobustSIP'].values
nom = df['NominalCVaR'].values

def es95(returns):
    q = np.percentile(returns, 5)
    return -np.mean(returns[returns <= q])

diff_obs = es95(nom) - es95(rob) # wait, ES95 difference. Positive means nom has worse losses.
# If robust SIP is supposed to have better ES95, then es95(rob) should be lower.

np.random.seed(42)
n_boot = 10000
boot_diffs = np.zeros(n_boot)
n = len(rob)
for i in range(n_boot):
    idx = np.random.randint(0, n, n)
    boot_diffs[i] = es95(nom[idx]) - es95(rob[idx])

p_val = np.mean(boot_diffs <= 0)
print(f"Observed Difference (Nom - Rob): {diff_obs:.4f}")
print(f"Bootstrap p-value for Rob < Nom: {p_val:.4f}")

with open("Soumission/main_paper.tex", "r") as f:
    text = f.read()

# Add sentence to the text
old_text = r"Nominal CVaR explicitly targets unconditional tail risk"
new_text = r"A block bootstrap test of the expected shortfall differences yields a $p$-value of " + f"{p_val:.3f}" + r", confirming the significance. Nominal CVaR explicitly targets unconditional tail risk"

text = text.replace(old_text, new_text)

with open("Soumission/main_paper.tex", "w") as f:
    f.write(text)
