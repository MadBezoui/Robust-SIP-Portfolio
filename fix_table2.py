import pandas as pd
import re

df = pd.read_csv("results/gap_verification.csv")

with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

for i, row in df.iterrows():
    label = row['Label']
    old_regex = re.compile(re.escape(label) + r" & [\d.]+ & [\d.]+ & [\d.]+ & [\d.eE+-]+")
    new_str = f"{label} & {row['MaxGradNorm']:.2f} & {row['GridDisp']:.4f} & {row['EmpiricalProduct']:.4f} & {row['LocalSearchImp']:.2e}"
    text = old_regex.sub(new_str, text)
    print(f"Replaced {label}")

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
