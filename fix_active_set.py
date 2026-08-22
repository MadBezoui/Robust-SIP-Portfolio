import re
with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

text = text.replace(r"\widehat{\mathcal{U}}_k", r"\mathcal{A}_k")
text = text.replace(r"\widehat{\mathcal{U}}_{k+1}", r"\mathcal{A}_{k+1}")
text = text.replace(r"\widehat{\mathcal{U}}_1", r"\mathcal{A}_1")
text = text.replace(r"\widehat{\mathcal{U}}^*", r"\mathcal{A}^*")

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
