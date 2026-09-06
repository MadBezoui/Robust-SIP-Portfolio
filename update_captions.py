import re

with open("Soumission/main_paper.tex", "r") as f:
    text = f.read()

# Replace Fig 3 caption
old_cap3 = r"\caption{Time-varying sector allocations for the Robust SIP strategy. The vertical width of each colored band represents the fractional weight assigned to the corresponding industry portfolio.}"
new_cap3 = r"\caption{Effective Number of Assets (ENA) over time for the Robust SIP strategy. ENA is calculated as the inverse of the Herfindahl-Hirschman Index of portfolio weights.}"
text = text.replace(old_cap3, new_cap3)

# Replace Fig 4 caption
old_cap4 = r"\caption{Time-varying sector allocations for the TC-MinVar strategy. The vertical width of each colored band represents the fractional weight assigned to the corresponding industry portfolio.}"
new_cap4 = r"\caption{Effective Number of Assets (ENA) over time for the TC-MinVar strategy. ENA is calculated as the inverse of the Herfindahl-Hirschman Index of portfolio weights.}"
text = text.replace(old_cap4, new_cap4)

# Replace Fig 11 text
old_cap11 = r"\caption{Convergence of the adaptive constraint-generation algorithm on a representative rolling window. The lower bound $\mathrm{LB}_k$ converges to the worst-case objective $\widehat{G}_k$ evaluated on the $21\times 21$ separation grid.}"
new_cap11 = r"\caption{Convergence of the adaptive constraint-generation algorithm on a representative rolling window. The top panel shows the lower bound $\mathrm{LB}_k$ and the worst-case objective $\widehat{G}_k$ on the $21\times 21$ separation grid. The bottom panel shows the optimality gap on a logarithmic scale.}"
text = text.replace(old_cap11, new_cap11)

with open("Soumission/main_paper.tex", "w") as f:
    f.write(text)
