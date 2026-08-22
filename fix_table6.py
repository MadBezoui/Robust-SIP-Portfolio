with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

import re

# Fix Sharpe ratios for TC-MinVar
old_sharpe = r"TC-MinVar & 0.880 & 0.876 & 0.873 & 0.866 & 0.846 \\"
new_sharpe = r"TC-MinVar & 0.874 & 0.871 & 0.867 & 0.861 & 0.841 \\"
text = text.replace(old_sharpe, new_sharpe)

# Fix Final Wealth for TC-MinVar
old_wealth = r"TC-MinVar & 22.74 & 22.45 & 22.16 & 21.59 & 19.97 \\"
new_wealth = r"TC-MinVar & 22.62 & 22.33 & 22.04 & 21.47 & 19.86 \\"
text = text.replace(old_wealth, new_wealth)

# "at 50 bps, its final wealth of \$21.74 exceeds Nominal CVaR (\$20.26) and TC-MinVar (\$19.97)"
text = text.replace("TC-MinVar (\\$19.97)", "TC-MinVar (\\$19.86)")

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
