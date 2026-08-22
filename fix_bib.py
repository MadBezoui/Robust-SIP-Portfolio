with open("submission_CompOptAlg_v2/references.bib", "r") as f:
    text = f.read()

text = text.replace(
    r"title        = {{v1.1.0: Continuous-state robust CVaR portfolio optimization via grid-restricted constraint generation}},",
    r"title        = {{v1.2.0: Continuous-state robust CVaR portfolio optimization via grid-restricted constraint generation}},"
)
text = text.replace(
    r"note         = {Zenodo. \href{https://doi.org/10.5281/zenodo.22050110}{[Zenodo DOI to be generated upon acceptance]}},",
    r"doi          = {10.5281/zenodo.22056130},"
)
text = text.replace(
    r"url          = {https://github.com/MadBezoui/Robust-SIP-Portfolio/releases/tag/v1.1.0}",
    r"url          = {https://github.com/MadBezoui/Robust-SIP-Portfolio/releases/tag/v1.2.0-submission-final}"
)

with open("submission_CompOptAlg_v2/references.bib", "w") as f:
    f.write(text)
