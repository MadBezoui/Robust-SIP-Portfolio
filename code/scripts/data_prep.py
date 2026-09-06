import pandas as pd
import numpy as np
import requests
from io import BytesIO, StringIO
import zipfile
import os

# Configuration
kf_url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/30_Industry_Portfolios_daily_CSV.zip"
ff_url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_daily_CSV.zip"
vix_url = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"
data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(data_dir, exist_ok=True)

def extract_kf(url, date_col_name='Date'):
    res = requests.get(url)
    with zipfile.ZipFile(BytesIO(res.content)) as z:
        with z.open(z.namelist()[0]) as f:
            content = f.read().decode('utf-8')
    lines = content.split('\n')
    start_idx = None
    end_idx = None
    # Find header
    for i, line in enumerate(lines):
        if line.strip().startswith(',') and len(line.split(',')) > 2:
            start_idx = i
            break
    for i in range(start_idx + 1, len(lines)):
        if not lines[i].strip():
            end_idx = i
            break
    data_lines = lines[start_idx:end_idx]
    data_lines[0] = date_col_name + data_lines[0]
    df = pd.read_csv(StringIO('\n'.join(data_lines)))
    df[date_col_name] = pd.to_datetime(df[date_col_name].astype(str), format='%Y%m%d')
    df = df.replace([-99.99, -99.9, -999.0], np.nan)
    return df.set_index(date_col_name)

# 1. Download KF 30 Industries
print("Downloading Kenneth French 30 Industry Portfolios...")
df_ind = extract_kf(kf_url)

# 2. Download F-F Factors
print("Downloading Fama-French Factors (RF)...")
df_ff = extract_kf(ff_url)
df_ff = df_ff[['RF']]

# Merge KF and FF
df_kf = df_ind.join(df_ff, how='inner')

# Start before 1990 to allow 63-day drawdown to be fully initialized on Jan 2 1990
# 63 trading days before 1990-01-01 is roughly 3 months, let's start at 1989-09-01
df_kf = df_kf[df_kf.index >= '1989-09-01']
df_kf = df_kf.dropna()

returns_cols = list(df_ind.columns)
for col in returns_cols:
    df_kf[col] = df_kf[col] / 100.0
df_kf['RF'] = df_kf['RF'] / 100.0

# Calculate Market Proxy
df_kf['MarketEWReturn'] = df_kf[returns_cols].mean(axis=1)

# Gross return
df_kf['MarketGrossReturn_EW'] = 1.0 + df_kf['MarketEWReturn']

# Cumulative wealth
wealth = df_kf['MarketGrossReturn_EW'].cumprod()
df_kf['MarketWealthIndex'] = wealth

# Drawdown 63
rolling_max = wealth.rolling(window=63, min_periods=1).max()
df_kf['Rolling63DayPeak'] = rolling_max
df_kf['Drawdown63'] = (1.0 - wealth / rolling_max).clip(lower=0.0)

# 3. Download VIX Data
print("Downloading VIX data from CBOE...")
res_vix = requests.get(vix_url)
df_vix = pd.read_csv(StringIO(res_vix.text))
df_vix['DATE'] = pd.to_datetime(df_vix['DATE'])
df_vix = df_vix.set_index('DATE')
df_vix = df_vix[['CLOSE']].rename(columns={'CLOSE': 'VIXClose'})

# 4. Merge all and filter >= 1990-01-01
df_merged = df_kf.join(df_vix, how='left')
df_merged = df_merged[df_merged.index >= '1990-01-01']

# Forward fill VIX if missing, though it shouldn't be since VIX starts 1990-01-02
df_merged['VIXClose'] = df_merged['VIXClose'].ffill().bfill()
df_merged['logVIX'] = np.log(df_merged['VIXClose'])
df_merged['Full63DayHistoryAvailable'] = True

# Reorder columns as requested
cols = returns_cols + ['MarketEWReturn', 'MarketGrossReturn_EW', 'MarketWealthIndex', 'Rolling63DayPeak', 'Drawdown63', 'VIXClose', 'logVIX', 'RF', 'Full63DayHistoryAvailable']
df_merged = df_merged[cols].rename(columns={'RF': 'RiskFreeReturn'})
df_merged.index.name = 'Date'

# Rename output to match what autoreview asks for
print("Writing data files...")
df_merged.to_csv(os.path.join(data_dir, "processed_state_return_pairs.csv"))

# Write raw market data
df_merged['DataRetrieved'] = pd.Timestamp('today').normalize()
df_merged['SourceVersion'] = "KF_CBOE_2026"
df_merged.to_csv(os.path.join(data_dir, "raw_market_data.csv"))

print(f"Data processing complete. {len(df_merged)} rows generated.")
