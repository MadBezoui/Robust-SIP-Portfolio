with open("submission_CompOptAlg_v2/main_paper.tex", "r") as f:
    text = f.read()

text = text.replace(r"L_{\Phi,k}\rho_k.", r"L_{\Phi,k}\rho_k")
text = text.replace(r"L_\Phi \rho.", r"L_\Phi \rho")

# Wait, let's just make sure there are no `\].` anymore?
text = text.replace(r"\].", r"\]")
text = text.replace(r"\]", r"\]")

# I need to add punctuation INSIDE the equation if the user wants it inside the equation.
# e.g. L_\Phi \rho. \]
text = text.replace(r"L_\Phi \rho \] \n\nWhere", r"L_\Phi \rho. \] \n\nWhere") # wait no, I already replaced \]\n\nWhere.

import re
# I'll just restore the original state for equations and put the punctuation at the end of the line.
