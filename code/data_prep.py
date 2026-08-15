import pandas as pd
import numpy as np
import requests
from io import BytesIO, StringIO
import zipfile
import os

# Configuration
kf_url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/30_Industry_Portfolios_daily_CSV.zip"
vix_url = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"
data_dir = "../data"
os.makedirs(data_dir, exist_ok=True)

# 1. Download Kenneth French Data
print("Downloading Kenneth French 30 Industry Portfolios...")
res = requests.get(kf_url)
with zipfile.ZipFile(BytesIO(res.content)) as z:
    with z.open(z.namelist()[0]) as f:
        content = f.read().decode('utf-8')

# The file contains a lot of metadata. Extract daily return table.
lines = content.split('\n')
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if line.startswith(','):
        if "Food" in line or "Smoke" in line: # Industry header
            start_idx = i
            break

for i in range(start_idx + 1, len(lines)):
    if not lines[i].strip():
        end_idx = i
        break

data_lines = lines[start_idx:end_idx]
data_lines[0] = "Date" + data_lines[0]
df_kf = pd.read_csv(StringIO('\n'.join(data_lines)))

df_kf['Date'] = pd.to_datetime(df_kf['Date'].astype(str), format='%Y%m%d')
# Convert missing codes (-99.99, -99.9, -999) to NaN
df_kf = df_kf.replace([-99.99, -99.9, -999.0], np.nan)
df_kf = df_kf.set_index('Date')

# 2. Download VIX Data
print("Downloading VIX data from CBOE...")
res_vix = requests.get(vix_url)
df_vix = pd.read_csv(StringIO(res_vix.text))
df_vix['DATE'] = pd.to_datetime(df_vix['DATE'])
df_vix = df_vix.set_index('DATE')
df_vix = df_vix[['CLOSE']].rename(columns={'CLOSE': 'VIX'})

# 3. Merge Datasets
print("Merging datasets...")
df_merged = df_kf.join(df_vix, how='inner')

# Filter for the required start date (1990-01-02 onwards)
df_merged = df_merged[df_merged.index >= '1990-01-01']

# Fill NAs with forward fill then drop any remaining
df_merged = df_merged.ffill().dropna()

# Convert percentage returns to decimals
returns_cols = [c for c in df_merged.columns if c != 'VIX']
for col in returns_cols:
    df_merged[col] = df_merged[col] / 100.0

# Calculate equal-weighted 30-industry market return proxy
df_merged['MarketReturn'] = df_merged[returns_cols].mean(axis=1)

# Calculate cumulative wealth and positive 63-day trailing Drawdown: D_t = 1 - P_t / max_{s in [t-63, t]} P_s in [0, 1]
wealth = (1.0 + df_merged['MarketReturn']).cumprod()
rolling_max = wealth.rolling(window=63, min_periods=1).max()
df_merged['Drawdown'] = 1.0 - (wealth / rolling_max)
# Ensure strictly non-negative numerical precision
df_merged['Drawdown'] = df_merged['Drawdown'].clip(lower=0.0)

# Calculate log(VIX)
df_merged['logVIX'] = np.log(df_merged['VIX'])

# Output to CSV
out_path = os.path.join(data_dir, "aligned_market_data.csv")
print(f"Writing final aligned data to {out_path}...")
df_merged.to_csv(out_path)
print(f"Data processing complete. {len(df_merged)} rows generated.")
