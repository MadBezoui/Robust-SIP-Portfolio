import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Wait for the CSV to exist...
import time, os
while not os.path.exists("results/bootstrap_diffs_for_fig12.csv"):
    time.sleep(1)

df = pd.read_csv("results/bootstrap_diffs_for_fig12.csv")
diffs = df['boot_diffs'].values

plt.figure(figsize=(8, 6))
plt.hist(diffs, bins=50, color='skyblue', edgecolor='black', alpha=0.7)
plt.axvline(x=np.mean(diffs), color='red', linestyle='--', linewidth=2, label=f"Mean $\Delta SR$ = {np.mean(diffs):.4f}")
plt.title("Studentized bootstrap distribution of Sharpe ratio difference")
plt.xlabel("$\Delta SR$ (Robust SIP - Nominal CVaR)")
plt.ylabel("Frequency")
plt.legend()
plt.tight_layout()
plt.savefig("submission_CompOptAlg_v2/Fig12.pdf")
