with open("Soumission/main_paper.tex", "r") as f:
    text = f.read()

# Fix the trailing single backslashes in table rows for MinVar, Nominal CVaR, Finite-Regime CVaR, Robust SIP
lines = text.split("\n")
for i, line in enumerate(lines):
    if (line.startswith("TC-MinVar &") or line.startswith("Nominal CVaR &") or 
        line.startswith("Finite-Regime CVaR &") or line.startswith("Robust SIP &")) and line.endswith(" \\"):
        lines[i] = line + "\\"

with open("Soumission/main_paper.tex", "w") as f:
    f.write("\n".join(lines))
