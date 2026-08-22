import re

with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

# Remove the specific sentence about initial master solve
pattern = r" The manuscript and\s*repository should define explicitly whether the initial master solve is\s*counted as an exchange iteration\.\."
text = re.sub(pattern, "", text)

# Let's also fix "an five active state blocks" to "five active state blocks"
text = text.replace("an five active state blocks", "five active state blocks")

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
