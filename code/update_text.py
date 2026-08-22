import pandas as pd
import re

tex_path = "submission_CompOptAlg_v2/main_paper.tex"
with open(tex_path, "r") as f:
    text = f.read()

df_grid = pd.read_csv("results/grid_comparison.csv")
ad_row = df_grid[df_grid['Method'].str.contains('Adaptive')].iloc[0]
d21_row = df_grid[df_grid['Method'].str.contains('21x21') & ~df_grid['Method'].str.contains('Adaptive')].iloc[0]

t_ad = ad_row['Runtime_sec']
t_d21 = d21_row['Runtime_sec']
act = ad_row['Active_States']
ratio = t_d21 / t_ad

# 71.43 seconds
text = re.sub(r"from \d+\.\d+ seconds for the dense", f"from {t_d21:.2f} seconds for the dense", text)
# 3.45 seconds
text = re.sub(r"to \d+\.\d+ seconds for the adaptive", f"to {t_ad:.2f} seconds for the adaptive", text)
# ratio 20.7
text = re.sub(r"ratio of approximately \d+\.\d+", f"ratio of approximately {ratio:.1f}", text)
# 3.66 active
text = re.sub(r"average of \d+\.\d+ active state blocks", f"average of {act:.2f} active state blocks", text)

with open(tex_path, "w") as f:
    f.write(text)
