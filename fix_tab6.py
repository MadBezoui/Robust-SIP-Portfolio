import re

with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

# Fix the broken Sharpe Ratio block:
text = text.replace("1/N & 0.721 & 0.720 & 0.720 & 0.719 & 0.715 \\\n", r"1/N & 0.721 & 0.720 & 0.720 & 0.719 & 0.715 \\" + "\n")
text = text.replace("TC-MinVar & 0.872 & 0.869 & 0.866 & 0.859 & 0.839 \\\n", r"TC-MinVar & 0.872 & 0.869 & 0.866 & 0.859 & 0.839 \\" + "\n")
text = text.replace("Nominal CVaR & 0.888 & 0.884 & 0.880 & 0.872 & 0.848 \\\n", r"Nominal CVaR & 0.888 & 0.884 & 0.880 & 0.872 & 0.848 \\" + "\n")
text = text.replace("Finite-Regime & 0.909 & 0.905 & 0.901 & 0.892 & 0.867 \\\n", r"Finite-Regime & 0.909 & 0.905 & 0.901 & 0.892 & 0.867 \\" + "\n")
text = text.replace("\textbf{Robust SIP} & \textbf{0.817} & \textbf{0.813} & \textbf{0.809} & \textbf{0.801} & \textbf{0.777} \\\n", r"\textbf{Robust SIP} & \textbf{0.817} & \textbf{0.813} & \textbf{0.809} & \textbf{0.801} & \textbf{0.777} \\" + "\n")

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
