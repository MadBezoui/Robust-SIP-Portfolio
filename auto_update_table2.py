import pandas as pd
import re

df = pd.read_csv("results/gap_verification.csv")

with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

def fmt_sci(val):
    if val == 0:
        return "$0$"
    s = f"{val:.2e}"
    base, exp = s.split('e')
    exp = int(exp)
    return f"${base}\\times10^{{{exp}}}$"

for _, row in df.iterrows():
    label = row['Label']
    maxgrad = f"{row['MaxGradNorm']:.2f}"
    griddisp = f"{row['GridDisp']:.4f}"
    empprod = fmt_sci(row['EmpiricalProduct'])
    localimp = fmt_sci(row['LocalSearchImp'])

    # Find the row in latex starting with the label
    prefix = label
    if "(" in prefix:
        prefix = prefix.split("(")[0].strip() # like 1998-08

    # We reconstruct the line
    new_line = f"{label} & {maxgrad} & {griddisp} & {empprod} & {localimp} \\\\"
    
    # Let's just do a plain string replacement because regex is tricky
    # We will search for prefix and replace the entire line
    lines = text.split("\n")
    for i in range(len(lines)):
        if lines[i].startswith(prefix):
            lines[i] = new_line
            break
    text = "\n".join(lines)

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)

