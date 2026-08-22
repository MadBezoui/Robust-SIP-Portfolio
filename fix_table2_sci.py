import re
with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

def repl(m):
    mantissa = m.group(1)
    exponent = int(m.group(2))
    return f"${mantissa}\\times10^{{{exponent}}}$"

text = re.sub(r"(\d\.\d+)e([+-]\d+)", repl, text)

# Table 2 uses $...$ for some, so replacing might result in $$...$$. Let's clean up.
text = text.replace("$$", "$")

with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
