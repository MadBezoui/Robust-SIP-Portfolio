import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# read daily returns and state variables
# The julia script created "strategy_daily_returns.csv"
# and we can merge it with "data/processed_state_return_pairs.csv"
df_rets = pd.read_csv("results/strategy_daily_returns.csv")
df_state = pd.read_csv("data/processed_state_return_pairs.csv")[['Date', 'logVIX', 'Drawdown63']]

df = pd.merge(df_rets, df_state, on="Date")

# Calculate ES95 (Conditional Value-at-Risk at 5%)
def es95(returns):
    if len(returns) == 0: return np.nan
    q = np.percentile(returns, 5)
    return -np.mean(returns[returns <= q])

# Quintiles
df['VIX_Group'] = pd.qcut(df['logVIX'], 5, labels=['Q1 (Low)', 'Q2', 'Q3', 'Q4', 'Q5 (High)'])
df['DD_Group'] = pd.qcut(df['Drawdown63'], 5, labels=['Q1 (Low DD)', 'Q2', 'Q3', 'Q4', 'Q5 (High DD)'])
# wait, drawdown is typically positive or negative?
# in the julia code, "df_state.Drawdown63 .> 0.20" implies it's positive.
# if it's positive, high DD means deep drawdown.
# let's just use 1 to 5.

vix_labels = ['Q5 (High)', 'Q4', 'Q3', 'Q2', 'Q1 (Low)'] # descending VIX for rows
dd_labels = ['Q1 (Low)', 'Q2', 'Q3', 'Q4', 'Q5 (High)']

results = np.zeros((5, 5))

for i, v in enumerate(vix_labels):
    for j, d in enumerate(dd_labels):
        subset = df[(df['VIX_Group'].astype(str).str.contains(v[:2])) & (df['DD_Group'].astype(str).str.contains(d[:2]))]
        if len(subset) > 0:
            es_rob = es95(subset['RobustSIP'])
            es_nom = es95(subset['NominalCVaR'])
            results[i, j] = (es_rob - es_nom) * 100 # % points
        else:
            results[i, j] = np.nan

# Check for all NaNs
if np.isnan(results).all():
    print("All NaNs!")

fig, ax = plt.subplots(figsize=(5, 4))
vmax = np.nanmax(np.abs(results))
if np.isnan(vmax): vmax = 1.0

# Diverging colormap, positive is bad (red) since Robust SIP has higher losses
c = ax.imshow(results, cmap='RdYlGn_r', aspect='auto', vmin=-vmax, vmax=vmax)
ax.set_xticks(np.arange(len(dd_labels)))
ax.set_yticks(np.arange(len(vix_labels)))
ax.set_xticklabels(dd_labels)
ax.set_yticklabels(vix_labels)
ax.set_xlabel('Drawdown Quintile')
ax.set_ylabel('VIX Quintile')
ax.set_title('Robust SIP $\mathrm{ES}_{95}$ - Nominal CVaR $\mathrm{ES}_{95}$ (% pts)')

for i in range(len(vix_labels)):
    for j in range(len(dd_labels)):
        val = results[i, j]
        if not np.isnan(val):
            color = "white" if abs(val) > 0.4*vmax else "black"
            ax.text(j, i, f"{val:+.2f}", ha="center", va="center", color=color, fontsize=8)

fig.colorbar(c, ax=ax)
plt.tight_layout()
plt.savefig("Soumission/Fig16.pdf", format='pdf')
plt.close()
