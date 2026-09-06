import re

with open("Soumission/main_paper.tex", "r") as f:
    text = f.read()

# Replace the Sharpe Ratio row in Table 4
# Original: \textbf{Annualized Sharpe Ratio} & 0.720 & 0.873 & 0.880 & 0.901 & \textbf{0.809} \\
old_row = r"\\textbf\{Annualized Sharpe Ratio\} & 0.720 & 0.873 & 0.880 & 0.901 & \\textbf\{0.809\} \\\\"
new_row = r"\\textbf{Annualized Sharpe Ratio (Excess)} & 0.578 & 0.674 & 0.683 & 0.706 & \textbf{0.636} \\\\"

text = re.sub(old_row, new_row, text)

# I should also patch Table 4 so it has the right wording
with open("Soumission/main_paper.tex", "w") as f:
    f.write(text)
