import pandas as pd
import numpy as np

perf = pd.read_csv("results/performance_table.csv")
cal = pd.read_csv("results/calendar.csv")

# We need the risk free return per 21-day holding period.
df_state = pd.read_csv("data/processed_state_return_pairs.csv")
# Convert Date to string
df_state['Date'] = df_state['Date'].astype(str)
cal['Hold_Start_Date'] = cal['Hold_Start_Date'].astype(str)
cal['Hold_End_Date'] = cal['Hold_End_Date'].astype(str)

rf_holding = []
for idx, row in cal.iterrows():
    start = row['Hold_Start_Date']
    end = row['Hold_End_Date']
    mask = (df_state['Date'] >= start) & (df_state['Date'] <= end)
    rf_daily = df_state.loc[mask, 'RiskFreeReturn']
    rf_compounded = np.prod(1.0 + rf_daily) - 1.0
    rf_holding.append(rf_compounded)

rf_holding = np.array(rf_holding)
mean_rf_ann = np.mean(rf_holding) * 12.0

for i, row in perf.iterrows():
    strat = row['Strategy']
    if strat == '1/N': strat_safe = '1N'
    else: strat_safe = strat
    strat_perf = pd.read_csv(f"results/perf_{strat_safe}.csv")
    ret = strat_perf['Return'].values
    
    # subtract rf
    excess_ret = ret - rf_holding
    ann_excess_mean = np.mean(excess_ret) * 12.0
    ann_vol = np.std(ret) * np.sqrt(12.0)
    
    genuine_sharpe = ann_excess_mean / ann_vol
    perf.loc[i, 'Sharpe'] = genuine_sharpe

print("New Genuine Sharpe Ratios:")
print(perf[['Strategy', 'Sharpe']])

perf.to_csv("results/performance_table.csv", index=False)
