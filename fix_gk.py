with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()
import re
text = re.sub(r"\\le\s*L_\{\\Phi,k\}\\rho_k\.\n\\\]\.", r"\\le L_{\\Phi,k}\\rho_k.\n\\]", text)
with open("submission_CompOptAlg_v2/main_paper.tex", "w") as f:
    f.write(text)
