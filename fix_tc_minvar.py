import re

with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

# Replace TC-MinVar values in prose and Table 4
# Annual mean = 10.73% (from 10.7298%)
# Volatility = 12.32% (from 12.3188%)
# Sharpe = 0.871 (from 0.8710)
# Final Wealth = 22.04 (from 22.0377)

text = text.replace("TC-MinVar & 10.75\\% & 12.32\\% & 0.873", "TC-MinVar & 10.73\\% & 12.32\\% & 0.871")
text = text.replace("TC-MinVar (10.75\%)", "TC-MinVar (10.73\%)")
text = text.replace("TC-MinVar (0.873)", "TC-MinVar (0.871)")
text = text.replace("TC-MinVar (\$22.16)", "TC-MinVar (\$22.04)")

# Table 6 values
text = text.replace("0 bps & 1.010 & 0.876 & 0.902", "0 bps & 1.010 & 0.874 & 0.902")
text = text.replace("5 bps & 0.910 & 0.874 & 0.901", "5 bps & 0.910 & 0.871 & 0.901")
text = text.replace("10 bps & 0.809 & 0.873 & 0.901", "10 bps & 0.809 & 0.867 & 0.901")
text = text.replace("20 bps & 0.608 & 0.867 & 0.899", "20 bps & 0.608 & 0.861 & 0.899")
text = text.replace("50 bps & 0.003 & 0.850 & 0.896", "50 bps & 0.003 & 0.841 & 0.896")

text = text.replace("0 bps & \$29.41 & \$22.75 & \$25.80", "0 bps & \$29.41 & \$22.62 & \$25.80")
text = text.replace("5 bps & \$29.33 & \$22.45 & \$25.74", "5 bps & \$29.33 & \$22.33 & \$25.74")
text = text.replace("10 bps & \$29.25 & \$22.16 & \$25.68", "10 bps & \$29.25 & \$22.04 & \$25.68")
text = text.replace("20 bps & \$29.10 & \$21.58 & \$25.56", "20 bps & \$29.10 & \$21.47 & \$25.56")
text = text.replace("50 bps & \$28.52 & \$19.97 & \$22.52", "50 bps & \$28.52 & \$19.86 & \$22.52")

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
