import re

with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

# Replace "\] with" -> "\].\n\nWith"
text = re.sub(r"\\\]\s+with\b", r"\\].\n\nWith", text)
text = re.sub(r"\\\]\s+where\b", r"\\].\n\nWhere", text)
text = re.sub(r"\\\]\s+We state\b", r"\\].\n\nWe state", text)

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
