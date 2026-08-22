import re

with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

text = re.sub(
    r" Delete this sentence from Section 2\.1\..*?research positioning\.",
    "",
    text,
    flags=re.IGNORECASE | re.DOTALL
)

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
print("Removed Section 2.1 editorial note.")
