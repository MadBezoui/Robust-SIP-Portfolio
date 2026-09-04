import pandas as pd
import os

if os.path.exists('results/performance_table.csv') and os.path.exists('results/active_states_history.csv'):
    df_perf = pd.read_csv('results/performance_table.csv')
    rob_row = df_perf[df_perf['Strategy'] == 'RobustSIP'].iloc[0]
    
    df_active = pd.read_csv('results/active_states_history.csv')
    avg_ess = df_active['Avg_Active_State_ESS'].mean()
    min_ess = df_active['Avg_Active_State_ESS'].min()
    
    df_new = pd.DataFrame([{
        'ESS_Min': 0.0,
        'Ann_Return_Decimal': rob_row['Ann_Mean'],
        'Ann_Vol_Decimal': rob_row['Ann_Vol'],
        'Sharpe': rob_row['Sharpe'],
        'Max_DD_Decimal': rob_row['Max_DD'],
        'Wealth': rob_row['Final_Wealth'],
        'Turnover_Decimal': rob_row['Avg_Turnover'],
        'Avg_ESS': avg_ess,
        'Min_ESS': min_ess,
        'Retained_Frac_Decimal': 1.0
    }])
    
    if os.path.exists('results/ess_full_backtest.csv'):
        df_old = pd.read_csv('results/ess_full_backtest.csv')
        # Remove old 0.0 if present
        df_old = df_old[df_old['ESS_Min'] != 0.0]
        df_final = pd.concat([df_new, df_old]).sort_values(by='ESS_Min')
    else:
        df_final = df_new
        
    df_final.to_csv('results/ess_full_backtest.csv', index=False)
    print("Built cached ess_full_backtest.csv with E_min = 0.0 aligned perfectly with performance_table.csv")
