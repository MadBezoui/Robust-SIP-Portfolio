with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

# Row 1
text = text.replace("1998-08 (LTCM) & 0.84 & 0.0424 & $3.57\\times10^{-2}$ & $1.56\\times10^{-5}$", "1998-08 (LTCM) & 0.84 & 0.0424 & $3.57\\times10^{-2}$ & $1.6\\times10^{-5}$")
text = text.replace("1998-08 (LTCM) & 0.84 & 0.0424 & $0.0357$ & $1.6\\times10^{-5}$", "1998-08 (LTCM) & 0.84 & 0.0424 & $3.57\\times10^{-2}$ & $1.6\\times10^{-5}$")

# Let's just find the block and rewrite it exactly
block = r"""1998-08 (LTCM) & 0.84 & 0.0424 & 0.0357 & $1.56\times10^{-5}$ \\
2008-10 (Lehman) & 1.79 & 0.0468 & 0.0838 & 0.00 \\
2013-05 (Taper Tantrum) & 0.16 & 0.0608 & 0.0100 & $8.07\times10^{-9}$ \\
2020-03 (COVID-19) & 0.27 & 0.0452 & 0.0121 & $1.90\times10^{-5}$ \\
2022-09 (Inflation Shock) & 0.64 & 0.0671 & 0.0432 & 0.00 \\"""

import re
# I'll just use a general replacement for these 5 lines.
text = re.sub(r"1998-08 \(LTCM\).*?\\\\", r"1998-08 (LTCM) & 0.84 & 0.0424 & $3.57\\times10^{-2}$ & $1.6\\times10^{-5}$ \\\\", text)
text = re.sub(r"2008-10 \(Lehman\).*?\\\\", r"2008-10 (Lehman) & 1.79 & 0.0468 & $8.38\\times10^{-2}$ & $0$ \\\\", text)
text = re.sub(r"2013-05 \(Taper Tantrum\).*?\\\\", r"2013-05 (Taper Tantrum) & 0.16 & 0.0608 & $9.96\\times10^{-3}$ & $8.1\\times10^{-9}$ \\\\", text)
text = re.sub(r"2020-03 \(COVID-19\).*?\\\\", r"2020-03 (COVID-19) & 0.27 & 0.0452 & $1.21\\times10^{-2}$ & $1.9\\times10^{-5}$ \\\\", text)
text = re.sub(r"2022-09 \(Inflation Shock\).*?\\\\", r"2022-09 (Inflation Shock) & 0.64 & 0.0671 & $4.32\\times10^{-2}$ & $0$ \\\\", text)

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
